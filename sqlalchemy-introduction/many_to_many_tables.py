from database_orm import SessionLocal
from models import Author, Book, Genre

session = SessionLocal()

# fiction = Genre(name="Fiction")
# historical = Genre(name="Historical")
# mythology = Genre(name="Mythology")
# session.add_all([fiction, historical, mythology])
# session.commit()


# # assign genres to books
# book = session.query(Book).filter(
#     Book.title == "The Immortals of Meluha").first()

# book.genres.append(session.query(Genre).filter(Genre.id == 1).first())
# book.genres.append(session.query(Genre).filter(Genre.id == 3).first())
# session.commit()

# print(book.title , book.genres)
# The Immortals of Meluha[Genre(name='Fiction'), Genre(name='Mythology')]




### check book.genres and genres.books

my_book = session.query(Book).filter(Book.id == 5).first()
print(my_book.title, my_book.genres)

# The Immortals of Meluha. [Genre(name='Fiction'), Genre(name='Mythology')]

print(my_book.genres[0].books)
# [Book(id=5, title='The Immortals of Meluha')]


