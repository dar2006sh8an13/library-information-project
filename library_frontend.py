import tkinter as tk
from tkinter import messagebox, simpledialog
from library_backend import Library

class LibraryApp:
    def __init__(self, root):
        self.lib = Library()
        self.root = root
        self.root.title("📚 Library Management System (Frontend)")
        self.root.geometry("950x600")
        self.root.config(bg="#f4f6fb")

        # Buttons
        top = tk.Frame(root, bg="#f4f6fb")
        top.pack(fill="x", pady=5)

        tk.Button(top, text="Add Book", width=14, command=self.add_book_gui).pack(side="left", padx=5)
        tk.Button(top, text="Register User", width=14, command=self.register_user_gui).pack(side="left", padx=5)
        tk.Button(top, text="Borrow Book", width=14, command=self.borrow_book_popup).pack(side="left", padx=5)
        tk.Button(top, text="Return Book", width=14, command=self.return_book_popup).pack(side="left", padx=5)
        tk.Button(top, text="View Transactions", width=16, command=self.view_transactions_gui).pack(side="left", padx=5)
        tk.Button(top, text="Refresh Lists", width=14, command=self.refresh_lists).pack(side="right", padx=5)

        # Lists
        main = tk.Frame(root, bg="#f4f6fb")
        main.pack(fill="both", expand=True, padx=10, pady=5)

        left = tk.LabelFrame(main, text="Books", padx=5, pady=5)
        left.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.book_list = tk.Listbox(left, width=50, height=20)
        self.book_list.pack(side="left", fill="both", expand=True)
        scroll1 = tk.Scrollbar(left, command=self.book_list.yview)
        scroll1.pack(side="right", fill="y")
        self.book_list.config(yscrollcommand=scroll1.set)

        right = tk.LabelFrame(main, text="Users", padx=5, pady=5)
        right.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.user_list = tk.Listbox(right, width=50, height=20)
        self.user_list.pack(side="left", fill="both", expand=True)
        scroll2 = tk.Scrollbar(right, command=self.user_list.yview)
        scroll2.pack(side="right", fill="y")
        self.user_list.config(yscrollcommand=scroll2.set)

        # Output box
        bottom = tk.LabelFrame(root, text="Output / Transactions", padx=5, pady=5)
        bottom.pack(fill="both", expand=False, padx=10, pady=5)
        self.output = tk.Text(bottom, height=8)
        self.output.pack(fill="both", expand=True)

        self.refresh_lists()

    def show_output(self, text):
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, text)

    def refresh_lists(self):
        self.book_list.delete(0, tk.END)
        for b in self.lib.books.values():
            self.book_list.insert(tk.END, f"{b.book_id} | {b.title} — {b.author} | Available: {b.available_copies}/{b.total_copies}")
        self.user_list.delete(0, tk.END)
        for u in self.lib.users.values():
            self.user_list.insert(tk.END, f"{u.user_id} | {u.name} ({u.role})")
        self.show_output("✅ Data loaded from disk.\n")

    def get_selected_user_id(self):
        sel = self.user_list.curselection()
        if not sel: return None
        return self.user_list.get(sel[0]).split("|")[0].strip()

    # ---- GUI Actions ----
    def add_book_gui(self):
        title = simpledialog.askstring("Add Book", "Book Title:")
        author = simpledialog.askstring("Add Book", "Author Name:")
        isbn = simpledialog.askstring("Add Book", "ISBN:")
        total = simpledialog.askinteger("Add Book", "Total Copies:", minvalue=1)
        if not title or not author or not isbn or not total:
            messagebox.showerror("Error", "All fields required.")
            return
        msg = self.lib.add_book(title, author, isbn, total)
        messagebox.showinfo("Add Book", msg)
        self.refresh_lists()

    def register_user_gui(self):
        name = simpledialog.askstring("Register User", "Name:")
        email = simpledialog.askstring("Register User", "Email:")
        role = simpledialog.askstring("Register User", "Role (Student/Faculty):")
        if not name or not email or not role:
            messagebox.showerror("Error", "All fields required.")
            return
        msg = self.lib.register_user(name, email, role.title())
        messagebox.showinfo("Register User", msg)
        self.refresh_lists()

    def borrow_book_popup(self):
        uid = self.get_selected_user_id()
        if not uid:
            messagebox.showerror("Error", "Select a user first.")
            return
        popup = tk.Toplevel(self.root)
        popup.title("Select Book to Borrow")
        popup.geometry("400x300")
        tk.Label(popup, text=f"Borrow for: {self.lib.users[uid].name}", font=("Arial", 12, "bold")).pack(pady=5)
        book_list = tk.Listbox(popup, width=50, height=10)
        book_list.pack(pady=10)
        for b in self.lib.books.values():
            if b.available_copies > 0:
                book_list.insert(tk.END, f"{b.book_id} | {b.title} — {b.author}")
        def confirm():
            sel = book_list.curselection()
            if not sel: return messagebox.showerror("Error", "Select a book.")
            bid = book_list.get(sel[0]).split("|")[0].strip()
            msg = self.lib.borrow_book(uid, bid)
            messagebox.showinfo("Borrow", msg)
            popup.destroy()
            self.refresh_lists()
            self.view_transactions_gui()
        tk.Button(popup, text="Confirm Borrow", bg="#007bff", fg="white", command=confirm).pack(pady=10)

    def return_book_popup(self):
        uid = self.get_selected_user_id()
        if not uid:
            messagebox.showerror("Error", "Select a user first.")
            return
        user = self.lib.users[uid]
        if not user.borrowed_books:
            return messagebox.showinfo("Return", "No borrowed books.")
        popup = tk.Toplevel(self.root)
        popup.title("Select Book to Return")
        popup.geometry("400x300")
        tk.Label(popup, text=f"Return for: {user.name}", font=("Arial", 12, "bold")).pack(pady=5)
        book_list = tk.Listbox(popup, width=50, height=10)
        book_list.pack(pady=10)
        for bid in user.borrowed_books:
            b = self.lib.books[bid]
            book_list.insert(tk.END, f"{b.book_id} | {b.title}")
        def confirm():
            sel = book_list.curselection()
            if not sel: return messagebox.showerror("Error", "Select a book.")
            bid = book_list.get(sel[0]).split("|")[0].strip()
            msg = self.lib.return_book(uid, bid)
            messagebox.showinfo("Return", msg)
            popup.destroy()
            self.refresh_lists()
            self.view_transactions_gui()
        tk.Button(popup, text="Confirm Return", bg="#28a745", fg="white", command=confirm).pack(pady=10)

    def view_transactions_gui(self):
        lines = []
        for t in self.lib.transactions:
            borrow = t.borrow_date.strftime("%Y-%m-%d")
            due = t.due_date.strftime("%Y-%m-%d")
            ret = t.return_date.strftime("%Y-%m-%d") if t.return_date else "-"
            lines.append(f"{t.transaction_id} | User: {t.user_id} | Book: {t.book_id} | {t.status} | Borrow: {borrow} | Due: {due} | Returned: {ret} | Fine: ₹{t.fine}")
        self.show_output("\n".join(lines) if lines else "No transactions yet.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()
