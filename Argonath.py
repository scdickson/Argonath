#Dependencies: RPi.GPIO, beacontools[scan]
import bluetooth._bluetooth as bluez
from datetime import datetime
import RPi.GPIO as GPIO
import blescan #https://github.com/switchdoclabs/iBeacon-Scanner-
import time

LOG_FILE_LOCATION = "/home/pi/argonath/logs" #Location of log file output
BLUETOOTH_DEVICE_ID = 0 #USB Bluetooth device number
BEACONS = {
	#UUID -> STATE | LAST EVENT TIME | LAST SEEN TIME
	"UUID_1": [True, 0, 0], #First beacon UUID
	"UUID_2": [True, 0, 0] #Second beacon UUID
}
NUM_BLE_PACKET_TRIGGER = 15 #Number of BLE packets to buffer before analyzing
VEHICLE_GONE_THRESHOLD_MS = 3000 #Number of milliseconds after we last saw a beacon advertisement before we consider a vehicle gone
DUPLICATE_EVENT_PROTECTION_THRESHOLD_MS = 4000 #Number of milliseconds to wait in between events to handle duplicate door open/close events
RSSI_LEAVE_THRESHOLD = -100 #RSSI value at or below which we consider a vehicle gone
GARAGE_DOOR_OPEN_DISTANCE_CM = 19 #Number of centimeters from our distance sensor to the garage door. Senses whether not the door is open
GARAGE_DOOR_PIN_DOWN_SEC = 16 #Number of seconds to hold the GPIO pin voltage high to open/close the garage door. This particular door needs a long hold or else the door stops opening/closing halfway
DEBUG_OUTPUT = True #Whether or not to output log messages to the command line for debugging
RELAY_PIN = 25 #The GPIO pin for the garage door relay

class DistanceSensor:
	TRIG = 23 #The GPIO pin for the distance sensor TRIGGER
	ECHO = 24 #The GPIO pin for the distance sensor ECHO

	#Returns the distance in cm from the sensor to either the garage door or the ground. Helps determine whether the door is open/closed independently of the script
	def measureDistance(self):
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		GPIO.setup(DistanceSensor.TRIG, GPIO.OUT)
		GPIO.setup(DistanceSensor.ECHO, GPIO.IN)
		GPIO.output(DistanceSensor.TRIG, False)
		time.sleep(1)

		GPIO.output(DistanceSensor.TRIG, True)
		time.sleep(0.00001)
		GPIO.output(DistanceSensor.TRIG, False)
		while GPIO.input(DistanceSensor.ECHO) == 0:
			pulse_start = time.time()

		while GPIO.input(DistanceSensor.ECHO) == 1:
			pulse_end = time.time()

		pulse_duration = pulse_end - pulse_start
		distance = pulse_duration * 17150 #Some physics magic
		distance = round(distance, 2)
		GPIO.cleanup()
		return distance


ds = DistanceSensor()
logfile = open(LOG_FILE_LOCATION + "/log.txt", 'a')
initialized = False #Start in uninitialized state to get an inventory of all vehicles when the script is first run

#Returns the time in milliseconds. Used for last seen time and last event time
def get_time_millis():
	return int(round(time.time() * 1000))

#Outputs a message to the log file (and stdout if constant is defined)
def write_log(msg):
	global logfile
	log_line = "%s -> %s\n" % (str(datetime.now()), msg)
	logfile.write(log_line)
	if DEBUG_OUTPUT:
		print log_line

#Returns True if the beacon changed its state (False -> True || True -> False), False otherwise
def state_changed(uuid, newState):
	if uuid in BEACONS:
		oldState = BEACONS[uuid][0]
		if oldState != newState:
			return True
	return False

#Returns whether or not the garage door is currently open using the distance sensor
def garage_door_open():
	global ds
	return ds.measureDistance() <= GARAGE_DOOR_OPEN_DISTANCE_CM

#Toggles the garage door state. No events will be captured while the door is opening/closing
def toggle_garage_door_state():
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(RELAY_PIN, GPIO.OUT)
	GPIO.output(RELAY_PIN, False)
	time.sleep(1)

	GPIO.output(RELAY_PIN, True)
	time.sleep(GARAGE_DOOR_PIN_DOWN_SEC) #Opening door requires pin to be ON for a significant amount of time
	GPIO.output(RELAY_PIN, False)
	GPIO.cleanup()

#Returns whether or not any other vehicle is in the garage by looking at the last state of all beacons
def other_vehicles_present(exclude):
	for uuid, status in BEACONS.iteritems():
		if uuid != exclude:
			if status[0]:
				return True
	return False

#Called every time a beacon state is changed. Looks at the garage door state and whether or not other vehicles are present to determine if the door needs to be opened or closed
def toggle_garage_door_state_if_required(uuid, newState):
	if newState: #Someone is arriving home
		if not garage_door_open(): #Garage door is closed
			write_log("Opening garage door")
			toggle_garage_door_state()
		else:
			write_log("Garage door is already open. Doing nothing.")
	else: #Someone has left
		if gone_threshold_met(uuid):
			if not other_vehicles_present(uuid): #If no one else is home
				write_log("Closing garage door")
				toggle_garage_door_state()
			else:
				write_log("Other vehicles are in the garage. Doing nothing.")
		else:
			write_log("Gone threshold of %d ms not met. Doing nothing." % VEHICLE_GONE_THRESHOLD_MS)

#Returns whether or not two beacon UUIDs are equal. May be necessary for additional equality logic
def uuids_equal(uuid1, uuid2):
	return uuid1 == uuid2

#Returns whether or not two events with the same beacon UUID are duplicates by checking if the time threshold has been met between the events
def is_duplicate_event(uuid):
	return BEACONS[uuid][1] + DUPLICATE_EVENT_PROTECTION_THRESHOLD_MS >= get_time_millis()

#Returns whether or not a vehicle should be marked as gone by checking if we haven't seen this a beacon for a cetain amount of time
def gone_threshold_met(uuid):
	return BEACONS[uuid][2] + VEHICLE_GONE_THRESHOLD_MS <= get_time_millis()

#Set up bluetooth scanner
sock = bluez.hci_open_dev(BLUETOOTH_DEVICE_ID)
blescan.hci_le_set_scan_parameters(sock)
blescan.hci_enable_le_scan(sock)
write_log("Argonath started listening for events...")
while True:
	#On each scan, initialize the seen dictionary to False. If we see a beacon, we will mark it True. Beacons not seen will be handled later
	seen = {}
	for uuid in BEACONS:
		seen[uuid] = False

	eventList = blescan.parse_events(sock, NUM_BLE_PACKET_TRIGGER)
	for event in eventList:
		#Event string format: MAC, UUID, MAJOR, MINOR, RSSI
		data = event.split(",")
		rssi = data[len(data)-1]
		for uuid, status in BEACONS.iteritems():
			if uuids_equal(data[1], uuid):
				if DEBUG_OUTPUT:
					print "%s -> %s [Threshold: %d]" % (uuid, rssi, RSSI_LEAVE_THRESHOLD)
				if not is_duplicate_event(uuid): #If time between events is at least x seconds (to protect against duplicate events)
					if int(rssi) <= RSSI_LEAVE_THRESHOLD: #Check the threshold for counting a vehicle as gone
						write_log("State of %s is below 'gone' threshold of %d" % (uuid, RSSI_LEAVE_THRESHOLD))
						seen[uuid] = False
						#Do not update last seen time
					else: 
						seen[uuid] = True
						newState = True
						if initialized: #On first run, don't toggle garage state. Just set initial vehicle state
							if state_changed(uuid, newState): #If the state changed, maybe we need to do something
								write_log("State of %s changed from %s to %s" % (uuid, BEACONS[uuid], newState))
								toggle_garage_door_state_if_required(uuid, newState)
								BEACONS[uuid][0] = newState #Update state
								BEACONS[uuid][1] = get_time_millis() #Update last event time
							BEACONS[uuid][2] = get_time_millis() #Update last seen time
					initialized = True

	for uuid in seen:
		if not seen[uuid]: #Look at all beacons not seen in this round
			newState = False
			if not is_duplicate_event(uuid): #More duplicate event protection
				newState = False
				if initialized:
					if state_changed(uuid, newState):
						write_log("State of %s changed from %s to %s" % (uuid, BEACONS[uuid], newState))
						toggle_garage_door_state_if_required(uuid, newState)
						BEACONS[uuid][1] = get_time_millis() #Update last event time
						BEACONS[uuid][0] = newState #Update state
						#Do not update last seen time
			initialized = True
					

