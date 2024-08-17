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
# @file ascii_gateway.py
# @date 9th August 2021
# @author Andrew Dachs
# @brief ASCII Dssp Gateway 
#
# Command line ascii gateway for DSSP connected CanOpen node
#
# 

import argparse
try:
    import readline # provides arrow up history in input function
except:
    pass #readline not available

from ast import literal_eval
import dssp_canopen as dssp
from ascii_command_parser import AsciiCommandParser
from float_double_byte_conversion import real_to_float


# create a dictionary to provide names for each error code
error_codes = {
    0:  "OK",
    1:  "INVALID_CFG",
    2:  "Driver layer error",
    3:  "INVALID_MSG",
    4:  "INVALID_CMD",
    5:  "OBJ_READ",
    6:  "OBJ_WRITE",
    7:  "OBJ_ACCESS",
    8:  "OBJ_RANGE",
    9:  "SDO transfer was aborted by node",
    10: "SDO invalid read operation",
    11: "SDO invalid write operation",
    12: "CAN",
    254: "No response from node",
    255: "An unknown error was reported"
}


class AsciiDsspGateway(dssp.DsspGateway):
    def __init__(self, port, baudrate = 115200, id = 127 ):
        dssp.DsspGateway.__init__(self, port, baudrate)
        self.parser = AsciiCommandParser()
        self.id = id
        self.display_heartbeat = False

    def __del__(self):
        dssp.DsspGateway.__del__(self)

    def to_str( self, msg):
        if (msg.msg_type == dssp.GATEWAY_MSG_SDO):
            if (msg.payload_type == 11):            # vs                                        
                return bytearray(msg.payload).decode('ascii')
            elif (msg.payload_type == 7):
                return str(msg.payload[0]+msg.payload[1]*0x100 + msg.payload[2]*0x10000 + msg.payload[3]*0x1000000)
            elif (msg.payload_type == 6):
                return str(msg.payload[0]+msg.payload[1]*0x100) 
            elif (msg.payload_type == 5):
                return str(msg.payload[0])
            elif (msg.payload_type == 9 or msg.payload_type == 10):
                return str(real_to_float(msg.payload))
            else:
                return str(msg.payload)
        elif (msg.msg_type == dssp.GATEWAY_MSG_CAN):
            return str(msg.cob_id) + ":" + str(msg.payload)
        else:
            return str(msg)

    def rxInd( self, msg):
        if ( msg.msg_type == dssp.GATEWAY_MSG_CAN ):
            if ( (msg.cob_id & 0x700) == 0x700):
                if (self.display_heartbeat):
                    print( f"\r{self.to_str(msg)}", end = '\n>' )
        else:
            print( f"\r{self.to_str(msg)}", end = '\n>' )
            
    def txCnf( self, error_code ):
        if (error_code == 0):
            print( "\rOK", end ='\n>')
        else:
            try:
                print( "\rERROR:", error_codes[error_code], end= '\n>')
            except:
                print( "\rERROR(", error_code, ")", end= '\n>')

    def parse(self, cmd_string):
        if (self.parser.parse(cmd_string)):
            try:
                if (self.parser.cmd == self.parser.CMD_HELP):
                    print(f"Command strings:\n"\
                        f"[[<net>]<node>] r[ead] <index> <subindex> <datatype>              # SDO Upload\n"\
                        f"[[<net>]<node>] w[rite] <index> <subindex> <datatype> <value>     # SDO Download\n"\
                        f"[[<net>]<node>] start                                             # NMT Start node\n"\
                        f"[[<net>]<node>] stop                                              # NMT Stop node\n"\
                        f"[[<net>]<node>] preop[erational]                                  # NMT Set node to pre-operational\n"\
                        f"[[<net>]<node>] reset node                                        # NMT Reset node\n"\
                        f"[[<net>]<node>] reset comm[unication]                             # NMT Reset communication\n"\
                        f"display <option> <value>                                          # control display \n"\
                        f"help                                                              # print this help\n"\
                        f"\n"\
                        f"exit                                                              # end program\n"\
                        f"\n"\
                        f"<datatype> is one of: bool, u8, i8, i16, u16, i32, u32, u64, r32, r64, vs\n"
                        f"\n"\
                        f"Response:\n"\
                        f"OK | <value> | ERROR:<SDO-abort-code> | ERROR:<internal-error-code>\n" )
                elif (self.parser.cmd == self.parser.CMD_SDO_WRITE):
                    gtp_msg = dssp.GatewayTransportMessage( dssp.GATEWAY_MSG_SDO, self.gtp.GATEWAY_CMD_SDO_DOWNLOAD, 
                                                       node = self.parser.node, 
                                                       index = self.parser.index, subindex = self.parser.subindex, 
                                                       payload_type = self.parser.payload_type, payload = self.parser.value)
                    self.post(gtp_msg)
                elif (self.parser.cmd == self.parser.CMD_SDO_READ):
                    gtp_msg = dssp.GatewayTransportMessage( dssp.GATEWAY_MSG_SDO, self.gtp.GATEWAY_CMD_SDO_UPLOAD, 
                                                       node = self.parser.node, 
                                                       index = self.parser.index, subindex = self.parser.subindex, 
                                                       payload_type=self.parser.payload_type )
                    self.post(gtp_msg)
                elif (self.parser.cmd == self.parser.CMD_NMT_START):
                    gtp_msg = dssp.GatewayTransportMessage( dssp.GATEWAY_MSG_CAN, 
                                                       cobid = 0,
                                                       payload = (0x01, self.parser.node))
                                                       
                    self.post(gtp_msg)
                elif (self.parser.cmd == self.parser.CMD_NMT_STOP):
                    gtp_msg = dssp.GatewayTransportMessage( dssp.GATEWAY_MSG_CAN, 
                                                       cobid = 0,
                                                       payload = (0x02, self.parser.node))
                                                       
                    self.post(gtp_msg)
                elif (self.parser.cmd == self.parser.CMD_NMT_PREOP):
                    gtp_msg = dssp.GatewayTransportMessage( dssp.GATEWAY_MSG_CAN, 
                                                       cobid = 0,
                                                       payload = (0x80, self.parser.node))
     
                    self.post(gtp_msg)
                elif (self.parser.cmd == self.parser.CMD_NMT_RESET_NODE):
                    gtp_msg = dssp.GatewayTransportMessage( dssp.GATEWAY_MSG_CAN, 
                                                       cobid = 0,
                                                       payload = (0x81, self.parser.node))
                                                       
                    self.post(gtp_msg)
                elif (self.parser.cmd == self.parser.CMD_NMT_RESET_COMM):
                    gtp_msg = dssp.GatewayTransportMessage( dssp.GATEWAY_MSG_CAN, 
                                                       cobid = 0,
                                                       payload = (0x82, self.parser.node))
                                                       
                    self.post(gtp_msg)
                elif (self.parser.cmd == self.parser.CMD_NMT_HEARTBEAT):
                    gtp_msg = dssp.GatewayTransportMessage( dssp.GATEWAY_MSG_CAN, 
                                                       cobid = 0x700+self.id,
                                                       payload = [self.parser.node])
                                                       
                    self.post(gtp_msg)        
                elif (self.parser.cmd == self.parser.CMD_DISPLAY):
                    if (self.parser.display_option == 'heartbeat'):
                        if (self.parser.display_value == 'on'):
                            self.display_heartbeat = True
                        else:
                            self.display_heartbeat = False
                else:
                    print ("Unrecognised command, try typing 'help'")
            except:
                print( "An unknown error occured processing input" )
            return True
        return False



def main():
    cmd_line = argparse.ArgumentParser(description="Dawn Aerospace ASCII DSSP Gateway")
    cmd_line.add_argument("device", help="The serial interface")
    cmd_line.add_argument("-b", "--baudrate", help="Serial baud rate", type=int, default=115200)
    cmd_line.add_argument("-i", "--id", help="Local node ID", type=int, default=127)
    args = cmd_line.parse_args()

    print( "Dawn Aerospace (c) 2021")
    print( "Starting ASCII DSSP gateway on ", args.device )
    print( "Type 'help' for the list of commands or 'exit' to leave")

    gateway = AsciiDsspGateway(args.device, args.baudrate, args.id)

    while True:
        cmdStr = input(">")
        if (cmdStr.lower() == "exit"):
            break
        if( not( gateway.parse(cmdStr)) ):
            print ('Syntax error (type "help")')
    
    print( "bye")

if __name__ == "__main__":
    main()
