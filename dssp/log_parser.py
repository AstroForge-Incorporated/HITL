#!/bin/python
#
#               /|\
#              / | \
#             /  |  \
#            /   |   \
#           /   / \   \
#          /   //|\\   \
#         /   // | \\   \  (c) Dawn Aerospace Ltd
#        /___//_/ \_\\___\  www.dawnaerospace.com
#
# @file log_parser.py
# @brief 
# 

import argparse
import struct
import time
import os
import sys

from numpy import byte


    
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def read_record( fs ):
    v = int.from_bytes(fs.read(1), byteorder='little', signed=False)          # version 
    u = []
    t = 0
    if (v < 255):
        n = int.from_bytes(fs.read(1), byteorder='little', signed=False)          # number of bytes in this record
        if ((n>6) and (n<255)):
            t = int.from_bytes(fs.read(4), byteorder='little', signed=False)
            u = fs.read(n-6)
        # print( v, n, t, u )
    return t, u    

def parse_record( u ):
    s = ''
    if (u[0] == 0):     # LOG_TYPE_INIT_LOG
        s = 'log init'
    elif (u[0] == 1):   # LOG_TYPE_INIT_NODE
        s = "Node {0} Initialised system:(cycles={1}, runtime={2}), heating:(cycles={3}, runtime ={4})".format(u[1], int.from_bytes(u[2:6],byteorder='little',signed=False), int.from_bytes(u[6:10],byteorder='little',signed=False), int.from_bytes(u[10:14],byteorder='little',signed=False), int.from_bytes(u[14:18],byteorder='little',signed=False))
    elif (u[0] == 2):   # LOG_TYPE_TIME_SCET
        s = 'scet'
    elif (u[0] == 3):   # LOG_TYPE_TIME_UTC
        s = 'utc'
    elif (u[0] == 4):   # LOG_TYPE_CMD_RECEIVED
        s = 'cmd'
    elif (u[0] == 5):   # LOG_TYPE_STATE_CHANGE
        s = "Node {0} State Change to {1}".format(u[1],u[2])
    elif (u[0] == 6):   # LOG_TYPE_FIRE_CMD
        if (len(u)<6):      # backwards compatibility
            s = "Fire Cmd " + u[1:5].hex()
        else:
            s = "Node {0}".format(u[1])
            s = s + " Fire Cmd " + u[2:6].hex()
    elif (u[0] == 7):   # LOG_TYPE_FIRE_COUNTERS
        s = "Node {0} Fire Counters".format(u[1])
        s = s + ' hot:(cycles={}, time={}, pint={})'.format(int.from_bytes(u[2:4],byteorder='little',signed=False), int.from_bytes(u[4:8],byteorder='little',signed=False), int.from_bytes(u[8:12],byteorder='little',signed=False))
        s = s + ' cold_fu:(cycles={}, time={}, pint={})'.format(int.from_bytes(u[12:14],byteorder='little',signed=False), int.from_bytes(u[14:18],byteorder='little',signed=False), int.from_bytes(u[18:22],byteorder='little',signed=False))
        s = s + ' cold_ox:(cycles={}, time={}, pint={})'.format(int.from_bytes(u[22:24],byteorder='little',signed=False), int.from_bytes(u[24:28],byteorder='little',signed=False), int.from_bytes(u[28:32],byteorder='little',signed=False))
    elif (u[0] == 8):   # LOG_TYPE_ANOMALY
        s = "Node {0} Anomaly {1}".format(u[1], u[2])
    elif (u[0] == 9):   # LOG_TYPE_THRUSTER_DATA
        s = "Node {0} Thruster state={1},".format(u[1], u[2])
        s = s + ' temp={}x0.1K, pressure={}mBar'.format(int.from_bytes(u[3:5],byteorder='little',signed=False), int.from_bytes(u[5:7],byteorder='little',signed=False))
        if (len(u)>7):      # backwards compatibility
            s = s + ' integral={}mBar.s'.format(int.from_bytes(u[7:9],byteorder='little',signed=False))
    elif (u[0] == 10):  # LOG_TYPE_FEEDLINE_DATA
        # deprecated but here for backwards compatibility
        s = "Node {0} Feedline".format(u[1])
        s = s + ' temp={}x0.1K'.format(int.from_bytes(u[3:5],byteorder='little',signed=False))
    elif (u[0] == 11):  # LOG_TYPE_TANK_DATA
        # deprecated but here for backwards compatibility
        s = "Node {0} Tank".format(u[1])
        s = s + ' temp={}x0.1K'.format(int.from_bytes(u[2:4],byteorder='little',signed=False))
        if (len(u)<8):      # backwards compatibility
            s = s + ' pressure={}mBar'.format(int.from_bytes(u[4:6],byteorder='little',signed=False))
        else:
            s = s + ' pressure={}mBar'.format(int.from_bytes(u[4:8],byteorder='little',signed=False))
    elif (u[0] == 12):  # LOG_TYPE_POWER_DATA
        s = "Node {0} Power".format(u[1])
        s = s + ' Vact V={}mV, I={}mA'.format(int.from_bytes(u[2:4],byteorder='little',signed=False),int.from_bytes(u[4:6],byteorder='little',signed=False))
    elif (u[0] == 13):  # LOG_TYPE_PDO
        s = "PDO id={}".format(int.from_bytes(u[1:3],byteorder='little',signed=False))
        s = s + ' ' + u[3:].hex()
    elif (u[0] == 14):  # LOG_TYPE_FU_FEEDLINE_STATE
        if (len(u)<7):      # backwards compatibility
            s = s + "Fu Feedline [{}]".format(u[1])
            s = s + ' valve state={}, heater state={}, temperature={}x0.1K'.format(u[2], u[3], int.from_bytes(u[4:6],byteorder='little',signed=False))
        else:
            s = "Node {0} Feedline".format(u[1])
            s = s + " Fu [{}]".format(u[2])
            s = s + ' valve state={}, heater state={}, temperature={}x0.1K'.format(u[3], u[4], int.from_bytes(u[5:7],byteorder='little',signed=False))
    elif (u[0] == 15):  # LOG_TYPE_OX_FEEDLINE_STATE
        if (len(u)<7):      # backwards compatibility
            s = "Ox Feedline [{}]".format(u[1])
            s = s + ' valve state={}, heater state={}, temperature={}x0.1K'.format(u[2], u[3], int.from_bytes(u[4:6],byteorder='little',signed=False))
        else:
            s = "Node {0} Feedline".format(u[1])
            s = s + " Ox [{}]".format(u[2])
            s = s + ' valve state={}, heater state={}, temperature={}x0.1K'.format(u[3], u[4], int.from_bytes(u[5:7],byteorder='little',signed=False))
    elif (u[0] == 16):  # LOG_TYPE_FEEDLINE_PRESSURE
        s = "Node {} Feedline".format(u[1])
        s = s + ' Fu pressure={}mBar, Ox pressure={}mBar'.format(int.from_bytes(u[2:6],byteorder='little',signed=False), int.from_bytes(u[6:10],byteorder='little',signed=False))
    elif (u[0] == 17):  # LOG_TYPE_FU_TANK_DATA
        s = "Node {} Tank".format(u[1])
        s = s + " Fu [{}]".format(u[2])
        s = s + ' heater state={}, temperature={}x0.1K'.format(u[3], int.from_bytes(u[4:6],byteorder='little',signed=False))
    elif (u[0] == 18):  # LOG_TYPE_OX_TANK_DATA
        s = "Node {} Tank".format(u[1])
        s = s + " Ox [{}]".format(u[2])
        s = s + ' heater state={}, temperature={}x0.1K'.format(u[3], int.from_bytes(u[4:6],byteorder='little',signed=False))
    elif (u[0] == 19):  # LOG_TYPE_TANK_PRESSURE
        s = "Node {} Tank".format(u[1])
        s = s + ' Fu pressure={}mBar, Ox pressure={}mBar'.format(int.from_bytes(u[2:6],byteorder='little',signed=False), int.from_bytes(u[6:10],byteorder='little',signed=False))
    elif (u[0] == 20):  # LOG_TYPE_VDIG_DATA
        s = "Node {0} Power".format(u[1])
        s = s + ' Vdig V={}mV, I={}mA'.format(int.from_bytes(u[2:4],byteorder='little',signed=False),int.from_bytes(u[4:6],byteorder='little',signed=False))
    else:
        s = 'unknown record'
    return s

def main():
    parser = argparse.ArgumentParser(description="Dawn Aerospace CANopen log parser")
    parser.add_argument("in_file", help="The binary log" )
    parser.add_argument("out_file", help="The text output" )
    args = parser.parse_args()

    print( f"Reading log data from {args.in_file}")
    print( f"Writing output to {args.out_file}")

    try:
        fd = open( args.out_file, "wt")
        fs = open(args.in_file, "rb")                                  # open log file
        starttime = time.time()
        major_version = 0
        minor_Version = 0
        processed_records = 0
        try:
            while True:
                t, u = read_record( fs )
                if (t == 0):
                    break
                fd.write( '{:010}: '.format(t) )
                if (len(u) > 0):
                    fd.write(parse_record(u))
                fd.write('\n')
                processed_records = processed_records + 1
        except IOError:
            pass

        fs.close()
        fd.close()
        processtime = time.time() - starttime
        print( f"Processed {processed_records} records in {processtime:.3f}s")
    except:
        print( f"Error" )
        pass


if __name__ == "__main__":
    main()
