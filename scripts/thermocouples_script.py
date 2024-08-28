from pywebio import start_server
from pywebio.output import put_html, put_text, put_error, put_table
from pywebio.input import input
import pilxi
import sqlite3
import datetime

# Global variables
session = None
card = None
subunits = list(range(1, 17))  # Subunit numbers 1 through 16
db_path = "/var/lib/grafana/db/thermocouple.db"

def connect_hardware():
    global session, card
    try:
        session = pilxi.Pi_Session("192.168.80.25")
        card = session.OpenCard(bus=2, device=13)
    except pilxi.Error as ex:
        put_error(f"Error occurred: {ex.message}")
        raise

def initialize_database():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS THERMOCOUPLES (
                subunit INTEGER,
                voltage INTEGER,
                timestamps REAL
            )
        """)
        connection.commit()

def update_database(subunit, voltage, timestamp):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO THERMOCOUPLES (subunit, voltage, timestamps) 
            VALUES (?, ?, ?)
        """, (subunit, voltage, timestamp))
        connection.commit()

def show_dashboard():
    connect_hardware()
    initialize_database()

    def collect_data():
        thermocouples = {i: [[], []] for i in subunits}
        for subunit in subunits:
            card.VsourceSetVoltage(subunit, 1)  # Initialize voltage
        
        while True:
            thermocouples_data = {subunit: [] for subunit in subunits}
            for subunit in subunits:
                timestamp = datetime.datetime.now().timestamp()
                voltage = card.VsourceGetVoltage(subunit)

                thermocouples[subunit][0].append(timestamp)
                thermocouples[subunit][1].append(voltage)
                update_database(subunit, voltage, timestamp)
                thermocouples_data[subunit].append(voltage)

            # Display the horizontal table
            table_data = [["Subunit"] + ["Voltage"]]
            for subunit, voltages in thermocouples_data.items():
                row = [f"Subunit {subunit}"] + voltages
                table_data.append(row)

            put_table(table_data)

            # Handling user input in PyWebIO
            subunit = input("Channel Number (1-16):")
            try:
                subunit = int(subunit)
                if subunit < 1 or subunit > 16:
                    raise ValueError("Channel number must be between 1 and 16")

                voltage = int(input("mV Request:"))
                card.VsourceSetVoltage(subunit, voltage)
                voltage = card.VsourceGetVoltage(subunit)

            except ValueError as ve:
                put_error(f"Invalid input: {ve}")

            except Exception as e:
                put_error(f"An error occurred: {e}")

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
        .input {
            background-color: #00a69c; 
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
        .hidden {
            display: none;
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
        <div id="thermocouples" class="hidden">
            <h2>Thermocouples Page</h2>
            <p>Content for TCs</p>
        </div>
        <div id="rtds" class="hidden">
            <h2>RTDs Page</h2>
            <p>Content for RTDs</p>
        </div>
        <div id="eload" class="hidden">
            <h2>Eload Page</h2>
            <p>Content for Eload</p>
        </div>
        <div id="ina" class="hidden">
            <h2>INA Page</h2>
            <p>Content for INA</p>
        </div>
    </div>
    ''')

    collect_data()

if __name__ == '__main__':
    start_server(show_dashboard, host='0.0.0.0', port=8081)










