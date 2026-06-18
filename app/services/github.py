# app/services/github.py
import os
import requests
from github import Github, GithubException
from fastapi import HTTPException
from app.models import PRReviewResult
from app.utils.diff_parser import annotate_diff
from app.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Map file extensions and special filenames to markdown language identifiers.
_EXT_TO_LANG = {
    ".py":    "python",
    ".js":    "javascript",
    ".jsx":   "jsx",
    ".ts":    "typescript",
    ".tsx":   "tsx",
    ".java":  "java",
    ".kt":    "kotlin",
    ".rb":    "ruby",
    ".rs":    "rust",
    ".go":    "go",
    ".c":     "c",
    ".cpp":   "cpp",
    ".cs":    "csharp",
    ".php":   "php",
    ".swift": "swift",
    ".sh":    "bash",
    ".bash":  "bash",
    ".zsh":   "bash",
    ".yaml":  "yaml",
    ".yml":   "yaml",
    ".json":  "json",
    ".toml":  "toml",
    ".html":  "html",
    ".css":   "css",
    ".scss":  "scss",
    ".sql":   "sql",
    ".md":    "markdown",
    ".tf":    "hcl",
    ".r":     "r",
}
_FILENAME_TO_LANG = {
    "dockerfile":        "dockerfile",
    "makefile":          "makefile",
    ".env":              "bash",
    ".gitignore":        "bash",
    "docker-compose.yml": "yaml",
}

def get_language_from_filename(file_path: str) -> str:
    """Return the markdown code-fence language identifier for a given file path.

    Falls back to the bare extension (without the dot) for unknown types so that
    the code block is at least annotated, or to an empty string if no extension
    is present.
    """
    basename = os.path.basename(file_path).lower()
    if basename in _FILENAME_TO_LANG:
        return _FILENAME_TO_LANG[basename]
    _, ext = os.path.splitext(basename)
    if ext in _EXT_TO_LANG:
        return _EXT_TO_LANG[ext]
    # Unknown extension: strip the leading dot and use it as-is (e.g. ".rb" -> "rb")
    return ext.lstrip(".") if ext else ""

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    logger.warning("GITHUB_TOKEN environment variable is not set")

gh = Github(GITHUB_TOKEN)

def get_pr_diff(repo_name: str, pr_number: int) -> str:
    """Fetch and annotate the diff for a pull request.
    
    Args:
        repo_name: Repository name in format "owner/repo"
        pr_number: Pull request number
        
    Returns:
        Annotated diff with line numbers
        
    Raises:
        HTTPException: If PR not found or diff fetch fails
    """
    logger.info(
        "Fetching PR diff",
        extra={
            "repo_name": repo_name,
            "pr_number": pr_number
        }
    )
    
    try:
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        diff_url = pr.diff_url
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        
        logger.debug(
            "Requesting diff from GitHub",
            extra={"diff_url": diff_url}
        )
        
        response = requests.get(diff_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logger.error(
                "Failed to fetch diff from GitHub",
                extra={
                    "status_code": response.status_code,
                    "repo_name": repo_name,
                    "pr_number": pr_number
                }
            )
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to fetch diff. Status code: {response.status_code}"
            )
            
        raw_diff = response.text
        annotated = annotate_diff(raw_diff)
        
        logger.info(
            "PR diff fetched successfully",
            extra={
                "repo_name": repo_name,
                "pr_number": pr_number,
                "diff_size": len(raw_diff),
                "annotated_size": len(annotated)
            }
        )
        
        return annotated

    except GithubException as e:
        logger.error(
            "GitHub API error while fetching PR",
            exc_info=True,
            extra={
                "repo_name": repo_name,
                "pr_number": pr_number,
                "github_status": e.status
            }
        )
        if e.status == 404:
            raise HTTPException(status_code=404, detail="Repo/PR not found.")
        raise HTTPException(status_code=e.status, detail=str(e))

def post_pr_review(repo_name: str, pr_number: int, review_data: PRReviewResult):
    """Post review summary and inline comments to a GitHub PR.
    
    Args:
        repo_name: Repository name in format "owner/repo"
        pr_number: Pull request number
        review_data: Review result containing summary and comments
        
    Raises:
        HTTPException: If posting review fails
    """
    logger.info(
        "Posting PR review to GitHub",
        extra={
            "repo_name": repo_name,
            "pr_number": pr_number,
            "risk_score": review_data.risk_score,
            "merge_decision": review_data.merge_decision,
            "comment_count": len(review_data.comments)
        }
    )
    
    try:
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # Post the top-of-PR summary markdown
        summary_body = (
            f"### 🤖 AI Review Summary\n"
            f"**Risk Score:** {review_data.risk_score}/10\n"
            f"**Decision:** `{review_data.merge_decision}`\n\n"
            f"**Analysis:** {review_data.risk_summary}"
        )
        pr.create_issue_comment(summary_body)
        
        logger.debug(
            "Posted summary comment to PR",
            extra={
                "repo_name": repo_name,
                "pr_number": pr_number
            }
        )
        
        # Pull latest commit object for comment pinning (safer list extraction)
        commits = list(pr.get_commits())
        latest_commit = commits[-1]
        
        inline_success = 0
        inline_failures = 0
        
        for comment in review_data.comments:
            body = (
                f"**[{comment.severity.upper()}]** {comment.summary}\n\n"
                f"**Why it matters:** {comment.explanation}\n\n"
                f"**Suggested Fix:**\n```{get_language_from_filename(comment.file_path)}\n{comment.suggested_fix}\n```"
            )
            try:
                pr.create_review_comment(
                    body=body,
                    commit=latest_commit,
                    path=comment.file_path,
                    line=comment.line_number
                )
                inline_success += 1
                
                logger.debug(
                    "Posted inline comment",
                    extra={
                        "file_path": comment.file_path,
                        "line_number": comment.line_number,
                        "severity": comment.severity
                    }
                )
                
            except Exception as inline_err:
                inline_failures += 1
                
                logger.error(
                    "Failed to post inline comment, using fallback",
                    exc_info=True,
                    extra={
                        "repo_name": repo_name,
                        "pr_number": pr_number,
                        "file_path": comment.file_path,
                        "line_number": comment.line_number,
                        "error": str(inline_err)
                    }
                )
                
                # Graceful fallback to general issue comment if line matching fails
                pr.create_issue_comment(
                    f"*(Line review fallback for {comment.file_path}:{comment.line_number})*\n" + body
                )
        
        logger.info(
            "PR review posted successfully",
            extra={
                "repo_name": repo_name,
                "pr_number": pr_number,
                "inline_comments_posted": inline_success,
                "inline_comments_failed": inline_failures
            }
        )

    except GithubException as e:
        logger.error(
            "GitHub API error while posting review",
            exc_info=True,
            extra={
                "repo_name": repo_name,
                "pr_number": pr_number,
                "github_status": e.status
            }
        )
        raise HTTPException(status_code=e.status, detail=f"Failed to post review: {str(e)}")
