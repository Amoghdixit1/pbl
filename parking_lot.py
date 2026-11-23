"""Module 2: Parking lot, check-in and check-out."""

import math
from datetime import datetime

from config import (
    ACTIVE_FILE, ALLOWED_SLOTS, COMPACT_PER_FLOOR, EV_PER_FLOOR, FLOORS,
    LARGE_PER_FLOOR, REVENUE_FILE, SLOTS_FILE, TIME_FMT, TRANS_FILE,
)
from slots import CompactSlot, EVChargingSlot, LargeSlot
from file_manager import get_ticket_number, load_records, save_records


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
