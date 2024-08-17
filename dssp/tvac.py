import time
import argparse
import csv
import dssp_canopen as dssp

# List of addresses
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

# Celsius to bytes conversion
def cel2bytes(celsius, byte_length=2):
    kelvin = (celsius + 273.15) * 10
    scaled_temp = int(round(kelvin))
    payload = scaled_temp.to_bytes(byte_length, byteorder='little', signed=False)
    return payload

# Bytes to Celsius conversion
def bytes2cel(byte_sequence):
    value = int.from_bytes(byte_sequence, byteorder='little')
    kelvin = value / 10
    celsius = kelvin - 273.15
    return celsius

def main():
    cmd_line = argparse.ArgumentParser(description="Dawn Aerospace DSSP Test")
    cmd_line.add_argument("device", help="The serial or CAN interface")
    cmd_line.add_argument("node", help="The target node id", type=int)
    cmd_line.add_argument("-b", "--baudrate", help="CAN or Serial baud rate", type=int, default=115200)
    cmd_line.add_argument("-o", "--output", help="Output CSV file", type=str, default="output.csv")
    args = cmd_line.parse_args()

    print("Dawn Aerospace (c) 2022")
    print("AstroForge TVAC Testing")

    try:
        gateway = dssp.CanInterface()
        try:
            gateway.connect(channel=args.device)
        except:
            print("Error connecting to ", args.device)
            exit(-1)

        node = gateway.add_node(args.node, None)

        # Open the CSV file for writing
        with open(args.output, mode='w', newline='') as csv_file:
            fieldnames = ['Timestamp', 'Address', 'Celsius Setpoint', 'Celsius Real']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            
            # Write the header
            writer.writeheader()

            print("Enter Heater 1-10 or quit to terminate")

            while True:

                node.sdo.download(0x2500, 1, b'\x00')

                # Prompt user for heater input
                heater = input("Heater #: ")

                # Check if the user wants to exit
                if heater.lower() == "quit":
                    print("Terminated")
                    break

                # Ensure the heater input is a valid number
                try:
                    heater_num = int(heater)
                    if heater_num not in range(1, 11):
                        raise ValueError("Heater number must be between 1 and 10")
                except ValueError:
                    print("Invalid input. Please enter a number between 1 and 10 or 'quit'.")
                    continue

                # Perform actions for the selected heater
                curr_address = addresses[heater_num - 1]
                if curr_address == addresses[0] or curr_address == addresses[1]:
                    node.sdo.download(curr_address, 7, cel2bytes(25))
                    node.sdo.download(0x2500, 1, b'\x05')
                else:
                    node.sdo.download(curr_address, 5, cel2bytes(25))
                    node.sdo.download(0x2500, 1, b'\x05')
        
                # Record the start time
                start_time = time.time()
                run_duration = 5 * 60  # 5 minutes in seconds
                interval = 30  # 30 seconds interval
                data_pass = 1

                while True:
                    num = 1
                    # Check if 5 minutes have passed
                    current_time = time.time()
                    if current_time - start_time > run_duration:
                        print("5 minutes have passed. Terminating.")
                        break

                    # Iterate through all addresses
                    print ("Data Iteration", data_pass)
                    for address in addresses:
                        try:
                            # Retrieve data based on address
                            if address == addresses[0] or address == addresses[1]:
                                setpoint = bytes2cel(node.sdo.upload(address, 7))
                                real_temp = bytes2cel(node.sdo.upload(address, 5))
                            else:
                                setpoint = bytes2cel(node.sdo.upload(address, 5))
                                real_temp = bytes2cel(node.sdo.upload(address, 3))

                            # Write data to CSV
                            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                            writer.writerow({
                                'Timestamp': timestamp,
                                'Address': hex(address),
                                'Celsius Setpoint': setpoint,
                                'Celsius Real': real_temp
                            })
                            csv_file.flush()

                            print(f"Heater {num}: Setpoint = {setpoint:.2f}°C, Real = {real_temp:.2f}°C")
                            num += 1

                        except Exception as e:
                            print(f"Error processing address {hex(address)}: {e}")

                    # Wait for the specified interval before next iteration
                    time.sleep(interval)
                    data_pass += 1
                            
                if curr_address == addresses[0] or curr_address == addresses[1]:
                    node.sdo.download(curr_address, 7, cel2bytes(0))
                else:
                    node.sdo.download(curr_address, 5, cel2bytes(0))

    except KeyboardInterrupt:
        print("Interrupted by user.")
        node.sdo.download(0x2500, 1, b'\x00')
    except Exception as e:
        print(f"Unknown error. Check you have the correct port and permissions to use it. Error: {e}")

if __name__ == "__main__":
    main()

