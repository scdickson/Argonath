#Tiny script to check if the distance sensor is working and calibrate the distance from the sensor to the garage door

import RPi.GPIO as GPIO
import time
import sys

TRIG = 23
ECHO = 24

def measure_distance():
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(TRIG, GPIO.OUT)
	GPIO.setup(ECHO, GPIO.IN)
	GPIO.output(TRIG, False)
	time.sleep(1)

	GPIO.output(TRIG, True)
	time.sleep(0.00001)
	GPIO.output(TRIG, False)
	while GPIO.input(ECHO) == 0:
		pulse_start = time.time()

	while GPIO.input(ECHO) == 1:
		pulse_end = time.time()

	pulse_duration = pulse_end - pulse_start
	distance = pulse_duration * 17150
	distance = round(distance, 2)
	GPIO.cleanup()
	return distance

min = 500
max = -1
values = []

print "Measuring..."
for i in xrange(0, 10):
	distance = measure_distance()
	if distance < min:
		min = distance
	if distance > max:
		max = distance
	values.append(distance)

sum = 0
for distance in values:
	sum += distance

print "Min: %d" % min
print "Max: %d" % max
print "Average: %d" % (sum / len(values))
