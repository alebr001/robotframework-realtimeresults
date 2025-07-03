from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Tuple, Union
from shared.helpers.log_line_datetime_patterns import DATETIME_PATTERNS
import re

# Log levels
LOG_LEVELS = ["TRACE", "DEBUG", "VERBOSE", "INFO", "NOTICE", "WARNING", "WARN", "ERROR", "FATAL", "CRITICAL", "ALERT", "EMERGENCY"]
LOG_LEVEL_PATTERN = re.compile(r'\[?\s*(' + '|'.join(LOG_LEVELS) + r')\s*\]?', re.IGNORECASE)

def parse_known_datetime_formats(text: str, tz_info: str = "Europe/Amsterdam") -> Tuple[str, str]:
    for pattern in DATETIME_PATTERNS:
        match = pattern["regex"].search(text)
        if match:
            raw = match.group(0)
            cleaned = raw.strip("[]") if pattern.get("strip_brackets") else raw
            cleaned = cleaned.replace(",", ".")
            fmt = None

            try:
                # Dynamisc format based on pattern
                if "format" in pattern:
                    fmt = pattern["format"]
                else:
                    fmt = pattern["format_base"]
                    if pattern.get("has_ms") and match.group(2):
                        fmt += ".%f"
                    if pattern.get("has_tz") and match.group(3):
                        fmt += " %z"

                if pattern.get("force_year"):
                    cleaned += f" {datetime.now().year}"
                    fmt += " %Y"

                if pattern.get("force_today"):
                    today = datetime.now().date()
                    cleaned = f"{today} {cleaned}"
                    fmt = "%Y-%m-%d " + fmt

                dt = datetime.strptime(cleaned, fmt)

                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo(tz_info))

                dt = dt.astimezone() # Convert to local timezone

                iso = dt.isoformat(timespec="microseconds")
                return iso, text.replace(raw, "").strip()

            except Exception as e:
                print(f"[parse] Failed to parse '{cleaned}' with format '{fmt}': {e}")

    # Fallback
    now = datetime.now(ZoneInfo(tz_info))
    return now.isoformat(timespec="microseconds"), text

def _extract_log_level(line: str) -> Tuple[Optional[str], str]:
    match = LOG_LEVEL_PATTERN.search(line)
    if match:
        level = match.group(1).upper()
        cleaned_line = line[:match.start()] + line[match.end():]
        cleaned_line = re.sub(r"^\[\s*[,\.]?\d*\]", "", cleaned_line).strip()  # also remove leftovers like [,234]
        return level, cleaned_line
    return None, line.strip()

def extract_timestamp_and_clean_message(line: str, tz_info: str = "Europe/Amsterdam") -> Tuple[str, str, Tuple[str, ...]]:
    timestamp, stripped_line = parse_known_datetime_formats(line, tz_info = tz_info)
    level, cleaned_line = _extract_log_level(stripped_line)

    # Splits op 2 of meer spaties
    if re.search(r"\s{2,}", cleaned_line):
        parts = tuple(re.split(r"\s{2,}", cleaned_line.strip()))
    else:
        parts = (cleaned_line.strip(),)

    return timestamp, level or "INFO", parts