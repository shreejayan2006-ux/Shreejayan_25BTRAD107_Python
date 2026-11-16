contacts = []
def find_contact(name):
for contact in contacts:
if contact["name"].lower() == name.lower():
return contact
return None
def add_contact():
name = input("Enter name: ").strip()
if not name:
print("Name cannot be empty.")
return
if find_contact(name):
print("A contact with this name already exists.")
return
phone = input("Enter phone number: ").strip()
email = input("Enter email address: ").strip()
contacts.append({
"name": name,
"phone": phone,
"email": email
})
print("Contact added successfully.")
def search_contact():
name = input("Enter name to search: ").strip()
contact = find_contact(name)
if contact:
print("Name:", contact["name"])
print("Phone:", contact["phone"])
print("Email:", contact["email"])
else:
print("Contact not found.")
def update_contact():
name = input("Enter name to update: ").strip()
contact = find_contact(name)
if not contact:
print("Contact not found.")
return
new_phone = input("Enter new phone number: ").strip()
new_email = input("Enter new email: ").strip()
contact["phone"] = new_phone
contact["email"] = new_email
print("Contact updated successfully.")
def delete_contact():
name = input("Enter name to delete: ").strip()
contact = find_contact(name)
if contact:
contacts.remove(contact)
print("Contact deleted successfully.")
else:
print("Contact not found.")
def display_contacts():
if not contacts:
print("The contact book is empty.")
return
for number, contact in enumerate(contacts, start=1):
print(f"{number}. {contact['name']} | "
f"{contact['phone']} | {contact['email']}")
while True:
print("\\n--- CONTACT BOOK ---")
print("1. Add 2. Search 3. Update")
print("4. Delete 5. Display 6. Exit")
choice = input("Enter your choice: ").strip()
if choice == "1":
add_contact()
elif choice == "2":
search_contact()
elif choice == "3":
update_contact()
elif choice == "4":
delete_contact()
elif choice == "5":
display_contacts()
elif choice == "6":
print("Exiting contact book.")
break
else:
print("Invalid choice. Enter a number from 1 to 6.")
