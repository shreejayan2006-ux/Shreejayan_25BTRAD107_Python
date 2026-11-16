class InsufficientFundsError(Exception):
    pass
class InvalidTransactionError(Exception):
    pass
class BankAccount:
    MIN_BALANCE = 0
    def __init__(self, account_no, holder, opening_balance=0):
        if opening_balance < 0:
            raise InvalidTransactionError("Opening balance cannot be negative.")

        self.__account_no = account_no
        self.__holder = holder
        self.__balance = opening_balance
        self.__history = []
        self.__log("OPEN", opening_balance)
    @property
    def account_no(self):
        return self.__account_no
    @property
    def holder(self):
        return self.__holder
    def __log(self, kind, amount):
        self.__history.append((kind, amount, self.__balance))
    @staticmethod
    def __validate(amount):
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidTransactionError("Amount must be a number.")
        if amount <= 0:
            raise InvalidTransactionError("Amount must be greater than zero.")
    def deposit(self, amount):
        self.__validate(amount)
        self.__balance += amount
        self.__log("DEPOSIT", amount)
        return self.__balance
    def withdraw(self, amount):
        self.__validate(amount)
        if self.__balance - amount < self.MIN_BALANCE:
            raise InsufficientFundsError(
                f"Insufficient balance: available {self.__balance}, requested {amount}."
            )
        self.__balance -= amount
        self.__log("WITHDRAW", amount)
        return self.__balance
    def get_balance(self):
        return self.__balance
    def statement(self):
        print(f"--- Statement: {self.__holder} (A/C {self.__account_no}) ---")
        print(f"{'Type':<10}{'Amount':>10}{'Balance':>12}")
        for kind, amt, bal in self.__history:
            print(f"{kind:<10}{amt:>10}{bal:>12}")
class SavingsAccount(BankAccount):
    def __init__(self, account_no, holder, opening_balance=0, rate=4.0):
        super().__init__(account_no, holder, opening_balance)
        self.rate = rate
    def add_interest(self):
        interest = round(self.get_balance() * self.rate / 100, 2)
        self.deposit(interest)
        return interest
def attempt(label, func, *args):
    try:
        result = func(*args)
        print(f"[PASS] {label} -> balance now {result}")

    except (InvalidTransactionError, InsufficientFundsError) as e:
        print(f"[REJECTED] {label} -> {e}")
if __name__ == "__main__":

    acc = BankAccount("SB1001", "Shreejayan", 5000)

    print("Account created. Opening balance:", acc.get_balance())

    print("\n== Routine transactions ==")
    attempt("Deposit 2000", acc.deposit, 2000)
    attempt("Withdraw 1500", acc.withdraw, 1500)
    attempt("Deposit 500.50", acc.deposit, 500.50)
    attempt("Withdraw 3000", acc.withdraw, 3000)

    print("\n== Invalid transactions ==")
    attempt("Deposit -100", acc.deposit, -100)
    attempt("Deposit 0", acc.deposit, 0)
    attempt("Withdraw 'abc'", acc.withdraw, "abc")
    attempt("Withdraw 50000 (insufficient)", acc.withdraw, 50000)
    attempt("Withdraw exact balance + 1", acc.withdraw, acc.get_balance() + 1)

    print("\n== Encapsulation check ==")

    try:
        print(acc.__balance)
    except AttributeError as e:
        print("Direct access blocked:", e)

    acc.balance = 10**9

    print("Real balance after tampering attempt:", acc.get_balance())

    print("\n== Balance enquiry & statement ==")
    print("Balance enquiry:", acc.get_balance())
    acc.statement()

    print("\n== Inheritance: SavingsAccount ==")

    sav = SavingsAccount("SV2001", "Shreejayan", 10000, rate=4)

    print("Interest credited:", sav.add_interest())
    print("Savings balance:", sav.get_balance())
