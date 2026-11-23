"""Module 1: Slot classes and polymorphism."""


class ParkingSlot:
    def __init__(self, floor, number, slot_type, hourly_rate):
        self.location = (floor, number)
        self.floor = floor
        self.number = number
        self.slot_type = slot_type
        self.hourly_rate = hourly_rate
        self.occupied = False

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
