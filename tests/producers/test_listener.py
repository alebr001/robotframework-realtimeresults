import pytest
from producers.listener import listener

def test_realtime_results_init():
    r = listener.RealTimeResults()
    assert hasattr(r, 'logger')
    assert hasattr(r, 'ROBOT_LISTENER_API_VERSION')
