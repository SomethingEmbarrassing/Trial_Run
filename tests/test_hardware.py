import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import builtins
from unittest import mock

import hardware


def test_hardware_controller_calls_gpio(monkeypatch):
    mock_gpio = mock.MagicMock()
    mock_gpio.BCM = "BCM"
    mock_gpio.OUT = "OUT"
    mock_gpio.HIGH = 1
    mock_gpio.LOW = 0
    monkeypatch.setattr(hardware, "GPIO", mock_gpio)

    ctrl = hardware.HardwareController(3, 4)
    ctrl.mic_on()
    ctrl.speaker_on()
    ctrl.mic_off()
    ctrl.speaker_off()
    ctrl.cleanup()

    mock_gpio.setmode.assert_called_once_with("BCM")
    mock_gpio.setup.assert_any_call(3, "OUT")
    mock_gpio.setup.assert_any_call(4, "OUT")
    mock_gpio.output.assert_any_call(3, 1)
    mock_gpio.output.assert_any_call(4, 1)
    mock_gpio.output.assert_any_call(3, 0)
    mock_gpio.output.assert_any_call(4, 0)
    mock_gpio.cleanup.assert_called_once()
