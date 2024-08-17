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
# @file dssp_gateway.py
# @date 20th October 2021
# @author Andrew Dachs
# @brief Gateway for DSSP
# 
# Provides primitives for sending and receiving GatewayTransportProtocol messages
# over a DSSP serial link.  The class is intended to be subclassed with more specific
# implementations of txcnf and rxind.
# 

import threading
import queue
import serial

from dssp_canopen.gateway_transport import *
from dssp_canopen.dssp_dll import DsspDataLinkLayer


class DsspGateway:
    RSP_TIMEOUT      = 3.0
    RETRIES          = 2
    ERROR_NONE       = 0
    ERROR_TIMEOUT    = 254

    def __init__(self, port, baudrate = 115200 ):

        # start modules
        self.dssp   = DsspDataLinkLayer()
        self.gtp    = GatewayTransportProtocol()

        self.tx_queue = queue.SimpleQueue()
        self.tx_count   = 0
        self.tx_ack = 0
        self.rx_count   = 0

        self._reading = False
        self._serial_rx_thread = None
        self._serialport = None
        self._serial_tx_thread = None
        self._writing = False

        self.ack_lock = threading.Lock()

        # open serial port and start threads
        try:
            self._serialport = serial.Serial(port, baudrate, timeout=None )
            self._reading = True
            self._serial_rx_thread = threading.Thread(target=self._read_thread, args=(self._serialport,self.ack_lock),daemon=True)
            self._serial_rx_thread.start()
            self._writing = True
            self._serial_tx_thread = threading.Thread(target=self._write_thread, args=(self._serialport,self.tx_queue,self.ack_lock,), daemon=True)
            self._serial_tx_thread.start()            
        except (serial.SerialException, serial.SerialTimeoutException) as err:
            print(f"Error connecting to serial port {err}")

    def __del__(self):
        # stop worker threads and close serial port
        if (self.ack_lock.locked()):
            self.ack_lock.release()
        if self._serial_rx_thread is not None:
            self._reading = False
            self._serial_rx_thread.join()
        if self._serial_tx_thread is not None:
            self._writing = False
            self._serial_tx_thread.join()
        if self._serialport is not None:
            if (self._serialport.is_open()):
                self._serialport.close()

    # the write thread waits for a message on the tx_queue, sends it
    # on the serial port.  If no ack is received it retries
    def _write_thread(self, port, txq, ack_lock):
        item = None
        retry_count = 0
        while self._writing and port:
            try:
                if (ack_lock.acquire( blocking = True, timeout=DsspGateway.RSP_TIMEOUT) == True):
                    item = txq.get()                      # wait for something to send
                    self.tx_count += 1
                    retry_count = self.RETRIES
                    port.write(item)
                    port.flush()                          # writing serial data takes ~20ms becuase of latency setting in PC USB serial driver
                else:
                    if (item != None):
                        if (retry_count > 0):
                            retry_count -= 1
                            #print( ".", end = '', flush=True)
                            port.write(item)
                            port.flush()
                        else:
                            self.txCnf( DsspGateway.ERROR_TIMEOUT )            # timeout 
                            item = None 
                            ack_lock.release()
            except:
                continue
        print( "Leaving tx thread")

    # read thread passes characters as they are received through
    # to dssp frame assembler.  Completed frames are then
    # decoded into gateway messages.
    def _read_thread(self, port, ack_lock):
        while self._reading and port:
            try:
                bytes_to_read = port.in_waiting
                if (bytes_to_read < 1):
                    bytes_to_read = 1
                var = port.read(bytes_to_read)
                if (var != b''):                 
                    frame = self.dssp.process(var)
                    if (frame != None ):
                        msg = self.gtp.decode( frame )
                        if (msg != None):
                            # we have a valid gateway message
                            if ((msg.msg_type == GATEWAY_MSG_ACK) or
                                ((msg.msg_type == GATEWAY_MSG_SDO) and (msg.cmd == GatewayTransportProtocol.GATEWAY_CMD_SDO_UPLOAD_RSP))):
                                    try:
                                        ack_lock.release()
                                    except:
                                        pass
                            if (msg.msg_type == GATEWAY_MSG_ACK):
                                self.tx_ack += 1
                                self.txCnf( msg.error_code )
                            else:
                                self.rx_count += 1
                                self.rxInd( msg )
            except:
                continue
        print( "Leaving rx thread")

    def post( self, msg ):
        # first pack the gateway message into an array of bytes
        payload_bytes = self.gtp.encode(msg)
        # now encode the bytes as DSSP with checksum and COBS framing
        dssp_frame = self.dssp.encode(payload_bytes)
        # send it on serial port
        self.tx_queue.put(dssp_frame)

    def rxInd( self, msg ):
        # override in child class
        return

    def txCnf( self, error_code ):
        # override in child class
        return

def main():
    print( "Unit test")

if __name__ == "__main__":
    main()
