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
# @file test_loop.py
# @brief DSSP sample code
#
# This code is not representative of flight software.  It is intended
# as a simple example usage of the dssp module.
#
# Requires dssp_canopen module.  See README.md for installation instructions
# If using a serial interface you will probably need to add your user to the 
# dialout group
#
# If using a CAN interface you will need to configure and initailise it for 1Mbps
#
# Example usage for cubedrive:
#   python test_loop.py /tmp/9/uart_rs422 9
# or
#   python test_loop.py /dev/ttyUSB0 9
# or 
#   python test_loop.py can0 9
# 
# Example usage for satdrive:
#   python test_loop.py /tmp/5/uart_rs422 5
# or
#   python test_loop.py /dev/ttyUSB0 5
# or 
#   python test_loop.py can0 5
#
# Try:
#   python test_loop.py -h
#
# !!! 
#     Caution: running this script on a real CubeDrive or Controller 
#     when connected to real hardware will enable heaters and
#     operate isolation valves
# !!!
# 

import time
import argparse
import dssp_canopen as dssp


# celsius to bytes
def cel2bytes(celsius, byte_length=2):
    kelvin = (celsius + 273.15) * 10
    scaled_temp = int(round(kelvin))
    payload = scaled_temp.to_bytes(byte_length, byteorder='little', signed=False)
    return payload

# bytes to celsius
def bytes2cel(byte_sequence):
    value = int.from_bytes(byte_sequence, byteorder='little')
    kelvin = value / 10
    celsius = kelvin - 273.15
    return celsius

def main():
    cmd_line = argparse.ArgumentParser(description="Dawn Aerospace DSSP Test")
    cmd_line.add_argument("device", help="The serial or CAN interface")
    cmd_line.add_argument("node", help="The target node id", type = int)
    cmd_line.add_argument("-b", "--baudrate", help="CAN or Serial baud rate", type=int, default=115200)
    args = cmd_line.parse_args()

    print( "Dawn Aerospace (c) 2022")
    print( "Starting DSSP loop test on ", args.device )

    try:
        gateway = dssp.CanInterface()
        try:
            gateway.connect(channel=args.device)
        except:
            print("Error connecting to ", args.device)
            exit(-1)

        node = gateway.add_node(args.node, None)

        
        node.sdo.download(0x2612, 7, cel2bytes(-1))
        node.sdo.download(0x2614, 7, cel2bytes(23))
        node.sdo.download(0x2616, 5, cel2bytes(23))
        node.sdo.download(0x261E, 5, cel2bytes(23))
        node.sdo.download(0x261A, 5, cel2bytes(23))
        node.sdo.download(0x2622, 5, cel2bytes(23))
        node.sdo.download(0x2617, 5, cel2bytes(23))
        node.sdo.download(0x261F, 5, cel2bytes(23))
        node.sdo.download(0x261B, 5, cel2bytes(23))
        node.sdo.download(0x2623, 5, cel2bytes(23))
        node.sdo.download(0x2500, 1, b'\x05')
        

        while True:
            time.sleep(5)
            try:
                # Read and decode operations
                addresses_and_subindexes = [
                    (0x2612, 7),
                    (0x2614, 7),
                    (0x2616, 5),
                    (0x261E, 5),
                    (0x261A, 5),
                    (0x2622, 5),
                    (0x2617, 5),
                    (0x261F, 5),
                    (0x261B, 5),
                    (0x2623, 5)
                ]

                for address, subindex in addresses_and_subindexes:
                    data = node.sdo.upload(address, subindex)
                    temp_celsius = bytes2cel(data)
                    print(f"Address {hex(address)}, Subindex {subindex}: {temp_celsius:.2f} °C")
            except Exception as e:
                print(f"Error during read operations: {e}")



    except KeyboardInterrupt:
        node.sdo.download(0x2500, 1, b'\x00')
    except:
        print( "Unknown error. Check you have the correct port and permissions to use it." )

if __name__ == "__main__":
    main()
