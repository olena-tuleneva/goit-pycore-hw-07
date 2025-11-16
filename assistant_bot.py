
from collections import UserDict
from datetime import datetime, timedelta, date
import re
import calendar

# -------------------- Декоратор для обробки помилок --------------------
def input_error(func):
    """Декоратор для обробки типових помилок введення."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            msg = str(e)
            if "Invalid date format" in msg:
                return "Invalid date format. Use DD.MM.YYYY."
            elif "exactly 10 digits" in msg:
                return "Invalid phone format. Phone number must contain exactly 10 digits."
            elif "Phone" in msg and "not found" in msg:
                return msg
            elif "already exists" in msg:
                return msg
            return "Give me name and phone/birthday please."
        except IndexError:
            return "Give me name and phone/birthday please."
        except KeyError:
            return "Contact not found."
        except Exception as e:
            return f"An unexpected error occurred: {e}"
    return wrapper

# -------------------- Поля запису --------------------
class Field:
    """Базовий клас для полів запису."""
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    def __str__(self):
        return str(self._value)

class Name(Field):
    """Поле для імені контакту."""
    pass

class Phone(Field):
    """Поле для номера телефону з валідацією формату (10 цифр)."""
    def __init__(self, value):
        validated = self._validate(value)
        super().__init__(validated)

    @staticmethod
    def _validate(phone_number: str):
        if not re.fullmatch(r"\d{10}", phone_number):
            raise ValueError("Phone number must contain exactly 10 digits.")
        return phone_number

    def set_phone(self, new_value):
        self._value = self._validate(new_value)

class Birthday(Field):
    """Поле для дня народження у форматі DD.MM.YYYY."""
    def __init__(self, value: str):
        try:
            super().__init__(datetime.strptime(value, "%d.%m.%Y").date())
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY.")

    def __str__(self):
        return self._value.strftime("%d.%m.%Y")

# -------------------- Запис контакту --------------------
class Record:
    """Запис контакту: ім'я, телефони, день народження."""
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number: str):
        if any(p.value == phone_number for p in self.phones):
            raise ValueError(f"Phone {phone_number} already exists.")
        phone = Phone(phone_number)
        self.phones.append(phone)

    def find_phone(self, phone_number: str):
        return next((p for p in self.phones if p.value == phone_number), None)

    def edit_phone(self, old_phone: str, new_phone: str):
        phone = self.find_phone(old_phone)
        if phone is None:
            raise ValueError(f"Phone '{old_phone}' not found.")
        phone.set_phone(new_phone)

    def remove_phone(self, phone_number: str):
        phone = self.find_phone(phone_number)
        if phone is None:
            raise ValueError(f"Phone '{phone_number}' not found.")
        self.phones.remove(phone)

    def add_birthday(self, birthday: str):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones) if self.phones else "no phones"
        birthday_str = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones}{birthday_str}"

# -------------------- Адресна книга --------------------
class AddressBook(UserDict):
    """Колекція записів як словник."""
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name: str):
        return self.data.get(name)

    def delete(self, name: str):
        if name not in self.data:
            raise KeyError
        del self.data[name]

    def get_upcoming_birthdays(self):
        """Повертає контакти з днями народження на наступний тиждень."""
        today = date.today()
        upcoming_birthdays = {}

        for record in self.data.values():
            if record.birthday:
                bday_this_year = record.birthday.value.replace(year=today.year)
                delta_days = (bday_this_year - today).days

                if delta_days < 0:
                    bday_this_year = bday_this_year.replace(year=today.year + 1)
                    delta_days = (bday_this_year - today).days

                if 0 <= delta_days <= 7:
                    weekday = bday_this_year.weekday()
                    if weekday >= 5:  # Субота або Неділя
                        bday_this_year += timedelta(days=(7 - weekday))

                    day_name = calendar.day_name[bday_this_year.weekday()]
                    upcoming_birthdays.setdefault(day_name, []).append(record.name.value)

        if not upcoming_birthdays:
            return "No upcoming birthdays next week."

        output = []
        for day in calendar.day_name:
            if day in upcoming_birthdays:
                names = ', '.join(sorted(upcoming_birthdays[day]))
                output.append(f"{day}: {names}")

        return "\n".join(output)

# -------------------- Обробники команд --------------------
@input_error
def parse_input(user_input):
    parts = user_input.split()
    if not parts:
        raise ValueError("Empty command")
    return parts[0].lower(), parts[1:]

@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        raise IndexError
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return "Contact updated successfully."

@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    phones = "; ".join(p.value for p in record.phones)
    return f"{record.name.value}'s phones: {phones}"

@input_error
def show_all(args, book: AddressBook):
    if not book:
        return "The address book is empty."
    return "\n".join(str(record) for record in book.data.values())

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.add_birthday(birthday)
    return f"Birthday {birthday} added for contact {name}."

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    if not record.birthday:
        return f"Contact {name} has no birthday record."
    return f"{name}'s birthday: {record.birthday}"

@input_error
def show_upcoming_birthdays(args, book: AddressBook):
    return book.get_upcoming_birthdays()

# -------------------- Головна функція --------------------
def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")

    commands = {
        "hello": lambda args, book: "How can I help you?",
        "add": add_contact,
        "change": change_contact,
        "phone": show_phone,
        "all": show_all,
        "add-birthday": add_birthday,
        "show-birthday": show_birthday,
        "birthdays": show_upcoming_birthdays,
    }

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)
        if command in ["close", "exit"]:
            print("Good bye!")
            break
        if command in commands:
            result = commands[command](args, book)
            print(result)
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()