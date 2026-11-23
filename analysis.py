"""Module 4: Parking lot analysis."""

from datetime import datetime

from config import FLOORS, TIME_FMT


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
