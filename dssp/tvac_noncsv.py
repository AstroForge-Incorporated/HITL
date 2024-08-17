import time
import argparse
import dssp_canopen as dssp

addresses = [
    0x2612,  # Address for heater 1
    0x2614,  # Address for heater 2
    0x2616,  # Address for heater 3
    0x261E,  # Address for heater 4
    0x261A,  # Address for heater 5
    0x2622,  # Address for heater 6
    0x2617,  # Address for heater 7
    0x261F,  # Address for heater 8
    0x261B,  # Address for heater 9
    0x2623   # Address for heater 10
]

# Assign each heater a number
heaters = {i: hex(addresses[i - 1]) for i in range(1, 11)}

# celsius to bytes
def cel2bytes(celsius, byte_length=2):
    kelvin = (celsius + 273.15) * 10
    scaled_temp = int(round(kelvin))
    payload = scaled_temp.to_bytes(byte_length, byteorder='little', signed=False)
    return payload

# bytes to celsius
def bytes2cel(byte_sequence):
    value = int.from_bytes(byte_sequence, byteorder='little')
    kelvin = value / 10
    celsius = kelvin - 273.15
    return celsius

def main():
    cmd_line = argparse.ArgumentParser(description="Dawn Aerospace DSSP Test")
    cmd_line.add_argument("device", help="The serial or CAN interface")
    cmd_line.add_argument("node", help="The target node id", type = int)
    cmd_line.add_argument("-b", "--baudrate", help="CAN or Serial baud rate", type=int, default=115200)
    args = cmd_line.parse_args()

    print( "Dawn Aerospace (c) 2022")
    print( "Starting DSSP loop test on ", args.device )

    try:
        gateway = dssp.CanInterface()
        try:
            gateway.connect(channel=args.device)
        except:
            print("Error connecting to ", args.device)
            exit(-1)

        node = gateway.add_node(args.node, None)
        
        print("Enter Heater 1-10 or quit to terminate")
        while True:

            # change sleep time for length of heater-on time
            time.sleep(1)
            node.sdo.download(0x2500, 1, b'\x00')

            heater = input("Heater #: ")

            # Check if the user wants to exit
            if heater.lower() == "quit":
                print("Terminated")
                break

            # Ensure the heater input is a valid number
            try:
                heater_num = int(heater)
            except ValueError:
                print("Invalid input. Please enter a number or 'quit'.")
                continue

            if int(heater) == 1:
                node.sdo.download(0x2612, 7, cel2bytes(23))
                node.sdo.download(0x2500, 1, b'\x05')
                print("Celsius Setpoint: ",bytes2cel(node.sdo.upload(0x2612, 7)))
                print("Celsius Real:",bytes2cel(node.sdo.upload(0x2612, 5)))
                node.sdo.download(0x2612, 7, cel2bytes(0))

            if int(heater) == 2:
                node.sdo.download(0x2614, 7, cel2bytes(23))
                node.sdo.download(0x2500, 1, b'\x05')
                print("Celsius Setpoint: ",bytes2cel(node.sdo.upload(0x2614, 7)))
                print("Celsius Real:",bytes2cel(node.sdo.upload(0x2614, 5)))
                node.sdo.download(0x2614, 7, cel2bytes(0))
                
            if int(heater) == 3:
                node.sdo.download(0x2616, 5, cel2bytes(23))
                node.sdo.download(0x2500, 1, b'\x05')
                print("Celsius Setpoint: ",bytes2cel(node.sdo.upload(0x2616, 5)))
                print("Celsius Real:",bytes2cel(node.sdo.upload(0x2616, 3)))
                node.sdo.download(0x2616, 5, cel2bytes(0))

            if int(heater) == 4:
                node.sdo.download(0x261E, 5, cel2bytes(23))
                node.sdo.download(0x2500, 1, b'\x05')
                print("Celsius Setpoint: ",bytes2cel(node.sdo.upload(0x261e, 5)))
                print("Celsius Real:",bytes2cel(node.sdo.upload(0x261e, 3)))
                node.sdo.download(0x261E, 5, cel2bytes(0))

            if int(heater) == 5:
                node.sdo.download(0x261A, 5, cel2bytes(23))
                node.sdo.download(0x2500, 1, b'\x05')
                print("Celsius Setpoint: ",bytes2cel(node.sdo.upload(0x261a, 5)))
                print("Celsius Real:",bytes2cel(node.sdo.upload(0x261a, 3)))
                node.sdo.download(0x261A, 5, cel2bytes(0))

            if int(heater) == 6:
                node.sdo.download(0x2622, 5, cel2bytes(23))
                node.sdo.download(0x2500, 1, b'\x05')
                print("Celsius Setpoint: ",bytes2cel(node.sdo.upload(0x2622, 5)))
                print("Celsius Real:",bytes2cel(node.sdo.upload(0x2622, 3)))
                node.sdo.download(0x2622, 5, cel2bytes(0))

            if int(heater) == 7:
                node.sdo.download(0x2617, 5, cel2bytes(23))
                node.sdo.download(0x2500, 1, b'\x05')
                print("Celsius Setpoint: ",bytes2cel(node.sdo.upload(0x2617, 5)))
                print("Celsius Real:",bytes2cel(node.sdo.upload(0x2617, 3)))
                node.sdo.download(0x2617, 5, cel2bytes(0))

            if int(heater) == 8:
                node.sdo.download(0x261F, 5, cel2bytes(23))
                node.sdo.download(0x2500, 1, b'\x05')
                print("Celsius Setpoint: ",bytes2cel(node.sdo.upload(0x261f, 5)))
                print("Celsius Real:",bytes2cel(node.sdo.upload(0x261f, 3)))
                node.sdo.download(0x261F, 5, cel2bytes(0))

            if int(heater) == 9:
                node.sdo.download(0x261B, 5, cel2bytes(23))
                node.sdo.download(0x2500, 1, b'\x05')
                print("Celsius Setpoint: ",bytes2cel(node.sdo.upload(0x261b, 5)))
                print("Celsius Real:",bytes2cel(node.sdo.upload(0x261b, 3)))
                node.sdo.download(0x261B, 5, cel2bytes(0))

            if int(heater) == 10:
                node.sdo.download(0x2623, 5, cel2bytes(23))
                node.sdo.download(0x2500, 1, b'\x05')
                print("Celsius Setpoint: ",bytes2cel(node.sdo.upload(0x2623, 5)))
                print("Celsius Real:",bytes2cel(node.sdo.upload(0x2623, 3)))
                node.sdo.download(0x2623, 5, cel2bytes(0))

            if heater.lower() == "exit":
                print("terminated")
                break



    except KeyboardInterrupt:
        node.sdo.download(0x2500, 1, b'\x00')
    except:
        print( "Unknown error. Check you have the correct port and permissions to use it." )
        
if __name__ == "__main__":
    main()