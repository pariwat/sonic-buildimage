#!/usr/bin/env python

#############################################################################
# Celestica
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Chassis information which are available in the platform
#
#############################################################################

import sys
import re
import os
import subprocess
import json
import time

try:
    from sonic_platform_base.chassis_base import ChassisBase
    # from sonic_platform.component import Component
    from sonic_platform.eeprom import Tlv
    from sonic_platform.fan import Fan
    # from sonic_platform.sfp import Sfp
    from sonic_platform.psu import Psu
    from sonic_platform.thermal import Thermal
    from helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

NUM_FAN_TRAY = 7
NUM_FAN = 2
NUM_PSU = 2
NUM_THERMAL = 14
NUM_QSFPDD = 6
NUM_QSFP = 24
NUM_COMPONENT = 5

IPMI_OEM_NETFN = "0x3A"
IPMI_GET_REBOOT_CAUSE = "0x03 0x00 0x01 0x06"


class Chassis(ChassisBase):
    """Platform-specific Chassis class"""

    def __init__(self):
        self.config_data = {}
        ChassisBase.__init__(self)
        self._eeprom = Tlv()
        self._api_helper = APIHelper()

        for fant_index in range(0, NUM_FAN_TRAY):
            for fan_index in range(0, NUM_FAN):
                fan = Fan(fant_index, fan_index)
                self._fan_list.append(fan)

        for index in range(0, NUM_PSU):
            psu = Psu(index)
            self._psu_list.append(psu)

        # for index in range(0, NUM_SFP):
        #     sfp = Sfp(index)
        #     self._sfp_list.append(sfp)

        # for index in range(0, NUM_COMPONENT):
        #     component = Component(index)
        #     self._component_list.append(component)

        for index in range(0, NUM_THERMAL):
            thermal = Thermal(index)
            self._thermal_list.append(thermal)

        # Initial Interrup MASK for QSFP, QSFPDD
        PATH_QSFP_SYSFS = "/sys/devices/platform/cls-xcvr/QSFP{0}/interrupt_mask"
        PATH_QSFPDD_SYSFS = "/sys/devices/platform/cls-xcvr/QSFPDD{0}/interrupt_mask"
        for i in range(NUM_QSFP):
            self._api_helper.write_hex_value(PATH_QSFP_SYSFS.format(i+1), 255)
        for i in range(NUM_QSFPDD):
            self._api_helper.write_hex_value(PATH_QSFPDD_SYSFS.format(i+1), 255)

    def get_base_mac(self):
        """
        Retrieves the base MAC address for the chassis
        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        return self._eeprom.get_mac()

    def get_serial_number(self):
        """
        Retrieves the hardware serial number for the chassis
        Returns:
            A string containing the hardware serial number for this chassis.
        """
        return self._eeprom.get_serial()

    def get_system_eeprom_info(self):
        """
        Retrieves the full content of system EEPROM information for the chassis
        Returns:
            A dictionary where keys are the type code defined in
            OCP ONIE TlvInfo EEPROM format and values are their corresponding
            values.
        """
        return self._eeprom.get_eeprom()

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot

        Returns:
            A tuple (string, string) where the first element is a string
            containing the cause of the previous reboot. This string must be
            one of the predefined strings in this class. If the first string
            is "REBOOT_CAUSE_HARDWARE_OTHER", the second string can be used
            to pass a description of the reboot cause.
        """

        status, raw_cause = self._api_helper.ipmi_raw(
            IPMI_OEM_NETFN, IPMI_GET_REBOOT_CAUSE)
        hx_cause = raw_cause.split()[0] if status and len(
            raw_cause.split()) > 0 else 00
        reboot_cause = {
            "00": self.REBOOT_CAUSE_HARDWARE_OTHER,
            "11": self.REBOOT_CAUSE_POWER_LOSS,
            "22": self.REBOOT_CAUSE_NON_HARDWARE,
            "33": self.REBOOT_CAUSE_HARDWARE_OTHER,
            "44": self.REBOOT_CAUSE_NON_HARDWARE,
            "55": self.REBOOT_CAUSE_NON_HARDWARE,
            "66": self.REBOOT_CAUSE_WATCHDOG,
            "77": self.REBOOT_CAUSE_NON_HARDWARE
        }.get(hx_cause, self.REBOOT_CAUSE_HARDWARE_OTHER)

        description = {
            "00": "Unknown reason",
            "11": "The last reset is Power on reset",
            "22": "The last reset is soft-set CPU warm reset",
            "33": "The last reset is soft-set CPU cold reset",
            "44": "The last reset is CPU warm reset",
            "55": "The last reset is CPU cold reset",
            "66": "The last reset is watchdog reset",
            "77": "The last reset is power cycle reset"
        }.get(hx_cause, "Unknown reason")

        return (reboot_cause, description)

    ##############################################################
    ####################### Other methods ########################
    ##############################################################

    def get_watchdog(self):
        """
        Retreives hardware watchdog device on this chassis
        Returns:
            An object derived from WatchdogBase representing the hardware
            watchdog device
        """
        if self._watchdog is None:
            from sonic_platform.watchdog import Watchdog
            self._watchdog = Watchdog()

        return self._watchdog

    ##############################################################
    ###################### Device methods ########################
    ##############################################################

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        return self._api_helper.hwsku

    def get_presence(self):
        """
        Retrieves the presence of the PSU
        Returns:
            bool: True if PSU is present, False if not
        """
        return True

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        return self._eeprom.get_pn()

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        return self.get_serial_number()

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return True

    ##############################################################
    ###################### Event methods ########################
    ##############################################################       
    def __clear_interrupt(self, name): 
        PATH_QSFP_SYSFS = "/sys/devices/platform/cls-xcvr/{0}/interrupt"
        self._api_helper.write_hex_value(PATH_QSFP_SYSFS.format(name),255)
        time.sleep(0.5)
        self._api_helper.write_hex_value(PATH_QSFP_SYSFS.format(name),0)
        return self._api_helper.read_txt_file(PATH_QSFP_SYSFS.format(name))

    def __check_devices_status(self, name):
        PATH_QSFP_SYSFS = "/sys/devices/platform/cls-xcvr/{0}/qsfp_modprsL"
        return self._api_helper.read_txt_file(PATH_QSFP_SYSFS.format(name))

    def __compare_event_object(self, interrup_devices):
        QSFP_devices = {}
        QSFPDD_devices = {}
        json_obj = {}

        for device_name in interrup_devices:
            if "QSFP" in device_name:
                QSFP_devices[device_name] = 1 - int(self.__check_devices_status(device_name))
            if "QSFPDD" in device_name:
                QSFPDD_devices[device_name] = 1 - int(self.__check_devices_status(device_name))
            self.__clear_interrupt(device_name)

        if len(QSFP_devices):
            json_obj['qsfp'] = QSFP_devices
        if len(QSFPDD_devices):
            json_obj['qsfp-dd'] = QSFPDD_devices
        return json.dumps(json_obj)

    def __check_all_interrupt_event(self):
        interrup_device = {}

        QSFP_NAME = "QSFP{0}"
        QSFPDD_NAME = "QSFPDD{0}"
        PATH_QSFP_SYSFS = "/sys/devices/platform/cls-xcvr/QSFP{0}/interrupt"
        PATH_QSFPDD_SYSFS = "/sys/devices/platform/cls-xcvr/QSFPDD{0}/interrupt"

        for i in range(NUM_QSFP):
            if self._api_helper.read_txt_file(PATH_QSFP_SYSFS.format(i+1)) != '0x00':
                interrup_device[QSFP_NAME.format(i+1)] = 1

        for i in range(NUM_QSFPDD):
            if self._api_helper.read_txt_file(PATH_QSFPDD_SYSFS.format(i+1)) != '0x00':
                interrup_device[QSFPDD_NAME.format(i+1)] = 1
                
        return interrup_device

    def get_change_event(self, timeout=0):
        if timeout == 0 :
            flag_change = True
            while flag_change:
                interrup_device = self.__check_all_interrupt_event()
                if len(interrup_device):
                    flag_change = False
                else:
                    time.sleep(0.5)
            return (True , self.__compare_event_object(interrup_device))
        else:
            device_list_change = {}
            while timeout:
                interrup_device = self.__check_all_interrupt_event()
                time.sleep(1)
                timeout -= 1;
            device_list_change = self.__compare_event_object(interrup_device)
            return (True , device_list_change)