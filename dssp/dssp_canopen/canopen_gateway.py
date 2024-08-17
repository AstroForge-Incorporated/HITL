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
# @file canopen_gateway.py
# @date 3rd December 2021
# @author Andrew Dachs
# @brief DSSP SatDrive SDO gateway
#
# Implement CAN Open functionality over a DSSP link
#
# NMT
#   reset
# SDO
#   upload
#   download
# 

from dssp_canopen.dssp_gateway import DsspGateway
from dssp_canopen.gateway_transport import *
import threading
import struct
import time
import canopen


class CanOpenGatewayTimeoutError(Exception):
    def __init__(self):
        pass
    def __str__(self):
        return  'No response from CanOpen device'

class CanOpenSdo:
    def __init__(self, gw, node_id, edsfile ):
        self.gw = gw
        self.id = node_id
        self.edsfile = edsfile
        self.od = canopen.objectdictionary.import_od(edsfile, node_id)
        self.fcb = None
        self.last = False

    def upload( self, index, subindex ):
        val, last = self.gw.upload(self.id, index, subindex, payload_type=GATEWAY_TYPE_DOMAIN, offset=0)
        return val

    def download(self,index, subindex, payload):
        self.gw.download(self.id, index, subindex, GATEWAY_TYPE_DOMAIN, payload, 0, True)

class CanOpenNmt:
    def __init__(self, gw, node_id ):
        self.gw = gw
        self.id = node_id

    def start( self ):
        gtp_msg = GatewayTransportMessage( msg_type = GATEWAY_MSG_CAN, 
                                           cobid = 0, payload = [1, self.id] )
        self.gw.post(gtp_msg)
        return

    def stop( self ):
        gtp_msg = GatewayTransportMessage( msg_type = GATEWAY_MSG_CAN, 
                                           cobid = 0, payload = [2, self.id] )
        self.gw.post(gtp_msg)
        return

    def preop( self ):
        gtp_msg = GatewayTransportMessage( msg_type = GATEWAY_MSG_CAN, 
                                           cobid = 0, payload = [128, self.id] )
        self.gw.post(gtp_msg)
        return

    def reset_node( self ):
        gtp_msg = GatewayTransportMessage( msg_type = GATEWAY_MSG_CAN, 
                                           cobid = 0, payload = [129, self.id] )
        self.gw.post(gtp_msg, False)
        return

    def reset_comms( self ):
        gtp_msg = GatewayTransportMessage( msg_type = GATEWAY_MSG_CAN, 
                                           cobid = 0, payload = [130, self.id] )
        self.gw.post(gtp_msg, False)
        return

    def send_command(self, cmd):
        gtp_msg = GatewayTransportMessage( msg_type = GATEWAY_MSG_CAN, 
                                           cobid = 0, payload = [cmd, self.id] )
        self.gw.post(gtp_msg, False)

class CanOpenNode:
    def __init__(self, gw, node_id, edsfile):
        self.sdo = CanOpenSdo(gw, node_id, edsfile)
        self.nmt = CanOpenNmt(gw, node_id)
        self.id = node_id

class CanOpenNetwork:
    def __init__(self, gw):
        self.gw = gw

class CanOpenScanner:
    def __init__(self, gw):
        self.gw = gw
        self.nodes = set()

    def search( self, limit: int = 127 ):
        stdtimeout = DsspGateway.RSP_TIMEOUT
        DsspGateway.RSP_TIMEOUT = 0.001
        for nid in range(1, limit+1):
            gtp_msg = GatewayTransportMessage( msg_type = GATEWAY_MSG_SDO, 
                                               cmd = GatewayTransportProtocol.GATEWAY_CMD_SDO_UPLOAD, 
                                               node=nid, 
                                               index = 0x1000, subindex = 0, 
                                               payload_type=GATEWAY_TYPE_UINT8 )
            self.gw.post(gtp_msg)
        DsspGateway.RSP_TIMEOUT = stdtimeout

    def reset( self ):
        self.nodes.clear()

class CanOpenGateway(DsspGateway):

    def __init__(self, port, baudrate = 115200 ):
        DsspGateway.__init__(self, port, baudrate)
        self.last_rx_msg = None
        self.tx_event = threading.Event()
        self.rsp_event = threading.Event()
        self.err_code = 0
        self.timeout = 10.0
        self.nodes = list()
        self.scanner = CanOpenScanner(self)

    def __del__(self):
        DsspGateway.__del__(self)

    def add_node( self, node_id, edsfile=''):
        node = CanOpenNode( self, node_id, edsfile )
        self.nodes.append(node)
        return node

    def rxInd( self, msg):
        self.last_rx_msg = msg
        if (msg.msg_type == GATEWAY_MSG_SDO ):
            self.scanner.nodes.add(msg.node)
            if (msg.cmd == GatewayTransportProtocol.GATEWAY_CMD_SDO_UPLOAD_RSP) or (msg.cmd == GatewayTransportProtocol.GATEWAY_CMD_SDO_UPLOAD_RSP_SEG):
                self.err_code = DsspGateway.ERROR_NONE
                self.tx_event.set()
                self.rsp_event.set()
        return

    def txCnf( self, error_code ):
        self.err_code = error_code
        self.tx_event.set()
        return

    def post(self, msg, blocking = True):
        self.tx_event.clear()
        super().post(msg)
        if (blocking == True):
            if not (self.tx_event.wait(timeout=self.timeout)):
                raise CanOpenGatewayTimeoutError
            #if (self.err_code == DsspGateway.ERROR_TIMEOUT):
            #   raise CanOpenGatewayTimeoutError

    def upload( self, node_id, index, subindex, payload_type=GATEWAY_TYPE_DOMAIN, offset = 0 ):
        gtp_msg = GatewayTransportMessage( GATEWAY_MSG_SDO, GatewayTransportProtocol.GATEWAY_CMD_SDO_UPLOAD, 
                                        node = node_id, index = index, subindex = subindex, payload_type=payload_type, offset=offset )
        last = True
        val = None
        self.rsp_event.clear()
        self.post(gtp_msg)
        self.rsp_event.wait()                   # can only proceed if we've had a response

        if (self.last_rx_msg != None):
            if (self.last_rx_msg.msg_type == GATEWAY_MSG_SDO):
                if (self.last_rx_msg.cmd == GatewayTransportProtocol.GATEWAY_CMD_SDO_UPLOAD_RSP):
                    if (payload_type == GATEWAY_TYPE_BOOL):
                        val = struct.unpack("<?", bytearray(self.last_rx_msg.payload))[0]
                    elif (payload_type == GATEWAY_TYPE_INT8):
                        val = struct.unpack("<b", bytearray(self.last_rx_msg.payload))[0]
                    elif (payload_type == GATEWAY_TYPE_UINT8):
                        val = struct.unpack("<B", bytearray(self.last_rx_msg.payload))[0]
                    elif (payload_type == GATEWAY_TYPE_INT16):
                        val = struct.unpack("<h", bytearray(self.last_rx_msg.payload))[0]
                    elif (payload_type == GATEWAY_TYPE_UINT16):
                        val = struct.unpack("<H", bytearray(self.last_rx_msg.payload))[0]
                    elif (payload_type == GATEWAY_TYPE_INT32):
                        val = struct.unpack("<i", bytearray(self.last_rx_msg.payload))[0]
                    elif (payload_type == GATEWAY_TYPE_UINT32):
                        val = struct.unpack("<I", bytearray(self.last_rx_msg.payload))[0]
                    elif (payload_type == GATEWAY_TYPE_INT64):
                        val = struct.unpack("<q", bytearray(self.last_rx_msg.payload))[0]
                    elif (payload_type == GATEWAY_TYPE_UINT64):
                        val = struct.unpack("<Q", bytearray(self.last_rx_msg.payload))[0]
                    elif (payload_type == GATEWAY_TYPE_REAL32):
                        val = struct.unpack("<f", bytearray(self.last_rx_msg.payload))[0]
                    elif (payload_type == GATEWAY_TYPE_REAL64):
                        val = struct.unpack("<d", bytearray(self.last_rx_msg.payload))[0]
                    elif (payload_type == GATEWAY_TYPE_STRING):
                        val = bytearray(self.last_rx_msg.payload).decode('ascii')
                    else:                            
                        val = bytearray(self.last_rx_msg.payload)
                        last = self.last_rx_msg.last
        return val, last

    def download( self, node_id, index, subindex, payload_type, payload, offset = 0, last = True ):
        if ((offset == 0) and (last==True)):
            gtp_msg = GatewayTransportMessage( GATEWAY_MSG_SDO, GatewayTransportProtocol.GATEWAY_CMD_SDO_DOWNLOAD, 
                                               node = node_id, index = index, subindex = subindex, payload_type=payload_type, payload = payload )
        else:
            gtp_msg = GatewayTransportMessage( GATEWAY_MSG_SDO, GatewayTransportProtocol.GATEWAY_CMD_SDO_DOWNLOAD_SEG, 
                                            node = node_id, index = index, subindex = subindex, payload_type=payload_type, payload = payload, offset = offset, last = last )
        self.post(gtp_msg)
        return

def main():
    print( "Sdo gateway unit test" )


if __name__ == "__main__":
    main()
