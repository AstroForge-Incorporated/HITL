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
# @file floating_point_conversion.py
# @date 18th November 2021
# @author Robert Rolleston, Josh Sinclair
# @brief converting IEEE format r32 and r64 numbers to floating points
#
# Command line ascii gateway for DSSP connected CanOpen node
# 

import struct

#Function for converting a floating point number into a 4 byte representation
def float_to_real32(f, num_of_bytes=4):
    #create hexidecimal string from the floating point number
    hex_str = hex(struct.unpack('<I', struct.pack('<f', f))[0])
    #catch the case where zeros at the front are not shown
    if (len(hex_str) < 10):
        pack_zeros = 10-len(hex_str)
        hex_str = "0x" + "0"*pack_zeros + hex_str[2:]
    #divide the string into pairs of hex digits and covert to byte numbers
    r32_array = [0]*num_of_bytes
    hex_base = 16
    for ii in range(num_of_bytes):
        #special case for the last two characters in the string
        if (ii == 0):
            r32_array[ii] = int(hex_str[-(ii+1)*2:], hex_base)
        else:
            r32_array[ii] = int(hex_str[-(ii+1)*2:-(ii+1)*2+2], hex_base)
    return r32_array


#Function for converting a double number into an 8 byte representation
def double_to_real64(f, num_of_bytes=8):
    #create hexidecimal string from the floating point number
    hex_str = hex(struct.unpack('<Q', struct.pack('<d', f))[0])
    #catch the case where zeros at the front are not shown
    if (len(hex_str) < 18):
        pack_zeros = 18-len(hex_str)
        hex_str = "0x" + "0"*pack_zeros + hex_str[2:]
    #divide the string into pairs of hex digits and covert to byte numbers
    r32_array = [0]*num_of_bytes
    hex_base = 16
    for ii in range(num_of_bytes):
        #special case for the last two characters in the string
        if (ii == 0):
            r32_array[ii] = int(hex_str[-(ii+1)*2:], hex_base)
        else:
            r32_array[ii] = int(hex_str[-(ii+1)*2:-(ii+1)*2+2], hex_base)
    return r32_array


# Function takes r32 or r64 array 'r' and returns the floating point equivalent
# in IEEE 754 format. eg. r32 is of the form [uint8, uint8, uint8, uint8]
def real_to_float(r):
    # List comes in LSB on left, need to reverse
    arr = reversed(r)
    # String prefix for hexadecimal format
    h = '0x'
    for num in arr:
        # Zero exception requires padding of zeros
        # print(len(hex(num)))
        # print(hex(num))
        if hex(num) == '0x0':
            h += '00'
        elif len(hex(num)) == 3:
            h += '0'
            h += hex(num)[2:4]
        else:
            h += hex(num)[2:4]
    # DEBUG
    # print(h)

    hex_value = hex(int(h, base=16))

    if len(r) == 4:
        return struct.unpack('<f', struct.pack('<I', int(hex_value, base=16)))[0]
    elif len(r) == 8:
        return struct.unpack('<d', struct.pack('<Q', int(hex_value, base=16)))[0]
    else:
        print("Invalid format, enter arrays of length 4 or 8")
        return

def main():
    # Testing float to real32
    test_array = [0.0, -1e-25, 1e-25, -1.70141173319e38, 3.4e38, 37.0, -69.87653443, 1.18e-38]
    result_array = [[], [], [], [], [], [], [], []]
    for ii in range(len(test_array)):
        result_array[ii] = float_to_real32(test_array[ii])
    expected_array = [[0, 0, 0, 0], [136, 150, 247, 149], [136, 150, 247, 21], [255, 255, 255, 254], [158, 201, 127, 127], [0, 0, 20, 66], [201, 192, 139, 194], [153, 125, 128, 0]]
    if (result_array == expected_array):
        print("PASS")
    else:
        print("FAIL")

    # Testing double to real64
    test_array = [0.0, -1.79769313486231570e308, -4.94065645841246544e-324, 4.94065645841246544e-324, 1.79769313486231570e+308, -6787.015573, 2333.656565]
    result_array = [[], [], [], [], [], [], []]
    for ii in range(len(test_array)):
        result_array[ii] = double_to_real64(test_array[ii])
    expected_array = [[0,0,0,0,0,0,0,0], [255,255,255,255,255,255,239,255], [1,0,0,0,0,0,0,128], [1,0,0,0,0,0,0,0], [255,255,255,255,255,255,239,127], [179,149,151,252,3,131,186,192], [101,165,73,41,80,59,162,64]]
    if (result_array == expected_array):
        print("PASS")
    else:
        print("FAIL")

    # Testing r32 to float
    # results from: https://www.h-schmidt.net/FloatConverter/IEEE754.html 
    r = [0, 16, 96, 69]
    print('Expected 3585.0 got {}'.format(real_to_float(r)))

    r = [0, 0, 0, 0]
    print('Expected 0.0 got {}'.format(real_to_float(r)))

    r = [212, 154, 134, 190]
    print('Expected -0.26289999485 got {}'.format(real_to_float(r)))

    r = [95, 112, 137, 176]
    print('Expected -9.99999971718e-10 got {}'.format(real_to_float(r)))

    r = [255, 255, 255, 255]
    print('Expected nan got {}'.format(real_to_float(r)))

    r = [255, 255, 255, 254]
    print('Expected -1.70141173319e+38 got {}'.format(real_to_float(r)))

    r = [255, 255, 255, 126]
    print('Expected 1.70141173319e+38 got {}'.format(real_to_float(r)))

    r = [212, 00, 134, 190]
    print('Expected -0.261725068092 got {}'.format(real_to_float(r)))

    r = [136, 150, 247, 21]
    print('Expected 1E-25 got {}'.format(real_to_float(r)))

    # Testing real64 to floats
    # results from: https://babbage.cs.qc.cuny.edu/IEEE-754.old/64bit.html 
    r = [136, 150, 247, 21, 136, 150, 247, 21]
    print('Expected 7.5234026909960690e-203 got {}'.format(real_to_float(r)))
    
    r = [255,255,255,255,255,255,255,254]
    print('-5.4861240687936880e+303 got {}'.format(real_to_float(r)))

    # Testing to and from accuracy
    # f1 is test float
    f1 = 1e-9
    f2 = real_to_float(float_to_real32(f1))
    print("Input: {}".format(f1)) 
    print("Output: {}".format(f2))
    print("differ by {}".format(abs(f1-f2)))
    arr = [abs(f1), abs(f2)]
    if (min(arr) != 0.0):
        print("Giving a percentage accuracy of {}".format(min(arr)/max(arr)*100))
    

if __name__ == "__main__":
    main()

