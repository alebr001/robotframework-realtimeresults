import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import json
import sys
from pathlib import Path

# Voeg root toe aan sys.path zodat imports werken
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.helpers.setup_wizard import run_setup_wizard, generate_event_type_from_path

class TestSetupWizard(unittest.TestCase):

    @patch("builtins.input", side_effect=[
        "y",                # enable viewer
        "",                 # viewer host (default)
        "",                 # viewer port (default 8000)
        "y",                # enable ingest
        "",                 # ingest host (default)
        "",                 # ingest port (default)
        "n",                # support_app_logs
        "",                 # listener sink type (default sqlite)
        "",                 # ingest sink type (default asyncsqlite)
        "y",                # continue
    ])
    @patch("builtins.print")
    @patch("pathlib.Path.open", new_callable=mock_open)
    @patch("pathlib.Path.exists", return_value=True)
    def test_run_setup_wizard_minimal_flow(
        self, mock_exists, mock_open_file, mock_print, mock_input
    ):
        config_path = Path("test_config.json")
        result = run_setup_wizard(config_path=config_path)

        self.assertTrue(result)

        # Extract the config that was written to the file
        written_data = "".join(call.args[0] for call in mock_open_file().write.mock_calls)
        config = json.loads(written_data)

        self.assertEqual(config["backend_strategy"], "sqlite")
        self.assertEqual(config["viewer_backend_host"], "127.0.0.1")
        self.assertEqual(config["viewer_backend_port"], 8000)
        self.assertEqual(config["ingest_backend_host"], "127.0.0.1")
        self.assertEqual(config["ingest_backend_port"], 8001)
        self.assertEqual(config["source_log_tails"], [])
        self.assertEqual(config["listener_sink_type"], "sqlite")
        self.assertEqual(config["ingest_sink_type"], "asyncsqlite")
        self.assertEqual(config["backend_endpoint"], "http://127.0.0.1:8000")

    def test_generate_event_type_from_path(self):
        path = "/var/log/app/output.log"
        result = generate_event_type_from_path(path)
        self.assertEqual(result, "output_log")

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    @patch("builtins.print")
    def test_keyboard_interrupt(self, mock_print, mock_input):
        with self.assertRaises(SystemExit) as cm:
            run_setup_wizard(config_path=Path("should_not_be_written.json"))
        self.assertEqual(cm.exception.code, 130)
        mock_print.assert_any_call("\n\nSetup cancelled by user (Ctrl+C). No config file was written.")


if __name__ == "__main__":
    unittest.main()