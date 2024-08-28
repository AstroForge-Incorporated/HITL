import socket
import datetime
import sqlite3
from contextlib import closing
import os

def main():
    # ina pi address
    IP_Address = "192.168.80.104"
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP_Address, 12346))
    
    addresses_all = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    addresses = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    add = {i: [[], [], [], []] for i in range(1, 21)}  # [timestamps], [currents], [voltages], [powers]
    
    # Desired directory for the SQLite database
    db_directory = '/var/lib/grafana/db'
    os.makedirs(db_directory, exist_ok=True)  # Create the directory if it doesn't exist

    # Database file path
    db_path = os.path.join(db_directory, 'vmbox.db')
    print(f"Using database path: {db_path}")  # Debugging line to check path

    # Connect to the SQLite database
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        # Create the table if it does not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS VMBOX (
                address INTEGER,
                current INTEGER,
                voltage INTEGER,
                power INTEGER,
                timestamps REAL
            )
        """)
    
        try:
            while True:
                for address in addresses_all:
                    data = client_socket.recv(1024).decode('utf-8')
                    print(data)
                    curr_curr = data.split(',')[0]
                    curr_vol = data.split(',')[1]
                    curr_pow = data.split(',')[2]
                    timestamp = datetime.datetime.now().timestamp()
                    add[address][0].append(timestamp)
                    add[address][1].append(curr_curr)
                    add[address][2].append(curr_vol)
                    add[address][3].append(curr_pow)
                    print(add[address][1])
                    print(add[address][2])
                    print(add[address][3])
                
                    # Insert data into the table
                    cursor.execute("""
                        INSERT INTO VMBOX (address, current, voltage, power, timestamps) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (address, curr_curr, curr_vol, curr_pow, timestamp))
                    # Commit the changes
                    connection.commit()
        
        except KeyboardInterrupt:
            print("Client interrupted")
        finally:
            client_socket.close()

if __name__ == "__main__":
    main()
