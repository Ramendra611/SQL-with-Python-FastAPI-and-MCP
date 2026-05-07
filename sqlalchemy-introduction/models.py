from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Table
from database_orm import Base
from sqlalchemy.orm import Relationship

class Author(Base):
    """
    This class represents the 'authors' table in the database.

    __tablename__ tells SQLAlchemy what to name the table.
    Each Column() defines a column: its type, constraints, and defaults.

    When you create an Author object, you are creating a row.
    When you query Author objects, you are reading rows.
    """

    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    bio = Column(Text)

    ## create a relationship ( author.books )
    books = Relationship("Book", back_populates="author")

    def __repr__(self):
        """
        __repr__ defines how the object is printed.
        Without this, printing an Author shows something like
        <models.Author object at 0x7f...>, which is useless.
        With this, it shows Author(id=1, name='Arundhati Roy').
        """
        return f"Author(id={self.id}, name='{self.name}')"


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)

    price = Column(Float, nullable=False)
    pages = Column(Integer)

    in_stock = Column(Integer, default=1)

    ## create a relationship such that can use attribte book.author
    author = Relationship("Author", back_populates="books")
    genres = Relationship("Genre", secondary ="book_genres", back_populates="books")

    def __repr__(self):
        return f"Book(id={self.id}, title='{self.title}')"


## junction table or association table
book_genres = Table( "book_genres", Base.metadata, 
                     Column("book_id", Integer, ForeignKey(
                         "books.id"), primary_key=True),
                     Column("genre_id", Integer, ForeignKey("genres.id"), primary_key=True), )


class Genre(Base):
    """A genre like fiction, thriller, historical, etc."""
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    # Many-to-many relationship through the book_genres junction table.
    # The 'secondary' parameter tells SQLAlchemy which table links them.
    books = Relationship("Book", 
                         secondary=book_genres, # go through the junction
                         back_populates="genres")

    def __repr__(self):
        return f"Genre(name='{self.name}')"





'''
# Raw sqlite3 (what you wrote before):
conn.execute("""
    CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        country TEXT NOT NULL,
        bio TEXT
    )
""")


'''