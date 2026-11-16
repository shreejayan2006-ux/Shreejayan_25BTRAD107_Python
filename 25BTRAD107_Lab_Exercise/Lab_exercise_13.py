import csv
def process_payroll(filename):
employee_count = 0
total_gross = 0.0
total_deductions = 0.0
total_net = 0.0
try:
with open(filename, "r", newline="", encoding="utf-8") as file:
reader = csv.DictReader(file)
required = {
"employee_id", "name", "basic_salary",
"hra", "allowance"
}
if not reader.fieldnames or not required.issubset(
set(reader.fieldnames)
):
print("Error: CSV file is missing required columns.")
return
print("\\nPAYROLL SUMMARY")
print("-" * 72)
for row_number, row in enumerate(reader, start=2):
try:
basic = float(row["basic_salary"])
hra = float(row["hra"])
allowance = float(row["allowance"])
if min(basic, hra, allowance) < 0:
raise ValueError("Salary values cannot be negative.")
gross = basic + hra + allowance
pf = basic * 0.12
tax = gross * 0.05
deductions = pf + tax
net = gross - deductions
print(f"Employee ID : {row['employee_id']}")
print(f"Name : {row['name']}")
print(f"Gross Salary: Rs. {gross:.2f}")
print(f"PF : Rs. {pf:.2f}")
print(f"Tax : Rs. {tax:.2f}")
print(f"Deductions : Rs. {deductions:.2f}")
print(f"Net Salary : Rs. {net:.2f}")
print("-" * 72)
employee_count += 1
total_gross += gross
total_deductions += deductions
total_net += net
except (ValueError, TypeError) as error:
print(f"Skipping row {row_number}: {error}")
print("\\nORGANIZATION PAYROLL TOTAL")
print("Employees processed :", employee_count)
print(f"Total gross salary : Rs. {total_gross:.2f}")
print(f"Total deductions : Rs. {total_deductions:.2f}")
print(f"Total net salary : Rs. {total_net:.2f}")
except FileNotFoundError:
print("Error: employees.csv was not found.")
except OSError as error:
print("Unable to read the CSV file:", error)
process_payroll("employees.csv")
