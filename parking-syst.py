import os
import math
from datetime import datetime

# Configuration
DATA_DIR = "parking_data"
SLOTS_FILE = DATA_DIR + "/slots.txt"
ACTIVE_FILE = DATA_DIR + "/active_sessions.txt"
TRANS_FILE = DATA_DIR + "/transactions.txt"
REVENUE_FILE = DATA_DIR + "/revenue.txt"

TIME_FMT = "%Y-%m-%d %H:%M:%S"
FLOORS = 3

# number of slots of each type on every floor
COMPACT_PER_FLOOR = 6
LARGE_PER_FLOOR = 3
EV_PER_FLOOR = 2

# which slot types each vehicle category can use
ALLOWED_SLOTS = {
    "compact": ["Compact", "Large"],
    "large": ["Large"],
    "ev": ["EV"],
}


# Module 1: Slot classes and polymorphism
class ParkingSlot:
    def __init__(self, floor, number, slot_type, hourly_rate):
        self.location = (floor, number)
        self.floor = floor
        self.number = number
        self.slot_type = slot_type
        self.hourly_rate = hourly_rate
        self.occupied = False

        # slot id looks like F1-C01
        if number < 10:
            self.slot_id = "F" + str(floor) + "-" + slot_type[0] + "0" + str(number)
        else:
            self.slot_id = "F" + str(floor) + "-" + slot_type[0] + str(number)

    def calculate_fee(self, hours):
        return self.hourly_rate * hours

    def __str__(self):
        if self.occupied:
            state = "OCCUPIED"
        else:
            state = "FREE"
        return f"{self.slot_id}\t{self.slot_type}\tRs.{self.hourly_rate}/hr\t{state}"


class CompactSlot(ParkingSlot):
    def __init__(self, floor, number):
        super().__init__(floor, number, "Compact", 20)


class LargeSlot(ParkingSlot):
    def __init__(self, floor, number):
        super().__init__(floor, number, "Large", 40)

    def calculate_fee(self, hours):
        # large vehicles pay at most Rs.400
        fee = self.hourly_rate * hours
        if fee > 400:
            fee = 400
        return fee


class EVChargingSlot(ParkingSlot):
    def __init__(self, floor, number):
        super().__init__(floor, number, "EV", 30)
        self.charging_rate = 25

    def calculate_fee(self, hours):
        # parking charge + charging charge
        return (self.hourly_rate + self.charging_rate) * hours


# Module 3: File management
def save_records(filename, records):
    try:
        if not os.path.exists(DATA_DIR):
            os.mkdir(DATA_DIR)
        file = open(filename, "w")
        for record in records:
            file.write(record + "\n")
        file.close()
    except OSError:
        print("[!] Could not save", filename)


def load_records(filename):
    records = []
    try:
        file = open(filename, "r")
        for line in file:
            line = line.strip()
            if line != "":
                records.append(line)
        file.close()
    except FileNotFoundError:
        # file not created yet, start with empty data
        return []
    except OSError:
        print("[!] Could not read", filename)
        return []
    return records


def get_ticket_number(ticket):
    # "T1005" -> 1005
    return int(ticket[1:])


# Module 2: Parking lot, check-in and check-out
class ParkingLot:
    def __init__(self):
        self.slots = []            # list of all slot objects
        self.active = {}           # ticket -> details of parked vehicle
        self.occupied_ids = set()  # slot ids that are in use
        self.transactions = []     # completed parking records
        self.revenue = 0.0
        self.next_ticket = 1001

        self.create_slots()
        self.load_data()

    def create_slots(self):
        for floor in range(1, FLOORS + 1):
            for number in range(1, COMPACT_PER_FLOOR + 1):
                self.slots.append(CompactSlot(floor, number))
            for number in range(1, LARGE_PER_FLOOR + 1):
                self.slots.append(LargeSlot(floor, number))
            for number in range(1, EV_PER_FLOOR + 1):
                self.slots.append(EVChargingSlot(floor, number))

    def find_slot(self, slot_id):
        for slot in self.slots:
            if slot.slot_id == slot_id:
                return slot
        return None

    def is_parked(self, reg):
        for ticket in self.active:
            if self.active[ticket]["reg"] == reg:
                return True
        return False

    def load_data(self):
        # load vehicles that were still parked when the program closed
        for line in load_records(ACTIVE_FILE):
            try:
                parts = line.split("|")
                ticket = parts[0]
                reg = parts[1]
                category = parts[2]
                slot = self.find_slot(parts[3])
                entry = datetime.strptime(parts[4], TIME_FMT)

                if slot is None or slot.occupied or self.is_parked(reg):
                    print("[!] Skipping invalid active session:", line)
                    continue

                slot.occupied = True
                self.occupied_ids.add(slot.slot_id)
                self.active[ticket] = {
                    "reg": reg,
                    "category": category,
                    "slot": slot,
                    "entry": entry,
                }

                if get_ticket_number(ticket) >= self.next_ticket:
                    self.next_ticket = get_ticket_number(ticket) + 1
            except (ValueError, IndexError):
                print("[!] Skipping invalid active session:", line)

        self.transactions = load_records(TRANS_FILE)

        # don't reuse ticket numbers from old transactions
        for line in self.transactions:
            try:
                ticket = line.split("|")[0]
                if get_ticket_number(ticket) >= self.next_ticket:
                    self.next_ticket = get_ticket_number(ticket) + 1
            except ValueError:
                pass

        records = load_records(REVENUE_FILE)
        if len(records) > 0:
            try:
                self.revenue = float(records[0])
            except ValueError:
                self.revenue = 0.0

        # create the files if they don't exist yet
        self.save_all()

    def save_slots(self):
        records = []
        for slot in self.slots:
            if slot.occupied:
                status = "1"
            else:
                status = "0"
            records.append(slot.slot_id + "|" + slot.slot_type + "|" + status)
        save_records(SLOTS_FILE, records)

    def save_active(self):
        records = []
        for ticket in self.active:
            session = self.active[ticket]
            entry_text = session["entry"].strftime(TIME_FMT)
            line = (ticket + "|" + session["reg"] + "|" + session["category"]
                    + "|" + session["slot"].slot_id + "|" + entry_text)
            records.append(line)
        save_records(ACTIVE_FILE, records)

    def save_all(self):
        self.save_slots()
        self.save_active()
        save_records(TRANS_FILE, self.transactions)
        save_records(REVENUE_FILE, [str(round(self.revenue, 2))])

    def check_in(self, reg, category):
        if category not in ALLOWED_SLOTS:
            raise ValueError("Invalid vehicle category.")

        # find the first free slot this vehicle is allowed to use
        slot = None
        for s in self.slots:
            if s.occupied == False and s.slot_type in ALLOWED_SLOTS[category]:
                slot = s
                break

        if slot is None:
            raise ValueError("No suitable parking slot available.")

        ticket = "T" + str(self.next_ticket)
        entry = datetime.now()

        slot.occupied = True
        self.occupied_ids.add(slot.slot_id)
        self.active[ticket] = {
            "reg": reg,
            "category": category,
            "slot": slot,
            "entry": entry,
        }
        self.next_ticket = self.next_ticket + 1

        self.save_all()
        return ticket, slot, entry

    def check_out(self, ticket):
        if ticket not in self.active:
            raise KeyError("Invalid ticket number or session not found.")

        session = self.active[ticket]
        slot = session["slot"]
        exit_time = datetime.now()

        # every started hour is charged, minimum 1 hour
        seconds = (exit_time - session["entry"]).total_seconds()
        hours = math.ceil(seconds / 3600)
        if hours < 1:
            hours = 1

        fee = slot.calculate_fee(hours)

        record = (ticket + "|" + session["reg"] + "|" + slot.slot_id + "|"
                  + session["entry"].strftime(TIME_FMT) + "|"
                  + exit_time.strftime(TIME_FMT) + "|"
                  + str(hours) + "|" + str(fee))

        slot.occupied = False
        self.occupied_ids.remove(slot.slot_id)
        del self.active[ticket]
        self.transactions.append(record)
        self.revenue = self.revenue + fee

        self.save_all()

        receipt = {
            "ticket": ticket,
            "reg": session["reg"],
            "slot": slot.slot_id,
            "entry": session["entry"],
            "exit": exit_time,
            "hours": hours,
            "fee": fee,
        }
        return receipt


# Module 4: Parking lot analysis
def get_slot_type(slot_id):
    # slot id looks like F1-C01, the letter after "-" tells the type
    letter = slot_id.split("-")[1][0]
    if letter == "C":
        return "Compact"
    elif letter == "L":
        return "Large"
    else:
        return "EV"


def read_transactions(lot):
    records = []
    for line in lot.transactions:
        try:
            parts = line.split("|")
            record = {
                "ticket": parts[0],
                "reg": parts[1],
                "slot_id": parts[2],
                "slot_type": get_slot_type(parts[2]),
                "entry": datetime.strptime(parts[3], TIME_FMT),
                "exit": datetime.strptime(parts[4], TIME_FMT),
                "hours": int(parts[5]),
                "fee": float(parts[6]),
            }
            records.append(record)
        except (ValueError, IndexError):
            print(f"[!] Skipping bad transaction record: {line}")
    return records


def analyse(lot):
    records = read_transactions(lot)

    revenue_by_type = {"Compact": 0.0, "Large": 0.0, "EV": 0.0}
    count_by_type = {"Compact": 0, "Large": 0, "EV": 0}
    entries_by_hour = [0] * 24
    exits_by_hour = [0] * 24
    inside_by_hour = [0] * 24

    total_minutes = 0
    longest_ticket = ""
    longest_minutes = 0

    for r in records:
        minutes = (r["exit"] - r["entry"]).total_seconds() / 60
        total_minutes = total_minutes + minutes

        if minutes > longest_minutes:
            longest_minutes = minutes
            longest_ticket = r["ticket"]

        revenue_by_type[r["slot_type"]] += r["fee"]
        count_by_type[r["slot_type"]] += 1

        entries_by_hour[r["entry"].hour] += 1
        exits_by_hour[r["exit"].hour] += 1

        # count the car in every hour it was parked
        # (only works for cars that left on the same day)
        if r["entry"].date() == r["exit"].date():
            for hour in range(r["entry"].hour, r["exit"].hour + 1):
                inside_by_hour[hour] += 1

    # cars that are still parked also count as entries
    for session in lot.active.values():
        entries_by_hour[session["entry"].hour] += 1

    avg_minutes = 0
    if len(records) > 0:
        avg_minutes = total_minutes / len(records)

    floor_total = {}
    floor_occupied = {}
    for floor in range(1, FLOORS + 1):
        floor_total[floor] = 0
        floor_occupied[floor] = 0
        for slot in lot.slots:
            if slot.floor == floor:
                floor_total[floor] += 1
                if slot.slot_id in lot.occupied_ids:
                    floor_occupied[floor] += 1

    return {
        "total_vehicles": len(records),
        "avg_minutes": avg_minutes,
        "longest_ticket": longest_ticket,
        "longest_minutes": longest_minutes,
        "revenue_by_type": revenue_by_type,
        "count_by_type": count_by_type,
        "entries_by_hour": entries_by_hour,
        "exits_by_hour": exits_by_hour,
        "inside_by_hour": inside_by_hour,
        "floor_total": floor_total,
        "floor_occupied": floor_occupied,
    }


def find_max_hour(counts):
    best = 0
    for hour in range(24):
        if counts[hour] > counts[best]:
            best = hour
    return best


def show_report(lot):
    data = analyse(lot)

    print("\n========== PARKING USAGE REPORT ==========")
    print("Completed sessions :", data["total_vehicles"])
    print("Currently parked   :", len(lot.active))
    print(f"Total revenue      : Rs.{lot.revenue:.2f}")

    if data["total_vehicles"] == 0:
        print("\nNo completed transactions yet.")
        print("==========================================\n")
        return

    avg = int(data["avg_minutes"])
    print(f"Average stay       : {avg // 60} hr {avg % 60} min")
    longest = int(data["longest_minutes"])
    print(f"Longest stay       : {data['longest_ticket']} "
          f"({longest // 60} hr {longest % 60} min)")

    print("\nRevenue by slot type")
    for slot_type in data["revenue_by_type"]:
        count = data["count_by_type"][slot_type]
        amount = data["revenue_by_type"][slot_type]
        print(f"  {slot_type} : {count} vehicles, Rs.{amount:.2f}")

    print("\nCurrent occupancy by floor")
    for floor in data["floor_total"]:
        used = data["floor_occupied"][floor]
        total = data["floor_total"][floor]
        percent = used / total * 100
        print(f"  Floor {floor} : {used}/{total} ({percent:.0f}%)")

    busiest = find_max_hour(data["inside_by_hour"])
    most_entries = find_max_hour(data["entries_by_hour"])
    print(f"\nPeak occupancy hour : {busiest}:00 to {busiest + 1}:00")
    print(f"Most entries at     : {most_entries}:00 to {most_entries + 1}:00")
    print("==========================================\n")


# Module 5: Visualization
def show_charts(lot):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[!] Matplotlib is not installed. Run: pip install matplotlib")
        return

    data = analyse(lot)
    labels = []
    occupied = []
    free = []
    for floor in data["floor_total"]:
        labels.append("Floor " + str(floor))
        occupied.append(data["floor_occupied"][floor])
        free.append(data["floor_total"][floor] - data["floor_occupied"][floor])

    hours = list(range(24))
    entry_x = []
    exit_x = []
    for h in hours:
        entry_x.append(h - 0.2)
        exit_x.append(h + 0.2)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Parking Lot Summary")

    # chart 1 - occupancy by floor
    ax = axes[0]
    ax.bar(labels, occupied, label="Occupied", color="tab:red")
    ax.bar(labels, free, bottom=occupied, label="Free", color="tab:green")
    ax.set_title("Occupancy by floor")
    ax.set_ylabel("Slots")
    ax.legend()

    # chart 2 - entries and exits per hour
    ax = axes[1]
    ax.bar(entry_x, data["entries_by_hour"], 0.4, label="Entries")
    ax.bar(exit_x, data["exits_by_hour"], 0.4, label="Exits")
    ax.set_title("Vehicle entries and exits by hour")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Vehicles")
    ax.set_xticks(range(0, 24, 2))
    ax.legend()

    # chart 3 - revenue by slot type
    ax = axes[2]
    types = list(data["revenue_by_type"].keys())
    amounts = list(data["revenue_by_type"].values())
    ax.bar(types, amounts, color=["tab:blue", "tab:orange", "tab:purple"])
    ax.set_title("Revenue by vehicle type")
    ax.set_ylabel("Revenue (Rs.)")
    for i in range(len(types)):
        ax.text(i, amounts[i], str(int(amounts[i])), ha="center")

    plt.tight_layout()

    chart_file = os.path.join(DATA_DIR, "parking_charts.png")
    try:
        plt.savefig(chart_file)
        print(f"Charts saved to {chart_file}")
    except OSError as e:
        print(f"[!] Could not save chart: {e}")

    plt.show()


# User interface
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


def main():
    lot = ParkingLot()

    menu = """
===== PARKING MANAGEMENT SYSTEM =====
1. Vehicle check-in
2. Vehicle check-out
3. Show slot status
4. Usage report
5. Show charts
6. Exit
"""

    while True:
        print(menu)

        try:
            choice = input("Enter choice: ").strip()

            match choice:
                case "1":
                    handle_check_in(lot)
                case "2":
                    handle_check_out(lot)
                case "3":
                    show_slots(lot)
                case "4":
                    show_report(lot)
                case "5":
                    show_charts(lot)
                case "6":
                    print("Goodbye! All data has been saved.")
                    break
                case _:
                    print("[!] Please enter a number from 1 to 6.")

        except (EOFError, KeyboardInterrupt):
            print("\nExiting. Data is saved.")
            break
        except Exception as e:
            print(f"[!] Unexpected error: {e}")


if __name__ == "__main__":
    main()
