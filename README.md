# PowerMeter Reader

Python code to read energetic usage data from a modbus connected 
PowerMeter device.

![PowerMeter Image](http://www.schneider-electric.com/en/product-image/238723-acti-9-iem3000)

Tested with device [Schneider Electric iEM3255](http://www.schneider-electric.com/en/product-range/61273-acti-9-iem3000/) (Acti 9 iEM 3000 series - code _A9MEM3255_)

## List of files

* main
Star class file

* SchneiderElectric_iEM3255
Class to read data from the device

* ModbusWrapperClient
Wrapper of pymodbus library with buffering support

* logmanagement
Simple log manager to save logs under 'logs/'

* settings.py
Configuration variables (device IP etc.)

* configs/

  * logging.json
  Logging settings

  * Map-Schneider-iEM3255.csv
  Modbus registry map file
