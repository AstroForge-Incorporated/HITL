# package/__init__.py
from dssp_canopen.canopen_gateway import *
from dssp_canopen.gateway_transport import *
from canopen import *
import canopen
import dssp_canopen

class CanInterface:
    def __init__(self):
        self.cif = None
        self.target_node = None
        self.target_node_id = 0

    def connect(self, channel, bustype='socketcan', bitrate=1000000 ):
        try:
            if (channel.startswith('can') or channel.startswith('vcan') or bustype=='slcan'):
                self.cif = canopen.Network()
                self.cif.connect(channel=channel, bustype=bustype, bitrate=bitrate )
                node = canopen.LocalNode(127, None)
                self.cif.add_node(node)
            else:
                self.cif = dssp_canopen.canopen_gateway.CanOpenGateway(channel, 112500)
            self.scanner = self.cif.scanner
        except:
            print("Error connecting to ", channel)
            exit(-1)

    def disconnect( self ):
        if self.cif is canopen.Network:
            self.cif.disconnect()

    def add_node(self, nodeid, edsfile):
        return self.cif.add_node(nodeid, edsfile)


