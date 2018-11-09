import RPi.GPIO as GPIO


class MotionSensor:
    """Motion Sensor"""

    # Variables
    is_initialized = False

    # Pin
    motion = 25

    # Initialize
    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.motion, GPIO.IN)

    # Motion Readout
    def read_motion_state(self):
        """Reads the motion state."""
        return GPIO.input(self.motion)

    # Disposal
    def __del__(self):
        """Releases the resources."""
        if self.is_initialized:
            GPIO.cleanup()
            del self.is_initialized
        return
