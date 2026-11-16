def read_log_file(filename):
  counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
total_lines = 0
try:
with open(filename, "r", encoding="utf-8") as file:
for line in file:
total_lines += 1
text = line.upper()
# Check the log level in each line
if "ERROR" in text:
counts["ERROR"] += 1
elif "WARNING" in text:
counts["WARNING"] += 1
elif "INFO" in text:
counts["INFO"] += 1
if total_lines == 0:
print("The log file is empty.")
return
print("\\nLOG FILE SUMMARY")
print("----------------")
print("Total lines :", total_lines)
print("ERROR :", counts["ERROR"])
print("WARNING :", counts["WARNING"])
print("INFO :", counts["INFO"])
except FileNotFoundError:
print("Error: The specified log file was not found.")
except OSError as error:
print("Unable to read the file:", error)
file_name = input("Enter log file name: ")
read_log_file(file_name)
