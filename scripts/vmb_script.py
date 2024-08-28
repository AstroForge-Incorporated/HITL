from pywebio import start_server
from pywebio.output import put_html, put_error
from pywebio.input import input
import socket
import datetime
import sqlite3
import os
import threading
from flask import Flask, jsonify
import time

# Configuration for the SQLite database
db_directory = '/var/lib/grafana/db'
os.makedirs(db_directory, exist_ok=True)  # Create the directory if it doesn't exist

# Database file path
db_path = os.path.join(db_directory, 'vmbox.db')

# Initialize Flask app
app = Flask(__name__)

def setup_database():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VMBOX (
                address INTEGER,
                current INTEGER,
                voltage INTEGER,
                power INTEGER,
                timestamps REAL
            )
        """)
        connection.commit()

def insert_data(address, timestamp, current, voltage, power):
    try:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO VMBOX (address, current, voltage, power, timestamps) 
                VALUES (?, ?, ?, ?, ?)
            """, (address, current, voltage, power, timestamp))
            connection.commit()
    except sqlite3.Error as e:
        put_error(f"Database error: {e}")

def collect_data():
    IP_Address = "192.168.80.104"
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((IP_Address, 12345))
        client_socket.settimeout(None)  # Disable timeout for continuous reading

        addresses_all = [i for i in range(1, 21)]

        while True:
            try:
                # Read data from the socket
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    continue

                data_split = data.split(',')
                if len(data_split) < 3:
                    continue

                # Process data for each address
                for address in addresses_all:
                    curr_curr, curr_vol, curr_pow = data_split[:3]
                    timestamp = datetime.datetime.now().timestamp()

                    # Insert data into the database
                    insert_data(address, timestamp, curr_curr, curr_vol, curr_pow)

            except socket.error as e:
                print(f"Socket error: {e}")
                break
            except Exception as e:
                print(f"Error in data collection: {e}")
                break

    except Exception as e:
        print(f"Failed to connect or socket error: {e}")
    finally:
        client_socket.close()

@app.route('/data')
def get_data():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM VMBOX ORDER BY timestamps DESC LIMIT 50")
        rows = cursor.fetchall()
        return jsonify([dict(zip(['address', 'current', 'voltage', 'power', 'timestamps'], row)) for row in rows])

def update_table():
    try:
        # Fetch latest data from the database
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM VMBOX ORDER BY timestamps DESC LIMIT 50")
            rows = cursor.fetchall()

        # Build HTML table
        if rows:
            html = '<table><thead><tr><th>Address</th><th>Timestamp</th><th>Current</th><th>Voltage</th><th>Power</th></tr></thead><tbody>'
            for row in rows:
                address, current, voltage, power, timestamp = row
                html += f'<tr><td>{address}</td><td>{timestamp}</td><td>{current}</td><td>{voltage}</td><td>{power}</td></tr>'
            html += '</tbody></table>'
        else:
            html = '<p>No data available</p>'

        # Update the HTML in the PyWebIO output
        put_html(html)
        
    except sqlite3.Error as e:
        put_html(f"Database error: {e}")

def show_dashboard():
    setup_database()

    def update():
        while True:
            update_table()
            time.sleep(5)  # Update every 5 seconds

    # Start the table update in a separate thread
    threading.Thread(target=update, daemon=True).start()

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
        .message {
            color: #FFFFFF;
            background-color: #ff4d4d;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
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
        <div class="message">Start script on Raspberry Pi INA@PI with IP 192.168.80.104</div>
        <script>
            function fetchData() {
                fetch('/data')  // Endpoint to fetch data
                    .then(response => response.json())
                    .then(data => {
                        const table = document.querySelector('#data');
                        table.innerHTML = '';
                        if (data.length > 0) {
                            let html = '<table><thead><tr><th>Address</th><th>Timestamp</th><th>Current</th><th>Voltage</th><th>Power</th></tr></thead><tbody>';
                            data.forEach(row => {
                                html += `<tr><td>${row.address}</td><td>${row.timestamps}</td><td>${row.current}</td><td>${row.voltage}</td><td>${row.power}</td></tr>`;
                            });
                            html += '</tbody></table>';
                            table.innerHTML = html;
                        } else {
                            table.innerHTML = '<p>No data available</p>';
                        }
                    })
                    .catch(error => console.error('Error fetching data:', error));
            }
            setInterval(fetchData, 5000);  // Refresh every 5 seconds
            fetchData();  // Initial fetch
        </script>
    </div>
    ''')

    # Start data collection in a separate thread
    threading.Thread(target=collect_data, daemon=True).start()

if __name__ == '__main__':
    start_server(show_dashboard, host='0.0.0.0', port=8084)


