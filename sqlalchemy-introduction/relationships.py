from database_orm import SessionLocal
from models import Book, Author


session = SessionLocal()

# book = session.query(Book).filter(Book.title == "Five Point Someone").first()
# print(book.title, book.author_id, book.author)
# Five Point Someone 2
# print(book.author)

# Five Point Someone 2 Author(id=2, name='Navneet Singh')


# # get the author of the book "The Room on the Roof"
# my_book = session.query(Book).filter(Book.title == "The Room on the Roof").all()
# print(my_book)# [Book(.....)]
# print(my_book.author)

# # my_author = my_book[0].author

# list_of_books = my_book[0].author.books
# print(list_of_books)
# [Book(id=3, title='The Room on the Roof'),
#  Book(id=4, title='The Blue Umbrella')]


## create objects using relationships

# author = Author(name="Jhumpa Lahiri", country="India")
# session.add(author)
# session.commit()

# book = Book(title="The Namesake", author_id=author.id, price=320, pages=291)
# session.add(book)
# session.commit()


# author = Author(name="Dan Brows", country="India")

# book1 = Book(title="Da vinci code", price=320, pages=291)
# book2 = Book(title="Inferno", price=275, pages=198)

# author.books.append(book1)
# author.books.append(book2)

# session.add(author)
# session.commit()

# session.rollback()


# author = Author(name="Vikram Seth", country="India")
# book = Book(title="A Suitable Boy", price=599, pages=1349, author=author)
# session.add(book)

# session.commit()






## Many to many relationships










