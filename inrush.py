import serial
import time

# Configure the serial connection
ser = serial.Serial(
    port='/dev/ttyACM1',
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1  # Timeout for read
)

try:
    # Send the *IDN? command followed by a newline haracter
    ser.write(b':CHAN? LIST\n')
    response = ser.readline().decode('utf-8').strip()
    print(f"Response from device: {response}")
    ser.write(b':CHAN 1\n')
    ser.write(b':CURR:STAT:L1 0\n')
    ser.write(b':RUN\n')
    num_iterations = 100

    # Generate the values and send commands
    for i in range(num_iterations):
        # Calculate the current phase of the loop
        t = i / (num_iterations - 1)
        # Use a triangular wave function to go up and down
        value = 2.4 * (1 - abs(2 * t - 1))
        # Format the command string with the current value
        command = f':CURR:STAT:L1 {value:.1f}\n'
        # Send the command via serial
        ser.write(command.encode())
    ser.write(b':ABOR\n')
except Exception as e:
    print(f"Error: {e}")

finally:
    # Close the serial connection
    ser.close()
