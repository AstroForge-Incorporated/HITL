import smbus
import time
import socket

bus1 = smbus.SMBus(1)  
bus6 = smbus.SMBus(6)  

buses = [bus1, bus6]
    
# bus addresses
addresses = [0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49]

# Register addresses
POWER_REGISTER = 0x03  # Power Register
VOLTAGE_REGISTER = 0x02  # Voltage Register
CURRENT_REGISTER = 0x01  # Current Register
CONFIG_REGISTER = 0x00   # Config Register

def read_register(bus, address, register):
    """Read a 16-bit value from the specified register."""
    raw_bytes = bus.read_i2c_block_data(address, register, 2)
    value = raw_bytes[0] << 8 | raw_bytes[1]
    return value

def two_complement_to_signed(value, bits):
    """Convert a two's complement encoded value to a signed integer."""
    if value & (1 << (bits - 1)):  # Check if the MSB is set
        value -= (1 << bits)  # Adjust for negative value
    return value

def get_voltage(bus, address):
    raw_value = read_register(bus, address, VOLTAGE_REGISTER)
    voltage = raw_value * 0.00125  # LSB size is 1.25 mV/bit
    return voltage

def get_power(bus, address):
    raw_value = read_register(bus, address, POWER_REGISTER)
    # Power is always positive in the register, no need for two's complement conversion
    power = raw_value * 0.01  # LSB size is 10 mW/bit
    return power

def get_current(bus, address):
    raw_value = read_register(bus, address, CURRENT_REGISTER)
    # Convert raw_value from two's complement to signed value
    signed_value = two_complement_to_signed(raw_value, 16)  # 16-bit register
    current = signed_value * 0.00125  # LSB size is 1.25 mA/bit
    return current

def configure_device(bus, address):
    data_block = [0x61, 0x27]
    bus.write_i2c_block_data(address, CONFIG_REGISTER, data_block)



def main():
        
    # create server connections
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12346))
    server_socket.listen(1)
    
    print("Waiting for Connection")
    connection,  client_address = server_socket.accept()
    print(f"Connected to {client_address}")
    
    # configure addresses for bus 1 and 6
    for bus in buses:
        for address in addresses:
            configure_device(bus, address)
    
    try:
        while True:
             for bus in buses:
                for address in addresses:
                    current = get_current(bus, address)
                    voltage = get_voltage(bus, address)
                    power = get_power(bus, address)
                    print(f"Current: {current:.2f} A")
                    print(f"Voltage: {voltage:.2f} V")
                    print(f"Power: {power:.2f} W")
                    message = f"{current:.2f}, {voltage:.2f}, {power:.2f}"
                    connection.sendall(message.encode('utf-8'))
                    time.sleep(0.25)
                    
    except KeyboardInterrupt:
        print("Server interrupted")
    finally: 
        connection.close()
    
if __name__ == "__main__":
    main()
