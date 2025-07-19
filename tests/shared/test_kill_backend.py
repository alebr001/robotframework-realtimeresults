import unittest
from unittest.mock import patch, mock_open, call
import os
import signal
import sys

# Zorg dat dit pad klopt
from shared.helpers.kill_backend import kill_backend, PID_FILE


class TestKillBackend(unittest.TestCase):

    @patch("builtins.print")
    @patch("os.path.exists", return_value=False)
    def test_pid_file_missing(self, mock_exists, mock_print):
        with self.assertRaises(SystemExit) as cm:
            kill_backend()
        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_called_once_with(f"PID file '{PID_FILE}' not found.")

    @patch("os.remove")
    @patch("os.kill")
    @patch("platform.system", return_value="Linux")
    @patch("builtins.open", new_callable=mock_open, read_data="api=1234\nworker=5678\n")
    @patch("os.path.exists", return_value=True)
    @patch("builtins.print")
    def test_kill_backend_linux(self, mock_print, mock_exists, mock_open_file, mock_platform, mock_kill, mock_remove):
        kill_backend()
        mock_kill.assert_has_calls([
            call(1234, signal.SIGTERM),
            call(5678, signal.SIGTERM),
        ])
        mock_remove.assert_called_once_with(PID_FILE)
        self.assertIn(call("Sending SIGTERM to api (PID 1234) on Linux..."), mock_print.mock_calls)
        self.assertIn(call("All listed processes are terminated and PID file removed."), mock_print.mock_calls)

    @patch("os.remove")
    @patch("os.system")
    @patch("platform.system", return_value="Windows")
    @patch("builtins.open", new_callable=mock_open, read_data="listener=4321\n")
    @patch("os.path.exists", return_value=True)
    @patch("builtins.print")
    def test_kill_backend_windows(self, mock_print, mock_exists, mock_open_file, mock_platform, mock_system, mock_remove):
        kill_backend()
        mock_system.assert_called_once_with("taskkill /PID 4321 /F")
        mock_remove.assert_called_once_with(PID_FILE)
        mock_print.assert_any_call("Terminating listener (PID 4321) on Windows...")

    @patch("os.remove")
    @patch("os.kill", side_effect=ProcessLookupError)
    @patch("platform.system", return_value="Linux")
    @patch("builtins.open", new_callable=mock_open, read_data="api=99999\n")
    @patch("os.path.exists", return_value=True)
    @patch("builtins.print")
    def test_process_lookup_error(self, mock_print, mock_exists, mock_open_file, mock_platform, mock_kill, mock_remove):
        kill_backend()
        mock_print.assert_any_call("No process found with PID 99999 for api.")
        mock_remove.assert_called_once_with(PID_FILE)

    @patch("os.remove")
    @patch("os.kill", side_effect=Exception("kill failed"))
    @patch("platform.system", return_value="Linux")
    @patch("builtins.open", new_callable=mock_open, read_data="api=1234\n")
    @patch("os.path.exists", return_value=True)
    @patch("builtins.print")
    def test_kill_exception_handled(self, mock_print, mock_exists, mock_open_file, mock_platform, mock_kill, mock_remove):
        kill_backend()
        mock_print.assert_any_call("Failed to kill api (PID 1234): kill failed")
        mock_remove.assert_called_once_with(PID_FILE)


if __name__ == "__main__":
    unittest.main()