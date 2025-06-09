"""Simple GPIO-based hardware controller."""

try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover - RPi may be unavailable
    GPIO = None  # type: ignore


class HardwareController:
    """Control microphone and speaker GPIO pins."""

    def __init__(self, mic_pin: int, speaker_pin: int) -> None:
        if GPIO is None:
            raise RuntimeError("RPi.GPIO library not available")
        self.mic_pin = mic_pin
        self.speaker_pin = speaker_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.mic_pin, GPIO.OUT)
        GPIO.setup(self.speaker_pin, GPIO.OUT)

    def mic_on(self) -> None:
        GPIO.output(self.mic_pin, GPIO.HIGH)

    def mic_off(self) -> None:
        GPIO.output(self.mic_pin, GPIO.LOW)

    def speaker_on(self) -> None:
        GPIO.output(self.speaker_pin, GPIO.HIGH)

    def speaker_off(self) -> None:
        GPIO.output(self.speaker_pin, GPIO.LOW)

    def cleanup(self) -> None:
        GPIO.cleanup()
