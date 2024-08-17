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
# @brief Retrieve log file over serial port
# 

import argparse
import time
import dssp_canopen as dssp


def main():
    parser = argparse.ArgumentParser(description="Dawn Aerospace CANopen DSSP log manager")
    parser.add_argument("file", help="The log file to store data from the target" )
    parser.add_argument("target_id", help="The CANopen node id of the target", type=int)
    parser.add_argument("device", help="The serial interface, typical /dev/ttyUSB0)")
    parser.add_argument("-r", "--region", help="The log number", type=int, choices=range(1,9,1), metavar="[1-8]", default=1)
    parser.add_argument("-e", "--erase", help="Erase log after download", action="store_true")
    parser.add_argument("-b", "--baud_rate", help="Serial baud rate", type=int, default=115200)
    parser.add_argument("-s", "--size", help="Block size, typical 64", type=int, choices=range(1,65,1), metavar="[1-64]", default =64)
    parser.add_argument("-y", "--confirm", help="Answer yes to any questions", action="store_true")
    
    args = parser.parse_args()

    print( "Dawn Aerospace (c) 2021")
    print( "Starting DSSP log manager on ", args.device )

    try:
        gateway = dssp.CanOpenGateway(args.device, args.baud_rate)

        activeLog, last = gateway.upload(args.target_id, 0x201A, 0, dssp.GATEWAY_TYPE_UINT16)
        print( f'Active log is {activeLog}')

        print( f"Writing log data from {args.target_id} to {args.file}")

        # now download the log
        fd = open(args.file, "wb")                                  # open log file
        starttime = time.time()
        bytes_processed = 0
        last = False
        while not(last):
            b, last = gateway.upload(args.target_id, 0x2018, args.region, dssp.GATEWAY_TYPE_DOMAIN, offset=bytes_processed)
            if len(b) == 0:
                break
            bytes_processed += len(b)
            print( bytes_processed, end ='\r', flush = True)
            fd.write(bytearray(b))
        fd.close()
        downloadtime = time.time() - starttime
        print(f"Downloaded {bytes_processed} bytes in {downloadtime:6.1f}s")

        if (args.erase):
            print( f"Erasing log {args.region}.  This takes approximately 15s.. ", end='', flush=True)
            gateway.timeout = 20.0
            gateway.download(args.target_id, 0x2019, args.region, dssp.GATEWAY_TYPE_UINT8, b'\x01')
            gateway.timeout = 2.0
            print( f"Complete")

    except dssp.CanOpenGatewayTimeoutError:
        print( f"No response from node" )
    except FileNotFoundError:
        print( f"{args.file} not found" )
    except ValueError:
        print( "Exiting")
    except:
        print( "Unknown error" )   

    print( "Done" )


if __name__ == "__main__":
    main()
