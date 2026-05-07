from database_orm import engine, Base

from models import Author, Book

Base.metadata.create_all(engine)

print("Tables created successfully")
