from collections import UserDict
import re
from datetime import date, datetime, timedelta
import pickle
import os

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)
    
class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not re.match(r'^\d{10}$', value):
            raise ValueError("Phone number must be 10 digits.")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            # Перевіряємо, чи рядок має вірний формат дати
            datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        # Якщо формат дати правильний, перетворюємо рядок у об'єкт datetime
        self.value = datetime.strptime(value, '%d.%m.%Y')

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        phone = Phone(phone_number)
        self.phones.append(phone)

    def remove_phone(self, phone_number):
        self.phones = [phone for phone in self.phones if phone.value != phone_number]

    def edit_phone(self, old_phone_number, new_phone_number):
        old_phone = self.find_phone(old_phone_number)
        if not old_phone:
            raise ValueError(f"Phone number '{old_phone_number}' not found.")
        
        try:
        # Якщо номер не валідний, конструктор Phone кине ValueError
            new_phone = Phone(new_phone_number)
        except ValueError as e:
            raise ValueError(f"New phone number is invalid: {e}")
         # Замінюємо старий номер на новий
        old_phone.value = new_phone.value
    

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def add_birthday(self, birthday):
        if not isinstance(birthday, Birthday):
            raise TypeError("Expected a Birthday object")
        self.birthday = birthday
        

    def show_birthday(self):
        return self.birthday
    
    def __str__(self):
        phones = '; '.join(phone.value for phone in self.phones)
        birthday_str = f", Birthday: {self.birthday.value.strftime('%d.%m.%Y')}" if self.birthday else ""
        return f"{self.name.value}: {phones}{birthday_str}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
    
    def get_upcoming_birthdays(self):
        today = date.today()
        end_date = today + timedelta(days=7)
        upcoming_birthdays = []
        
        for record in self.data.values():
            if record.birthday:
                birthday_date = record.birthday.value.replace(year=today.year).date()
                if today <= birthday_date <= end_date:
                    upcoming_birthdays.append((record.name.value, birthday_date))
                    
        return upcoming_birthdays

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book.data, f)
    print(f"Data saved to {filename}")
    
def load_data(filename="addressbook.pkl"):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            try:
                book = pickle.load(f)
                print(f"Data loaded from {filename}")
                return book
            except (EOFError, pickle.UnpicklingError):
                print(f"Error reading {filename}. Creating a new AddressBook.")
                return AddressBook()
    print(f"No data file found. Creating a new AddressBook.")
    return AddressBook()

def parse_input(user_input):
    if not user_input.strip():
        return None, []
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args,

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Enter user name."
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Enter arguments both name and phone number."

    return inner
@input_error
def add_contact(args, book):
    name, phone = args
    record = Record(name)
    record.add_phone(phone)
    book.add_record(record)
    save_data(book)
    return "Contact added."

@input_error
def change_contact(args, book):
    name, new_phone = args
    record = book.find(name)
    if record is not None:
        record.phones = []
        record.add_phone(new_phone)
        save_data(book)
        return f"Contact {name} updated."
    else:
        return f"Contact {name} not found."
    
@input_error
def show_phone(args, book):
    name = args[0]
    if name in book:
        return book[name]
    else:
        return f"Contact {name} not found."        

@input_error
def show_all_contact(book):
    if not book:
        return "No contacts"
    else:
        return '\n'.join(str(record) for record in book.data.values())

@input_error  
def add_birthday(args, book):
    name = args[0]
    birthday_str = args[1]
    birthday = Birthday(birthday_str)
    record = book.find(name)
    if record is not None:
        record.add_birthday(birthday)
        save_data(book)
        return f"Birthday added for {name}."
    else:
        return f"Contact '{name}' not found."

# Функція обробник для команди show-birthday, яка відображає день народження контакту
@input_error
def show_birthday(args, book):
    name, *_ = args
    record = book.find(name)
    if record:
        birthday = record.show_birthday()
        if birthday:
            return f"{name}'s birthday is on {birthday.value.strftime('%d.%m.%Y')}."
        else:
            return f"{name} does not have a birthday recorded."
    return f"Contact '{name}' not found."

# Функція обробник для команди birthdays, яка повертає список користувачів, яких потрібно привітати по днях на наступному тижні
@input_error
def birthdays(book):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if upcoming_birthdays:
        return "Upcoming birthdays:\n" + "\n".join([f"{name}: {birthday.strftime('%d.%m.%Y')}" for name, birthday in upcoming_birthdays])
    return "No upcoming birthdays."

def main(): 
    book = load_data()
    if isinstance(book, dict):
        book = AddressBook(book)
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command is None:
            continue

        if command in ["close", "exit"]:
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "all":
            print(show_all_contact(book))
        elif command == "add":
            print(add_contact(args, book))
        elif command == 'add_birthday':
            print(add_birthday(args, book))
        elif command == "show_birthday":
            print(show_birthday(args, book))
        elif command == 'birthdays':
            print(birthdays(book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        else:
            print("Invalid command.")
            
if __name__ == "__main__":
    main()