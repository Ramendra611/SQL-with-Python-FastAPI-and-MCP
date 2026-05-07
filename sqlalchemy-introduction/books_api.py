# main.py -- Bookstore API with SQLAlchemy

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import Author, Book, Genre

app = FastAPI(title="Bookstore API")

# Create tables on startup
Base.metadata.create_all(engine)


# ──────────────────────────────────────────────
# Author endpoints
# ──────────────────────────────────────────────

@app.post("/authors", status_code=201)
def create_author(name: str, country: str, bio: str = None,
                  db: Session = Depends(get_db)):
    """
    Create a new author.

    db: Session = Depends(get_db) is FastAPI's dependency injection.
    FastAPI calls get_db(), gets the session, and passes it as 'db'.
    When this function returns, get_db()'s finally block closes the session.
    """
    author = Author(name=name, country=country, bio=bio)

    db.add(author)
    db.commit()

    # After commit, the author object has its database-generated ID
    db.refresh(author)     # Reload the object from the database to get
    # the latest state (including the auto-generated id)

    return {"id": author.id, "name": author.name, "country": author.country}


@app.get("/authors")
def list_authors(db: Session = Depends(get_db)):
    """Get all authors."""
    authors = db.query(Author).order_by(Author.name).all()

    # Convert each author to a dictionary.
    # We include the count of their books using the relationship.
    return [
        {
            "id": a.id,
            "name": a.name,
            "country": a.country,
            "book_count": len(a.books)   # Relationship in action!
        }
        for a in authors
    ]


@app.get("/authors/{author_id}")
def get_author(author_id: int, db: Session = Depends(get_db)):
    """Get a single author with all their books."""
    author = db.query(Author).get(author_id)

    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    return {
        "id": author.id,
        "name": author.name,
        "country": author.country,
        "bio": author.bio,
        # author.books is the relationship -- SQLAlchemy fetches
        # all books by this author automatically
        "books": [
            {"id": b.id, "title": b.title, "price": b.price}
            for b in author.books
        ]
    }


# ──────────────────────────────────────────────
# Book endpoints
# ──────────────────────────────────────────────

@app.post("/books", status_code=201)
def create_book(title: str, author_id: int, price: float,
                pages: int = None, db: Session = Depends(get_db)):
    """Create a new book."""
    # Verify the author exists
    author = db.query(Author).get(author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    book = Book(title=title, author_id=author_id, price=price, pages=pages)
    db.add(book)
    db.commit()
    db.refresh(book)

    return {
        "id": book.id,
        "title": book.title,
        "author": book.author.name,    # Relationship!
        "price": book.price
    }


@app.get("/books")
def list_books(min_price: float = None, max_price: float = None,
               author_id: int = None, db: Session = Depends(get_db)):
    """
    Get books with optional filters.

    Look at how clean the filtering is compared to building SQL strings
    with sqlite3. We start with a base query and add filters conditionally.
    """
    # Start with the base query
    query = db.query(Book)

    # Add filters conditionally -- each .filter() adds a WHERE clause
    if min_price is not None:
        query = query.filter(Book.price >= min_price)
    if max_price is not None:
        query = query.filter(Book.price <= max_price)
    if author_id is not None:
        query = query.filter(Book.author_id == author_id)

    books = query.order_by(Book.price.asc()).all()

    return [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author.name,    # No JOIN needed in our code
            "price": b.price,
            "pages": b.pages,
            "in_stock": bool(b.in_stock)
        }
        for b in books
    ]


@app.put("/books/{book_id}")
def update_book(book_id: int, title: str = None, price: float = None,
                in_stock: bool = None, db: Session = Depends(get_db)):
    """
    Update a book. Only updates the fields that are provided.
    """
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Update only the fields that were provided.
    # This is much cleaner than building a dynamic UPDATE SQL string.
    if title is not None:
        book.title = title
    if price is not None:
        book.price = price
    if in_stock is not None:
        book.in_stock = 1 if in_stock else 0

    db.commit()
    db.refresh(book)

    return {"id": book.id, "title": book.title, "price": book.price}


@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Delete a book."""
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(book)
    db.commit()

    return {"message": f"'{book.title}' deleted"}
