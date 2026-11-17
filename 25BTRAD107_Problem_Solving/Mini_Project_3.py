Attendance Tracker
Name : Shreejayan
USN : 25BTRAD107
Class : CSE AIDE-B
Data structure:
attendance = {
"Student Name": ["P", "A", "P", ...] # one entry per class session
}
students = ["Student Name", ...] # list keeps the roll order
"""
VALID_STATUS = ("P", "A")
def add_student(students, attendance, name):
"""Add a new student. Returns True if added, False if already present."""
name = name.strip().title()
if not name:
print(" [!] Name cannot be empty.")
return False
if name in attendance:
print(f" [!] '{name}' already exists.")
return False
students.append(name)
attendance[name] = []
print(f" [+] Student '{name}' added.")
return True
def mark_attendance(attendance, name, status):
"""Append a new session record (P/A) for a student."""
name = name.strip().title()
status = status.strip().upper()
if name not in attendance:
print(f" [!] '{name}' not found.")
return False
if status not in VALID_STATUS:
print(f" [!] Invalid status '{status}'. Use P or A.")
return False
attendance[name].append(status)
return True
def update_attendance(attendance, name, session_no, status):
"""Correct an existing record. session_no starts from 1."""
name = name.strip().title()
status = status.strip().upper()
if name not in attendance:
print(f" [!] '{name}' not found.")
return False
if status not in VALID_STATUS:
print(f" [!] Invalid status '{status}'. Use P or A.")
return False
if not 1 <= session_no <= len(attendance[name]):
print(f" [!] Session {session_no} does not exist for '{name}'.")
return False
old = attendance[name][session_no - 1]
attendance[name][session_no - 1] = status
print(f" [~] {name}: session {session_no} changed {old} -> {status}")
return True
def percentage(records):
"""Attendance percentage for one list of P/A records."""
if not records:
return 0.0
return records.count("P") / len(records) * 100
def display_attendance(students, attendance):
"""Print all records in a table."""
max_sessions = max((len(r) for r in attendance.values()), default=0)
print("\n" + "=" * 72)
print(f"{'Roll':<5}{'Name':<16}{'Sessions':<{max(max_sessions * 3, 10)}}"
f"{'Pres':>5}{'Total':>6}{'%':>8}")
print("-" * 72)
for i, name in enumerate(students, 1):
rec = attendance[name]
sess = " ".join(rec) if rec else "-"
print(f"{i:<5}{name:<16}{sess:<{max(max_sessions * 3, 10)}}"
f"{rec.count('P'):>5}{len(rec):>6}{percentage(rec):>7.1f}%")
print("=" * 72)
def below_threshold(students, attendance, threshold=75.0):
"""Return list of (name, percentage) for students under the threshold."""
return [(n, percentage(attendance[n])) for n in students
if percentage(attendance[n]) < threshold]
def show_defaulters(students, attendance, threshold=75.0):
low = below_threshold(students, attendance, threshold)
print(f"\nStudents below {threshold:.0f}% attendance:")
if not low:
print(" None - everyone meets the requirement.")
for n, p in low:
print(f" - {n:<14} {p:5.1f}% (short by {threshold - p:.1f}%)")
return low
def classes_needed(records, threshold=75.0):
"""How many consecutive presents are needed to reach the threshold."""
present, total = records.count("P"), len(records)
extra = 0
while total + extra and (present + extra) / (total + extra) * 100 < threshold:
extra += 1
if extra > 1000:
break
return extra
def run_scenario(title, setup):
print("\n" + "#" * 72)
print(f"# {title}")
print("#" * 72)
students, attendance = [], {}
setup(students, attendance)
