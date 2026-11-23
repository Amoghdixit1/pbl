"""Module 3: File management."""

import os

from config import DATA_DIR


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
