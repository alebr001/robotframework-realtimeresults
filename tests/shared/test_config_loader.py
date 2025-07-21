import unittest
from unittest.mock import patch, mock_open
from pathlib import Path
import os

# Pas dit pad aan als nodig
from shared.helpers.config_loader import load_config


class TestLoadConfig(unittest.TestCase):

    @patch("pathlib.Path.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_json_file(self, mock_exists, mock_open_file):
        config = load_config("config.json")
        self.assertEqual(config["key"], "value")

    @patch("pathlib.Path.open", new_callable=mock_open)
    @patch("pathlib.Path.exists", return_value=True)
    @patch("shared.helpers.config_loader.tomllib.load", return_value={"section": {"key": "value"}})
    def test_load_toml_file(self, mock_toml_load, mock_exists, mock_open_file):
        config = load_config("config.toml")
        self.assertEqual(config["section"]["key"], "value")
        mock_toml_load.assert_called_once()

    @patch.dict(os.environ, {"REALTIME_RESULTS_CONFIG": "from_env.json"})
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open", new_callable=mock_open, read_data='{"env": true}')
    def test_load_config_from_env_variable(self, mock_open_file, mock_exists):
        config = load_config()
        self.assertEqual(config["env"], True)

    @patch("pathlib.Path.exists", return_value=False)
    def test_config_file_not_found(self, mock_exists):
        with self.assertRaises(FileNotFoundError):
            load_config("missing.json")

    @patch("builtins.print")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open", new_callable=mock_open, read_data="irrelevant")
    def test_unsupported_file_extension(self, mock_open_file, mock_exists, mock_print):
        with self.assertRaises(SystemExit) as context:
            load_config("config.yaml")
        self.assertEqual(context.exception.code, 1)
        mock_print.assert_called_once()
        self.assertIn("Failed to load config from config.yaml", mock_print.call_args[0][0])

    @patch("builtins.print")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_load_fails_with_exception(self, mock_open_file, mock_exists, mock_print):
        # Simuleer fout bij openen/parsen
        mock_open_file.return_value.__enter__.side_effect = Exception("read error")
        with self.assertRaises(SystemExit) as cm:
            load_config("config.json")
        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_called_once()
        self.assertIn("Failed to load config", mock_print.call_args[0][0])


if __name__ == "__main__":
    unittest.main()