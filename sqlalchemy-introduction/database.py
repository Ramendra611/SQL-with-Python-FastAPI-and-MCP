import sqlite3

conn = sqlite3.connect("bookstore.db")
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")

# Create tables
conn.execute("""
    CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        country TEXT NOT NULL
    )
""")

conn.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author_id INTEGER NOT NULL,
        price REAL NOT NULL,
        pages INTEGER,
        in_stock INTEGER DEFAULT 1,
        FOREIGN KEY (author_id) REFERENCES authors(id)
    )
""")

conn.commit()


# Insert an author
conn.execute(
    "INSERT INTO authors (name, country) VALUES (?, ?)",
    ("Arundhati Roy", "India")
)
conn.commit()

# Get the author's ID (we need it to insert a book)
author = conn.execute(
    "SELECT id FROM authors WHERE name = ?", ("Arundhati Roy",)
).fetchone()

# Insert a book by that author
conn.execute(
    "INSERT INTO books (title, author_id, price, pages) VALUES (?, ?, ?, ?)",
    ("The God of Small Things", author["id"], 350, 321)
)
conn.commit()


rows = conn.execute("""
    SELECT books.id, books.title, books.price, books.pages,
           authors.name as author_name, authors.country as author_country
    FROM books
    JOIN authors ON books.author_id = authors.id
    ORDER BY books.title
""").fetchall()

for row in rows:
    print(f"{row['title']} by {row['author_name']} -- Rs. {row['price']}")


'''
SELECT books.title, books.price, authors.name,
       AVG(reviews.rating) as avg_rating
FROM books
JOIN authors ON books.author_id = authors.id
JOIN book_genres ON books.id = book_genres.book_id
JOIN genres ON book_genres.genre_id = genres.id
LEFT JOIN reviews ON books.id = reviews.book_id
WHERE genres.name = 'fiction'
  AND authors.country = 'India'
GROUP BY books.id
ORDER BY books.price ASC
'''

'''
book = Book(title="The White Tiger", author_id=3, price=299)
session.add(book)
session.commit()
'''