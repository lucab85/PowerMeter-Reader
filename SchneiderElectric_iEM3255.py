#!/usr/bin/python
# coding: utf-8
# Copyright 2017 Luca Berton
__author__ = 'lucab85'

import sys

from ModbusWrapperClient import ModbusWrapperClient
from settings import PATH_PM_SCHNEIDERELECTRICIEM3255, PM_settings, PM_config
import math
import datetime

from logmanagement import logmanagement
log = logmanagement.getlog('SchneiderElectriciEM3255', 'powermeter').getLogger()

class SchneiderElectric_iEM3255():
	def __init__(self, PM_modbusHost, PM_modbusPort, PM_modbusAddress, PM_startReg, PM_maxRegsRead,
	             PM_timeout, PM_endian, PM_modbusAddressoffset=0, PM_cacheEnabled=False, PM_base_commands=0):
		self.mb = ModbusWrapperClient(PM_modbusAddress, PM_maxRegsRead, PM_timeout, PM_endian)
		self.PM_addressoffset = PM_modbusAddressoffset
		self.mb.openConnectionTCP(modbusHost=PM_modbusHost, modbusPort=PM_modbusPort)
		self.PM_getData_start = PM_startReg
		self.PM_getData_count = PM_maxRegsRead
		self.PM_cacheEnabled = PM_cacheEnabled
		self.PM_base_commands = PM_base_commands
		
		self.load_modbus_map()
		valid_addresses = self.elaborate_validAddresses()
		log.debug("valid_addresses: %s" % valid_addresses)
		self.mb.load_valid_addresses(valid_addresses)
		self.buffer_skip = []
		self.data_default = []

	def load_modbus_map(self):
		filename = PATH_PM_SCHNEIDERELECTRICIEM3255
		self.modbusmap = {}
		i = 0
		separator = ";"
		with open(filename) as f:
			for line in f:
				line = line.rstrip()
				line.replace("'", "")
				if separator not in line:
					continue
				if line.startswith("#"):
					continue
				if line.startswith(separator):
					continue
				key, address, size, datatype = line.split(separator)
				try:
					self.modbusmap.setdefault(key, [])
					self.modbusmap[key].append(int(address) + self.PM_addressoffset)
					self.modbusmap[key].append(int(size))
					self.modbusmap[key].append(datatype)
				except ValueError:
					pass
				i += 1

		text = "["
		validaddresses = []
		for k in self.modbusmap.keys():
			if len(self.modbusmap[k]) == 3:
				text += "'%s => %s,%s,%s', " % (k, self.modbusmap[k][0], self.modbusmap[k][1], self.modbusmap[k][2])
				if self.modbusmap[k][0] not in validaddresses:
					validaddresses.append(self.modbusmap[k][0])
			else:
				text += "**SKIP** item \"%s\"" % k
		text += "]"
		log.debug("Read %s modbus registers: %s" % (i, text))

	def elaborate_validAddresses(self):
		addresses = []
		log.debug("modbusmap: %s" % self.modbusmap)
		for k in self.modbusmap.keys():
			address = self.modbusmap[k][0]
			i = 0
			size = self.modbusmap[k][1]
			while i <= size:
				address = address + i
				if address not in addresses:
					addresses.append(address)
				i += 1
		return sorted(addresses)

	def _modbusRead(self, key):
		if self.PM_cacheEnabled is False:
			# W/O cache
			val = self.mb.readRegistersAndDecode(self.modbusmap[key][0],self.modbusmap[key][1],self.modbusmap[key][2])
		else:
			# with cache
			val = self.mb.cachedRead(self.modbusmap[key][0], self.modbusmap[key][1], self.modbusmap[key][2])
		log.debug('"%s" Modbus: (%s,%s,%s) = %s' % (key, self.modbusmap[key][0],
		                                            self.modbusmap[key][1], self.modbusmap[key][2], val))
		if self.modbusmap[key][2].startswith("float"):
			try:
				if math.isnan(val):
					log.debug("NaN regs %s => 0" % self.modbusmap[key][0])
					val = 0
			except TypeError:
				val = 0
		return val

	def readL1Active(self):
		# *1000 kW => W
		return self._modbusRead('L1Active')*1000

	def readL2Active(self):
		# *1000 kW => W
		return self._modbusRead('L2Active')*1000

	def readL3Active(self):
		# *1000 kW => W
		return self._modbusRead('L3Active')*1000

	def readL1Current(self):
		return self._modbusRead('L1Current')

	def readL2Current(self):
		return self._modbusRead('L2Current')

	def readL3Current(self):
		return self._modbusRead('L3Current')

	def readL1Voltage(self):
		return self._modbusRead('L1Voltage')

	def readL2Voltage(self):
		return self._modbusRead('L2Voltage')

	def readL3Voltage(self):
		return self._modbusRead('L3Voltage')

	def readFreq(self):
		return self._modbusRead('FREQ')

	def readDinput(self):
		Dinput = self._modbusRead('Digital Input Status')

	def readL1Apparent(self, L1Voltage=None, L1Current=None):
		if L1Voltage is None:
			L1Voltage = self.readL1Voltage()
		if L1Current is None:
			L1Current = self.readL1Current()
		return L1Voltage * L1Current

	def readL2Apparent(self, L2Voltage=None, L2Current=None):
		if L2Voltage is None:
			L2Voltage = self.readL2Voltage()
		if L2Current is None:
			L2Current = self.readL2Current()
		return L2Voltage * L2Current

	def readL3Apparent(self, L3Voltage=None, L3Current=None):
		if L3Voltage is None:
			L3Voltage = self.readL3Voltage()
		if L3Current is None:
			L3Current = self.readL3Current()
		return L3Voltage * L3Current

	def readL1CosPhi(self, L1Voltage=None, L1C=None, L1AC=None):
		if L1Voltage is None:
			L1Voltage = self.readL1Voltage()
		if L1C is None:
			L1C = self.readL1Current()
		if L1AC is None:
			L1AC = self.readL1Active()
		VI = L1Voltage * L1C
		if VI == 0:
			return 0
		return L1AC / VI

	def readL2CosPhi(self, L2Voltage=None, L2C=None, L2AC=None):
		if L2Voltage is None:
			L2Voltage = self.readL2Voltage()
		if L2C is None:
			L2C = self.readL2Current()
		if L2AC is None:
			L2AC = self.readL2Active()
		VI = L2Voltage * L2C
		if VI == 0:
			return 0
		return L2AC / VI

	def readL3CosPhi(self, L3Voltage=None, L3C=None, L3AC=None):
		if L3Voltage is None:
			L3Voltage = self.readL3Voltage()
		if L3C is None:
			L3C = self.readL3Current()
		if L3AC is None:
			L3AC = self.readL3Active()
		VI = L3Voltage * L3C
		if VI == 0:
			return 0
		return L3AC / VI

	def readL1Reactive(self):
		V = float(self.readL1Voltage())
		I = float(self.readL1Current())
		return math.sqrt(math.pow((V*I), 2) - math.pow(self.readL1Active(), 2))

	def readL2Reactive(self):
		V = float(self.readL2Voltage())
		I = float(self.readL2Current())
		return math.sqrt(math.pow((V*I), 2) - math.pow(self.readL2Active(), 2))

	def readL3Reactive(self):
		V = float(self.readL3Voltage())
		I = float(self.readL3Current())
		return math.sqrt(math.pow((V*I), 2) - math.pow(self.readL3Active(), 2))

	def readActiveEnergy(self):
		return self._modbusRead('PartialActiveEnergy')

	def readReactiveEnergy(self):
		return self._modbusRead('PartialReactiveEnergy')

	def readTotalPowerFactor(self):
		return self._modbusRead('TotalPowerFactor')

	def _capacitiveOrInductive(self):
		tpf = self.readTotalPowerFactor()
		if tpf < -1:
			return "-C"
		elif tpf >= -1 and tpf < 0:
			return "-I"
		elif tpf >= 0 and tpf < 1:
			return "+I"
		elif tpf >= 1:
			return "+C"

	def readInductiveEnergy(self):
		return self.readReactiveEnergy()

	def readCapacitiveEnergy(self):
		return self.readReactiveEnergy()

	def readTotalActivePW(self):
		# *1000 kW => W
		return self._modbusRead('TotalActivePW')*1000

	def readTotalApparentPW(self):
		# *1000 kVA => VA
		return self._modbusRead('TotalApparentPW')*1000

	def bysec_value(self, x, size=16):
		val_shift = size/2
		if size == 8:
			val_mask = 0xf
		else:
			val_mask = 0xff

		c = (x >> val_shift) & val_mask
		f = x & val_mask
		return c, f

	def read_date_time(self):
		date = None
		year = 2000 + int(self._modbusRead("YYYY"))
		month, tmp = self.bysec_value(self._modbusRead("MM-WW-GG"))
		weekday, day = self.bysec_value(tmp, 8)
		hours, minutes = self.bysec_value(self._modbusRead("HH-MM"))
		seconds = int(self._modbusRead("MS")) / 1000

		log.warn("read YYYY=%s MM=%s DD=%s HH=%s MM=%s SS=%s" % (year, month, day, hours, minutes, seconds))
		date = datetime.datetime(year, month, day, hours, minutes, seconds)
		log.warn("data: %s" % date)
		return date

	def _modbusWrite(self, command, base_address, value, mb_funcall, force=False):
		log.debug('CMD: %s Modbus (FC=%s): %s = %s' % (command, mb_funcall, base_address, value))
		skip_encode = True
		val = self.mb.writeRegisters((base_address + self.PM_addressoffset), value, mb_funcall, force, skip_encode=skip_encode)
		log.debug('Write done: %s' % val)
		val = self.mb.readRegisters(address=(5375 + self.PM_addressoffset), count=2, mb_type='int16', mb_funcall=3, force=True)
		log.debug("result: %s" % val)
		if val[1] == 0:
			log.warn("!!! Command SUCCESSFUL !!!")
		elif val[1] == 3000:
			log.warn("INVALID Command or COM.PROTECTION")
		elif val[1] == 3001:
			log.warn("INVALID Parameter")
		elif val[1] == 3002:
			log.warn("INVALID number of parameters")
		elif val[1] == 3007:
			log.warn("Operation Not Performed")
		else:
			log.warn('NOT valid value: "%s"' % val[1])
		return val[1]

	def encode_data(self, payload):
		payload_processed = []
		for i in payload:
			try:
				value = self.mb.encode_field(i[0], i[1])
				for item in value:
					payload_processed.append(item)
				if len(value) > 1:
					log.debug("multibyte %s => %s" % (i, value))
			except Exception as e:
				log.exception(e)
		return payload_processed

	def cmd_set_date_time(self, key='Set DateTime', data=datetime.datetime.today()):
		log.debug('Start "cmd_set_date_time" routine: %s %s' % (PM_settings[key], data))
		payload = [
				[int(PM_settings[key]['command']), 'int16'],
				[0, 'int16'],
				[int(data.year), 'int16'],
				[int(data.month), 'int16'],
				[int(data.day), 'int16'],
				[int(data.hour), 'int16'],
				[int(data.minute), 'int16'],
				[int(data.second), 'int16'],
				[0, 'int16'],
			]
		payload_processed = self.encode_data(payload)
		ret = self._modbusWrite(command=PM_settings[key],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		log.debug('End "cmd_set_date_time" routine: %s' % ret)

	def cmd_set_wiring(self, key='Set Wiring'):
		log.debug('Start "cmd_set_wiring" routine: %s' % PM_settings[key])
		payload = [
				[int(PM_settings[key]['command']), 'int16'],
				[0, 'uint16'],
				[0, 'uint16'],
				[0, 'uint16'],
				[int(PM_settings[key]['Power System Configuration']), 'uint16'],
				[int(PM_settings[key]['Nominal Frequency']), 'uint16'],
				[0, 'float32'],
				[0, 'float32'],
				[0, 'float32'],
				[0, 'uint16'],
				[0, 'uint16'],
				[float(PM_settings[key]['VT Primary']), 'float32'],
				[int(PM_settings[key]['VT Secondary']), 'uint16'],
				[int(PM_settings[key]['Number of CTs']), 'uint16'],
				[int(PM_settings[key]['CT Primary']), 'uint16'],
				[int(PM_settings[key]['CT Secondary']), 'uint16'],
				[0, 'uint16'],
				[0, 'uint16'],
				[0, 'uint16'],
				[0, 'uint16'],
				[int(PM_settings[key]['VT Connection type']), 'uint16']
			]
		payload_processed = self.encode_data(payload)
		ret = self._modbusWrite(command=PM_settings[key]['command'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		log.debug('End "cmd_set_wiring" routine: %s' % ret)

	def cmd_set_pulse_output(self, key='Set Pulse Output'):
		log.debug('Start "cmd_set_pulse_output" routine: %s' % PM_settings[key])
		payload = [
				[int(PM_settings[key]['command']), 'int16'],
				[0, 'uint16'],
				[0, 'uint16'],
				[int(PM_settings[key]['Pulse Output enable']), 'uint16'],
				[float(PM_settings[key]['Pulse constant']), 'float32'],
				[0, 'uint16'],
				[0, 'uint16'],
				[float(0), 'float32'],
				[0, 'uint16'],
				[0, 'uint16'],
				[float(0), 'float32'],
			]
		payload_processed = self.encode_data(payload)
		ret = self._modbusWrite(command=PM_settings[key]['command'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)

		payload = [
				[int(PM_settings[key]['command2']), 'int16'],
				[0, 'uint16'],
				[0, 'uint16'],
				[int(PM_settings[key]['Pulse width']), 'uint16'],
			]
		payload_processed = self.encode_data(payload)
		ret2 = self._modbusWrite(command=PM_settings[key]['command2'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		log.debug('End "cmd_set_pulse_output" routine: %s %s' % (ret, ret2))

	def cmd_set_tariff(self, key='Set Tariff'):
		log.debug('Start "cmd_set_tariff" routine: %s' % PM_settings[key])
		payload = [
			[int(PM_settings[key]['command']), 'int16'],
			[0, 'uint16'],
			[int(PM_settings[key]['Multi Tariff Mode']), 'uint16']
		]
		payload_processed = self.encode_data(payload)
		ret = self._modbusWrite(command=PM_settings[key]['command'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		payload = [
			[int(PM_settings[key]['command2']), 'int16'],
			[0, 'uint16'],
			[int(PM_settings[key]['Tariff']), 'uint16']
		]
		payload_processed = self.encode_data(payload)
		ret2 = self._modbusWrite(command=PM_settings[key]['command'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		log.debug('End "cmd_set_tariff" routine: %s %s' % (ret, ret2))

	def cmd_set_digital_input_as_partial_energy_reset(self, key='Set Digital Input as Partial Energy Reset'):
		log.debug('Start "cmd_set_digital_input_as_partial_energy_reset" routine: %s' % PM_settings[key])
		payload = [
			[int(PM_settings[key]['command']), 'int16'],
			[0, 'uint16'],
			[int(PM_settings[key]['Digital Input to Associate']), 'uint16']
		]
		payload_processed = self.encode_data(payload)
		ret = self._modbusWrite(command=PM_settings[key]['command'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		log.debug('End "cmd_set_digital_input_as_partial_energy_reset" routine: %s' % ret)

	def cmd_input_metering_setup(self, key='Input Metering Setup'):
		log.debug('Start "cmd_input_metering_setup" routine: %s' % PM_settings[key])
		payload = [
			[int(PM_settings[key]['command']), 'int16'],
			[0, 'uint16'],
			[int(PM_settings[key]['Input Metering Channel']), 'uint16'],
			[PM_settings[key]['Label'], 'str'],
			[float(PM_settings[key]['Pulse Weight']), 'float32'],
			[0, 'uint16'],
			[int(PM_settings[key]['Digital Input Association']), 'uint16']
		]
		payload_processed = self.encode_data(payload)
		ret = self._modbusWrite(command=PM_settings[key]['command'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		log.debug('End "cmd_input_metering_setup" routine: %s' % ret)

	def cmd_overload_alarm_setup(self, key='Overload Alarm Setup'):
		log.debug('Start "cmd_overload_alarm_setup" routine: %s' % PM_settings[key])
		payload = [
			[int(PM_settings[key]['command']), 'int16'],
			[0, 'uint16'],
			[int(PM_settings[key]['Alarm ID']), 'uint16'],
			[0, 'uint16'],
			[0, 'uint16'],
			[0, 'uint16'],
			[int(PM_settings[key]['Enabled']), 'uint16'],
			[float(PM_settings[key]['Pickup value']), 'float32'],
			[0, 'uint32'],
			[0, 'float32'],
			[0, 'uint32'],
			[0, 'uint16'],
			[0, 'uint16'],
			[0, 'uint16'],
			[0, 'uint16']
		]
		payload_processed = self.encode_data(payload)
		ret = self._modbusWrite(command=PM_settings[key]['command'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		payload = [
			[int(PM_settings[key]['command2']), 'int16'],
			[0, 'uint16'],
			[0, 'float32'],
			[0, 'uint32'],
			[int(PM_settings[key]['Digital Output to Associate']), 'bitmap']
		]
		payload_processed = self.encode_data(payload)
		ret2 = self._modbusWrite(command=PM_settings[key]['command'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		payload = [
			[int(PM_settings[key]['command2']), 'int16'],
			[0, 'uint16']
		]
		payload_processed = self.encode_data(payload)
		ret3 = self._modbusWrite(command=PM_settings[key]['command'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		log.debug('End "cmd_overload_alarm_setup" routine: %s %s %s' % (ret, ret2, ret3))

	def cmd_communications_setup(self, key='Communications Setup'):
		log.debug('Start "cmd_communications_setup" routine: %s' % PM_settings[key])
		payload = [
			[int(PM_settings[key]['command']), 'int16'],
			[0, 'uint16'],
			[0, 'uint16'],
			[0, 'uint16'],
			[int(PM_settings[key]['Address']), 'uint16'],
			[int(PM_settings[key]['Baud Rate']), 'uint16'],
			[int(PM_settings[key]['Parity']), 'uint16'],
			[0, 'uint16']
		]
		payload_processed = self.encode_data(payload)
		ret = self._modbusWrite(command=PM_settings[key]['command'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		log.debug('End "cmd_communications_setup" routine: %s' % ret)

	def cmd_reset_partial_energy_counters(self, key='Reset Partial Energy Counters'):
		log.debug('Start "cmd_reset_partial_energy_counters" routine: %s' % PM_settings[key])
		payload = [
			[int(PM_settings[key]['command']), 'int16']
		]
		payload_processed = self.encode_data(payload)
		ret = self._modbusWrite(command=PM_settings[key]['command'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		log.debug('End "cmd_reset_partial_energy_counters" routine: %s' % ret)

	def cmd_reset_input_metering_counter(self, key='Reset Input Metering Counter'):
		log.debug('Start "cmd_reset_input_metering_counter" routine: %s' % PM_settings[key])
		payload = [
			[int(PM_settings[key]['command']), 'int16']
		]
		payload_processed = self.encode_data(payload)
		ret = self._modbusWrite(command=PM_settings[key]['command'],base_address=self.PM_base_commands, value=payload_processed, mb_funcall=16, force=True)
		log.debug('End "cmd_reset_input_metering_counter" routine: %s' % ret)

