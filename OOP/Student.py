from User import User
from Book import Book

class Student(User):
    def borrow(self, book: Book):
        if len(self.borrowed_books) >= 3:
            print("Student limit has reached book limit.")
            return
        if book.is_borrowed:
            self.borrowed_books.append(book)
            print(f"Student {self.id}, {self.name} has borrowed book {book.title} successfully.")
            book.unborrow()
        print("Book borrowed")




