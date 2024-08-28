from pywebio import start_server
from pywebio.output import put_html, put_table, put_text, put_error
from pywebio.input import input
import serial
import sqlite3
import datetime
from time import sleep
import os
from contextlib import closing

# Configure the serial connection
ser = serial.Serial(
    port='/dev/ttyACM1',
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1  # Timeout for read
)

# Establish loads
loads = [1, 2, 3, 4]

# Initialize the dictionary with load keys, each with four empty lists [time, voltage, current, power]
modules = {i: [[], [], [], []] for i in range(1, 5)}

# Desired directory for the SQLite database
db_directory = '/var/lib/grafana/db'
os.makedirs(db_directory, exist_ok=True)  # Create the directory if it doesn't exist

# Database file path
db_path = os.path.join(db_directory, 'eload.db')
print(f"Using database path: {db_path}")  # Debugging line to check path

# Connect to the SQLite database and create the table if it does not exist
def setup_database():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ELOADS (
                load INTEGER,
                voltage INTEGER,
                current INTEGER,
                power INTEGER,
                timestamps REAL
            )
        """)
        connection.commit()

def insert_data(load, timestamp, voltage, current, power):
    try:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO ELOADS (load, timestamps, voltage, current, power) 
                VALUES (?, ?, ?, ?, ?)
            """, (load, timestamp, voltage, current, power))
            connection.commit()
    except sqlite3.Error as e:
        put_error(f"Database error: {e}")

def collect_data():
    try:
        while True:
            try:
                sleep(5)
                ser.write(b':FETC:ALLV?\n')
                voltages = ser.readline().decode('utf-8').strip().split(',')
                ser.write(b':FETC:ALLC?\n')
                currents = ser.readline().decode('utf-8').strip().split(',')
                ser.write(b':FETC:ALLP?\n')
                powers = ser.readline().decode('utf-8').strip().split(',')
                
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
                    insert_data(load, timestamp, curr_vol, curr_curr, curr_pow)

                print("Data updated in ELOADS table successfully.")

            except serial.SerialException as e:
                put_error(f"Serial error: {e}")
            except Exception as e:
                put_error(f"Unexpected error: {e}")

    except KeyboardInterrupt:
        print("Program interrupted.")
    finally:
        ser.close()

def show_dashboard():
    setup_database()

    def update_table():
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM ELOADS ORDER BY timestamps DESC LIMIT 50")  # Limit to the latest 50 rows
            rows = cursor.fetchall()
            
            # Prepare data for display
            table_data = [["Load", "Voltage", "Current", "Power", "Timestamp" ]]
            for row in rows:
                table_data.append(row)

            put_table(table_data)

    # Display the initial HTML layout with updated styles
    put_html('''
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=New+Amsterdam&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Jersey:wght@400&display=swap');

        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            width: 100%;
            font-family: 'Roboto', sans-serif;
            background-color: #3e3f43;
        }
        .navbar {
            background-color: #00a69c;
            color: #f3a834;
            padding: 15px 30px;
            text-align: center;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 1000;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .navbar h1 {
            margin: 0;
            font-size: 50px;
            font-weight: 700;
            font-family: 'New Amsterdam', sans-serif;
            cursor: pointer;
        }
        .button-container {
            display: flex;
            gap: 20px;
        }
        .navbar-button {
            background-color: #f3a834;
            color: #FFFFFF;
            border: none;
            padding: 15px 25px;
            font-size: 18px;
            cursor: pointer;
            border-radius: 5px;
            text-transform: uppercase;
            font-weight: 700;
            font-family: 'Bebas Neue', sans-serif;
        }
        .navbar-button:hover {
            background-color: #d68e2b;
        }
        .content {
            margin-top: 80px;
            padding: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        table, th, td {
            border: 1px solid #4a4a4a;
        }
        th {
            background-color: #00a69c;
            color: #FFFFFF;
            padding: 10px;
        }
        td {
            background-color: #333333;
            color: #FFFFFF;
            padding: 10px;
            text-align: left;
        }
        tr:nth-child(even) td {
            background-color: #4a4a4a;
        }
        tr:nth-child(odd) td {
            background-color: #333333;
        }
    </style>
    <div class="navbar">
        <h1 onclick="window.location.href='http://192.168.80.85:8080'">AstroForge HITL</h1>
        <div class="button-container">
            <button class="navbar-button" onclick="window.location.href='http://192.168.80.85:8081'">Thermocouples</button>
            <button class="navbar-button" onclick="window.location.href='http://192.168.80.85:8082'">RTDs</button>
            <button class="navbar-button" onclick="window.location.href='http://192.168.80.85:8083'">Eloads</button>
            <button class="navbar-button" onclick="window.location.href='http://192.168.80.85:8084'">INA</button>
        </div>
    </div>
    <div class="content">
        <div id="data">
            <!-- Table will be inserted here -->
        </div>
    </div>
    ''')

    # Call to update the table with the most recent data
    update_table()

    # Start data collection in a separate thread
    import threading
    threading.Thread(target=collect_data, daemon=True).start()

if __name__ == '__main__':
    start_server(show_dashboard, host='0.0.0.0', port=8083)


