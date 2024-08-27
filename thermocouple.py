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
    device = 13

    # establish subunits
    subunits = [1, 2, 3, 4 , 5, 6 ,7 ,8 ,9, 10, 11, 12, 13, 14, 15, 16]

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

    # initialize the dictionary with subunit keys 1-16, each with two empty lists [timestamps, voltage]
    thermocouples = {i : [[], []] for i in range(1, 17)} 

    # Connect to the SQLite database
    db_path = "/var/lib/grafana/db/thermocouple.db"
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        # Create the table if it does not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS THERMOCOUPLES (
                subunit INTEGER,
                voltage INTEGER,
                timestamps REAL
            )
        """)

    for subunit in subunits:
        card.VsourceSetVoltage(subunit, 1)

    # Allow continuous input
    while True:
         
        # Collect data from channels 1 to 16
        for subunit in subunits: 
            timestamp = datetime.datetime.now().timestamp()
            curr_vol = card.VsourceGetVoltage(subunit)

            thermocouples[subunit][0].append(timestamp)
            thermocouples[subunit][1].append(curr_vol)

            # Insert data into the table
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO THERMOCOUPLES (subunit, voltage, timestamps) 
                    VALUES (?, ?, ?)
                """, (subunit, curr_vol, timestamp))
                connection.commit()

        print("Data updated in THERMOCOUPLES table successfully.")

        # Print thermocouples data in a pretty format
        print("Thermocouples Data:")
        for subunit in subunits:
            print(f"\nSubunit {subunit}:")
            pprint.pprint(list(zip(thermocouples[subunit][0], thermocouples[subunit][1])), indent=2, width=80)

        # Specify desired subunit to modify or quit to terminate program
        subunit = input("Channel Number (1-16): ")
        
        if subunit.lower() == 'quit':
            print("Program Terminated")
            break

        try:
            # Convert input to integer and check valid range
            subunit = int(subunit)
            if subunit < 1 or subunit > 16:
                raise ValueError("Channel number must be between 1 and 16")

            # Specify desired mV for subunit
            voltage = int(input("mV Request: "))

            # Set voltage on the subunit
            print("Setting voltage", subunit, "to", voltage, "mV...")
            card.VsourceSetVoltage(subunit, voltage)

            # Read the voltage of the subunit
            voltage = card.VsourceGetVoltage(subunit)
            print("Voltage", subunit, "set to", voltage, "mV.")
            
        except ValueError as ve:
            print(f"Invalid input: {ve}")

        except Exception as e:
            print(f"An error occurred: {e}")

    # Print the number of rows inserted
    with sqlite3.connect(db_path) as connection:
        with closing(connection.cursor()) as cursor:
            rows = cursor.execute("SELECT * FROM THERMOCOUPLES").fetchall()
            print("Data in THERMOCOUPLES table:")
            for row in rows:
                print(row)
