import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from shared.helpers.log_line_parser import extract_timestamp_and_clean_message

def to_amsterdam_datetime(timestamp_str: str) -> datetime:
    """Parse an ISO 8601 timestamp and convert to Europe/Amsterdam timezone."""
    dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    return dt.astimezone(ZoneInfo("Europe/Amsterdam"))

class TestLogLineParser(unittest.TestCase):
    def test_log_lines(self):
        log_lines = [
            "[2025-07-02 13:45:01,234] INFO     main.api     Starting up API server on port 8000",
            "[2025-07-02 13:45:02] DEBUG    db.connector     Connection to database established (host=localhost)",
            "2025-07-02T13:45:03.567Z WARN  scheduler.job    Job 'cleanup_temp_files' took too long (42s)",
            '[02/Jul/2025:13:45:04 +0200] "GET /health HTTP/1.1" 200 42',
            "2025-07-02 13:45:05 ERROR    user.auth         Invalid login attempt for user 'admin'",
            "[2025-07-02 13:45:07,012] CRITICAL core.system  Unhandled exception: ValueError('config missing')",
            "13:45:08.123 DEBUG metrics.collector Memory usage: 382MB | CPU: 27.1%",
            "[2025-07-02 13:45:09] INFO     backup.runner   Backup completed successfully in 127s",
            "02-07-2025 13:45:10 ERROR    http.client       Timeout while contacting https://example.com/api",
            "127.0.0.1 [02/Jul/2025:17:14:47.605] GET /doesnotexist http 404 NOT FOUND 207 None python-requests/2.32.4",
            "2025-07-17 21:26:03.457478 - INFO - +-- END TEST: Example API Call - Root (1.012288 s)"
        ]

        today = datetime.now(ZoneInfo("Europe/Amsterdam")).date().isoformat()
        expected = [
            ('2025-07-02T13:45:01.000000+02:00', 'INFO', ('main.api', 'Starting up API server on port 8000')),
            ('2025-07-02T13:45:02.000000+02:00', 'DEBUG', ('db.connector', 'Connection to database established (host=localhost)')),
            ('2025-07-02T13:45:03.567000+02:00', 'WARN', ('scheduler.job', "Job 'cleanup_temp_files' took too long (42s)")),
            ('2025-07-02T13:45:04.000000+02:00', 'INFO', ('"GET /health HTTP/1.1" 200 42',)),
            ('2025-07-02T13:45:05.000000+02:00', 'ERROR', ('user.auth', "Invalid login attempt for user 'admin'")),
            ('2025-07-02T13:45:07.000000+02:00', 'CRITICAL', ('core.system', "Unhandled exception: ValueError('config missing')")),
            (f'{today}T13:45:08.123000+02:00', 'DEBUG', ('metrics.collector Memory usage: 382MB | CPU: 27.1%',)),
            ('2025-07-02T13:45:09.000000+02:00', 'INFO', ('backup.runner', 'Backup completed successfully in 127s')),
            ('2025-07-02T13:45:10.000000+02:00', 'ERROR', ('http.client', 'Timeout while contacting https://example.com/api')),
            ('2025-07-02T17:14:47.605000+02:00', 'INFO', ('127.0.0.1', 'GET /doesnotexist http 404 NOT FOUND 207 None python-requests/2.32.4')),
            ('2025-07-17T21:26:03.457478+02:00', 'INFO', ('+-- END TEST: Example API Call - Root (1.012288 s)',))
        ]

        for i, line in enumerate(log_lines):
            with self.subTest(i=i):
                actual = extract_timestamp_and_clean_message(line)
                actual_dt = to_amsterdam_datetime(actual[0])
                expected_dt = to_amsterdam_datetime(expected[i][0])
                self.assertEqual((actual_dt, *actual[1:]), (expected_dt, *expected[i][1:]))

if __name__ == '__main__':
    unittest.main()