from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Tuple, Union
from shared.helpers.log_line_datetime_patterns import DATETIME_PATTERNS
import re

# Log levels
LOG_LEVELS = ["TRACE", "DEBUG", "VERBOSE", "INFO", "NOTICE", "WARNING", "WARN", "ERROR", "FATAL", "CRITICAL", "ALERT", "EMERGENCY"]
LOG_LEVEL_PATTERN = re.compile(r'\[?\s*(' + '|'.join(LOG_LEVELS) + r')\s*\]?', re.IGNORECASE)
ANSI_ESCAPE_PATTERN = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def remove_ansi_codes(s: str) -> str:
    return ANSI_ESCAPE_PATTERN.sub('', s)

def parse_known_datetime_formats(text: str, tz_info: str = "Europe/Amsterdam") -> Tuple[Optional[str], str]:
    """
    Try to detect and parse a timestamp in known formats.
    If found, returns (iso_timestamp, cleaned_text). If not, returns (None, original_text).
    """
    for pattern in DATETIME_PATTERNS:
        match = pattern["regex"].search(text)
        if match:
            raw = match.group(0)
            cleaned = raw.strip("[]") if pattern.get("strip_brackets") else raw
            cleaned = cleaned.replace(",", ".")
            fmt = None

            try:
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

                dt = dt.astimezone()
                iso = dt.isoformat(timespec="microseconds")
                return iso, text.replace(raw, "").strip()

            except Exception as e:
                print(f"[parse] Failed to parse '{cleaned}' with format '{fmt}': {e}")

    # No timestamp found
    return None, text


def _extract_log_level(line: str) -> Tuple[Optional[str], str]:
    """
    Extract log level if present. Also returns cleaned line without the level prefix.
    """
    match = LOG_LEVEL_PATTERN.search(line)
    if match:
        level = match.group(1).upper()
        cleaned_line = line[:match.start()] + line[match.end():]
        cleaned_line = re.sub(r"^\[\s*[,\.]?\d*\]", "", cleaned_line).strip()
        cleaned_line = re.sub(r"^\s*[-–—]+\s*", "", cleaned_line)
        return level, cleaned_line.strip()
    return None, line.strip()


def extract_timestamp_and_clean_message(line: str, tz_info: str = "Europe/Amsterdam") -> Tuple[Optional[str], str, Tuple[str, ...]]:
    """
    Extracts timestamp, log level, and parsed message parts from a single log line.
    Timestamp may be None if not found.
    """
    timestamp, stripped_line = parse_known_datetime_formats(line, tz_info=tz_info)
    level, cleaned_line = _extract_log_level(stripped_line)
    cleaned_line = remove_ansi_codes(cleaned_line)

    if re.search(r"\s{2,}", cleaned_line):
        parts = tuple(re.split(r"\s{2,}", cleaned_line.strip()))
    else:
        parts = (cleaned_line.strip(),)

    return timestamp, level or "INFO", parts
