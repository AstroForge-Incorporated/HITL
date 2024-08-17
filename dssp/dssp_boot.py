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
# @brief DSSP SatDrive Bootloader
#
# Boot SatDrive node over DSSP serial port
# 

import time
import argparse
import dssp_canopen as dssp
from io import SEEK_END

# Naive and slow crc32 calculator is deliberately not the same implementation as
# embedded code
def crc32( initial, buffer ):
    remainder = initial ^ 0xFFFFFFFF    

    for val in buffer:
        remainder = remainder ^ val
        for bit in range(8,0,-1):
            if (remainder & 1):
                remainder = (remainder >> 1) ^ 0xEDB88320
            else:
                remainder = (remainder >> 1)
    return remainder ^ 0xFFFFFFFF

def main():
    parser = argparse.ArgumentParser(description="Dawn Aerospace DSSP CANopen bootloader")
    parser.add_argument("file", help="The binary file to load to the target" )
    parser.add_argument("target_id", help="The CANopen node id of the target", type=int)
    parser.add_argument("device", help="The serial interface, typical /dev/ttyUSB0)")
    parser.add_argument("-r", "--region", help="The flash region to program", type=int, choices=range(1,4,1), metavar="[1-3]", default=2)
    parser.add_argument("-b", "--baud_rate", help="Serial baud rate", type=int, default=115200)
    parser.add_argument("-s", "--size", help="Block size, typical 64", type=int, choices=range(1,65,1), metavar="[1-64]", default =64)
    parser.add_argument("-q", "--quiet", help="Don't ask questions, just load and execute", action="store_true")
    parser.add_argument("-v", "--validate", help="Just sign whats there", action="store_true")
    parser.add_argument("-y", "--confirm", help="Answer yes to any questions", action="store_true")
    parser.add_argument("-e", "--erase", help="Erase region only", action="store_true")

    args = parser.parse_args()

    print( "Dawn Aerospace (c) 2021")
    print( "Starting DSSP bootloader on ", args.device )

    try:
        gateway = dssp.CanOpenGateway(args.device, args.baud_rate)

        target_node = gateway.add_node(args.target_id, None)
        
        # make sure we're in the bootloader by resetting twice
        err = target_node.nmt.reset_node()
        time.sleep(0.5)                      # delay to allow bootloader to start
        err = target_node.nmt.reset_node()

        # show information about the device     
        if not (args.quiet):
            print()
            # read out manufacturer, version numbers and check device type is bootloader
            for index in (0x1008, 0x1009, 0x100A): # device name, h/w and s/w version
                val, last = gateway.upload(args.target_id, index, 0, dssp.GATEWAY_TYPE_STRING)
                if (val != None):
                    print ('%-30s' % ("OD[" + hex(index) + "]"), ":", val)

            print( '%-30s' % "Flash region", ":", args.region)
            region_length, last = gateway.upload(args.target_id, 0x1F58, args.region, dssp.GATEWAY_TYPE_UINT32)  
            print( '%-30s' % "Flash region length", ":", region_length)

            # read out the current signature
            sig, last = gateway.upload(args.target_id, 0x1F56, args.region, dssp.GATEWAY_TYPE_UINT32)
            print( '%-30s' % "Flash region signature", ": %08X" % sig )

        if not(args.quiet):
            print("Unlocking...")
        gateway.download(args.target_id, 0x7F50, args.region, dssp.GATEWAY_TYPE_UINT32, b'INIT' )     # unlocks flash region

        if not (args.validate):
            # erase flash and download the binary 
            if (args.quiet) or (args.confirm):
                ch = 'Y'
            elif(args.erase):
                ch = input( f"Erase flash region {args.region} on node {args.target_id}? [y/N]" )
            else:
                ch = input( f"Erase flash region {args.region} and download {args.file} to node {args.target_id}? [y/N]" )

            if (ch[0].upper() != 'Y'):
                raise(ValueError)

            if not(args.quiet):
                print("Erasing...", end ='')
            
            starttime = time.time()
            gateway.download(args.target_id, 0x1F51, args.region, dssp.GATEWAY_TYPE_UINT8, b'\x03')      # erase flash block
            erasetime = time.time() - starttime
            if not(args.quiet):
                print( f"\rErased flash in {erasetime:.2f} s")

            time.sleep(2.0)
            
            if not (args.erase):
                # now download the firmware
                fs = open(args.file, "rb")                                  # open firmware file
                fs.seek(0, SEEK_END)
                filelen = fs.tell()                                         # find length
                fs.seek(0)
                if not (args.quiet):
                    print(f"About to download {filelen} bytes")
                starttime = time.time()
                blocknum = 0
                crc = 0
                bytes_processed = 0
                while True:
                    b = fs.read(args.size)
                    if len(b) == 0:
                        break
                    if (filelen > 0 ) and not (args.quiet):
                        print (f'\r{((blocknum*args.size)/filelen):.0%} ', end='')
                    gateway.download(args.target_id, 0x1F50, args.region, dssp.GATEWAY_TYPE_DOMAIN, b, blocknum*args.size, False )
                        
                    bytes_processed += len(b)
                    crc = crc32(crc, b)
                    blocknum = blocknum + 1

                # force the target to commit buffers to flash
                gateway.download(args.target_id, 0x1F50, args.region, dssp.GATEWAY_TYPE_DOMAIN, b, blocknum*args.size, True )

                # close file
                fs.close()

                # record the time it took for the download
                downloadtime = time.time() - starttime

                if not(args.quiet):
                    print( f"Downloaded file in {downloadtime:.2f} s")

                # calculate file signature by padding rest of the region with 0xFF
                erased_byte= {0xff}
                while (bytes_processed < region_length):
                    crc = crc32(crc, erased_byte)
                    bytes_processed += 1

                # read the newly generated signature from device
                val, last = gateway.upload(args.target_id, 0x1F56, args.region, dssp.GATEWAY_TYPE_UINT32 )
                
                if not(args.quiet):
                    print( '%-30s' % "File signature",  ": %08X" % crc )
                    print( '%-30s' % "Flash signature", ": %08X" % val )

                # compare the file and flash signatures
                if (crc != val):
                    print( "Signature is invalid, download failed ")
                    gateway.download(args.target_id, 0x1F51, args.region, dssp.GATEWAY_TYPE_UINT8, b'\x84')       # clear signature in device
                    return

        # validate signature
        if not( args.erase ):
            if not(args.quiet):
                print( "Setting signature to valid")
            gateway.download(args.target_id, 0x1F51,args.region, dssp.GATEWAY_TYPE_UINT8, b'\x83')
            
    except dssp.CanOpenGatewayTimeoutError:
        print( f"No response from node" )
    except FileNotFoundError:
        print( f"{args.file} not found" )
    except ValueError:
        print( "Exiting")
    except:
        print( "Unknown error" )

    try:
        if (not(args.erase)):
            if (args.quiet) or (args.confirm):
                ch = 'Y'
            else:
                ch = input( f"Do you want to execute {args.file} on node {args.target_id}? [y/N]" )

                if (ch[0].upper() != 'Y'):
                    raise(ValueError)

            print( "Executing")
            gateway.download(args.target_id, 0x1F51, args.region, dssp.GATEWAY_TYPE_UINT8, b'\x01' )

    except dssp.CanOpenGatewayTimeoutError:
        # expected
        pass
    except ValueError:
        # chose not to execute 
        pass
    except:
        print( "Unknown error" )

    # print some stats before we exit
    print()
    print( f"Tx count   {gateway.tx_count}")
    print( f"Tx ack     {gateway.tx_ack}")
    print( f"Rx count   {gateway.rx_count}")


if __name__ == "__main__":
    main()
