import json, uuid, os
from datetime import datetime, timedelta

DATA_DIR = "library_data"
os.makedirs(DATA_DIR, exist_ok=True)

BOOKS_FILE = os.path.join(DATA_DIR, "books.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
TRANS_FILE = os.path.join(DATA_DIR, "transactions.json")

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4, default=str)

def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

# ---------- Models ----------
class Book:
    def __init__(self, book_id, title, author, isbn, total_copies, available_copies=None):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.isbn = isbn
        self.total_copies = total_copies
        self.available_copies = available_copies if available_copies is not None else total_copies

    def to_dict(self):
        return vars(self)

class User:
    def __init__(self, user_id, name, email, role, borrowed_books=None):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.role = role
        self.borrowed_books = borrowed_books if borrowed_books else []

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "borrowed_books": self.borrowed_books,
        }

class Transaction:
    def __init__(self, transaction_id, user_id, book_id, borrow_date, due_date, return_date=None, fine=0, status="Borrowed"):
        self.transaction_id = transaction_id
        self.user_id = user_id
        self.book_id = book_id
        self.borrow_date = datetime.fromisoformat(borrow_date) if isinstance(borrow_date, str) else borrow_date
        self.due_date = datetime.fromisoformat(due_date) if isinstance(due_date, str) else due_date
        self.return_date = datetime.fromisoformat(return_date) if isinstance(return_date, str) and return_date else return_date
        self.fine = fine
        self.status = status

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "borrow_date": self.borrow_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "fine": self.fine,
            "status": self.status,
        }

    def mark_returned(self, return_date, fine=0):
        self.return_date = return_date
        self.fine = fine
        self.status = "Returned"

# ---------- Main Library Class ----------
class Library:
    def __init__(self):
        self.books = {}
        self.users = {}
        self.transactions = []
        self.load_all()

    def save_all(self):
        save_json(BOOKS_FILE, [b.to_dict() for b in self.books.values()])
        save_json(USERS_FILE, [u.to_dict() for u in self.users.values()])
        save_json(TRANS_FILE, [t.to_dict() for t in self.transactions])

    def load_all(self):
        for b in load_json(BOOKS_FILE):
            self.books[b["book_id"]] = Book(**b)
        for u in load_json(USERS_FILE):
            self.users[u["user_id"]] = User(**u)
        for t in load_json(TRANS_FILE):
            self.transactions.append(Transaction(**t))

    # ---------- CRUD & Borrow/Return ----------
    def add_book(self, title, author, isbn, total_copies):
        book_id = f"B{len(self.books)+1}"
        self.books[book_id] = Book(book_id, title, author, isbn, total_copies)
        self.save_all()
        return f"✅ Book '{title}' added successfully!"

    def register_user(self, name, email, role):
        user_id = f"U{len(self.users)+1}"
        self.users[user_id] = User(user_id, name, email, role)
        self.save_all()
        return f"✅ {role} '{name}' registered successfully!"

    def borrow_book(self, user_id, book_id):
        if user_id not in self.users or book_id not in self.books:
            return "Invalid user or book ID."

        user = self.users[user_id]
        book = self.books[book_id]
        if book.available_copies <= 0:
            return "❌ No copies available."
        if user.role == "Student" and len(user.borrowed_books) >= 3:
            return "❌ Borrow limit reached (3 books max for students)."

        borrow_date = datetime.now()
        due_days = 14 if user.role == "Student" else 30
        due_date = borrow_date + timedelta(days=due_days)

        transaction = Transaction(str(uuid.uuid4())[:8], user_id, book_id, borrow_date, due_date)
        self.transactions.append(transaction)
        user.borrowed_books.append(book_id)
        book.available_copies -= 1

        self.save_all()
        return f"✅ '{book.title}' borrowed successfully. Due on {due_date.date()}"

    def return_book(self, user_id, book_id):
        if user_id not in self.users or book_id not in self.books:
            return "Invalid user or book ID."

        user = self.users[user_id]
        book = self.books[book_id]

        if book_id not in user.borrowed_books:
            return "❌ This user didn’t borrow this book."

        tr = next((t for t in self.transactions if t.user_id == user_id and t.book_id == book_id and t.status == "Borrowed"), None)
        if not tr:
            return "Transaction not found."

        return_date = datetime.now()
        fine = 0
        if user.role == "Student" and return_date > tr.due_date:
            days_late = (return_date - tr.due_date).days
            fine = days_late * 5

        tr.mark_returned(return_date, fine)
        user.borrowed_books.remove(book_id)
        book.available_copies += 1

        self.save_all()
        if fine > 0:
            return f"⚠️ Returned late! Fine: ₹{fine}"
        return f"✅ '{book.title}' returned successfully."
