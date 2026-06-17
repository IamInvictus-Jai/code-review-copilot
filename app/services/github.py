# app/services/github.py
import os
import requests
from github import Github, GithubException
from fastapi import HTTPException
from app.models import PRReviewResult
from app.utils.diff_parser import annotate_diff # <-- NEW IMPORT

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
    print("WARNING: GITHUB_TOKEN environment variable is not set!")

gh = Github(GITHUB_TOKEN)

def get_pr_diff(repo_name: str, pr_number: int) -> str:
    try:
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        diff_url = pr.diff_url
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        response = requests.get(diff_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to fetch diff. Status code: {response.status_code}"
            )
            
        raw_diff = response.text
        # Pass the raw diff through our new parser
        return annotate_diff(raw_diff) 

    except GithubException as e:
        # ... keep your existing exception handling ...
        if e.status == 404:
            raise HTTPException(status_code=404, detail="Repo/PR not found.")
        raise HTTPException(status_code=e.status, detail=str(e))

def post_pr_review(repo_name: str, pr_number: int, review_data: PRReviewResult):
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
        
        # Pull latest commit object for comment pinning (safer list extraction)
        commits = list(pr.get_commits())
        latest_commit = commits[-1] 
        
        for comment in review_data.comments:
            body = (
                f"**[{comment.severity.upper()}]** {comment.summary}\n\n"
                f"**Why it matters:** {comment.explanation}\n\n"
                f"**Suggested Fix:**\n```{get_language_from_filename(comment.file_path)}\n{comment.suggested_fix}\n```"
            )
            try:
                pr.create_review_comment(
                    body=body,
                    commit=latest_commit,  # <-- Updated parameter name and object
                    path=comment.file_path,
                    line=comment.line_number
                )
            except Exception as inline_err:
                # Graceful fallback to general issue comment if line matching fails
                print(f"Failed to post inline comment: {inline_err}")
                pr.create_issue_comment(f"*(Line review fallback for {comment.file_path}:{comment.line_number})*\n" + body)

    except GithubException as e:
        raise HTTPException(status_code=e.status, detail=f"Failed to post review: {str(e)}")
