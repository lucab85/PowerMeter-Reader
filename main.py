#!/usr/bin/python
# coding: utf-8
# Copyright 2017 Luca Berton
__author__ = 'lucab85'

from settings import PM_config, PM_SETTINGS_LABELS
from SchneiderElectric_iEM3255 import SchneiderElectric_iEM3255

from logmanagement import logmanagement
log = logmanagement.getlog('main', 'utils').getLogger()

def main():
	PM_cacheEnabled = PM_config['cacheEnabled']
	pm = SchneiderElectric_iEM3255(PM_config['host'], PM_config['port'], 
		int(PM_config['address']), PM_config['start_reg'], 
		PM_config['max_regs'], PM_config['timeout'], 
		PM_config['endian'], PM_config['addressoffset'], 
		PM_cacheEnabled, PM_config['base_commands'])

	print("Connesso? %s" % pm.mb.isConnected)

	print("--------------------------------------")
	print(" SETTINGS ")
	for i in PM_SETTINGS_LABELS:
		value = pm._modbusRead(i)
		print("%s = %s" % (i, value))

	print("--------------------------------------")
	print(" ACTIVE ENERGY ")
	l1 = pm.readL1Active()
	l2 = pm.readL2Active()
	l3 = pm.readL3Active()
	print("line 1: %s 2: %s 3: %s" % (l1, l2, l3))
	
	print("--------------------------------------")
	print(" CURRENT")
	l1 = pm.readL1Current()
	l2 = pm.readL2Current()
	l3 = pm.readL3Current()
	print("line 1: %s 2: %s 3: %s" % (l1, l2, l3))

	print("--------------------------------------")
	print(" VOLTAGE")
	l1 = pm.readL1Voltage()
	l2 = pm.readL2Voltage()
	l3 = pm.readL3Voltage()
	print("line 1: %s 2: %s 3: %s" % (l1, l2, l3))

	print("--------------------------------------")
	print(" COMMAND")
	print("date: %s" % pm.read_date_time())
	pm.cmd_set_date_time()
	print("date: %s" % pm.read_date_time())
	
if __name__ == '__main__':
	main()
