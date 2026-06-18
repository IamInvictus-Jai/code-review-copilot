from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Header
from pydantic import BaseModel, Field
from app.services.github import get_pr_diff, post_pr_review
from app.services.reviewer import analyze_pr_diff
from app.services.chroma import learn_convention, retrieve_relevant_rules
from app.services.history import extract_rules_from_history_task
from app.middleware import setup_exception_handlers, LoggingMiddleware
from app.logging import get_logger
from app.logging.context import set_repo_name, set_pr_number
import hmac
import hashlib
import os
import json
from json import JSONDecodeError

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(title="Code Review Copilot")

# Add logging middleware (must be added before exception handlers)
app.add_middleware(LoggingMiddleware)

# Setup global exception handlers
setup_exception_handlers(app)

# Load configuration
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

logger.info(
    "Application startup",
    extra={
        "app_name": "Code Review Copilot",
        "webhook_configured": bool(WEBHOOK_SECRET)
    }
)

def verify_github_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verifies the HMAC SHA256 signature from GitHub."""
    if not signature_header or not WEBHOOK_SECRET:
        logger.warning(
            "GitHub signature verification failed",
            extra={
                "has_signature": bool(signature_header),
                "has_secret": bool(WEBHOOK_SECRET)
            }
        )
        return False
        
    # Hash the raw payload using your secret
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'), 
        msg=payload_body, 
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    # Use hmac.compare_digest to prevent timing attacks
    is_valid = hmac.compare_digest(expected_signature, signature_header)
    
    if is_valid:
        logger.debug("GitHub signature verified successfully")
    else:
        logger.warning("GitHub signature mismatch")
    
    return is_valid

# --- DATA MODELS ---
class ManualReviewRequest(BaseModel):
    repo_name: str = Field(min_length=1, examples=["Owner/Repository"])
    pr_number: int = Field(gt=0)

class ConventionRequest(BaseModel):
    repo_name: str = Field(min_length=1, examples=["Owner/Repository"])
    rule: str = Field(min_length=1)

# --- ENDPOINTS ---
@app.post("/conventions/learn")
async def add_house_rule(request: ConventionRequest):
    """Endpoint to teach the Copilot a new house rule."""
    logger.info(
        "Learning new house rule",
        extra={
            "repo_name": request.repo_name,
            "rule_length": len(request.rule)
        }
    )
    
    # Set context for subsequent logs
    set_repo_name(request.repo_name)
    
    learn_convention(request.rule, request.repo_name)
    
    logger.info(
        "House rule learned successfully",
        extra={"repo_name": request.repo_name}
    )
    
    return {
        "status": "success",
        "repo_name": request.repo_name,
        "message": f"Learned new rule: {request.rule}",
    }

@app.post("/review/manual")
async def manual_review(request: ManualReviewRequest):
    """Manual endpoint for testing PRs."""
    logger.info(
        "Manual review requested",
        extra={
            "repo_name": request.repo_name,
            "pr_number": request.pr_number
        }
    )
    
    # Set context for subsequent logs
    set_repo_name(request.repo_name)
    set_pr_number(request.pr_number)
    
    # Fetch PR diff
    diff = get_pr_diff(request.repo_name, request.pr_number)
    logger.debug("PR diff fetched", extra={"diff_length": len(diff)})
    
    # Query ChromaDB for rules related to this specific code diff
    house_rules = retrieve_relevant_rules(diff, request.repo_name)
    
    # Pass the targeted rules into the Gemini reasoning engine
    review_result = analyze_pr_diff(diff, house_rules=house_rules)
    
    # Post review to GitHub
    post_pr_review(request.repo_name, request.pr_number, review_result)
    
    logger.info(
        "Manual review completed",
        extra={
            "risk_score": review_result.risk_score,
            "merge_decision": review_result.merge_decision,
            "comment_count": len(review_result.comments)
        }
    )
    
    return {
        "status": "success",
        "applied_rules": house_rules,
        "summary": review_result.risk_summary
    }

@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks, x_hub_signature_256: str = Header(None)):
    """Receives GitHub webhooks and coordinates the AI review."""
    
    payload_body = await request.body()

    # Verify webhook signature
    if not verify_github_signature(payload_body, x_hub_signature_256):
        logger.error("Webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid signature. Unauthorized webhook.")

    # Parse payload
    try:
        payload = json.loads(payload_body)
    except JSONDecodeError as e:
        logger.error(
            "Failed to parse webhook payload",
            exc_info=True,
            extra={"payload_preview": str(payload_body[:200])}
        )
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    action = payload.get("action")
    repo_name = payload.get("repository", {}).get("full_name")
    
    logger.info(
        "GitHub webhook received",
        extra={
            "action": action,
            "repo_name": repo_name
        }
    )
    
    if not repo_name:
        logger.error("Repository full_name missing from webhook payload")
        raise HTTPException(status_code=400, detail="Repository full_name missing from payload")

    # Only process newly opened or synchronized (updated) PRs
    if action not in ["opened", "synchronize"]:
        logger.info(
            "Webhook action ignored",
            extra={"action": action, "reason": "not reviewable"}
        )
        return {"status": "ignored", "reason": f"Action '{action}' is not reviewable"}

    pr_number = payload.get("pull_request", {}).get("number")
    if not isinstance(pr_number, int):
        logger.error("Pull request number missing or invalid in webhook payload")
        raise HTTPException(status_code=400, detail="Pull request number missing from payload")
    
    # Set context for all subsequent logs
    set_repo_name(repo_name)
    set_pr_number(pr_number)
    
    logger.info(
        "Processing PR for review",
        extra={
            "action": action,
            "pr_number": pr_number
        }
    )
    
    # FIRE AND FORGET: Trigger the history scraper in the background
    logger.debug("Triggering background history analysis task")
    background_tasks.add_task(extract_rules_from_history_task, repo_name)

    # Proceed with the immediate PR review
    diff = get_pr_diff(repo_name, pr_number)
    logger.debug("PR diff fetched", extra={"diff_length": len(diff)})
    
    # Pass the isolated repo_name to Chroma to ensure we only get this repo's rules
    house_rules = retrieve_relevant_rules(diff, repo_name)
    
    # Generate the review JSON
    review_result = analyze_pr_diff(diff, house_rules=house_rules)
    
    # Post the comments back to GitHub
    post_pr_review(repo_name, pr_number, review_result)
    
    logger.info(
        "Webhook processing completed",
        extra={
            "risk_score": review_result.risk_score,
            "merge_decision": review_result.merge_decision,
            "comment_count": len(review_result.comments)
        }
    )
    
    return {"status": "review_triggered_and_history_checked"}
