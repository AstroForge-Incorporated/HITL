import pilxi

IP_Address = "192.168.80.25"

# Port, timeout parameters are optional, defaults will be used otherwise.
session = pilxi.Pi_Session(IP_Address)
# or 
session = pilxi.Pi_Session(IP_Address, port=1024, timeout=5000)

# Get list of Card IDs for cards in chassis
cardID_array = session.GetUsableCards(0)
print("Card IDs:", cardID_array)


# Get list of Card Bus and Device Numbers
card_array = session.FindFreeCards()

for card in card_array:
    bus, device = card
    print("Card at bus {} device {}".format(bus, device))
