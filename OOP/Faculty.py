from OOP.Book import Book
from OOP.User import User


class Faculty:
    def borrow(self, book: Book, user: User):
        if len(user.borrowed_books) >= 5:
            print(f"{user.name} faculty limit has been reached 5")
        if book.is_borrowed:
            user.borrowed_books.append(book)
            print(f"{user.name} faculty borrowed successfully {book.title}")
            book.borrow()
        print(f"{book.title} has been borrowed")
