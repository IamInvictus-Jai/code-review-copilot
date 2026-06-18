import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.models import PRReviewResult
from app.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.0  # Dropped to 0 for maximum strictness
)

parser = PydanticOutputParser(pydantic_object=PRReviewResult)

REVIEW_PROMPT = """
You are a machine-to-machine code review API. Your ONLY purpose is to analyze code diffs and return raw JSON data.

House Rules to Enforce:
{house_rules}

Code Diff:
{diff}

LINE NUMBER INSTRUCTIONS:
The diff has been pre-processed. Added and context lines start with a bracketed number, e.g., [15].
Extract the integer inside the brackets for the `line_number` field. Do not guess.

CRITICAL SYSTEM INSTRUCTION:
You are forbidden from using conversational text, greetings, or markdown formatting (do NOT wrap the output in ```json blocks). 
You MUST output EXACTLY and ONLY a valid JSON object matching this schema:
{format_instructions}
"""

def analyze_pr_diff(diff: str, house_rules: str = "None") -> PRReviewResult:
    """Analyze a PR diff using Gemini AI and return structured review results.
    
    Args:
        diff: Annotated git diff with line numbers
        house_rules: Retrieved coding conventions from vector store
        
    Returns:
        PRReviewResult containing risk score, comments, and merge decision
    """
    logger.info(
        "Starting PR diff analysis",
        extra={
            "diff_length": len(diff),
            "house_rules_present": house_rules != "None",
            "house_rules_length": len(house_rules) if house_rules != "None" else 0
        }
    )
    
    prompt = PromptTemplate(
        template=REVIEW_PROMPT,
        input_variables=["house_rules", "diff"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    
    start_time = time.time()
    
    try:
        logger.debug("Invoking Gemini AI for code analysis")
        
        result = chain.invoke({
            "house_rules": house_rules,
            "diff": diff
        })
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "PR diff analysis completed successfully",
            extra={
                "risk_score": result.risk_score,
                "merge_decision": result.merge_decision,
                "comment_count": len(result.comments),
                "duration_ms": duration_ms
            }
        )
        
        return result
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.error(
            "Error analyzing PR diff",
            exc_info=True,
            extra={
                "diff_length": len(diff),
                "house_rules_length": len(house_rules) if house_rules != "None" else 0,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__
            }
        )
        
        return PRReviewResult(
            risk_score=1,
            risk_summary="The AI Reviewer encountered a parsing error.",
            merge_decision="COMMENT",
            comments=[]
        )