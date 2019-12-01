import RPi.GPIO as GPIO
import time
from PCF8591 import PCF8591


class LaserMeasure(object):
    def __init__(self, addr=0x48, device_num=0):
        # PCF8591_MODULE SETUP
        self.PCF8591_MODULE = PCF8591.PCF8591()
        # SET GPIO WARNINGS AS FALSE
        GPIO.setwarnings(False)
        # SET DEVICE ID
        self.device_id = device_num

    def get_object_detected(self):
        value = self.PCF8591_MODULE.read(2)
        print(value)
        return value > 70

    def destroy(self):
        GPIO.cleanup()

if __name__ == "__main__":
    module = LaserMeasure(0x48, 0)
    while True:
        module.get_object_detected()
        time.sleep(0.2)
