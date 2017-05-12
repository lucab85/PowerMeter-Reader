#!/usr/bin/python
# Copyright 2017 Luca Berton
__author__ = 'lucab85'

debug = True

PM_config = {
	'host': '127.0.0.1',
	'port': 502,
	'address': 1,
	'addressoffset': -1,
	'start_reg': 0,
	'max_regs': 125,
	'timeout': 2,
	'endian': 'big',
	'cacheEnabled': True,
	'base_commands': 5250
}

PM_settings = {
	'Set DateTime': {
		'command': 1003
	},
	'Set Wiring': {
		'command': 2000,
		'Power System Configuration': 11,
		'Nominal Frequency': 60,
		'VT Primary': 100.0,
		'VT Secondary': 100,
		'Number of CTs': 3,
		'CT Primary': 60,
		'CT Secondary': 5,
		'VT Connection type': 0
	},
	'Set Pulse Output': {
		'command': 2003,
		'Pulse Output enable': 1,
		'Pulse constant': 1,

		'command2': 2038,
		'Pulse width': 50
	},
	'Set Tariff': {
		'command': 2060,
		'Multi Tariff Mode': 0,
		'command2': 2008,
		'Tariff': 1
	},
	'Set Digital Input as Partial Energy Reset': {
		'command': 6017,
		'Digital Input to Associate': 0
	},
	'Input Metering Setup': {
		'command': 6014,
		'Input Metering Channel': 1,
		'Label': 'input',
		'Pulse Weight': 1000,
		'Digital Input Association': 0
	},
	'Overload Alarm Setup': {
		'command': 7000,
		'Alarm ID': 0,
		'Enabled': 0,
		'Pickup value': float(100000000),
		'command2': 20000,
		'Digital Output to Associate': 0,
		'command3': 20001
	},
	'Communications Setup': {
		'command': 5000,
		'Address': 1,
		'Baud Rate': 1,
		'Parity': 0
	},
	'Reset Partial Energy Counters': {
		'command': 2020
	},
	'Reset Input Metering Counter': {
		'command': 2023
	},
}

MODBUS_CONNECTIONRETRY = 3
PATH_LOGGING = 'configs/logging.json'
PATH_PM_SCHNEIDERELECTRICIEM3255 = 'configs/Map-Schneider-iEM3255.csv'
PM_SETTINGS_LABELS = [
	"Meter Name", "Meter Model", "Manufacturer", "Serial Number", 
	"Date of Manufacture", "Hardware Revision", "Firmware Version", 
	"Meter Operation Timer", "Number of Phases", "Number of Wires",
	"Power System", "Nominal Frequency", "Number VTs", "CT Primary", 
	"CT Secondary",	"Number CTs", "CT Primary", "CT Secondary", 
	"VT Connection Type", "Energy Pulse Duration", 
	"Digital Output Association", "Pulse Weight"
]

