import re

DATETIME_PATTERNS = [
    # [02/Jul/2025:17:14:47.605 +0200] of zonder ms of zonder offset
    {
        "regex": re.compile(r"\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})(\.\d+)?( [+\-]\d{4})?\]"),
        "format_base": "%d/%b/%Y:%H:%M:%S",
        "strip_brackets": True,
        "has_ms": True,
        "has_tz": True,
    },

    # 2025-07-17 21:26:03.457478
    {
        "regex": re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+"),
        "format": "%Y-%m-%d %H:%M:%S.%f",
        "strip_brackets": False
    },

    # 2025-07-02T13:45:03.567Z
    {
        "regex": re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z"),
        "format": "%Y-%m-%dT%H:%M:%S.%fZ",
        "strip_brackets": False
    },

    # 2025-07-02 13:45:05
    {
        "regex": re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"),
        "format": "%Y-%m-%d %H:%M:%S",
        "strip_brackets": False
    },

    # 02-07-2025 13:45:10
    {
        "regex": re.compile(r"\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}"),
        "format": "%d-%m-%Y %H:%M:%S",
        "strip_brackets": False
    },

    # Jul 02 13:45:06
    {
        "regex": re.compile(r"\w{3} \d{2} \d{2}:\d{2}:\d{2}"),
        "format": "%b %d %H:%M:%S",
        "strip_brackets": False,
        "force_year": True
    },

    # 13:45:08.123
    {
        "regex": re.compile(r"\d{2}:\d{2}:\d{2}\.\d+"),
        "format": "%H:%M:%S.%f",
        "strip_brackets": False,
        "force_today": True
    }
]