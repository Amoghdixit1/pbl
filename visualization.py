"""Module 5: Visualization."""

import os

from config import DATA_DIR
from analysis import analyse


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
