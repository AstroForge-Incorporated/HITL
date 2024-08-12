import serial
import datetime
from time import sleep
import requests
import sqlite3
import pprint
from contextlib import closing

# Configure the serial connection
ser = serial.Serial(
    port='COM3',
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1  # Timeout for read
)

# establish loads
loads = [1, 2, 3, 4]

# initialize the dictionary with load keys, each with four empty lists [time, voltage, current, power]
modules = {i : [[], [], [], []] for i in range(1, 5)} 

# Connect to the SQLite database
with sqlite3.connect("eload.db") as connection:
    cursor = connection.cursor()

    # Create the table if it does not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ELOADS (
            load INTEGER,
            voltage INTEGER,
            current INTEGER,
            power INTEGER,
            timestamps REAL
        )
    """)
try:
    while True:
        sleep(5)
        ser.write(b':FETC:ALLV?\n')
        voltages = ser.readline().decode('utf-8').strip().split(',')
        print(voltages)
        ser.write(b':FETC:ALLC?\n')
        currents = ser.readline().decode('utf-8').strip().split(',')
        print(currents)
        ser.write(b':FETC:ALLP?\n')
        powers = ser.readline().decode('utf-8').strip().split(',')
        print(powers)
        
        # Collect data from loads 1-4
        for load in loads: 
            timestamp = datetime.datetime.now().timestamp()
            
            curr_vol = voltages[load-1]
            curr_curr = currents[load-1]
            curr_pow = powers[load-1]

            modules[load][0].append(timestamp)
            modules[load][1].append(curr_vol)
            modules[load][2].append(curr_curr)
            modules[load][3].append(curr_pow)
            

            # Insert data into the table
            cursor.execute("""
                INSERT INTO ELOADS (load, timestamps, voltage, current, power) 
                VALUES (?, ?, ?, ?, ?)
            """, (load, timestamp, curr_vol, curr_curr, curr_pow))

        # Commit the changes
        connection.commit()
        print("Data updated in ELOADS table successfully.")

        # Print rtds data in a pretty format
        print("Eloads Data:")
        for load in loads:
            print(f"\nLoad {load}:")
            pprint.pprint(list(zip(modules[load][0], modules[load][1], modules[load][2], modules[load][3])), indent=2, width=80)
            
except KeyboardInterrupt:
    # Print the number of rows inserted
    print("Number of rows inserted:", connection.total_changes)

    # Optional: Verify the data was inserted correctly
    with sqlite3.connect("eload.db") as connection:
        with closing(connection.cursor()) as cursor:
            rows = cursor.execute("SELECT * FROM ELOADS").fetchall()
            print("Data in ELOADS table:")
            for row in rows:
                print(row)


    ser.close()
