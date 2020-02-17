#!/usr/bin/env python
#
# Platform-specific PSU control functionality for SONiC
#

__version__ = "0.0.1"

try:
    import os.path
    import subprocess
    from sonic_psu.psu_base import PsuBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

NUM_PSU = 2
PSU_STATUS_REGISTER = "0xA160"
BASE_CPLD_PLATFORM = "questone2bd.cpldb"
GETREG_PATH = "/sys/devices/platform/{}/getreg".format(BASE_CPLD_PLATFORM)

SCALE = 16
BIN_BITS = 8
PRESENT_BIT = '0'
POWER_OK_BIT = '1'
PSU_STATUS_REG_MAP = {
    1: {
        "status": 0,
        "present": 2
    },
    2: {
        "status": 1,
        "present": 3
    },
}


class PsuUtil(PsuBase):
    """Platform-specific PSUutil class"""

    def __init__(self):
        PsuBase.__init__(self)
        self.__get_psu_status()

    def __get_register_value(self, register):
        cmd = "echo {1} > {0}; cat {0}".format(GETREG_PATH, register)
        p = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        raw_data, err = p.communicate()
        return raw_data.strip() if not err else None

    def __hex_to_bin(self, ini_string):
        return bin(int(ini_string, SCALE)).zfill(BIN_BITS)

    def __get_psu_status(self):
        psu_status_raw = self.__get_register_value(PSU_STATUS_REGISTER)
        psu_status_bin = self.__hex_to_bin(psu_status_raw)
        psu_status_all = str(psu_status_bin)[2:][::-1]

        psu_status_dict = dict()
        for psu_num in range(1, NUM_PSU+1):
            psu_status = dict()
            psu_status["status"] = True if psu_status_all[PSU_STATUS_REG_MAP[psu_num]
                                                          ["status"]] == POWER_OK_BIT else False
            psu_status["present"] = True if psu_status_all[PSU_STATUS_REG_MAP[psu_num]
                                                           ["present"]] == PRESENT_BIT else False
            psu_status_dict[psu_num] = psu_status
        return psu_status_dict

    def get_num_psus(self):
        """
        Retrieves the number of PSUs available on the device

        :return: An integer, the number of PSUs available on the device
        """

        return NUM_PSU

    def get_psu_status(self, index):
        """
        Retrieves the oprational status of power supply unit (PSU) defined by 1-based index <index>

        :param index: An integer, 1-based index of the PSU of which to query status
        :return: Boolean, True if PSU is operating properly, False if PSU is faulty
        """
        psu_status_dict = self.__get_psu_status()

        return psu_status_dict[index].get("status", False)

    def get_psu_presence(self, index):
        """
        Retrieves the presence status of power supply unit (PSU) defined by 1-based index <index>

        :param index: An integer, 1-based index of the PSU of which to query status
        :return: Boolean, True if PSU is plugged, False if not
        """
        psu_status_dict = self.__get_psu_status()

        return psu_status_dict[index].get("present", False)
