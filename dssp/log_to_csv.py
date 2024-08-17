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
"""Log to CSV converter"""

import argparse
import time
import pandas as pd

def read_record( fs ):
    v = int.from_bytes(fs.read(1), byteorder='little', signed=False)          # version 
    u = []
    t = 0
    if (v < 255):
        n = int.from_bytes(fs.read(1), byteorder='little', signed=False)          # number of bytes in this record
        if ((n>6) and (n<255)):
            t = int.from_bytes(fs.read(4), byteorder='little', signed=False)
            u = fs.read(n-6)        
    return t, u    

def state_change(row):
    u = row["u"]
    row["log_id"] = u[0]
    if u[0] == 0:       # LOG_TYPE_INIT_LOG
        s = 'log init'
    elif u[0] == 1:     # LOG_TYPE_INIT_NODE
        row["node"] = int(u[1])
        row["system_runtime"] = int.from_bytes(u[2:6],byteorder='little',signed=False)
        row["system_cycles"] = int.from_bytes(u[6:10],byteorder='little',signed=False)
        row["heating_runtime"] = int.from_bytes(u[10:14],byteorder='little',signed=False)
        row["heating_cycles"] = int.from_bytes(u[14:18],byteorder='little',signed=False)
    elif u[0] == 2:     # LOG_TYPE_TIME_SCET
        row["scet_coarse"] = int.from_bytes(u[1:5],byteorder='little',signed=False)
        row["scet_fine"] = int.from_bytes(u[5:9],byteorder='little',signed=False)
    elif u[0] == 3:     # LOG_TYPE_TIME_UTC
        row["utc_day"] = int.from_bytes(u[1:3],byteorder='little',signed=False)
        row["utc_ms_of_day"] = int.from_bytes(u[3:7],byteorder='little',signed=False)
        row["utc_sub_ms"] = int.from_bytes(u[7:9], byteorder='little', signed=False)
    elif u[0] == 4:     # LOG_TYPE_CMD_RECEIVED
        pass
    elif u[0] == 5:     # LOG_TYPE_STATE_CHANGE
        row["node"] = int(u[1])
        row["state"] = int(u[2])
    elif u[0] == 6:     # LOG_TYPE_FIRE_CMD
        if (len(u)<6):      # backwards compatibility
            row["fire_cmd"] = u[1:5].hex()
        else:
            row["node"] = int(u[1])
            row["fire_cmd"] = u[2:6].hex()
    elif u[0] == 7:     # LOG_TYPE_FIRE_COUNTERS
        row["node"] = int(u[1])
        row["hot_cycles"] = int.from_bytes(u[2:4],byteorder='little',signed=False)
        row["hot_time"] = int.from_bytes(u[4:8],byteorder='little',signed=False)
        row["hot_pint"] = int.from_bytes(u[8:12],byteorder='little',signed=False)
        row["cold_fu_cycles"] = int.from_bytes(u[12:14],byteorder='little',signed=False)
        row["cold_fu_time"] = int.from_bytes(u[14:18],byteorder='little',signed=False)
        row["cold_fu_pint"] = int.from_bytes(u[18:22],byteorder='little',signed=False)
        row["cold_ox_cycles"] = int.from_bytes(u[22:24],byteorder='little',signed=False)
        row["cold_ox_time"] = int.from_bytes(u[24:28],byteorder='little',signed=False)
        row["cold_ox_pint"] = int.from_bytes(u[28:32],byteorder='little',signed=False)
    elif u[0] == 8:     # LOG_TYPE_ANOMALY
        row["node"] = int(u[1])
        row["anomaly"] = u[2]
    elif u[0] == 9:     # LOG_TYPE_THRUSTER_DATA
        row["node"] = int(u[1])
        row["thruster_state"] = u[2]
        row["temperature"] = int.from_bytes(u[3:5], byteorder='little', signed=False)
        row["pressure"] = int.from_bytes(u[5:7], byteorder='little', signed=False)
        if (len(u)>7):      # backwards compatibility
            row["pressure_integral"] = int.from_bytes(u[7:9], byteorder='little', signed=False)
    elif u[0] == 10:    # LOG_TYPE_FEEDLINE_DATA
        # deprecated but here for backwards compatibility
        row["node"] = int(u[1])
        row["temperature"] = int.from_bytes(u[2:4], byteorder='little', signed=False)
    elif u[0] == 11:    # LOG_TYPE_TANK_DATA
        # deprecated but here for backwards compatibility
        row["node"] = int(u[1])
        row["temperature"] = int.from_bytes(u[2:4],byteorder='little',signed=False)
        if (len(u)<8):      # backwards compatibility
            row["pressure"] = int.from_bytes(u[4:6],byteorder='little',signed=False)
        else:            
            row["pressure"] = int.from_bytes(u[4:8],byteorder='little',signed=False)
    elif u[0] == 12:    # LOG_TYPE_POWER_DATA
        row["node"] = int(u[1])
        row["vact_v"] = int.from_bytes(u[2:4],byteorder='little',signed=False)
        row["vact_i"] = int.from_bytes(u[4:6],byteorder='little',signed=False)
    elif u[0] == 13:    # LOG_TYPE_PDO
        row["pdo_id"] = int.from_bytes(u[1:3],byteorder='little',signed=False)
        row["pdo"] = u[3:].hex()
    elif u[0] == 14:    # LOG_TYPE_FU_FEEDLINE_STATE
        if (len(u)<7):      # backwards compatibility
            row["fu_feedline"] = u[1]
            row["valve_state"] = u[2]
            row["heater_state"] = u[3]
            row["temperature"] = int.from_bytes(u[4:6],byteorder='little',signed=False)
        else:
            row["node"] = int(u[1])
            row["fu_feedline"] = u[2]
            row["valve_state"] = u[3]
            row["heater_state"] = u[4]
            row["temperature"] = int.from_bytes(u[5:7],byteorder='little',signed=False)
    elif u[0] == 15:    # LOG_TYPE_OX_FEEDLINE_STATE
        if (len(u)<7):      # backwards compatibility
            row["ox_feedline"] = u[1]
            row["valve_state"] = u[2]
            row["heater_state"] = u[3]
            row["temperature"] = int.from_bytes(u[4:6],byteorder='little',signed=False)
        else:
            row["node"] = int(u[1])
            row["ox_feedline"] = u[2]
            row["valve_state"] = u[3]
            row["heater_state"] = u[4]
            row["temperature"] = int.from_bytes(u[5:7],byteorder='little',signed=False)
    elif u[0] == 16:    # LOG_TYPE_FEEDLINE_PRESSURE
        row["node"] = int(u[1])
        row["pressure"] = int.from_bytes(u[2:6],byteorder='little',signed=False)
        row["pressure_2"] = int.from_bytes(u[6:10],byteorder='little',signed=False)
    elif u[0] == 17:    # LOG_TYPE_FU_TANK_DATA
        row["node"] = int(u[1])
        row["fu_tank"] = u[2]
        row["heater_state"] = u[3]
        row["temperature"] = int.from_bytes(u[4:6],byteorder='little',signed=False)
    elif u[0] == 18:    # LOG_TYPE_OX_TANK_DATA
        row["node"] = int(u[1])
        row["ox_tank"] = u[2]
        row["heater_state"] = u[3]
        row["temperature"] = int.from_bytes(u[4:6],byteorder='little',signed=False)
    elif u[0] == 19:    # LOG_TYPE_TANK_PRESSURE
        row["node"] = int(u[1])
        row["pressure"] = int.from_bytes(u[2:6],byteorder='little',signed=False)
        row["pressure_2"] = int.from_bytes(u[6:10],byteorder='little',signed=False)
    elif u[0] == 20:    # LOG_TYPE_VDIG_DATA
        row["node"] = int(u[1])
        row["vdig_v"] = int.from_bytes(u[2:4],byteorder='little',signed=False)
        row["vdig_i"] = int.from_bytes(u[4:6],byteorder='little',signed=False)
    return row

def main():
    parser = argparse.ArgumentParser(description="Dawn Aerospace CANopen log to csv converter")
    parser.add_argument("in_file", help="The binary log" )
    parser.add_argument("out_file", help="The csv output" )
    args = parser.parse_args()

    print( f"Reading log data from {args.in_file}")
    print( f"Writing output to {args.out_file}")

    fname = args.out_file    
    l = []
          
    fs = open(args.in_file, "rb")                                  # open log file
    starttime = time.time()        
    processed_records = 0
    try:
        while True:
            t, u = read_record( fs )               
            if (t == 0):
                break                
            if (len(u) > 0):                    
                l.append([t, u])                
            processed_records = processed_records + 1
    except IOError:
        pass

    fs.close()        
    df = pd.DataFrame(l, columns= ["t", "u"])
    df = df.apply(state_change, axis=1)        
    df.to_csv(fname)
    processtime = time.time() - starttime
    print( f"Processed {processed_records} records in {processtime:.3f}s")

if __name__ == "__main__":
    main()
