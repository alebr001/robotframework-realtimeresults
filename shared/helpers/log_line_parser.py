from datetime import datetime, timezone
from typing import Optional, Tuple
from dateparser.search import search_dates
import re

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_LEVEL_PATTERN = re.compile(r'\[?\s*(' + '|'.join(LOG_LEVELS) + r')\s*\]?', re.IGNORECASE)

def extract_timestamp_and_clean_message(line: str) -> Tuple[str, str, str]:
    result = search_dates(line)
    timestamp = datetime.now(timezone.utc).isoformat()  # Default to current time if no date found
    if result:
        token, dt = result[0]    
        line = line.replace(str(token), '', 1)
        timestamp = dt.astimezone(timezone.utc).isoformat()
    level, cleaned_line = _extract_log_level(line)
    level = level or "INFO"  # fallback default
    return timestamp, cleaned_line, level

def _extract_log_level(line: str) -> Tuple[Optional[str], str]:
    match = LOG_LEVEL_PATTERN.search(line)
    if match:
        level = match.group(1).upper()  # Normalize to uppercase
        cleaned_line = line[:match.start()] + line[match.end():]  # Remove the match from the line
        return level, cleaned_line.strip()
    return None, line.strip()
