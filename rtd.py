from __future__ import print_function
import pilxi
import datetime
import sqlite3
import pprint
from contextlib import closing

if __name__ == "__main__":

    # Connect to a chassis using an IP address.
    # The ClientBridge driver can also connect to local PXI chassis by passing
    # 'PXI' in place of the IP.
    print("pilxi wrapper version: {}".format(pilxi.__version__))

    IP_Address = "192.168.80.25"

     # Default port and timeout settings in mS
    port = 1024
    timeout = 1000

    # In this example we'll directly connect to the card using bus and device numbers:
    bus = 2
    device = 12

    try:

        # Open a session with the LXI unit
        session = pilxi.Pi_Session(IP_Address)

        # Open a card by bus and device numbers
        card = session.OpenCard(bus, device)

        # Get the card ID
        cardId = card.CardId()

    # On any errors, print a description of the error and exit
    except pilxi.Error as ex:
        print("Error occurred: ", ex.message)
        exit()

    print("Connected to chassis at", IP_Address)
    print("Successfully connected to card at bus", bus, "device", device)
    print("Card ID: ", cardId)

    subunits = [1, 2, 3, 4, 5, 6] 
    # subunits = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

    rtds = {i : [[], []] for i in range(1, 7)} 

    # Connect to the SQLite database
    db_path = "/var/lib/grafana/db/rtd.db"
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        # Create the table if it does not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RTDs (
                subunit INTEGER,
                resistance INTEGER,
                timestamps REAL
            )
        """)

    for subunit in subunits:
        card.ResSetResistance(subunit, 0)

    while True:
        
        # Collect data from channels 1 to 16
        for subunit in subunits: 
            timestamp = datetime.datetime.now().timestamp()
            curr_ohm = card.ResGetResistance(subunit)

            rtds[subunit][0].append(timestamp)
            rtds[subunit][1].append(str(curr_ohm))

            # Insert data into the table
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO RTDs (subunit, resistance, timestamps) 
                    VALUES (?, ?, ?)
                """, (subunit, curr_ohm, timestamp))
                connection.commit()

        print("Data updated in RTDs table successfully.")

        # Print rtds data in a pretty format
        print("RTDs Data:")
        for subunit in subunits:
            print(f"\nSubunit {subunit}:")
            pprint.pprint(list(zip(rtds[subunit][0], rtds[subunit][1])), indent=2, width=80)

        # Specify desired subunit to modify or quit to terminate program
        subunit = input("Channel Number (1-6): ")
        
        if subunit.lower() == 'quit':
            print("Program Terminated")
            break

        try:
            # Convert input to integer and check valid range
            subunit = int(subunit)
            if subunit < 1 or subunit > 20:
                raise ValueError("Channel number must be between 1 and 16")

            # Specify desired resistance for subunit (40 - 900 ohms) 
            ohms = int(input("Resistance Request (40-900): "))

            # Set ohms on the subunit
            print("Setting resistance", subunit, "to", ohms, "Ω...")
            card.ResSetResistance(subunit, ohms)

            # Read the ohms of the subunit
            ohms = card.ResGetResistance(subunit)
            print("Resistance", subunit, "set to", ohms, "Ω")
            

        except ValueError as ve:
            print(f"Invalid input: {ve}")

        except Exception as e:
            print(f"An error occurred: {e}")

    # Print the number of rows inserted
    with sqlite3.connect(db_path) as connection:
        with closing(connection.cursor()) as cursor:
            rows = cursor.execute("SELECT * FROM RTDs").fetchall()
            print("Data in RTDs table:")
            for row in rows:
                print(row)

