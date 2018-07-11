#Tiny script to observe BLE advertisement packets for debugging

import bluetooth._bluetooth as bluez
import blescan

BLUETOOTH_DEVICE_ID = 0

sock = bluez.hci_open_dev(BLUETOOTH_DEVICE_ID)
blescan.hci_le_set_scan_parameters(sock)
blescan.hci_enable_le_scan(sock)
print "Sniffing BLE traffic for known UUIDs"
while True:
	eventList = blescan.parse_events(sock, 10)
	for event in eventList:
		data = event.split(",")
		print data
