"""User interface: input handling and printing tickets, receipts and slot status."""

from config import FLOORS, TIME_FMT


def ask_category():
    print("Vehicle category:")
    print("1. Compact")
    print("2. Large")
    print("3. EV")
    choice = input("Choose (1-3): ").strip()

    match choice:
        case "1":
            return "compact"
        case "2":
            return "large"
        case "3":
            return "ev"
        case _:
            raise ValueError("Invalid vehicle category.")


def valid_registration(reg):
    if reg == "":
        return False
    for ch in reg:
        if not (ch.isalnum() or ch == "-" or ch == " "):
            return False
    return True


def print_ticket(ticket, reg, slot, entry):
    print("\n========== PARKING TICKET ==========")
    print("Ticket       :", ticket)
    print("Registration :", reg)
    print("Slot         :", slot.slot_id)
    print("Slot type    :", slot.slot_type)
    print("Floor        :", slot.floor)
    print("Entry time   :", entry.strftime(TIME_FMT))
    print("====================================\n")


def print_receipt(receipt):
    print("\n========== PARKING RECEIPT =========")
    print("Ticket       :", receipt["ticket"])
    print("Registration :", receipt["reg"])
    print("Slot         :", receipt["slot"])
    print("Entry        :", receipt["entry"].strftime(TIME_FMT))
    print("Exit         :", receipt["exit"].strftime(TIME_FMT))
    print("Billed hours :", receipt["hours"])
    print(f"Total fee    : Rs.{receipt['fee']:.2f}")
    print("====================================\n")


def handle_check_in(lot):
    reg = input("Registration number: ").strip().upper()

    if not valid_registration(reg):
        print("[!] Invalid registration number.")
        return

    if lot.is_parked(reg):
        print("[!] This vehicle is already parked.")
        return

    try:
        category = ask_category()
        ticket, slot, entry = lot.check_in(reg, category)
        print_ticket(ticket, reg, slot, entry)
    except ValueError as e:
        print("[!]", e)


def handle_check_out(lot):
    ticket = input("Ticket number (e.g. T1001): ").strip().upper()

    try:
        receipt = lot.check_out(ticket)
        print_receipt(receipt)
    except KeyError:
        print("[!] Invalid ticket number or session not found.")


def show_slots(lot):
    print("\n========== PARKING SLOT STATUS ==========")

    for floor in range(1, FLOORS + 1):
        print("\nFloor", floor)
        for slot in lot.slots:
            if slot.floor == floor:
                print(slot)

    occupied = len(lot.occupied_ids)
    free = len(lot.slots) - occupied

    print("\nTotal slots :", len(lot.slots))
    print("Available   :", free)
    print("Occupied    :", occupied)
    print(f"Revenue     : Rs.{lot.revenue:.2f}\n")
