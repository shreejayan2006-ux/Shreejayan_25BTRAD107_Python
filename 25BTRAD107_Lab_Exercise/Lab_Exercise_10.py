sentence = input("Enter a sentence: ")
# Convert to lowercase and split into words.
words = sentence.lower().split()
frequency = {}
for word in words:
if word in frequency:
frequency[word] += 1
else:
frequency[word] = 1
print("\\n--- WORD FREQUENCY ---")
if not frequency:
print("No words were entered.")
else:
for word, count in frequency.items():
print(f"{word}: {count}")
