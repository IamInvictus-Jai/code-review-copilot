# app/utils/diff_parser.py

from app.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


def annotate_diff(raw_diff: str) -> str:
    """Parse a raw git diff and prepend line numbers to added and context lines.
    
    The diff is annotated with bracketed line numbers [X] to help the AI
    pinpoint exact line numbers for inline comments.
    
    Args:
        raw_diff: Raw git diff content
        
    Returns:
        Annotated diff with line numbers in brackets
    """
    logger.debug(
        "Starting diff annotation",
        extra={"diff_length": len(raw_diff)}
    )
    
    annotated_lines = []
    new_line_num = 0
    lines_processed = 0
    parse_errors = 0
    
    for line in raw_diff.split('\n'):
        lines_processed += 1
        
        if line.startswith('+++ b/'):
            annotated_lines.append(line)
        elif line.startswith('@@ '):
            # Parse the hunk header: @@ -1,5 +10,8 @@
            # We want the '10', which is the starting line of the new code
            try:
                plus_part = line.split('+')[1].split(' ')[0]
                new_line_num = int(plus_part.split(',')[0])
                
                logger.debug(
                    "Parsed hunk header",
                    extra={
                        "line": line,
                        "new_line_num": new_line_num
                    }
                )
                
            except (IndexError, ValueError) as e:
                parse_errors += 1
                
                logger.warning(
                    "Failed to parse hunk header line number",
                    extra={
                        "line": line,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                
            annotated_lines.append(line)
            
        elif line.startswith('+') and not line.startswith('+++'):
            # Added line
            annotated_lines.append(f"[{new_line_num}] {line}")
            new_line_num += 1
            
        elif line.startswith(' '):
            # Unchanged context line
            annotated_lines.append(f"[{new_line_num}] {line}")
            new_line_num += 1
            
        else:
            # Removed line (-) or other diff metadata
            annotated_lines.append(line)
    
    result = '\n'.join(annotated_lines)
    
    logger.debug(
        "Diff annotation completed",
        extra={
            "input_lines": lines_processed,
            "output_lines": len(annotated_lines),
            "parse_errors": parse_errors,
            "output_length": len(result)
        }
    )
    
    if parse_errors > 0:
        logger.info(
            "Diff annotation completed with parse errors",
            extra={
                "parse_errors": parse_errors,
                "total_lines": lines_processed
            }
        )
            
    return result