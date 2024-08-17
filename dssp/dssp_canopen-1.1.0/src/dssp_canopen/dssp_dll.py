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
# @file dssp_dll.py
# @date 9th August 2021
# @author Andrew Dachs
# @brief DSSP Data Link Layer
# 


class DsspDataLinkLayer:
    def __init__(self):
        self.rx_frame = []
        self.rx_in_frame = False
        self.CRC16_INITIAL_VALUE = 0xFFFF

        return

    # CRC16-CCITT
    def crc16( self, crc_in, b):
        crc = crc_in & 0xFFFF
        for x in b:
            x = (crc >> 8) ^ x
            x ^= x>>4
            crc = ((crc << 8) ^ (x << 12) ^ (x <<5) ^ (x)) & 0xFFFF
        return crc


    def cobs_encode( self, payload):  
        rd_len = len(payload)
        encoded_message = []
        encoded_message.append(0)       # send a sarting zero to clear any potential junk
        encoded_message.append(0)       # will get replaced by run length
        rd_pos = 0
        wr_pos = 1
        run_length = 0
        # count run length (number of bytes) before we encounter a zero
        while (rd_pos<rd_len):
            if (payload[rd_pos] == 0):
                # replace run length byte
                encoded_message[wr_pos] = run_length+1
                wr_pos = wr_pos + run_length+1
                run_length = 0
                encoded_message.append(0)
                rd_pos += 1
            elif (run_length == 255):
                encoded_message[wr_pos] = 0xFF
                wr_pos += run_length+1
                encoded_message.append(0)
                run_length = 0
            else:
                encoded_message.append(payload[rd_pos])
                run_length += 1
                rd_pos+=1
        encoded_message[wr_pos] = run_length+1
        encoded_message.append(0)
        return encoded_message

    def cobs_decode(self, frame_in):
        if (frame_in == None):
            return None
        frame_out = []
        rll_pos = frame_in[0]
        rll_len = frame_in[0]
        rd_pos = 1
        while (rd_pos < len(frame_in)):
            if (rll_pos == rd_pos):
                if (rll_len != 0xFF):
                    frame_out.append(0)
                rll_len = frame_in[rd_pos]
                rll_pos = rd_pos + rll_len
            else:
                frame_out.append(frame_in[rd_pos])
            rd_pos += 1
        return frame_out

    def encode( self, message):
        frame = bytearray(message)
        crc = self.crc16(self.CRC16_INITIAL_VALUE, frame)
        frame.append( crc & 0xFF )
        frame.append( (crc>>8) & 0xFF )
        return self.cobs_encode(frame)

    def process(self, input_data):
        rx_valid_frame = None
        for x in input_data:
            if (self.rx_in_frame == True):
                if (x == 0):                    # if we're in a frame, receiving a 0 means its the end
                    self.rx_in_frame = False
                    rx_valid_frame = self.cobs_decode(self.rx_frame)
                    if (rx_valid_frame != None):
                        if (len(rx_valid_frame) >=2 ):
                            crc = self.crc16(self.CRC16_INITIAL_VALUE, rx_valid_frame[:-2])
                            if ((rx_valid_frame[len(rx_valid_frame)-2] + 256*rx_valid_frame[len(rx_valid_frame)-1] ) != crc):
                                rx_valid_frame = None # discard if CRC fails
                    self.rx_frame.clear()
                else:
                    self.rx_frame.append(x)
            else:                               # if we're not in a frame
                if (x == 0):                    # a zero means flush what's there
                    self.rx_frame.clear()
                else:                           # anything else could be start of a frame as the leading zero is optional
                    self.rx_in_frame = True
                    self.rx_frame.append(x)

        return rx_valid_frame

def main():
    dssp = DsspDataLinkLayer()
    test_str = '123456789'
    crc = dssp.crc16( dssp.CRC16_INITIAL_VALUE, bytearray(test_str, "ascii"))
    # print( f"crc = {hex(crc)}")
    if (crc != 0x29B1):
        print("Fail CRC")
        exit(-1)

    # encode a test message
    test_array = (0x10, 0x52, 0x01, 0x17, 0x10, 0x00, 0x02, 0xE8, 0x03, 0xA8, 0xA6)
    result_array = dssp.cobs_encode(test_array)
    if (result_array != [0x06, 0x10, 0x52, 0x01, 0x17, 0x10, 0x06, 0x02, 0xE8, 0x03, 0xA8, 0xA6, 0x00]):
        print("Fail COBS")
        exit(-1)

    # encode a short test message with no zeros
    test_array = [x+1 for x in range(0,16)]
    result_array = dssp.cobs_encode(test_array)
    expected_result = test_array
    expected_result.insert( 0, len(test_array)+1 )
    expected_result.append(0)

    if (result_array != expected_result):
        print("Fail COBS")
        exit(-1)

    # encode a long message with no zeros
    test_array = [x+1 for x in range(0,255)]
    test_array.append(1)

    result_array = dssp.cobs_decode(test_array)
    
    expected_result = [x+1 for x in range(0,255)]
    expected_result.insert( 0, 0xFF )
    expected_result.append(2)
    expected_result.append(1)
    expected_result.append(0)

    if (result_array != expected_result):
        print("Fail COBS")
        exit(-1)


    test_message = (0x52, 0x01, 0x17, 0x10, 0x00, 0x02, 0xE8, 0x03)
    result_array = dssp.encode(test_message)
    if (result_array != [0x06, 0x10, 0x52, 0x01, 0x17, 0x10, 0x06, 0x02, 0xE8, 0x03, 0xA8, 0xA6, 0x00]):
        print("Fail DSSP encode test")
        exit(-1)

    print( "Pass all DSSP Data Link Layer tests")

if __name__ == "__main__":
    main()
