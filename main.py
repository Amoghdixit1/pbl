"""Parking Management System - entry point.

Run with:  python main.py
"""

from parking_lot import ParkingLot
from analysis import show_report
from visualization import show_charts
from ui import handle_check_in, handle_check_out, show_slots


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
