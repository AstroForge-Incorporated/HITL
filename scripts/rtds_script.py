from pywebio import start_server
from pywebio.output import put_html, put_text, put_error, put_table
from pywebio.input import input
import pilxi
import sqlite3
import datetime

# Global variables
session = None
card = None
subunits = list(range(1, 7))  # RTD subunit numbers 1 through 6
db_path = "/var/lib/grafana/db/rtd.db"

def connect_hardware():
    global session, card
    try:
        session = pilxi.Pi_Session("192.168.80.25")
        card = session.OpenCard(bus=2, device=12)
    except pilxi.Error as ex:
        put_error(f"Error occurred: {ex.message}")
        raise

def initialize_database():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RTDS (
                subunit INTEGER,
                resistance INTEGER,
                timestamps REAL
            )
        """)
        connection.commit()

def update_database(subunit, resistance, timestamp):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO RTDS (subunit, resistance, timestamps) 
            VALUES (?, ?, ?)
        """, (subunit, resistance, timestamp))
        connection.commit()

def show_dashboard():
    connect_hardware()
    initialize_database()

    def collect_data():
        rtds = {i: [[], []] for i in subunits}
        for subunit in subunits:
            card.ResSetResistance(subunit, 0)  # Initialize resistance
        
        while True:
            rtds_data = {subunit: [] for subunit in subunits}
            for subunit in subunits:
                timestamp = datetime.datetime.now().timestamp()
                resistance = card.ResGetResistance(subunit)

                rtds[subunit][0].append(timestamp)
                rtds[subunit][1].append(resistance)
                update_database(subunit, resistance, timestamp)
                rtds_data[subunit].append(resistance)

            # Display the horizontal table
            table_data = [["Subunit"] + ["Resistance"]]
            for subunit, resistances in rtds_data.items():
                row = [f"Subunit {subunit}"] + resistances
                table_data.append(row)

            put_table(table_data)

            # Handling user input in PyWebIO
            subunit = input("Channel Number (1-6):")
            try:
                subunit = int(subunit)
                if subunit < 1 or subunit > 6:
                    raise ValueError("Channel number must be between 1 and 6")

                resistance = int(input("Resistance Request (40-900):"))
                if resistance < 40 or resistance > 900:
                    raise ValueError("Resistance must be between 40 and 900 ohms")

                card.ResSetResistance(subunit, resistance)
                resistance = card.ResGetResistance(subunit)

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
        <div id="rtds">
        </div>
        <div id="thermocouples" class="hidden">
        </div>
        <div id="eload" class="hidden">
        </div>
        <div id="ina" class="hidden">
        </div>
    </div>
    ''')

    collect_data()

if __name__ == '__main__':
    start_server(show_dashboard, host='0.0.0.0', port=8082)
