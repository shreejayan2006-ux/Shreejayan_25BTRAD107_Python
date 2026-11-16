from datetime import date, timedelta
class Item:
    LOAN_DAYS = 14
    def __init__(self, item_id, title):
        self.item_id = item_id
        self.title = title
        self.available = True
        self.issued_to = None
        self.due_date = None
    def describe(self):
        return f"{self.item_id}: {self.title}"

    def __str__(self):
        status = "Available" if self.available else f"Issued to {self.issued_to} (due {self.due_date})"
        return f"{self.describe():<58} [{status}]"
class Book(Item):
    def __init__(self, item_id, title, author):
        super().__init__(item_id, title)
        self.author = author
    def describe(self):
        return f"{self.item_id}: {self.title} by {self.author}"
class ReferenceBook(Book):
    LOAN_DAYS = 0

    def describe(self):
        return super().describe() + " (Ref)"

class Member:
    MAX_BOOKS = 2

    def __init__(self, member_id, name):
        self.member_id = member_id
        self.name = name
        self.borrowed = []

class Library:
    def __init__(self):
        self.items = {}
        self.members = {}

    def add_item(self, item):
        self.items[item.item_id] = item

    def add_member(self, member):
        self.members[member.member_id] = member

    def issue(self, item_id, member_id, today):
        item = self.items.get(item_id)
        member = self.members.get(member_id)

        if item is None:
            return f"FAILED: book {item_id} does not exist."

        if member is None:
            return f"FAILED: member {member_id} not registered."

        if isinstance(item, ReferenceBook):
            return f"FAILED: '{item.title}' is a reference book and cannot be issued."

        if not item.available:
            return f"FAILED: '{item.title}' is already issued to {item.issued_to}."

        if len(member.borrowed) >= Member.MAX_BOOKS:
            return f"FAILED: {member.name} has reached the limit of {Member.MAX_BOOKS} books."

        item.available = False
        item.issued_to = member.name
        item.due_date = today + timedelta(days=item.LOAN_DAYS)
        member.borrowed.append(item_id)

        return f"ISSUED: '{item.title}' to {member.name}, due {item.due_date}."

    def return_item(self, item_id, today):
        item = self.items.get(item_id)

        if item is None:
            return f"FAILED: book {item_id} does not exist."

        if item.available:
            return f"FAILED: '{item.title}' was not issued."

        fine = max(0, (today - item.due_date).days) * 2

        for m in self.members.values():
            if item_id in m.borrowed:
                m.borrowed.remove(item_id)

        who = item.issued_to
        item.available, item.issued_to, item.due_date = True, None, None

        msg = f"RETURNED: '{item.title}' from {who}."

        return msg + (f" Late fine: Rs. {fine}." if fine else " No fine.")

    def search(self, keyword):
        k = keyword.lower()

        return [
            i for i in self.items.values()
            if k in i.title.lower()
            or (isinstance(i, Book) and k in i.author.lower())
        ]

    def report(self):
        for item in self.items.values():
            print(" ", item)

        avail = sum(1 for i in self.items.values() if i.available)

        print(f" Total: {len(self.items)} Available: {avail} Issued: {len(self.items) - avail}")


if __name__ == "__main__":

    lib = Library()

    for b in [
        Book("B01", "Python Crash Course", "Eric Matthes"),
        Book("B02", "Data Structures in Python", "Narasimha Karumanchi"),
        Book("B03", "Automate the Boring Stuff", "Al Sweigart"),
        ReferenceBook("R01", "Python Reference Manual", "Guido van Rossum")
    ]:
        lib.add_item(b)

    lib.add_member(Member("M01", "Shreejayan"))
    lib.add_member(Member("M02", "Arjun"))

    day0 = date(2026, 11, 2)

    print("== Initial catalogue ==")
    lib.report()

    print("\n== Issue operations ==")
    print(lib.issue("B01", "M01", day0))
    print(lib.issue("B01", "M02", day0))
    print(lib.issue("B02", "M01", day0))
    print(lib.issue("B03", "M01", day0))
    print(lib.issue("R01", "M02", day0))
    print(lib.issue("B99", "M02", day0))
    print(lib.issue("B03", "M09", day0))

    print("\n== Catalogue after issues ==")
    lib.report()

    print("\n== Return operations ==")
    print(lib.return_item("B01", day0 + timedelta(days=10)))
    print(lib.return_item("B02", day0 + timedelta(days=20)))
    print(lib.return_item("B03", day0 + timedelta(days=1)))

    print("\n== Search 'python' ==")
    for i in lib.search("python"):
        print(" ", i.describe())

    print("\n== Final catalogue ==")
    lib.report()
