#Tiny script to check if the relay is working and to open/close the garage door

import RPi.GPIO as GPIO
import time

RELAY_PIN = 25

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(RELAY_PIN, GPIO.OUT)
time.sleep(1)

GPIO.output(RELAY_PIN, False)
time.sleep(1)
GPIO.output(RELAY_PIN, True)
time.sleep(1)
GPIO.output(RELAY_PIN, False)
GPIO.cleanup()
