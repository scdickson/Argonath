# Argonath: Automatic Garage Door Opener
<img src="https://github.com/scdickson/Argonath/raw/master/images/argonath.jpg" width="315" height="239">

Argonath is named after the [Gates of Argonath](http://lotr.wikia.com/wiki/Argonath) from Lord of the Rings and is an automatic garage door opener that uses BLE beacons to determine the state of vehicles in the garage. When the last vehicle leaves the garage, the door will automatically close and when a vehicle arrives home, the door with automatically open. To work properly with existing garage door openers, a distance sensor is used to determine the current state of the garage door.

# Hardware
* Raspberry Pi 3 Model B
* HC-SR04 Ultrasonic Range Sensor
* SainSmart 2 Channel Relay
* Off-the-shelf Bluetooth USB Dongle
* [Bluetooth Low Energy Beacons](https://www.amazon.com/sanwo-Replaceable-Waterproof-Dustproof-Covering/dp/B01I57KL7G/ref=sr_1_14?ie=UTF8&qid=1531290425&sr=8-14&keywords=ble+beacon)
![Hardware Setup](https://github.com/scdickson/Argonath/raw/master/images/hardware_setup.jpg)
<img src="https://github.com/scdickson/Argonath/raw/master/images/hardware_1.jpg" width="885" height="576">

# Setup
The components are placed in an enclosure and mounted to the ceiling of the garage with the distance sensor obscured by the garage door when it is open. Distance readings from the sensor to the garage door so the state of the door can be reliably determined independent of the operation of the automatic door opener. 
![Mounting](https://github.com/scdickson/Argonath/raw/master/images/hardware_2.jpg)

# Implementation
Argonath is driven by a Python script that runs as a system service. Bluetooth Low Energy advertisements are sniffed over the air and checked for matching UUIDs of beacons defined in the script. When the last vehicle leaves and the RSSI of its beacon falls below a certain threshold, the garage door is closed with the relay. When a vehicle arrives home, the distance sensor is used to determine the state of the garage door. If the door is closed, the relay will be switched on the the door opened. Adjusting the constants in the python script allows for fine tuning of the thresholds and timings.

# Python Dependencies
* RPi.GPIO
* beacontools[scan]
* [blescan](https://github.com/switchdoclabs/iBeacon-Scanner-)