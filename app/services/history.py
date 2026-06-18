import os
import json
import time
from github import Github
import google.generativeai as genai
from app.services.chroma import learn_convention
from app.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Store the tracking file in the root of the Docker container
TRACKING_FILE = "processed_repos.json"

def has_been_processed(repo_name: str) -> bool:
    """Checks if the Owner/Repo_Name has already had its history analyzed."""
    if not os.path.exists(TRACKING_FILE):
        return False
    with open(TRACKING_FILE, "r") as f:
        return repo_name in json.load(f)

def mark_as_processed(repo_name: str):
    """Flags the Owner/Repo_Name as complete to ensure idempotency."""
    processed = []
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, "r") as f:
            processed = json.load(f)
            
    if repo_name not in processed:
        processed.append(repo_name)
        with open(TRACKING_FILE, "w") as f:
            json.dump(processed, f)

def extract_rules_from_history_task(repo_name: str):
    """BACKGROUND TASK: Scrapes merged PRs, extracts rules, and saves them.
    
    This runs asynchronously and will not block the main FastAPI thread.
    
    Args:
        repo_name: Repository name in format "owner/repo"
    """
    if has_been_processed(repo_name):
        logger.debug(
            "Repository history already processed, skipping",
            extra={"repo_name": repo_name}
        )
        return  # Silently exit if we already learned this repo's history

    logger.info(
        "Background task started: Analyzing PR history",
        extra={
            "repo_name": repo_name,
            "task": "history_analysis"
        }
    )
    
    start_time = time.time()
    
    gh = Github(GITHUB_TOKEN)
    genai.configure(api_key=GEMINI_API_KEY)
    llm = genai.GenerativeModel('gemini-2.5-flash')

    try:
        # repo_name is guaranteed to be "Owner/Repo_Name"
        repo = gh.get_repo(repo_name)
        pulls = repo.get_pulls(state='closed', sort='updated', direction='desc')
        
        logger.debug(
            "Fetching merged PRs for history analysis",
            extra={"repo_name": repo_name, "pr_limit": 10}
        )
        
        raw_comments = []
        pr_count = 0
        
        for pr in pulls[:10]:  # Look at the 10 most recent PRs
            if pr.merged:
                pr_count += 1
                for comment in pr.get_review_comments():
                    raw_comments.append(comment.body)
        
        logger.debug(
            "PR history fetched",
            extra={
                "repo_name": repo_name,
                "prs_analyzed": pr_count,
                "comments_found": len(raw_comments)
            }
        )
                    
        if not raw_comments:
            logger.info(
                "No historical review comments found",
                extra={
                    "repo_name": repo_name,
                    "prs_checked": pr_count
                }
            )
            mark_as_processed(repo_name)
            return

        # Use Gemini to extract rules
        logger.debug(
            "Extracting coding rules using Gemini AI",
            extra={
                "repo_name": repo_name,
                "comment_count": len(raw_comments)
            }
        )
        
        prompt = f"""
        Analyze these code review comments from our team. 
        Extract the 3 most important, generalized coding conventions or "house rules" being enforced.
        Format strictly as a bulleted list of actionable rules without markdown blocks.
        
        Comments:
        {raw_comments}
        """
        
        response = llm.generate_content(prompt)
        rules = [r.replace("*", "").replace("-", "").strip() for r in response.text.strip().split('\n') if r.strip()]
        
        # Save to Pinecone / ChromaDB
        logger.debug(
            "Saving extracted rules to vector store",
            extra={
                "repo_name": repo_name,
                "rule_count": len(rules)
            }
        )
        
        for rule in rules:
            if rule:
                learn_convention(rule, repo_name)
                
        mark_as_processed(repo_name)
        
        duration_sec = int(time.time() - start_time)
        
        logger.info(
            "Background task complete: Rules extracted and saved",
            extra={
                "repo_name": repo_name,
                "prs_analyzed": pr_count,
                "comments_analyzed": len(raw_comments),
                "rules_extracted": len(rules),
                "duration_sec": duration_sec
            }
        )

    except Exception as e:
        duration_sec = int(time.time() - start_time)
        
        logger.error(
            "Failed to extract history",
            exc_info=True,
            extra={
                "repo_name": repo_name,
                "duration_sec": duration_sec,
                "error_type": type(e).__name__
            }
        )