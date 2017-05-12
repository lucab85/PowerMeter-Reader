#!/usr/bin/python
# coding: utf-8
# Copyright 2017 Luca Berton
__author__ = 'lucab85'

import sys

from pymodbus.constants import Endian
from pymodbus.client.sync import ModbusSerialClient, ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from settings import MODBUS_CONNECTIONRETRY
import unittest

from logmanagement import logmanagement
log = logmanagement.getlog('ModbusWrapperClient', 'utils').getLogger()

class ModbusWrapperClient():
	def __init__(self, modbusUnitAddress, maxRegsRead, modbusTimeout, endian="little"):
		self.client = None
		self.modbusAddress = modbusUnitAddress
		self.bufferStart = 0
		self.bufferEnd = 0
		self.data_buffer = None
		self.maxRegsRead = maxRegsRead
		self.timeout = modbusTimeout
		if endian == 'auto':
			self.endian = Endian.Auto
		elif endian == 'little':
			self.endian = Endian.Little
		else:
			self.endian = Endian.Big
		self.isConnected = False
		self.validaddresses = None
		self.validaddresses_write = None

	def openConnectionSerial(self, modbusSerialPort, modbusMethon, modbusByte, modbusStopBits, modbusParity,
	                         modbusBaudrate, modbusTimeout):
		self.client = ModbusSerialClient(method=modbusMethon, port=modbusSerialPort, stopbits=modbusStopBits,
		                                 bytesize=modbusByte, parity=modbusParity, baudrate=modbusBaudrate,
		                                 timeout=modbusTimeout)
		self.tryReconnect()

	def openConnectionTCP(self, modbusHost, modbusPort):
		self.client = ModbusTcpClient(modbusHost, modbusPort)
		self.tryReconnect()

	def closeConnection(self):
		if self.isConnected is True:
			self.client.close()

	def tryReconnect(self):
		retry = MODBUS_CONNECTIONRETRY+1
		for i in range(1, retry):
			if self.isConnected is False:
				self.isConnected = self.client.connect()
				break
			log.debug("riconessione %s/%s" % (i, retry))

	def load_valid_addresses(self, lista=None):
		log.debug("load_valid_addresses")
		self.validaddresses = lista

	def check_address(self, address):
		if self.validaddresses is None:
			return True
		ret = True if (address in self.validaddresses) else False
		return ret

	def readRegisters(self, address, count, mb_type='uint16', mb_funcall=3, force=False):
		if self.isConnected is False:
			self.tryReconnect()
		tmp = None
		if (self.check_address(address) is True) or (force is True):
			try:
				if mb_funcall == 1:
					# Read Coil Status (FC=01)
					result = self.client.read_coils(address, count=count, unit=self.modbusAddress)
					tmp = result.bits
				elif mb_funcall == 2:
					# Read Dscrete Input (FC=02)
					result = self.client.read_discrete_inputs(address, count=count, unit=self.modbusAddress)
					tmp = result.bits
				elif mb_funcall == 3:
					# Read Holding Registers (FC=03)
					result = self.client.read_holding_registers(address, count=count, unit=self.modbusAddress)
					if result != None:
						tmp = result.registers
				elif mb_funcall == 4:
					# Read Input Registers (FC=04)
					result = self.client.read_input_registers(address, count=count, unit=self.modbusAddress)
					#tmp = result.bits
					if result != None:
						tmp = result.registers
					#log.debug("out: %s" % tmp)
				else:
					log.debug("Function call not supported: %s" % mb_funcall)
					result = None
					tmp = result
			except Exception as e:
				log.exception(e)
		return tmp

	def check_address_write(self, address):
		if self.validaddresses_write is None:
			return True
		ret = True if (address in self.validaddresses_write) else False
		return ret


	def writeRegisters(self, address, value, mb_funcall=5, force=False, skip_encode=False):
		# Refer to "libmodbus" C library: http://libmodbus.org/documentation/
		# log.info('writeRegisters(address="%s", value="%s", mb_funcall="%s"' % (address, value, mb_funcall))
		if self.isConnected is False:
			self.tryReconnect()
		result = None
		if (self.check_address_write(address) is True) or (force is True):
			try:
				if mb_funcall == 5:
					# Single Coil (FC=05) => modbus_write_bit
					result = self.client.write_coil(address, value, unit=self.modbusAddress)
				elif mb_funcall == 6:
					# Single Register (FC=06)
					result = self.client.write_register(address, value, unit=self.modbusAddress, skip_encode=skip_encode)
				elif mb_funcall == 15:
					# Multiple Coils (FC=15) => modbus_write_bits
					result = self.client.write_coils(address, value, unit=self.modbusAddress)
				elif mb_funcall == 16:
					# Multiple Registers (FC=16)
					result = self.client.write_registers(address, value, unit=self.modbusAddress, skip_encode=skip_encode)
				else:
					log.warn("Function call not supported: %s" % mb_funcall)
			except Exception as e:
				log.exception(e)
		return result

	def encode_field(self, value, mb_type='unit16'):
		builder = BinaryPayloadBuilder(endian=self.endian)
		if mb_type == 'bit' or mb_type == 'bits':
			builder.add_bits(value)
		elif mb_type == 'uint8':
			builder.add_8bit_uint(value)
		elif mb_type == 'uint16':
			builder.add_16bit_uint(value)
		elif mb_type == 'uint32':
			builder.add_32bit_uint(value)
		elif mb_type == 'uint64':
			builder.add_64bit_uint(value)
		elif mb_type == 'int8':
			builder.add_8bit_int(value)
		elif mb_type == 'int16':
			builder.add_16bit_int(value)
		elif mb_type == 'int32':
			builder.add_32bit_int(value)
		elif mb_type == 'int64':
			builder.add_64bit_int(value)
		elif mb_type == 'float32':
			builder.add_32bit_float(value)
		elif mb_type == 'float64':
			builder.add_64bit_float(value)
		elif mb_type == 'string' or mb_type == 'str':
			builder.add_string(value)
		else:
			log.warn('Not supported DataType: "%s"' % mb_type)
		return builder.build()

	def readRegistersAndDecode(self, registri, counter, mb_type='uint16', mb_funcall=3, force=False):
		tmp = None
		if (self.check_address(registri) is True) or (force is True):
			ret = self.readRegisters(registri, counter, mb_type, mb_funcall, force)
			if ret is not None:
				tmp = self.decode(ret, counter, mb_type, mb_funcall)
		return tmp

	def decode(self, raw, size, mb_type, mb_funcall=3):
		log.debug('decode param (raw=%s, size=%s, mb_type=%s, mb_funcall=%s)' % (raw, size, mb_type, mb_funcall))
		if mb_funcall == 1:
			# Read Coil Status (FC=01)
			log.debug("decoder FC1 (raw: %s)" % raw)
			decoder = BinaryPayloadDecoder.fromCoils(raw, endian=self.endian)
		elif mb_funcall == 2:
			# Read Discrete Input (FC=02)
			log.debug("decoder FC2 (raw: %s)" % raw)
			decoder = BinaryPayloadDecoder(raw, endian=self.endian)
		elif mb_funcall == 3:
			# Read Holding Registers (FC=03)
			log.debug("decoder FC3 (raw: %s)" % raw)
			decoder = BinaryPayloadDecoder.fromRegisters(raw, endian=self.endian)
		elif mb_funcall == 4:
			# Read Input Registers (FC=04)
			log.debug("decoder stub FC4 (raw: %s)" % raw)
			decoder = BinaryPayloadDecoder(raw, endian=self.endian)
		else:
			log.debug("Function call not supported: %s" % mb_funcall)
			decoder = None

		result = ""
		if mb_type == 'bitmap':
			if size == 1:
				mb_type = 'int8'
			elif size == 2:
				mb_type = 'int16'
			elif size == 2:
				mb_type = 'int32'
			elif size == 4:
				mb_type = 'int64'

		if decoder is None:
			log.debug("decode none")
			result = raw
		else:
			try:
				if mb_type == 'string' or mb_type == 'utf8':
					result = decoder.decode_string(size)
				#elif mb_type == 'bitmap':
				#	result = decoder.decode_string(size)
				elif mb_type == 'datetime':
					result = decoder.decode_string(size)
				elif mb_type == 'uint8':
					result = int(decoder.decode_8bit_uint())
				elif mb_type == 'int8':
					result = int(decoder.decode_8bit_int())
				elif mb_type == 'uint16':
					result = int(decoder.decode_16bit_uint())
				elif mb_type == 'int16':
					result = int(decoder.decode_16bit_int())
				elif mb_type == 'uint32':
					result = int(decoder.decode_32bit_uint())
				elif mb_type == 'int32':
					result = int(decoder.decode_32bit_int())
				elif mb_type == 'uint64':
					result = int(decoder.decode_64bit_uint())
				elif mb_type == 'int64':
					result = int(decoder.decode_64bit_int())
				elif mb_type == 'float32' or mb_type == 'float':
					result = float(decoder.decode_32bit_float())
				elif mb_type == 'float64':
					result = float(decoder.decode_64bit_float())
				elif mb_type == 'bit':
					result = int(decoder.decode_bits())
				elif mb_type == 'bool':
					result = bool(raw[0])
				elif mb_type == 'raw':
					result = raw[0]
				else:
					result = raw
			except ValueError as e:
				log.exception(e)
				result = raw
		return result

	def read1(self, startreg, mb_type, mb_funcall=3):
		return self.readRegisters(startreg, 1, mb_type, mb_funcall)

	def read2(self, startreg, mb_type, mb_funcall=3):
		return self.readRegisters(startreg, 2, mb_type, mb_funcall)

	def read3(self, startreg, mb_type, mb_funcall=3):
		return self.readRegisters(startreg, 3, mb_type, mb_funcall)

	def read4(self, startreg, mb_type, mb_funcall=3):
		return self.readRegisters(startreg, 4, mb_type, mb_funcall)

	def buffer_print(self):
		if not self.bufferReady():
			log.debug('BUFFER empty ---')
		else:
			text = 'BUFFER [%s-%s]: ' % (self.bufferStart, self.bufferEnd)
			i = self.bufferStart
			for item in self.data_buffer:
				text += "%s(%s) " % (i, item)
				i += 1
			log.debug(text)

	def bufferedReadRegisters(self, startreg, counter, mb_type='uint16', mb_funcall=3):
		log.debug('bufferedReadRegisters param (startreg=%s, counter=%s, mb_type=%s, mb_funcall=%s)' %
		          (startreg, counter, mb_type, mb_funcall))

		valido = False
		offset = self.maxRegsRead
		while (offset >= 0) and (valido != True):
			valido = self.check_address(startreg + offset)
			if valido is True:
				self.data_buffer = self.readRegisters(startreg, offset, mb_type, mb_funcall)
				if self.data_buffer != None:
					self.bufferStart = startreg
					self.bufferEnd = startreg + len(self.data_buffer) - 1
			offset -= 1

		self.buffer_print()
		return self.bufferReady()

	def bufferReady(self):
		return True if (self.data_buffer is not None) else False

	def bufferCleanup(self):
		if self.bufferReady():
			self.data_buffer = None

	def inBuffer(self, startreg, conteggio):
		if not self.bufferReady():
			return False
		return True if (
		(startreg >= self.bufferStart) and ((startreg + conteggio) <= self.bufferEnd)) else False

	def cachedRead(self, startreg, counter, mb_type='uint16', mb_funcall=3):
		log.debug('cachedRead param (startreg=%s, counter=%s, mb_type=%s, mb_funcall=%s)' %
		          (startreg, counter, mb_type, mb_funcall))
		if not self.bufferReady():
			self.bufferedReadRegisters(startreg, counter, mb_type, mb_funcall)
		if not self.inBuffer(startreg, counter):
			self.bufferedReadRegisters(startreg, counter, mb_type, mb_funcall)
		regs = []
		i = 0
		while i < counter:
			regs.append(self.data_buffer[startreg - self.bufferStart + i])
			i += 1
		return self.decode(regs, counter, mb_type, mb_funcall)

	def cachedRead1(self, startreg, mb_type='uint16', mb_funcall=3):
		if not self.bufferReady():
			self.bufferedReadRegisters(startreg, 1, mb_type, mb_funcall)
		if not self.inBuffer(startreg, 1):
			self.bufferedReadRegisters(startreg, 1, mb_type, mb_funcall)
		return self.decode(self.data_buffer[startreg - self.bufferStart], 1, mb_type)

	def cachedRead2(self, startreg, mb_type='uint16', mb_funcall=3):
		if not self.bufferReady():
			self.bufferedReadRegisters(startreg, 2, mb_type, mb_funcall)
		if not self.inBuffer(startreg, 2):
			self.bufferedReadRegisters(startreg, 2, mb_type, mb_funcall)

		regs = []
		regs.append(self.data_buffer[startreg - self.bufferStart])
		regs.append(self.data_buffer[startreg - self.bufferStart + 1])
		return self.decode(regs, 2, mb_type)

	def cachedRead3(self, startreg, mb_type='uint16', mb_funcall=3):
		if not self.bufferReady():
			self.bufferedReadRegisters(startreg, 3, mb_type, mb_funcall)
		if not self.inBuffer(startreg, 3):
			self.bufferedReadRegisters(startreg, 3, mb_type, mb_funcall)

		regs = []
		regs.append(self.data_buffer[startreg - self.bufferStart])
		regs.append(self.data_buffer[startreg - self.bufferStart + 1])
		regs.append(self.data_buffer[startreg - self.bufferStart + 2])
		return self.decode(regs, 3, mb_type)

	def cachedRead4(self, startreg, mb_type='uint16', mb_funcall=3):
		if not self.bufferReady():
			self.bufferedReadRegisters(startreg, 4, mb_type, mb_funcall)
		if not self.inBuffer(startreg, 4):
			self.bufferedReadRegisters(startreg, 4, mb_type, mb_funcall)

		regs = []
		regs.append(self.data_buffer[startreg - self.bufferStart])
		regs.append(self.data_buffer[startreg - self.bufferStart + 1])
		regs.append(self.data_buffer[startreg - self.bufferStart + 2])
		regs.append(self.data_buffer[startreg - self.bufferStart + 3])
		return self.decode(regs, 4, mb_type)


class TestModbusWrapperClientTest(unittest.TestCase):
	def test_bufferReady(self):
		mb = ModbusWrapperClient(1, 103, 2)
		self.assertEqual(mb.bufferReady(), False)


if __name__ == '__main__':
	unittest.main()
