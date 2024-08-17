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
# @file ascii_command_parser.py
# @date 9th August 2021
# @author Andrew Dachs
# @brief Command parser for ASCII input, similar to CIA309-3
# 

import re
from ast import literal_eval
from float_double_byte_conversion import double_to_real64, float_to_real32
import dssp_canopen as dssp

class AsciiCommandParser:
    def __init__(self):
        self.CMD_SDO_ACK        = 0
        self.CMD_SDO_WRITE      = 1
        self.CMD_SDO_READ       = 2
        self.CMD_SDO_READ_RSP   = 3
        self.CMD_NMT_START      = 4
        self.CMD_NMT_STOP       = 5
        self.CMD_NMT_PREOP      = 6
        self.CMD_NMT_RESET_NODE = 7
        self.CMD_NMT_RESET_COMM = 8
        self.CMD_NMT_HEARTBEAT  = 9
        self.CMD_HELP           = 10
        self.CMD_DISPLAY        = 11

        self.default_net = 1
        self.default_node = 1
        self.node = 1
        self.net = 1
        self.cmd = 0
        self.index = 0
        self.subindex = 0
        self.payload_type = 0
        self.value = ""
        self.valid = False
        self.display_option = ""
        self.display_value = ""

        # dictionary where key is the payload type
        self.payload_type_names = \
        {
            "bool": dssp.GATEWAY_TYPE_BOOL,
            "i8"  : dssp.GATEWAY_TYPE_INT8,
            "i16" : dssp.GATEWAY_TYPE_INT16,
            "i32" : dssp.GATEWAY_TYPE_INT32,
            "i64" : dssp.GATEWAY_TYPE_INT64,
            "u8"  : dssp.GATEWAY_TYPE_UINT8,
            "u16" : dssp.GATEWAY_TYPE_UINT16,
            "u32" : dssp.GATEWAY_TYPE_UINT32,
            "u64" : dssp.GATEWAY_TYPE_UINT64,
            "r32" : dssp.GATEWAY_TYPE_REAL32,
            "r64" : dssp.GATEWAY_TYPE_REAL64,
            "vs"  : dssp.GATEWAY_TYPE_STRING
        }
        #corresponding payload sizes
        self.payload_type_sizes = \
            (1, 1, 2, 4, 8, 1, 2, 4, 8, 4, 8, -1)

        # regular expression is looking for matches to the patterns:
        # [[net] node] w[rite] index subindex payload_type value
        # [[net] node] r[ead] index subindex payload_type
        # [[net] node] start
        # [[net] node] stop
        # [[net] node] preop[erational]
        # [[net] node] reset node
        # [[net] node] reset comm[unications]
        # [[net] node] h[eartbeat]
        # help
        # display <option> <value>
        self.regex =   (r'^(ack)',
                        r'^([0-9]*)\s*([0-9]*)\s*(w\w*)\s*(\w+)\s+(\w+)\s+(\w+)\s+(0x[0-9a-fA-F]+|[0-9.\-\+eE]+)',
                        r'^([0-9]*)\s*([0-9]*)\s*(r\w*)\s*(\w+)\s+(\w+)\s+(\w+)',
                        r'^(rsp)',
                        r'^([0-9]*)\s*([0-9]*)\s*(start)',
                        r'^([0-9]*)\s*([0-9]*)\s*(stop)',
                        r'^([0-9]*)\s*([0-9]*)\s*(preop\w*)',
                        r'^([0-9]*)\s*([0-9]*)\s*(reset\s*node)',
                        r'^([0-9]*)\s*([0-9]*)\s*(reset\s*comm\w*)',
                        r'^([0-9]*)\s*([0-9]*)\s*(heartbeat)',
                        r'^(help)',
                        r'^(display)\s+(\w+)\s+(\w+)',
                         )

    def convert_value_to_bytes(self, value_type, value_str):
        b = []
        if (value_type < 9):    # simple integer types
            n = literal_eval(value_str)
            for i in range(0, self.payload_type_sizes[value_type]):
                b.append( n & 0xFF )
                n >>= 8
        elif (value_type == 9):    # single precision floating point
            n = literal_eval(value_str)
            b = float_to_real32(n)
        elif (value_type == 10):    # double precision floating point
            n = literal_eval(value_str)
            b = double_to_real64(n)
        elif (value_type == 11):    # string
            b.append( bytes(value_str, 'ascii'))                 
        return bytes(b)

    def parse(self, str):
        str = str.lower()
        self.node = self.default_node
        self.net  = self.default_net
        self.cmd = 0
        self.index = 0
        self.subindex = 0
        self.payload_type = 0
        self.value = []
        self.valid = False
        self.display_value = ""
        self.display_option = ""

        try:
            match = re.search(self.regex[self.CMD_SDO_WRITE], str, re.MULTILINE)
            if (match != None):
                if ((match.regs[1][1]-match.regs[1][0]) > 0):
                    if ((match.regs[2][1]-match.regs[2][0]) == 0):
                        self.node = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                    else:
                        self.net  = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                        self.node = literal_eval(match.string[match.regs[2][0]:match.regs[2][1]])
                self.cmd = self.CMD_SDO_WRITE
                self.index = literal_eval(match.string[match.regs[4][0]:match.regs[4][1]])
                self.subindex = literal_eval(match.string[match.regs[5][0]:match.regs[5][1]])
                self.payload_type = self.payload_type_names[match.string[match.regs[6][0]:match.regs[6][1]]]
                self.value = self.convert_value_to_bytes(self.payload_type, match.string[match.regs[7][0]:match.regs[7][1]])     
                      
                self.valid = True
            else:
                match = re.search(self.regex[self.CMD_SDO_READ], str, re.MULTILINE)
                if (match != None):
                    if ((match.regs[1][1]-match.regs[1][0]) > 0):
                        if ((match.regs[2][1]-match.regs[2][0]) == 0):
                            self.node = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                        else:
                            self.net  = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                            self.node = literal_eval(match.string[match.regs[2][0]:match.regs[2][1]])
                    self.cmd = self.CMD_SDO_READ
                    self.index = literal_eval(match.string[match.regs[4][0]:match.regs[4][1]])
                    self.subindex = literal_eval(match.string[match.regs[5][0]:match.regs[5][1]])
                    self.payload_type = self.payload_type_names[match.string[match.regs[6][0]:match.regs[6][1]]]
                    self.valid = True
                else:
                    match = re.search(self.regex[self.CMD_NMT_START], str, re.MULTILINE)
                    if (match != None):
                        if ((match.regs[1][1]-match.regs[1][0]) > 0):
                            if ((match.regs[2][1]-match.regs[2][0]) == 0):
                                self.node = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                            else:
                                self.net  = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                                self.node = literal_eval(match.string[match.regs[2][0]:match.regs[2][1]])
                        self.cmd = self.CMD_NMT_START
                        self.valid = True
                    else:
                        match = re.search(self.regex[self.CMD_NMT_STOP], str, re.MULTILINE)
                        if (match != None):
                            if ((match.regs[1][1]-match.regs[1][0]) > 0):
                                if ((match.regs[2][1]-match.regs[2][0]) == 0):
                                    self.node = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                                else:
                                    self.net  = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                                    self.node = literal_eval(match.string[match.regs[2][0]:match.regs[2][1]])
                                self.cmd = self.CMD_NMT_STOP
                                self.valid = True
                        else:
                            match = re.search(self.regex[self.CMD_NMT_PREOP], str, re.MULTILINE)
                            if (match != None):
                                if ((match.regs[1][1]-match.regs[1][0]) > 0):
                                    if ((match.regs[2][1]-match.regs[2][0]) == 0):
                                        self.node = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                                    else:
                                        self.net  = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                                        self.node = literal_eval(match.string[match.regs[2][0]:match.regs[2][1]])
                                self.cmd = self.CMD_NMT_PREOP
                                self.valid = True
                            else:
                                match = re.search(self.regex[self.CMD_NMT_RESET_NODE], str, re.MULTILINE)
                                if (match != None):
                                    if ((match.regs[1][1]-match.regs[1][0]) > 0):
                                        if ((match.regs[2][1]-match.regs[2][0]) == 0):
                                            self.node = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                                        else:
                                            self.net  = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                                            self.node = literal_eval(match.string[match.regs[2][0]:match.regs[2][1]])
                                    self.cmd = self.CMD_NMT_RESET_NODE
                                    self.valid = True
                                else:
                                    match = re.search(self.regex[self.CMD_NMT_RESET_COMM], str, re.MULTILINE)
                                    if (match != None):
                                        if ((match.regs[1][1]-match.regs[1][0]) > 0):
                                            if ((match.regs[2][1]-match.regs[2][0]) == 0):
                                                self.node = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                                            else:
                                                self.net  = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                                                self.node = literal_eval(match.string[match.regs[2][0]:match.regs[2][1]])
                                        self.cmd = self.CMD_NMT_RESET_COMM
                                        self.valid = True
                                    else:
                                        match = re.search(self.regex[self.CMD_NMT_HEARTBEAT], str, re.MULTILINE)
                                        if (match != None):
                                            if ((match.regs[1][1]-match.regs[1][0]) > 0):
                                                if ((match.regs[2][1]-match.regs[2][0]) == 0):
                                                    self.node = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                                                else:
                                                    self.net  = literal_eval(match.string[match.regs[1][0]:match.regs[1][1]])
                                                    self.node = literal_eval(match.string[match.regs[2][0]:match.regs[2][1]])
                                            self.cmd = self.CMD_NMT_HEARTBEAT
                                            self.valid = True
                                        else:
                                            match = re.search(self.regex[self.CMD_HELP], str, re.MULTILINE)
                                            if (match != None):
                                                self.cmd = self.CMD_HELP
                                                self.valid = True
                                            else:
                                                match = re.search(self.regex[self.CMD_DISPLAY], str, re.MULTILINE)
                                                if (match != None):
                                                    ''' parse display option and value '''
                                                    self.display_option = match.string[match.regs[2][0]:match.regs[2][1]]
                                                    self.display_value  = match.string[match.regs[3][0]:match.regs[3][1]]
                                                    self.cmd = self.CMD_DISPLAY
                                                    self.valid = True
                                                else:
                                                    self.valid = False
        except:
            self.valid = False

        return self.valid


def main():
    print( "Command parser unit test")
    parser = AsciiCommandParser()

    #str = input(">")

    # Series of test commands (string, expected_result)
    commands = ( (u"help", True),
                 (u"1 16 WRITE 0x1017 0 u16 1000", True),
                 (u"1 16 write 0x1017 0 u16 1000", True),
                 (u"1 16 w 0x1017 0 u16 1000", True),
                 (u"16 w 0x1017 0 u16 1000", True),
                 (u"16 w 0x1017 0 1000", False),
                 (u"16 w 0x1017 0 u16", False),
                 (u"16 w 0x1017", False),
                 (u"write 0x1017", False),
                 (u"write", False),
                 (u"1 16 read 0x1017 0 u16", True),
                 (u"1 16 read 0x100A 0 u16", True),
                 (u"1 16 read 4106 0 u16", True),
                 (u"1 16 start", True),
                 (u"1 16 stop", True),
                 (u"1 16 preop", True),
                 (u"1 16 reset node", True),
                 (u"1 16 reset comm", True) )

    for entry in commands:
        parser.parse(entry[0])

        if (parser.valid != entry[1]):
            print( "Test failed on ", entry[0], "==", entry[1] )
            exit(-1)
    print( "Tests passed")

if __name__ == "__main__":
    main()

