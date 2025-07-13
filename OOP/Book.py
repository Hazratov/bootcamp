class Book:
    def __init__(self, id, title, author, is_borrowed: bool):
        self.id = id
        self.title = title
        self.author = author
        self.is_borrowed = is_borrowed

    def borrow(self):
        self.is_borrowed = True

    def unborrow(self):
        self.is_borrowed = False