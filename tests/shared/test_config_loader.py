import unittest
import os
from unittest.mock import patch, mock_open

from shared.helpers.config_loader import load_config, ConfigError


class TestLoadConfig(unittest.TestCase):

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open", new_callable=mock_open, read_data='{"database_url": "sqlite:///test.db", "ingest_sink_type": "async"}')
    def test_load_json_file(self, mock_open_file, mock_exists):
        config = load_config("config.json")
        self.assertEqual(config["database_url"], "sqlite:///test.db")
        self.assertEqual(config["ingest_sink_type"], "async")

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open", new_callable=mock_open)
    @patch("shared.helpers.config_loader.tomllib.load", return_value={"database_url": "sqlite:///test.db", "ingest_sink_type": "async"})
    def test_load_toml_file(self, mock_toml_load, mock_exists, mock_open_file):
        config = load_config("config.toml")
        self.assertEqual(config["database_url"], "sqlite:///test.db")
        self.assertEqual(config["ingest_sink_type"], "async")

    @patch("pathlib.Path.exists", return_value=False)
    def test_config_file_not_found(self, mock_exists):
        with self.assertRaises(ConfigError) as cm:
            load_config("missing.json")
        self.assertIn("Missing required config key", str(cm.exception))

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open", new_callable=mock_open, read_data='{"env": true}')
    def test_config_missing_required_keys(self, mock_open_file, mock_exists):
        with self.assertRaises(ConfigError) as cm:
            load_config("incomplete.json")
        self.assertIn("Missing required config key", str(cm.exception))

    @patch.dict(os.environ, {"REALTIME_RESULTS_CONFIG": "from_env.json"})
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open", new_callable=mock_open, read_data='{"database_url": "sqlite:///env.db", "ingest_sink_type": "async"}')
    def test_load_config_from_env_variable(self, mock_open_file, mock_exists):
        config = load_config()
        self.assertEqual(config["database_url"], "sqlite:///env.db")
        self.assertEqual(config["ingest_sink_type"], "async")

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///override.db", "INGEST_SINK_TYPE": "postgres"})
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.open", new_callable=mock_open, read_data='{"database_url": "sqlite:///original.db", "ingest_sink_type": "async"}')
    def test_env_override_on_keys(self, mock_open_file, mock_exists):
        config = load_config("config.json")
        self.assertEqual(config["database_url"], "sqlite:///override.db")
        self.assertEqual(config["ingest_sink_type"], "postgres")
