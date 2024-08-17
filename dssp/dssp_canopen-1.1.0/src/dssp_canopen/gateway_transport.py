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
# @file gateway_transport.py
# @date 9th August 2021
# @author Andrew Dachs
# @brief Implementation of the gateway transport protocol 
# Gateway transport protocol messages are encapsulated in DSSP frames
# for transmission over the serial port
# 


# gateway transport payload types
GATEWAY_TYPE_BOOL         = 0
GATEWAY_TYPE_INT8         = 1
GATEWAY_TYPE_INT16        = 2
GATEWAY_TYPE_INT32        = 3
GATEWAY_TYPE_INT64        = 4
GATEWAY_TYPE_UINT8        = 5
GATEWAY_TYPE_UINT16       = 6
GATEWAY_TYPE_UINT32       = 7
GATEWAY_TYPE_UINT64       = 8
GATEWAY_TYPE_REAL32       = 9
GATEWAY_TYPE_REAL64       = 10
GATEWAY_TYPE_STRING       = 11
GATEWAY_TYPE_DOMAIN       = 12

# gateway transport message types
GATEWAY_MSG_ACK     = 0
GATEWAY_MSG_SDO     = 1
GATEWAY_MSG_CAN     = 2

class GatewayTransportMessage:
    def __init__(self, msg_type=0, cmd=0, error_code=0, node=0, index=0, subindex=0, payload_type=0, offset = 0, last = True, payload=[], cobid=0):
        self.msg_type = msg_type
        self.cmd = cmd
        self.error_code = error_code
        self.node = node
        self.index = index
        self.subindex = subindex
        self.offset = offset
        self.payload_type = payload_type
        self.payload = payload
        self.cob_id = cobid
        self.last = last


class GatewayTransportProtocol:
    # if the type field is not this, it isn't GTP
    TYPE_FIELD          = 0x10 

    # gateway transport command field
    GATEWAY_CMD_ACK                = 0
    GATEWAY_CMD_SDO_DOWNLOAD       = 1
    GATEWAY_CMD_SDO_UPLOAD         = 2
    GATEWAY_CMD_SDO_UPLOAD_RSP     = 3
    GATEWAY_CMD_SDO_ABORT          = 4
    GATEWAY_CMD_SDO_DOWNLOAD_SEG   = 5
    GATEWAY_CMD_SDO_UPLOAD_RSP_SEG = 6
    GATEWAY_CMD_CFG_RETRIES        = 249
    GATEWAY_CMD_CFG_TIMEOUT        = 250
    GATEWAY_CMD_CFG_RESET          = 251
    GATEWAY_CMD_CFG_NETWORK        = 252
    GATEWAY_CMD_CFG_NODE           = 253
    GATEWAY_CMD_CFG_SDO_TIME       = 254
    GATEWAY_CMD_CFG_SDO_BLOCK      = 255

    def __init__(self):
        self.req_payload_type = 0

    ''' 
        Returns a byte array representation of the gateway transport protocol frame
        See ICD for details of message structure
    '''
    def encode(self, msg ):
        if (msg.msg_type == GATEWAY_MSG_ACK):
            b = [self.TYPE_FIELD, 0, self.GATEWAY_CMD_ACK, msg.error_code & 0xFF, (msg.error_code<<8) & 0xFF]            
        elif (msg.msg_type == GATEWAY_MSG_SDO):
            if (msg.cmd == self.GATEWAY_CMD_SDO_DOWNLOAD):
                b = [self.TYPE_FIELD, msg.node & 0x7F, self.GATEWAY_CMD_SDO_DOWNLOAD, msg.index & 0xFF, (msg.index >> 8) & 0xFF, msg.subindex, msg.payload_type ]
                b += bytes(msg.payload)
            elif (msg.cmd == self.GATEWAY_CMD_SDO_DOWNLOAD_SEG ):
                if (msg.last == True):
                    last_flag = 0x80
                else:
                    last_flag = 0
                b = [self.TYPE_FIELD, msg.node & 0x7F, self.GATEWAY_CMD_SDO_DOWNLOAD_SEG, msg.index & 0xFF, (msg.index >> 8) & 0xFF, msg.subindex, msg.payload_type, 
                     msg.offset & 0xFF, (msg.offset>>8) & 0xFF, (msg.offset>>16) & 0xFF, (msg.offset>>24) & 0x7F | last_flag ]
                b += bytes(msg.payload)
                self.req_payload_type = msg.payload_type
            elif (msg.cmd == self.GATEWAY_CMD_SDO_UPLOAD ):
                b = [self.TYPE_FIELD, msg.node & 0x7F, self.GATEWAY_CMD_SDO_UPLOAD, msg.index & 0xFF, (msg.index >> 8) & 0xFF, msg.subindex, msg.payload_type ]
                if (msg.offset != 0):
                    b += [msg.offset & 0xFF, (msg.offset>>8) & 0xFF, (msg.offset>>16) & 0xFF, (msg.offset>>24) & 0x7F]
                self.req_payload_type = msg.payload_type
        elif (msg.msg_type == GATEWAY_MSG_CAN):
            b = [self.TYPE_FIELD, 0x80, msg.cob_id & 0xFF, (msg.cob_id >>8)& 0xFF, (msg.cob_id >>16)& 0xFF, (msg.cob_id >>24)& 0xFF ]
            b += bytes(msg.payload)
        else:
            b=[]
        return bytes(b)

    '''
        Returns gateway message, parsed from raw frame bytes
        The first byte of the frame must be the correct type field
    '''
    def decode(self, frame):
        if (len(frame)==0):
            return None
        if (frame[0] != self.TYPE_FIELD):
            return None
        else:
            msg = GatewayTransportMessage()
            msg.last = True
            if ((frame[1] & 0x80) == 0):
                if (frame[2] == self.GATEWAY_CMD_ACK):
                    msg.msg_type = GATEWAY_MSG_ACK
                    msg.cmd = self.GATEWAY_CMD_ACK
                    msg.error_code = frame[3]
                elif (frame[2] == self.GATEWAY_CMD_SDO_UPLOAD):
                    msg.msg_type = GATEWAY_MSG_SDO
                    msg.node = frame[1] & 0x7F
                    msg.cmd = frame[2]
                    msg.index = frame[3] + (frame[4]<<8)
                    msg.subindex = frame[5]
                    msg.payload_type = frame[6]
                    msg.offset = 0
                    if( len(frame) >= 11 ):
                        msg.offset = frame[7] + (frame[8]<<8) + (frame[9]<<16) + ((frame[10] & 0x7F) << 24)
                elif (frame[2] == self.GATEWAY_CMD_SDO_DOWNLOAD):
                    msg.msg_type = GATEWAY_MSG_SDO
                    msg.node = frame[1] & 0x7F
                    msg.cmd = frame[2]
                    msg.index = frame[3] + (frame[4]<<8)
                    msg.subindex = frame[5]
                    msg.payload_type = frame[6]
                    msg.payload = frame[7:]
                elif (frame[2] == self.GATEWAY_CMD_SDO_DOWNLOAD_SEG):
                    msg.msg_type = GATEWAY_MSG_SDO
                    msg.node = frame[1] & 0x7F
                    msg.cmd = frame[2]
                    msg.index = frame[3] + (frame[4]<<8)
                    msg.subindex = frame[5]                    
                    msg.payload_type = frame[6]
                    msg.offset = frame[7] + (frame[8]<<8) + (frame[9]<<16) + ((frame[10] & 0x7F) <<24)
                    if ((frame[10] & 0x80) == 0):
                        msg.last = False
                    msg.payload = frame[11:]
                elif (frame[2] == self.GATEWAY_CMD_SDO_UPLOAD_RSP):
                    msg.msg_type = GATEWAY_MSG_SDO
                    msg.node = frame[1] & 0x7F
                    msg.cmd = frame[2]
                    msg.index = frame[3] + (frame[4]<<8)
                    msg.subindex = frame[5]
                    msg.payload_type = self.req_payload_type
                    msg.payload = frame[6:-2]
                elif (frame[2] == self.GATEWAY_CMD_SDO_UPLOAD_RSP_SEG):
                    msg.msg_type = GATEWAY_MSG_SDO
                    msg.node = frame[1] & 0x7F
                    msg.cmd = self.GATEWAY_CMD_SDO_UPLOAD_RSP
                    msg.index = frame[3] + (frame[4]<<8)
                    msg.subindex = frame[5]
                    msg.payload_type = self.req_payload_type
                    msg.offset = frame[6] + (frame[7]<<8) + (frame[8]<<16) + ((frame[9] & 0x7F)<<24)
                    if ((frame[9] & 0x80) == 0):
                        msg.last = False
                    msg.payload = frame[10:-2]
            else:
                msg.msg_type = GATEWAY_MSG_CAN
                msg.cob_id   = frame[2] + (frame[3]<<8) + (frame[4]<<16) + (frame[5]<<24)
                msg.payload  = frame[6:-2]
            return msg

def main():
    # unit tests
    return
    
    

if __name__ == "__main__":
    main()
