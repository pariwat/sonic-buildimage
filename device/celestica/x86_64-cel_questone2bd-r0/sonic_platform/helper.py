#!/usr/bin/env python

import os
import struct
import subprocess
from mmap import *

SCALE = 16
BIN_BITS = 8
EMPTY_STRING = ""
HOST_CHK_CMD = "docker > /dev/null 2>&1"
BASE_CPLD_PLATFORM = "questone2bd.cpldb"
GETREG_PATH = "/sys/devices/platform/{}/getreg".format(BASE_CPLD_PLATFORM)


class APIHelper():

    def __init__(self):
        pass

    def get_register_value(self, register):
        cmd = "echo {1} > {0}; cat {0}".format(GETREG_PATH, register)
        p = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        raw_data, err = p.communicate()
        return raw_data.strip() if not err else None

    def hex_to_bin(self, ini_string):
        return bin(int(ini_string, SCALE)).zfill(BIN_BITS)

    def is_host(self):
        return os.system(HOST_CHK_CMD) == 0

    def pci_get_value(self, resource, offset):
        status = True
        result = ""
        try:
            fd = os.open(resource, os.O_RDWR)
            mm = mmap(fd, 0)
            mm.seek(int(offset))
            read_data_stream = mm.read(4)
            result = struct.unpack('I', read_data_stream)
        except:
            status = False
        return status, result

    def run_command(self, cmd):
        status = True
        result = ""
        try:
            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_data, err = p.communicate()
            if err == '':
                result = raw_data.strip()
        except:
            status = False
        return status, result

    def run_interactive_command(self, cmd):
        try:
            os.system(cmd)
        except:
            return False
        return True

    def read_txt_file(self, file_path):
        try:
            with open(file_path, 'r') as fd:
                data = fd.read()
                return data.strip()
        except IOError:
            pass
        return None

    def read_one_line_file(self, file_path):
        try:
            with open(file_path, 'r') as fd:
                data = fd.readline()
                return data.strip()
        except IOError:
            pass
        return None

    def search_file_by_contain(self, directory, search_str, file_start):
        for dirpath, dirnames, files in os.walk(directory):
            for name in files:
                file_path = os.path.join(dirpath, name)
                if name.startswith(file_start) and search_str in self._api_helper.read_txt_file(file_path):
                    return dirpath
        return None

    def write_file(self, file_path, data):
        try:
            with open(file_path, 'w') as fd:
                fd.write(str(data))
                return True
        except:
            pass
        return False

    def ipmi_raw(self, netfn, cmd):
        status = True
        result = ""
        try:
            cmd = "ipmitool raw {} {}".format(str(netfn), str(cmd))
            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_data, err = p.communicate()
            if err == '':
                result = raw_data.strip()
            else:
                status = False
        except:
            status = False
        return status, result

    def ipmi_fru_id(self, id, key=None):
        status = True
        result = ""
        try:
            cmd = "ipmitool fru print {}".format(str(
                id)) if not key else "ipmitool fru print {0} | grep '{1}' ".format(str(id), str(key))

            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_data, err = p.communicate()
            if err == '':
                result = raw_data.strip()
            else:
                status = False
        except:
            status = False
        return status, result

    def ipmi_set_ss_thres(self, id, threshold_key, value):
        status = True
        result = ""
        try:
            cmd = "ipmitool sensor thresh '{}' {} {}".format(
                str(id), str(threshold_key), str(value))
            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            raw_data, err = p.communicate()
            if err == '':
                result = raw_data.strip()
            else:
                status = False
        except:
            status = False
        return status, result
