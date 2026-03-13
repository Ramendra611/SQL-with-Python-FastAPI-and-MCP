# SQL Lecture 01 — Introduction to SQL & Databases
> **PostgreSQL** | Beginner Reference Sheet | Use this during class 🐘

---

## Table of Contents

1. [What is a Database?](#1-what-is-a-database)
2. [Types of Databases](#2-types-of-databases)
3. [What is SQL?](#3-what-is-sql)
4. [How SQL Commands Are Grouped](#4-how-sql-commands-are-grouped)
5. [Creating a Table — Full Breakdown](#5-creating-a-table--full-breakdown)
6. [Data Types in PostgreSQL](#6-data-types-in-postgresql)
7. [Constraints — Rules for Your Data](#7-constraints--rules-for-your-data)
8. [Primary Key & Foreign Key](#8-primary-key--foreign-key)
9. [Common SQL Commands with Examples](#9-common-sql-commands-with-examples)
10. [What Happens When You Violate a Constraint?](#10-what-happens-when-you-violate-a-constraint)
11. [Practice Table & 10 Beginner Questions](#11-practice-table--10-beginner-questions)

---

## 1. What is a Database?

A **database** is an organised collection of data stored so it can be easily accessed, managed, and updated.

Think of it like this:

```
Real World Analogy:
┌─────────────────────────────────────────────────┐
│  A school keeps student records                 │
│  → Filing cabinet   =  Database                 │
│  → Each drawer      =  Table                    │
│  → Each folder      =  Row (one student)        │
│  → Labels on folder =  Columns (name, age, etc) │
└─────────────────────────────────────────────────┘
```

**Why not just use Excel?**

| Excel | Database |
|-------|----------|
| Good for small data | Built for millions of rows |
| One user at a time | Many users simultaneously |
| No rules enforced | Strict rules (constraints) |
| Easy to corrupt | Transactional, safe |
| No relationships | Tables linked together |

---

## 2. Types of Databases

### Relational Databases (SQL)
Data is stored in **tables** with rows and columns. Tables can be **related** to each other.

```
Examples: PostgreSQL, MySQL, SQLite, SQL Server, Oracle
Use when: Structured data, relationships matter, consistency is critical
```

### Non-Relational Databases (NoSQL)
Data is stored in other formats — documents, key-value pairs, graphs, etc.

```
Examples: MongoDB (documents), Redis (key-value), Neo4j (graph)
Use when: Unstructured data, high speed, flexible schema
```

### For this course → We use **PostgreSQL**, a powerful open-source relational database.

---

## 3. What is SQL?

**SQL = Structured Query Language** (pronounced "sequel" or "S-Q-L")

SQL is the language you use to **talk to a relational database**. You use it to:
- Create tables and structure
- Insert, update, delete data
- Ask questions of your data (queries)
- Control who can access what

```sql
-- This is a SQL query. It asks: "Show me all students."
SELECT * FROM students;
```

The `--` means it's a **comment** — ignored by the database, just for humans reading the code.

---

## 4. How SQL Commands Are Grouped

SQL commands are organised into 5 categories:

```
┌─────────────────────────────────────────────────────────────────┐
│                     SQL COMMAND GROUPS                          │
├──────────┬──────────────────────────────┬───────────────────────┤
│ Category │ Full Name                    │ Commands              │
├──────────┼──────────────────────────────┼───────────────────────┤
│ DDL      │ Data Definition Language     │ CREATE, ALTER, DROP,  │
│          │ (structure of the database)  │ TRUNCATE, RENAME      │
├──────────┼──────────────────────────────┼───────────────────────┤
│ DML      │ Data Manipulation Language   │ INSERT, UPDATE,       │
│          │ (the actual data)            │ DELETE, MERGE         │
├──────────┼──────────────────────────────┼───────────────────────┤
│ DQL      │ Data Query Language          │ SELECT                │
│          │ (reading/fetching data)      │                       │
├──────────┼──────────────────────────────┼───────────────────────┤
│ DCL      │ Data Control Language        │ GRANT, REVOKE         │
│          │ (permissions & access)       │                       │
├──────────┼──────────────────────────────┼───────────────────────┤
│ TCL      │ Transaction Control Language │ BEGIN, COMMIT,        │
│          │ (grouping operations safely) │ ROLLBACK, SAVEPOINT   │
└──────────┴──────────────────────────────┴───────────────────────┘
```

> **For beginners:** Focus on DDL + DML + DQL — that's 90% of what you'll write day to day.

---

## 5. Creating a Table — Full Breakdown

### Basic Syntax

```sql
CREATE TABLE table_name (
    column_name  data_type  constraints,
    column_name  data_type  constraints,
    ...
);
```

### Real Example — Step by Step

```sql
CREATE TABLE students (
    student_id   SERIAL        PRIMARY KEY,
    first_name   VARCHAR(50)   NOT NULL,
    last_name    VARCHAR(50)   NOT NULL,
    email        VARCHAR(100)  UNIQUE NOT NULL,
    age          INT           CHECK (age >= 5 AND age <= 100),
    enrolled_on  DATE          DEFAULT CURRENT_DATE,
    grade        CHAR(1)       CHECK (grade IN ('A','B','C','D','F')),
    is_active    BOOLEAN       DEFAULT TRUE
);
```

Let's break down each part:

```
┌────────────────┬──────────────┬────────────────────────────────┐
│ Part           │ Example      │ What it means                  │
├────────────────┼──────────────┼────────────────────────────────┤
│ Column name    │ student_id   │ Name of the column             │
│ Data type      │ SERIAL       │ What kind of data it holds     │
│ Constraint     │ PRIMARY KEY  │ Rule that applies to the data  │
│ Default value  │ DEFAULT TRUE │ Value used if none given       │
└────────────────┴──────────────┴────────────────────────────────┘
```

---

## 6. Data Types in PostgreSQL

### Most Commonly Used

```
┌──────────────┬────────────────────────────────────────────────────┐
│ Data Type    │ Description & Example                              │
├──────────────┼────────────────────────────────────────────────────┤
│ INT          │ Whole numbers: 1, 42, -7                           │
│ BIGINT       │ Very large whole numbers                           │
│ SERIAL       │ Auto-incrementing integer (1, 2, 3…) — use for IDs │
│ NUMERIC(p,s) │ Exact decimal: NUMERIC(10,2) → 99999999.99         │
│ FLOAT        │ Approximate decimal (for science, not money)       │
│ VARCHAR(n)   │ Text up to n characters: VARCHAR(50)               │
│ TEXT         │ Unlimited length text                              │
│ CHAR(n)      │ Fixed-length text — always exactly n chars         │
│ BOOLEAN      │ TRUE or FALSE                                      │
│ DATE         │ Date only: '2024-01-15'                            │
│ TIMESTAMP    │ Date + time: '2024-01-15 09:30:00'                 │
│ TIME         │ Time only: '14:30:00'                              │
└──────────────┴────────────────────────────────────────────────────┘
```

### Choosing the Right Type

```sql
-- ✅ Good choices
salary       NUMERIC(12, 2)   -- money: exact, 2 decimal places
phone        VARCHAR(20)      -- phone numbers vary in length
is_member    BOOLEAN          -- yes/no flag
birth_date   DATE             -- just a date, no time needed
created_at   TIMESTAMP        -- when a record was created

-- ❌ Common mistakes
salary       FLOAT            -- BAD: floating point rounds money!
age          VARCHAR(10)      -- BAD: age is a number, not text
```

---

## 7. Constraints — Rules for Your Data

Constraints are **rules enforced by the database**. If you try to break them, the database **refuses** and gives an error.

### Overview of All Constraints

```
┌─────────────────┬───────────────────────────────────────────────────────┐
│ Constraint      │ What it does                                          │
├─────────────────┼───────────────────────────────────────────────────────┤
│ PRIMARY KEY     │ Uniquely identifies each row. Cannot be NULL.         │
│ NOT NULL        │ This column must always have a value.                 │
│ UNIQUE          │ No two rows can have the same value in this column.   │
│ CHECK           │ Value must pass a custom condition.                   │
│ DEFAULT         │ Uses a fallback value if none is provided.            │
│ FOREIGN KEY     │ Links to a PRIMARY KEY in another table.              │
└─────────────────┴───────────────────────────────────────────────────────┘
```

### Examples of Each

```sql
CREATE TABLE employees (
    -- PRIMARY KEY: every employee needs a unique ID
    emp_id      SERIAL        PRIMARY KEY,

    -- NOT NULL: name is required, cannot be left empty
    full_name   VARCHAR(100)  NOT NULL,

    -- UNIQUE: no two employees can share the same email
    email       VARCHAR(100)  UNIQUE,

    -- CHECK: salary must be a positive number
    salary      NUMERIC(10,2) CHECK (salary > 0),

    -- DEFAULT: if no join date is given, use today's date
    joined_on   DATE          DEFAULT CURRENT_DATE,

    -- FOREIGN KEY: dept_id must exist in the departments table
    dept_id     INT           REFERENCES departments(dept_id)
);
```

---

## 8. Primary Key & Foreign Key

### Primary Key

A **Primary Key** is the unique identifier for each row in a table. Think of it like a fingerprint — no two rows can have the same primary key, and it can never be NULL.

```sql
-- When you use SERIAL PRIMARY KEY:
-- PostgreSQL automatically generates 1, 2, 3, 4...
-- You never have to provide it manually

CREATE TABLE customers (
    customer_id  SERIAL  PRIMARY KEY,   -- auto-generated: 1, 2, 3...
    name         VARCHAR(100) NOT NULL
);

INSERT INTO customers (name) VALUES ('Alice');   -- customer_id = 1
INSERT INTO customers (name) VALUES ('Bob');     -- customer_id = 2
INSERT INTO customers (name) VALUES ('Charlie'); -- customer_id = 3
```

### Foreign Key

A **Foreign Key** is a column in one table that **refers to the Primary Key of another table**. It creates a link (relationship) between two tables.

```sql
-- Table 1: departments (the "parent" table)
CREATE TABLE departments (
    dept_id    SERIAL       PRIMARY KEY,
    dept_name  VARCHAR(100) NOT NULL
);

-- Table 2: employees (the "child" table)
CREATE TABLE employees (
    emp_id   SERIAL       PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    dept_id  INT          REFERENCES departments(dept_id)
    --                    ↑ This is the FOREIGN KEY
    --                      It MUST match a dept_id that exists in departments
);
```

### How They Work Together

```
departments table               employees table
┌─────────┬──────────────┐     ┌────────┬────────┬─────────┐
│ dept_id │ dept_name    │     │ emp_id │ name   │ dept_id │
├─────────┼──────────────┤     ├────────┼────────┼─────────┤
│    1    │ Engineering  │◄────│   1   │ Alice  │    1    │
│    2    │ Marketing    │◄────│   2   │ Bob    │    2    │
│    3    │ HR           │     │   3   │ Carol  │    1    │
└─────────┴──────────────┘     └────────┴────────┴─────────┘
                                              ↑
                            Alice and Carol both work in Engineering (dept_id=1)
                            Bob works in Marketing (dept_id=2)
```

**The rule:** You cannot put a `dept_id` in the employees table that doesn't exist in the departments table. If you try, the database will refuse.

---

## 9. Common SQL Commands with Examples

We'll use this simple table for all examples:

```sql
CREATE TABLE products (
    product_id   SERIAL        PRIMARY KEY,
    name         VARCHAR(100)  NOT NULL,
    category     VARCHAR(50),
    price        NUMERIC(8,2)  CHECK (price >= 0),
    stock        INT           DEFAULT 0,
    is_available BOOLEAN       DEFAULT TRUE
);
```

---

### CREATE — Make a new table or database

```sql
-- Create a database
CREATE DATABASE school;

-- Create a table (already shown above)
CREATE TABLE products ( ... );
```

> **Think of it as:** Building the empty filing cabinet drawer before you put any files in it.

---

### INSERT — Add new rows of data

```sql
-- Insert one row
INSERT INTO products (name, category, price, stock)
VALUES ('Apple MacBook Pro', 'Laptops', 1999.99, 15);

-- Insert multiple rows at once
INSERT INTO products (name, category, price, stock)
VALUES
    ('Samsung TV 55"',    'Electronics', 799.99,  30),
    ('Nike Running Shoes','Clothing',    129.99,  50),
    ('Python Cookbook',   'Books',        49.99, 100),
    ('USB-C Cable',       'Accessories',   9.99, 200);
```

> **Note:** You don't provide `product_id` — `SERIAL` generates it automatically.
> **Note:** You don't provide `is_available` — it uses the `DEFAULT TRUE`.

---

### SELECT — Read / query data

```sql
-- Get all columns, all rows
SELECT * FROM products;

-- Get specific columns only
SELECT name, price FROM products;

-- Filter rows with WHERE
SELECT name, price FROM products
WHERE category = 'Electronics';

-- Sort results
SELECT name, price FROM products
ORDER BY price DESC;   -- DESC = highest first, ASC = lowest first

-- Limit how many rows you get back
SELECT name, price FROM products
ORDER BY price DESC
LIMIT 3;

-- Filter with multiple conditions
SELECT name, price FROM products
WHERE category = 'Laptops' AND price < 2000;
```

> **SELECT never changes your data.** It is always safe to run.

---

### UPDATE — Modify existing rows

```sql
-- Update one column for one specific row
UPDATE products
SET price = 1899.99
WHERE product_id = 1;

-- Update multiple columns at once
UPDATE products
SET price = 89.99,
    stock = 75
WHERE name = 'Nike Running Shoes';

-- Update all rows in a category
UPDATE products
SET is_available = FALSE
WHERE stock = 0;
```

> ⚠️ **Always use WHERE with UPDATE.** Without it, you update EVERY row in the table!

```sql
-- DANGEROUS — updates ALL products:
UPDATE products SET price = 0;   -- ❌ Don't do this by accident!
```

---

### DELETE — Remove rows from a table

```sql
-- Delete one specific row
DELETE FROM products
WHERE product_id = 3;

-- Delete all rows matching a condition
DELETE FROM products
WHERE is_available = FALSE;

-- Delete all rows (keeps the table structure, removes all data)
DELETE FROM products;
```

> ⚠️ **Always use WHERE with DELETE.** Without it, you delete ALL rows!

---

### ALTER — Change the structure of an existing table

```sql
-- Add a new column
ALTER TABLE products
ADD COLUMN discount_pct NUMERIC(5,2) DEFAULT 0;

-- Remove a column
ALTER TABLE products
DROP COLUMN discount_pct;

-- Rename a column
ALTER TABLE products
RENAME COLUMN name TO product_name;

-- Change a column's data type
ALTER TABLE products
ALTER COLUMN stock TYPE BIGINT;

-- Add a constraint after the fact
ALTER TABLE products
ADD CONSTRAINT chk_stock CHECK (stock >= 0);

-- Rename the table itself
ALTER TABLE products RENAME TO inventory;
```

---

### DROP — Permanently delete a table or database

```sql
-- Delete the entire table (structure AND all data)
DROP TABLE products;

-- Safe version — won't error if table doesn't exist
DROP TABLE IF EXISTS products;

-- Delete a database entirely
DROP DATABASE school;
```

> ⚠️ **DROP is permanent and irreversible.** There is no undo. Always double-check before running.

---

### TRUNCATE — Remove all data but keep the table

```sql
-- Empties the table completely, but the table itself still exists
TRUNCATE TABLE products;

-- Also resets the auto-increment counter back to 1
TRUNCATE TABLE products RESTART IDENTITY;
```

---

### Quick Comparison: DELETE vs DROP vs TRUNCATE

```
┌──────────┬────────────────────────────┬─────────────┬────────────────┐
│ Command  │ What it removes            │ Table stays?│ Can filter?    │
├──────────┼────────────────────────────┼─────────────┼────────────────┤
│ DELETE   │ Rows (can be filtered)     │ Yes ✅      │ Yes (WHERE)    │
│ TRUNCATE │ All rows (no filter)       │ Yes ✅      │ No             │
│ DROP     │ Everything (table + data)  │ No ❌       │ No             │
└──────────┴────────────────────────────┴─────────────┴────────────────┘
```

---

## 10. What Happens When You Violate a Constraint?

The database will **reject the operation** and give you an error. Your data is NOT changed. Let's see each one.

### NOT NULL Violation

```sql
-- ❌ Trying to insert a row without the required 'name' column
INSERT INTO products (category, price)
VALUES ('Electronics', 999.99);
```
```
ERROR: null value in column "name" of relation "products"
       violates not-null constraint
DETAIL: Failing row contains (6, null, Electronics, 999.99, 0, true).
```
**Fix:** Always provide a value for NOT NULL columns.

---

### UNIQUE Violation

```sql
-- Setup: email must be unique
CREATE TABLE users (
    user_id  SERIAL       PRIMARY KEY,
    email    VARCHAR(100) UNIQUE NOT NULL
);

INSERT INTO users (email) VALUES ('alice@gmail.com');  -- ✅ Works
INSERT INTO users (email) VALUES ('alice@gmail.com');  -- ❌ FAILS
```
```
ERROR: duplicate key value violates unique constraint "users_email_key"
DETAIL: Key (email)=(alice@gmail.com) already exists.
```
**Fix:** Each email must be different.

---

### CHECK Constraint Violation

```sql
-- ❌ Price cannot be negative
INSERT INTO products (name, price)
VALUES ('Mystery Item', -50.00);
```
```
ERROR: new row for relation "products" violates check constraint "products_price_check"
DETAIL: Failing row contains (7, Mystery Item, null, -50.00, 0, true).
```
**Fix:** Price must be >= 0.

---

### PRIMARY KEY Violation

```sql
-- ❌ Trying to manually insert a duplicate primary key
INSERT INTO products (product_id, name, price)
VALUES (1, 'Duplicate Product', 99.99);
```
```
ERROR: duplicate key value violates unique constraint "products_pkey"
DETAIL: Key (product_id)=(1) already exists.
```
**Fix:** Use SERIAL and don't specify product_id — let the database generate it.

---

### FOREIGN KEY Violation

```sql
-- Setup
CREATE TABLE departments (
    dept_id   SERIAL PRIMARY KEY,
    dept_name VARCHAR(100)
);
CREATE TABLE employees (
    emp_id  SERIAL PRIMARY KEY,
    name    VARCHAR(100),
    dept_id INT REFERENCES departments(dept_id)
);

INSERT INTO departments VALUES (1, 'Engineering');

-- ❌ dept_id = 999 doesn't exist in departments!
INSERT INTO employees (name, dept_id)
VALUES ('Alice', 999);
```
```
ERROR: insert or update on table "employees" violates foreign key constraint
       "employees_dept_id_fkey"
DETAIL: Key (dept_id)=(999) is not present in table "departments".
```
**Fix:** Insert the department first, then insert the employee with a valid dept_id.

---

### Trying to DROP a Referenced Table

```sql
-- ❌ Can't delete departments while employees depend on it
DROP TABLE departments;
```
```
ERROR: cannot drop table departments because other objects depend on it
DETAIL: constraint employees_dept_id_fkey on table employees depends on table departments
HINT:  Use DROP ... CASCADE to drop the dependent objects too.
```
**Fix:** Drop the child table (employees) first, then drop the parent (departments). Or use `CASCADE`.

---

## 11. Practice Table & 10 Beginner Questions

### The Table

Run this to set up your practice data:

```sql
-- Create the table
CREATE TABLE books (
    book_id     SERIAL        PRIMARY KEY,
    title       VARCHAR(200)  NOT NULL,
    author      VARCHAR(100)  NOT NULL,
    genre       VARCHAR(50),
    price       NUMERIC(6,2)  CHECK (price >= 0),
    pages       INT           CHECK (pages > 0),
    published   INT,          -- year e.g. 2020
    in_stock    BOOLEAN       DEFAULT TRUE
);

-- Insert sample data
INSERT INTO books (title, author, genre, price, pages, published, in_stock)
VALUES
    ('The Alchemist',              'Paulo Coelho',      'Fiction',     14.99, 208,  1988, TRUE),
    ('Atomic Habits',              'James Clear',       'Self-Help',   16.99, 320,  2018, TRUE),
    ('Sapiens',                    'Yuval Noah Harari', 'History',     18.99, 443,  2011, TRUE),
    ('The Great Gatsby',           'F. Scott Fitzgerald','Fiction',     9.99, 180,  1925, TRUE),
    ('Thinking, Fast and Slow',    'Daniel Kahneman',   'Psychology',  17.99, 499,  2011, FALSE),
    ('1984',                       'George Orwell',     'Fiction',     10.99, 328,  1949, TRUE),
    ('Educated',                   'Tara Westover',     'Memoir',      15.99, 352,  2018, TRUE),
    ('The Lean Startup',           'Eric Ries',         'Business',    19.99, 336,  2011, TRUE),
    ('Dune',                       'Frank Herbert',     'Sci-Fi',      13.99, 412,  1965, FALSE),
    ('To Kill a Mockingbird',      'Harper Lee',        'Fiction',     11.99, 281,  1960, TRUE);
```

### The Table Contents

```
book_id | title                      | author              | genre      | price | pages | published | in_stock
--------+----------------------------+---------------------+------------+-------+-------+-----------+---------
1       | The Alchemist              | Paulo Coelho        | Fiction    | 14.99 | 208   | 1988      | true
2       | Atomic Habits              | James Clear         | Self-Help  | 16.99 | 320   | 2018      | true
3       | Sapiens                    | Yuval Noah Harari   | History    | 18.99 | 443   | 2011      | true
4       | The Great Gatsby           | F. Scott Fitzgerald | Fiction    |  9.99 | 180   | 1925      | true
5       | Thinking, Fast and Slow    | Daniel Kahneman     | Psychology | 17.99 | 499   | 2011      | false
6       | 1984                       | George Orwell       | Fiction    | 10.99 | 328   | 1949      | true
7       | Educated                   | Tara Westover       | Memoir     | 15.99 | 352   | 2018      | true
8       | The Lean Startup           | Eric Ries           | Business   | 19.99 | 336   | 2011      | true
9       | Dune                       | Frank Herbert       | Sci-Fi     | 13.99 | 412   | 1965      | false
10      | To Kill a Mockingbird      | Harper Lee          | Fiction    | 11.99 | 281   | 1960      | true
```

---

### 10 Practice Questions

Try to write the query yourself before looking at the answer!

---

**Q1.** Show all books in the table — every column, every row.

<details>
<summary>Answer</summary>

```sql
SELECT * FROM books;
```
</details>

---

**Q2.** Show only the `title` and `author` of every book.

<details>
<summary>Answer</summary>

```sql
SELECT title, author FROM books;
```
</details>

---

**Q3.** Show all books that belong to the `'Fiction'` genre.

<details>
<summary>Answer</summary>

```sql
SELECT * FROM books
WHERE genre = 'Fiction';
```
</details>

---

**Q4.** Show all books where the price is less than `15.00`. Display only title, author, and price.

<details>
<summary>Answer</summary>

```sql
SELECT title, author, price
FROM books
WHERE price < 15.00;
```
</details>

---

**Q5.** Show all books that are **currently in stock** (`in_stock = TRUE`), sorted by price from lowest to highest.

<details>
<summary>Answer</summary>

```sql
SELECT title, price
FROM books
WHERE in_stock = TRUE
ORDER BY price ASC;
```
</details>

---

**Q6.** How many books are in the table in total?

<details>
<summary>Answer</summary>

```sql
SELECT COUNT(*) FROM books;
-- Returns: 10
```
</details>

---

**Q7.** What is the most expensive book? Show its title and price.

<details>
<summary>Answer</summary>

```sql
SELECT title, price
FROM books
ORDER BY price DESC
LIMIT 1;
```
</details>

---

**Q8.** A new book has arrived. Insert it into the table:
- Title: `'Deep Work'`
- Author: `'Cal Newport'`
- Genre: `'Self-Help'`
- Price: `15.49`
- Pages: `304`
- Published: `2016`
- In Stock: `TRUE`

<details>
<summary>Answer</summary>

```sql
INSERT INTO books (title, author, genre, price, pages, published, in_stock)
VALUES ('Deep Work', 'Cal Newport', 'Self-Help', 15.49, 304, 2016, TRUE);
```
</details>

---

**Q9.** The price of `'Sapiens'` has been reduced. Update its price to `14.99`.

<details>
<summary>Answer</summary>

```sql
UPDATE books
SET price = 14.99
WHERE title = 'Sapiens';
```
</details>

---

**Q10.** `'Dune'` has just come back in stock. Update the `in_stock` column to `TRUE` for that book.

<details>
<summary>Answer</summary>

```sql
UPDATE books
SET in_stock = TRUE
WHERE title = 'Dune';
```
</details>

---

## Quick Reference Card

```
┌───────────────────────────────────────────────────────────────┐
│                    SQL QUICK REFERENCE                        │
├──────────────────────┬────────────────────────────────────────┤
│ CREATE TABLE         │ Build the table structure              │
│ INSERT INTO          │ Add new rows                           │
│ SELECT ... FROM      │ Read / query data                      │
│ WHERE                │ Filter rows                            │
│ ORDER BY             │ Sort results (ASC / DESC)              │
│ LIMIT                │ Return only N rows                     │
│ UPDATE ... SET       │ Change existing data                   │
│ DELETE FROM          │ Remove rows                            │
│ ALTER TABLE          │ Change table structure                 │
│ DROP TABLE           │ Delete table permanently               │
├──────────────────────┴────────────────────────────────────────┤
│ GOLDEN RULES:                                                 │
│  ✅ Always use WHERE with UPDATE and DELETE                   │
│  ✅ DROP is permanent — double-check before running           │
│  ✅ SERIAL handles your ID column automatically               │
│  ✅ Constraints protect your data quality                     │
│  ✅ Foreign Key = link between two tables                     │
└───────────────────────────────────────────────────────────────┘
```

---

*End of Lecture 01 — Happy querying! 🐘*
