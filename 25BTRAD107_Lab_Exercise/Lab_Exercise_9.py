def calculate_grade(marks):
if marks >= 90:
return "A+"
elif marks >= 80:
return "A"
elif marks >= 70:
return "B"
elif marks >= 60:
return "C"
elif marks >= 50:
 return "D"
else:
return "F"
students = {}
number = int(input("Enter number of students: "))
for i in range(number):
name = input(f"Enter name of student {i + 1}: ").strip()
while True:
try:
marks = float(input(f"Enter marks for {name} (0-100): "))
if 0 <= marks <= 100:
break
print("Marks must be between 0 and 100.")
except ValueError:
print("Please enter a valid numeric mark.")
students[name] = marks
print("\\n--- STUDENT RESULTS ---")
print(f"{'Name':20s} {'Marks':>8s} {'Grade':>8s}")
for name, marks in students.items():
grade = calculate_grade(marks)
print(f"{name:20s} {marks:8.2f} {grade:>8s}")
