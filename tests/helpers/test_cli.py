import pytest
import sys
from shared.helpers import cli

def test_help_option_shows_help(capsys):
    sys.argv = ['rt-robot', '--help']
    with pytest.raises(SystemExit) as e:
        cli.parse_args()
    captured = capsys.readouterr()
    assert 'Usage:' in captured.out
    assert e.value.code == 0

def test_invalid_option_exits(capsys):
    sys.argv = ['rt-robot', '--notarealoption']
    with pytest.raises(SystemExit):
        cli.parse_args()

def test_runservice_option(monkeypatch):
    sys.argv = ['rt-robot', '--runservice', 'api.viewer.main:app']
    monkeypatch.setattr(cli, 'run_service', lambda name: name)
    result = cli.parse_args()
    # Assuming the first element of the tuple is runservice
    assert result[0] == 'api.viewer.main:app'

def test_killbackend_option(monkeypatch):
    sys.argv = ['rt-robot', '--killbackend']
    monkeypatch.setattr(cli, 'kill_backend', lambda: True)
    result = cli.parse_args()
    assert result[0] == 'killbackend'

def test_config_option(monkeypatch):
    sys.argv = ['rt-robot', '--config', 'myconfig.json']
    monkeypatch.setattr(cli, 'load_config', lambda path: {'config': path})
    result = cli.parse_args()
    # Assuming the config path is the second element in the tuple
    assert str(result[1]) == 'myconfig.json'
