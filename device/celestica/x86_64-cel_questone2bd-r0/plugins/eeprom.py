#!/usr/bin/env python
#
# Platform and model specific eeprom subclass, inherits from the base class and provides the followings:
# - the eeprom format definition
# - specific encoder/decoder if there is special need
#

__version__ = "0.0.1"

try:
    from sonic_eeprom import eeprom_tlvinfo
except ImportError, e:
    raise ImportError(str(e) + "- required module not found")

TLV_I2C = "i2c-0"
TLV_REG = "0-0056"
TLV_PATH = "/sys/class/i2c-adapter/{}/{}/eeprom".format(TLV_I2C, TLV_REG)


class board(eeprom_tlvinfo.TlvInfoDecoder):

    def __init__(self, name, path, cpld_root, ro):
        self.eeprom_path = TLV_PATH
        super(board, self).__init__(self.eeprom_path, 0, '', True)
