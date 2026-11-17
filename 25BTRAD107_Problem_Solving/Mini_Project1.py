def unit_converter():
print("=" * 45) print(" UNIT
CONVERTER") print("=" * 45)
print("1. Kilometres to Miles")
print("2. Miles to Kilometres")
print("3. Metres to Feet")
print("4. Feet to Metres")
print("5. Celsius to
Fahrenheit") print("6.
Fahrenheit to Celsius")
print("=" * 45)
choice = int(input("Enter your choice (1-6): "))
value = float(input("Enter the value: "))
if choice == 1:
result = value * 0.621371
print(f"{value} km = {result:.2f}
miles")
elif choice == 2:
result = value * 1.60934
print(f"{value} miles = {result:.2f} km")
elif choice == 3:
result = value * 3.28084 print(f"{value}
metres = {result:.2f} feet")
elif choice == 4:
result = value * 0.3048 print(f"{value}
feet = {result:.2f} metres")
elif choice == 5:
result = (value * 9/5) + 32
print(f"{value} C = {result:.2f} F")
elif choice == 6:
result = (value - 32) * 5/9
print(f"{value} F = {result:.2f} C")
else: print("Invalid choice! Please select 1
to 6.")
unit_converter()
