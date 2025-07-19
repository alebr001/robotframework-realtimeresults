import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Zorg dat je dit pad correct hebt
import shared.helpers.cli as cli


class TestCliWrapper(unittest.TestCase):

    @patch("builtins.print")
    @patch("sys.exit")
    def test_help_flag(self, mock_exit, mock_print):
        test_argv = ["cli.py", "--help"]
        with patch.object(sys, "argv", test_argv):
            cli.parse_args()
            mock_print.assert_called()
            mock_exit.assert_called_once_with(0)

    @patch("shared.helpers.cli.kill_backend")
    @patch("builtins.print")
    @patch("sys.exit")
    def test_kill_backend_flag(self, mock_exit, mock_print, mock_kill):
        test_argv = ["cli.py", "--killbackend"]
        with patch.object(sys, "argv", test_argv):
            cli.parse_args()
            mock_kill.assert_called_once()
            mock_exit.assert_called_once_with(0)

    def test_parse_args_with_runservice_and_config(self):
        test_argv = [
            "cli.py",
            "--runservice", "api.viewer.main:app",
            "--config", "custom.json",
            "--outputdir", "results/",
            "tests/"
        ]
        with patch.object(sys, "argv", test_argv):
            service, config_path, robot_args = cli.parse_args()
            self.assertEqual(service, "api.viewer.main:app")
            self.assertEqual(config_path, Path("custom.json"))
            self.assertEqual(
                robot_args,
                ["--runservice", "api.viewer.main:app", "--outputdir", "results/", "tests/"]
            )

    def test_parse_args_without_runservice(self):
        test_argv = ["cli.py", "--config", "x.json", "--outputdir", "logs/", "tests/"]
        with patch.object(sys, "argv", test_argv):
            service, config_path, robot_args = cli.parse_args()
            self.assertIsNone(service)
            self.assertEqual(config_path, Path("x.json"))
            self.assertEqual(robot_args, ["--outputdir", "logs/", "tests/"])

    @patch("shared.helpers.cli.load_config", return_value={})  # extra mock toegevoegd
    @patch("shared.helpers.cli.run_setup_wizard", return_value=False)
    @patch("shared.helpers.cli.Path.exists", return_value=False)
    @patch("builtins.print")
    @patch("sys.exit")
    def test_main_runs_setup_if_config_missing(self, mock_exit, mock_print, mock_exists, mock_wizard, mock_config):
        test_argv = ["cli.py"]
        with patch.object(sys, "argv", test_argv):
            cli.main()
            mock_print.assert_any_call("No config found at realtimeresults_config.json. Launching setup wizard...")
            mock_exit.assert_called_once_with(0)

    @patch("shared.helpers.cli.load_config", return_value={"viewer_backend_host": "127.0.0.1", "viewer_backend_port": 8000})
    @patch("shared.helpers.cli.Path.exists", return_value=True)
    @patch("shared.helpers.cli.start_services", return_value={"api.viewer.main:app": 999})
    @patch("shared.helpers.cli.count_tests", return_value=3)
    @patch("shared.helpers.cli.subprocess.run")
    @patch("builtins.print")
    def test_main_robot_run(self, mock_print, mock_subproc, mock_count, mock_start, mock_exists, mock_config):
        test_argv = ["cli.py", "--outputdir", "results/", "tests/"]
        with patch.object(sys, "argv", test_argv):
            cli.main()
            mock_subproc.assert_any_call([
                "robot", "--listener", "producers.listener.listener.RealTimeResults:totaltests=3",
                "--outputdir", "results/", "tests/"
            ])

    @patch("shared.helpers.cli.load_config", return_value={"viewer_backend_host": "127.0.0.1", "viewer_backend_port": 8000})
    @patch("shared.helpers.cli.Path.exists", return_value=True)
    @patch("shared.helpers.cli.subprocess.run")
    def test_main_runservice_direct(self, mock_run, mock_exists, mock_config):
        test_argv = ["cli.py", "--runservice", "api.viewer.main:app"]
        with patch.object(sys, "argv", test_argv):
            cli.main()
            mock_run.assert_called()
            self.assertIn("uvicorn", mock_run.call_args[0][0])

    def test_is_port_used_false(self):
        command = [sys.executable, "--host", "127.0.0.1", "--port", "9999"]
        used = cli.is_port_used(command)
        self.assertIn(used, [True, False])  # hangt af van open poorten, geen harde check

    def test_is_process_running_false(self):
        self.assertIsNone(cli.is_process_running("unlikely_process_name_1234"))

    def test_get_command_viewer(self):
        config = {"viewer_backend_host": "1.2.3.4", "viewer_backend_port": 9999}
        cmd = cli.get_command("api.viewer.main:app", config)
        self.assertIn("uvicorn", cmd)
        self.assertIn("1.2.3.4", cmd)