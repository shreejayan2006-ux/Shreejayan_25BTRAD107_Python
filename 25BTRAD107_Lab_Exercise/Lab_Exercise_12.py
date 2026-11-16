import json
FILE_NAME = "students.json"
def load_students():
try:
with open(FILE_NAME, "r", encoding="utf-8") as file:
data = json.load(file)
if isinstance(data, list):
return data
print("Invalid data format. Starting with an empty list.")
return []
except FileNotFoundError:
return []
except json.JSONDecodeError:
print("The student file contains invalid JSON.")
return []
def save_students(students):
with open(FILE_NAME, "w", encoding="utf-8") as file:
json.dump(students, file, indent=4)
def find_student(students, usn):
for student in students:
if student["usn"].lower() == usn.lower():
return student
return None
def add_student(students):
usn = input("Enter USN: ").strip()
if not usn:
print("USN cannot be empty.")
return
if find_student(students, usn):
print("A student with this USN already exists.")
return
name = input("Enter name: ").strip()
student_class = input("Enter class: ").strip()
try:
marks = float(input("Enter marks (0-100): "))
if not 0 <= marks <= 100:
print("Marks must be between 0 and 100.")
return
except ValueError:
print("Enter marks as a valid number.")
return
students.append({
"usn": usn, "name": name,
"class": student_class, "marks": marks
})
save_students(students)
print("Student record added successfully.")
def display_students(students):
if not students:
print("No student records found.")
return
for student in students:
print("\\nUSN :", student["usn"])
print("Name :", student["name"])
print("Class :", student["class"])
print("Marks :", student["marks"])
def search_student(students):
usn = input("Enter USN to search: ").strip()
student = find_student(students, usn)
if student:
  print("Record found:", student)
else:
print("Student not found.")
def update_student(students):
usn = input("Enter USN to update: ").strip()
student = find_student(students, usn)
if not student:
print("Student not found.")
return
new_name = input("Enter new name: ").strip()
new_class = input("Enter new class: ").strip()
new_marks_text = input("Enter new marks (0-100): ").strip()
try:
new_marks = float(new_marks_text)
if not 0 <= new_marks <= 100:
print("Marks must be between 0 and 100.")
return
except ValueError:
print("Enter marks as a valid number.")
return
if new_name:
student["name"] = new_name
if new_class:
student["class"] = new_class
student["marks"] = new_marks
save_students(students)
print("Student record updated successfully.")
def main():
students = load_students()
while True:
print("\\nSTUDENT DATA MANAGER")
print("1. Add student")
print("2. Display students")
print("3. Search student")
print("4. Update student")
print("5. Exit")
choice = input("Enter your choice: ").strip()
if choice == "1":
add_student(students)
elif choice == "2":
display_students(students)
elif choice == "3":
search_student(students)
elif choice == "4":
update_student(students)
elif choice == "5":
print("Exiting Student Data Manager.")
break
else:
print("Invalid choice. Select 1 to 5.")
if __name__ == "__main__":
main()
