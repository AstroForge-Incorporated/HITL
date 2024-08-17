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
# @file test_rsp.py
# @date 20th October 2021
# @author Andrew Dachs
# @brief DSSP Gateway Upload response test
#
# Command line ascii gateway for DSSP connected CanOpen node
# 

import time
import argparse
import dssp_canopen as dssp

class TestDsspGateway(dssp.DsspGateway):
    def __init__(self, node, port, baudrate = 115200 ):
        dssp.DsspGateway.__init__(self, port, baudrate)
        self.gtp_msg = dssp.GatewayTransportMessage( dssp.GATEWAY_MSG_SDO, dssp.GatewayTransportProtocol.GATEWAY_CMD_SDO_UPLOAD, 
                                                node=node, index = 0x1005, subindex=0, payload_type=7 )
        #self.s = 0
        self.loopback = False

    def __del__(self):
        dssp.DsspGateway.__del__(self)

    def rxInd( self, msg):
        #e = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
        #print( "Rsp time: ", (e-self.s)/1E6, " ms")
        if (self.loopback == True):
            self.post(self.gtp_msg)
        return

    def txCnf( self, error_code ):
        if (error_code == 0):
            if (self.loopback == True):
                self.post(self.gtp_msg)
        else:
            print( "\rERROR(", error_code, ")", end= '\n', flush=True )
        
    def post( self, msg ):
        #self.s = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
        dssp.DsspGateway.post(self, msg)

    def start(self):
        self.loopback = True
        self.post(self.gtp_msg)

    def stop(self):
        self.loopback = False

def main():
    cmd_line = argparse.ArgumentParser(description="Dawn Aerospace DSSP Response Test")
    cmd_line.add_argument("device", help="The serial interface")
    cmd_line.add_argument("node", help="The target node id", type = int)
    cmd_line.add_argument("-b", "--baudrate", help="Serial baud rate", type=int, default=115200)
    cmd_line.add_argument("-t", "--time", help="Test duration", type=float, default=3)
    args = cmd_line.parse_args()

    print( "Dawn Aerospace (c) 2021")
    print( "Starting DSSP test gateway on ", args.device )


    gateway = TestDsspGateway(args.node, args.device, args.baudrate)

    print( f"Waiting for {args.time} seconds")
    gateway.start()        # kick start
    time.sleep(args.time)
    gateway.stop()

    time.sleep(0.1)
    print( f"Tx count   {gateway.tx_count}")
    print( f"Tx ack     {gateway.tx_ack}")
    print( f"Rx count   {gateway.rx_count}")

    print( f"{int((gateway.tx_count + gateway.tx_ack + gateway.rx_count )/args.time + 0.5)} messages per second")

    print( "bye")

if __name__ == "__main__":
    main()
