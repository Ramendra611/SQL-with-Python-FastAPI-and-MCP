# Lesson 2.2 — Filtering & Querying Data
### Theory + Practice | ShopDB — Indian E-commerce Dataset

---

## Before You Start

1. Run `setup.sql` in pgAdmin to create and populate ShopDB.
2. Verify you see 5 tables with the correct row counts.
3. Then work through this file top to bottom.

**What you'll learn in this lesson:**

| Concept | What it does |
|---|---|
| `DISTINCT` | Remove duplicate values from results |
| `IN` / `NOT IN` | Match against a list of values |
| `BETWEEN` | Filter within a range |
| `LIKE` / `ILIKE` | Pattern matching on text |
| `IS NULL` / `IS NOT NULL` | Handle missing values |
| `CASE WHEN` | Conditional logic inside a query |
| Date functions | Filter and extract parts of dates |
| `COALESCE` | Replace NULL with a fallback value |

All queries in this lesson run on ShopDB. The dataset has:
- 20 customers from 12+ Indian cities
- 6 product categories and 25 products
- 15 orders with 30 order line items

---

## Part 1 — Quick Refresh: The ShopDB Schema

```
customers                          orders
┌────┬───────┬───────┬───────┐    ┌────┬─────────────┬────────────┬──────────┐
│ id │ name  │ city  │ state │    │ id │ customer_id │ order_date │ status   │
└────┴───────┴───────┴───────┘    └────┴─────────────┴────────────┴──────────┘
         │                                   │ │
         └───────────── FK ──────────────────┘ │
                                               │
order_items                          products  │           categories
┌────┬──────────┬────────────┬──────┐ ┌────┬──┴────┬───────────┐  ┌────┬──────────┐
│ id │ order_id │ product_id │  qty │ │ id │ name  │ price_inr │  │ id │ name     │
└────┴──────────┴────────────┴──────┘ └────┴───────┴───────────┘  └────┴──────────┘
          │               │                        │ FK
          └── FK ─────────┘                        └──────────────────────────────┘
```

The flow of a customer purchase:
`customer` places an `order` → order contains `order_items` → each item references a `product` → product belongs to a `category`

---

## Part 2 — DISTINCT: Remove Duplicates

`DISTINCT` removes duplicate rows from results.

```sql
-- Which states do our customers come from?
-- Without DISTINCT, a state like Maharashtra appears once per customer
SELECT state
FROM customers
ORDER BY state;
```

```sql
-- With DISTINCT — each state appears only once
SELECT DISTINCT state
FROM customers
ORDER BY state;
```

```sql
-- Which payment methods have been used? (across all orders)
SELECT DISTINCT payment_method
FROM orders
ORDER BY payment_method;
```

```sql
-- How many distinct states are our customers from?
-- Combining COUNT with DISTINCT
SELECT COUNT(DISTINCT state) AS unique_states
FROM customers;
```

> `DISTINCT` applies to the **entire row** when multiple columns are listed.
> `SELECT DISTINCT city, state` returns distinct *combinations* of city + state.

```sql
-- Distinct city-state combinations
SELECT DISTINCT city, state
FROM customers
ORDER BY state, city;
```

---

## Part 3 — IN and NOT IN: Match a List

`IN` is a cleaner way to write multiple `OR` conditions.

```sql
-- Customers from Maharashtra OR Gujarat OR Delhi
-- The long way:
SELECT name, city, state
FROM customers
WHERE state = 'Maharashtra'
   OR state = 'Gujarat'
   OR state = 'Delhi';

-- The clean way:
SELECT name, city, state
FROM customers
WHERE state IN ('Maharashtra', 'Gujarat', 'Delhi')
ORDER BY state, name;
```

```sql
-- Orders that are NOT delivered and NOT cancelled
SELECT id, customer_id, order_date, status
FROM orders
WHERE status NOT IN ('Delivered', 'Cancelled')
ORDER BY order_date;
```

```sql
-- Products in the Electronics or Sports category
-- (category_id 1 = Electronics, 5 = Sports)
SELECT name, price_inr, stock_quantity
FROM products
WHERE category_id IN (1, 5)
ORDER BY category_id, price_inr DESC;
```

> ⚠️ **NULL trap with NOT IN:**
> If the list contains even one NULL, `NOT IN` returns no rows.
> Always make sure the values you compare against cannot be NULL.
> `WHERE column NOT IN (1, 2, NULL)` → always empty!

---

## Part 4 — BETWEEN: Filter a Range

`BETWEEN low AND high` is inclusive — both endpoints are included.

```sql
-- Products priced between ₹500 and ₹3000
SELECT name, price_inr
FROM products
WHERE price_inr BETWEEN 500 AND 3000
ORDER BY price_inr;
```

```sql
-- Orders placed in the first quarter of 2024 (Jan–Mar)
SELECT id, customer_id, order_date, status
FROM orders
WHERE order_date BETWEEN '2024-01-01' AND '2024-03-31'
ORDER BY order_date;
```

```sql
-- Products NOT in the ₹500–₹3000 range (budget or premium)
SELECT name, price_inr
FROM products
WHERE price_inr NOT BETWEEN 500 AND 3000
ORDER BY price_inr;
```

> `BETWEEN` with dates includes the full day for both endpoints.
> `BETWEEN '2024-01-01' AND '2024-03-31'` includes all of March 31st.

---

### ✏️ Practice Set 1 — DISTINCT, IN, BETWEEN

**Q1.** List all distinct roles (job roles) in the players table from CricketDB.
*(Switch to cricketdb for this one: `\c cricketdb` or reconnect in pgAdmin)*

Actually — stay in ShopDB for all questions in this lesson.

**Q1.** List all distinct cities our customers come from, alphabetically.

**Q2.** Show all orders placed by customers with id IN (1, 3, 5, 7).
Show order_id, customer_id, order_date, and status.

**Q3.** Find all products priced between ₹1000 and ₹10000.
Show product name and price, ordered by price ascending.

**Q4.** Which customers joined the platform between 1st April 2023 and
30th September 2023? Show name, city, and joined_on date.

**Q5.** Find all orders with status NOT IN ('Delivered', 'Cancelled').
How many are there? (Use COUNT)

---

## Part 5 — LIKE and ILIKE: Pattern Matching

`LIKE` matches text patterns using wildcards:
- `%` matches **any sequence** of characters (including none)
- `_` matches **exactly one** character

```sql
-- Products whose name starts with "boAt"
SELECT name, price_inr
FROM products
WHERE name LIKE 'boAt%';
```

```sql
-- Products with "Cricket" anywhere in the name
SELECT name, price_inr
FROM products
WHERE name LIKE '%Cricket%';
```

```sql
-- Customers whose name ends in "Sharma"
SELECT name, email, city
FROM customers
WHERE name LIKE '%Sharma';
```

```sql
-- Customers whose email is from gmail.com
SELECT name, email
FROM customers
WHERE email LIKE '%@gmail.com';
```

```sql
-- Products with exactly 5 characters before a space (pattern: _____ %)
-- e.g. "Nivia Football" — 5 chars then space
SELECT name FROM products WHERE name LIKE '_____ %';
```

### ILIKE — Case-Insensitive LIKE (PostgreSQL only)

```sql
-- Find products with "samsung" in the name — regardless of capitalisation
SELECT name, price_inr
FROM products
WHERE name ILIKE '%samsung%';
```

> `LIKE` is case-sensitive: `'Samsung'` ≠ `'samsung'`
> `ILIKE` is case-insensitive (PostgreSQL-specific)
> Standard SQL alternative: `LOWER(name) LIKE '%samsung%'`

---

## Part 6 — IS NULL and IS NOT NULL

Some columns allow NULL — `batting_style` in CricketDB, or optional fields.
In ShopDB, `categories.description` can be NULL.

```sql
-- Categories that have no description filled in
SELECT name
FROM categories
WHERE description IS NULL;
```

```sql
-- Categories that DO have a description
SELECT name, description
FROM categories
WHERE description IS NOT NULL;
```

```sql
-- COALESCE: show a fallback when a value is NULL
-- Returns first non-NULL argument
SELECT
    name,
    COALESCE(description, 'No description provided') AS description
FROM categories;
```

> **Rule:** Never write `WHERE column = NULL` — it always returns 0 rows.
> SQL uses three-value logic: TRUE, FALSE, and NULL (unknown).
> `NULL = NULL` evaluates to NULL, not TRUE.

---

## Part 7 — CASE WHEN: Conditional Logic

`CASE WHEN` is SQL's version of if/else. It creates a new column
based on conditions evaluated row by row.

```sql
-- Label products as budget / mid-range / premium based on price
SELECT
    name,
    price_inr,
    CASE
        WHEN price_inr < 1000           THEN 'Budget'
        WHEN price_inr BETWEEN 1000 AND 9999 THEN 'Mid-range'
        ELSE                                 'Premium'
    END AS price_segment
FROM products
ORDER BY price_inr;
```

```sql
-- Show order status with an emoji label
SELECT
    id,
    order_date,
    CASE status
        WHEN 'Delivered'  THEN '✅ Delivered'
        WHEN 'Shipped'    THEN '🚚 On the Way'
        WHEN 'Pending'    THEN '⏳ Pending'
        WHEN 'Cancelled'  THEN '❌ Cancelled'
    END AS status_label
FROM orders
ORDER BY order_date;
```

```sql
-- Count orders in each status using CASE + SUM (pivot pattern)
SELECT
    COUNT(*)                                        AS total_orders,
    SUM(CASE WHEN status = 'Delivered'  THEN 1 ELSE 0 END) AS delivered,
    SUM(CASE WHEN status = 'Shipped'    THEN 1 ELSE 0 END) AS shipped,
    SUM(CASE WHEN status = 'Pending'    THEN 1 ELSE 0 END) AS pending,
    SUM(CASE WHEN status = 'Cancelled'  THEN 1 ELSE 0 END) AS cancelled
FROM orders;
```

This last pattern is called a **pivot** — turning row values into columns.
Very useful for dashboards and summary reports.

```sql
-- Flag whether each product is available or out of stock
SELECT
    name,
    price_inr,
    stock_quantity,
    CASE
        WHEN is_available = FALSE   THEN 'Out of Stock'
        WHEN stock_quantity = 0     THEN 'Out of Stock'
        WHEN stock_quantity < 20    THEN 'Low Stock'
        ELSE                             'In Stock'
    END AS stock_status
FROM products
ORDER BY stock_quantity;
```

---

### ✏️ Practice Set 2 — LIKE, IS NULL, CASE WHEN

**Q6.** Find all products whose name contains the word "Maths" or "Cricket".
Hint: use two LIKE conditions with OR.

**Q7.** How many customers have email addresses ending in '@gmail.com'?
Use LIKE and COUNT.

**Q8.** Write a query that shows every product's name, price_inr,
and a new column called `affordability` with these labels:
- `'Under ₹500'` — price below 500
- `'₹500–₹5000'` — price between 500 and 5000
- `'Above ₹5000'` — price above 5000

**Q9.** List categories that have a description (IS NOT NULL).
Show name and description.

**Q10.** Write a query that shows the total number of orders
for each payment method using GROUP BY.
Then rewrite it using the CASE + SUM pivot pattern
to show all four payment methods in a single row.

---

## Part 8 — Date Functions

PostgreSQL has rich built-in date functions.
Our `orders` and `customers` tables both have date columns.

### Extracting Parts of a Date

```sql
-- Extract the month and year from order_date
SELECT
    id,
    order_date,
    EXTRACT(YEAR  FROM order_date) AS order_year,
    EXTRACT(MONTH FROM order_date) AS order_month,
    EXTRACT(DAY   FROM order_date) AS order_day
FROM orders
ORDER BY order_date;
```

```sql
-- How many orders were placed each month?
SELECT
    EXTRACT(MONTH FROM order_date) AS month,
    COUNT(*) AS order_count
FROM orders
GROUP BY month
ORDER BY month;
```

```sql
-- Format the date for display
SELECT
    id,
    TO_CHAR(order_date, 'DD Mon YYYY')  AS formatted_date,
    TO_CHAR(order_date, 'Month YYYY')   AS month_year
FROM orders;
```

### Comparing and Calculating Dates

```sql
-- Orders placed in the last 6 months from today
-- CURRENT_DATE = today's date in PostgreSQL
SELECT id, customer_id, order_date, status
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '6 months'
ORDER BY order_date DESC;
```

```sql
-- How many days ago was each order placed?
SELECT
    id,
    order_date,
    CURRENT_DATE - order_date AS days_ago
FROM orders
ORDER BY days_ago;
```

```sql
-- Customers who joined in 2023 Q4 (October–December)
SELECT name, city, joined_on
FROM customers
WHERE joined_on BETWEEN '2023-10-01' AND '2023-12-31'
ORDER BY joined_on;
```

```sql
-- The most recent and oldest orders
SELECT
    MIN(order_date) AS first_order,
    MAX(order_date) AS latest_order
FROM orders;
```

---

## Part 9 — Putting It All Together: Multi-Condition Queries

Real queries combine multiple clauses. Here are some realistic business queries on ShopDB.

```sql
-- All active, in-stock products under ₹5000 in the Sports or Books category
SELECT
    p.name,
    c.name      AS category,
    p.price_inr,
    p.stock_quantity
FROM products   AS p
JOIN categories AS c  ON p.category_id = c.id
WHERE p.is_available  = TRUE
  AND p.stock_quantity > 0
  AND p.price_inr < 5000
  AND c.name IN ('Sports', 'Books')
ORDER BY p.price_inr;
```

```sql
-- Customers from Maharashtra or Kerala who joined after June 2023
SELECT
    name,
    city,
    state,
    joined_on
FROM customers
WHERE state IN ('Maharashtra', 'Kerala')
  AND joined_on > '2023-06-30'
ORDER BY state, joined_on;
```

```sql
-- Orders placed in 2024 that are still not delivered
-- (Pending or Shipped)
SELECT
    o.id            AS order_id,
    c.name          AS customer,
    c.city,
    o.order_date,
    o.status
FROM orders     AS o
JOIN customers  AS c  ON o.customer_id = c.id
WHERE EXTRACT(YEAR FROM o.order_date) = 2024
  AND o.status NOT IN ('Delivered', 'Cancelled')
ORDER BY o.order_date;
```

```sql
-- Products containing "Maths" or "Cricket" or priced above ₹50000
SELECT
    name,
    price_inr,
    stock_quantity
FROM products
WHERE name ILIKE '%maths%'
   OR name ILIKE '%cricket%'
   OR price_inr > 50000
ORDER BY price_inr DESC;
```

---

### ✏️ Practice Set 3 — Date Functions & Combined Queries

**Q11.** How many orders were placed in each month of 2024?
Show month number and order_count, sorted by month.

**Q12.** Write a query to find all customers who joined before
1st July 2023. Show name, city, and joined_on date.

**Q13.** Find all Delivered orders that were placed using UPI.
Show order_id, customer_id, order_date.

**Q14.** Write a query that labels each order with a quarter:
- 'Q1' — January to March
- 'Q2' — April to June
- 'Q3' — July to September
- 'Q4' — October to December
Show order_id, order_date, and the quarter label.

**Q15.** Find products where the name starts with 'B' AND the price
is under ₹1000. Show name and price_inr.

---

## Part 10 — Practice Set Answers

### Answers: Practice Set 1

**Q1.** Distinct cities:
```sql
SELECT DISTINCT city
FROM customers
ORDER BY city;
```

**Q2.** Orders by specific customers:
```sql
SELECT id AS order_id, customer_id, order_date, status
FROM orders
WHERE customer_id IN (1, 3, 5, 7)
ORDER BY order_date;
```

**Q3.** Products between ₹1000 and ₹10000:
```sql
SELECT name, price_inr
FROM products
WHERE price_inr BETWEEN 1000 AND 10000
ORDER BY price_inr;
```

**Q4.** Customers who joined Apr–Sep 2023:
```sql
SELECT name, city, joined_on
FROM customers
WHERE joined_on BETWEEN '2023-04-01' AND '2023-09-30'
ORDER BY joined_on;
```

**Q5.** Non-delivered, non-cancelled orders:
```sql
SELECT COUNT(*) AS count
FROM orders
WHERE status NOT IN ('Delivered', 'Cancelled');
```

---

### Answers: Practice Set 2

**Q6.** Products with "Maths" or "Cricket" in the name:
```sql
SELECT name, price_inr
FROM products
WHERE name LIKE '%Maths%'
   OR name LIKE '%Cricket%';
```

**Q7.** Gmail customers:
```sql
SELECT COUNT(*) AS gmail_customers
FROM customers
WHERE email LIKE '%@gmail.com';
```

**Q8.** Affordability label:
```sql
SELECT
    name,
    price_inr,
    CASE
        WHEN price_inr < 500                    THEN 'Under ₹500'
        WHEN price_inr BETWEEN 500 AND 5000     THEN '₹500–₹5000'
        ELSE                                         'Above ₹5000'
    END AS affordability
FROM products
ORDER BY price_inr;
```

**Q9.** Categories with a description:
```sql
SELECT name, description
FROM categories
WHERE description IS NOT NULL;
```

**Q10a.** Payment method breakdown (GROUP BY):
```sql
SELECT payment_method, COUNT(*) AS order_count
FROM orders
GROUP BY payment_method
ORDER BY order_count DESC;
```

**Q10b.** Same result as a pivot (single row):
```sql
SELECT
    SUM(CASE WHEN payment_method = 'UPI'        THEN 1 ELSE 0 END) AS upi,
    SUM(CASE WHEN payment_method = 'Card'       THEN 1 ELSE 0 END) AS card,
    SUM(CASE WHEN payment_method = 'COD'        THEN 1 ELSE 0 END) AS cod,
    SUM(CASE WHEN payment_method = 'NetBanking' THEN 1 ELSE 0 END) AS netbanking
FROM orders;
```

---

### Answers: Practice Set 3

**Q11.** Orders per month:
```sql
SELECT
    EXTRACT(MONTH FROM order_date) AS month,
    COUNT(*) AS order_count
FROM orders
WHERE EXTRACT(YEAR FROM order_date) = 2024
GROUP BY month
ORDER BY month;
```

**Q12.** Customers who joined before July 2023:
```sql
SELECT name, city, joined_on
FROM customers
WHERE joined_on < '2023-07-01'
ORDER BY joined_on;
```

**Q13.** Delivered + UPI orders:
```sql
SELECT id AS order_id, customer_id, order_date
FROM orders
WHERE status = 'Delivered'
  AND payment_method = 'UPI'
ORDER BY order_date;
```

**Q14.** Quarter labels using CASE WHEN:
```sql
SELECT
    id AS order_id,
    order_date,
    CASE
        WHEN EXTRACT(MONTH FROM order_date) BETWEEN 1 AND 3  THEN 'Q1'
        WHEN EXTRACT(MONTH FROM order_date) BETWEEN 4 AND 6  THEN 'Q2'
        WHEN EXTRACT(MONTH FROM order_date) BETWEEN 7 AND 9  THEN 'Q3'
        ELSE                                                       'Q4'
    END AS quarter
FROM orders
ORDER BY order_date;
```

**Q15.** Products starting with 'B' under ₹1000:
```sql
SELECT name, price_inr
FROM products
WHERE name LIKE 'B%'
  AND price_inr < 1000
ORDER BY price_inr;
```

---

## What's Next

You have covered:
- ✅ `DISTINCT` — remove duplicate rows
- ✅ `IN` / `NOT IN` — match against a list of values
- ✅ `BETWEEN` — filter by range (inclusive)
- ✅ `LIKE` / `ILIKE` — pattern matching with `%` and `_`
- ✅ `IS NULL` / `IS NOT NULL` — handle missing values
- ✅ `COALESCE` — fallback value for NULLs
- ✅ `CASE WHEN` — conditional logic and pivot pattern
- ✅ Date functions — `EXTRACT`, `TO_CHAR`, `CURRENT_DATE`, `INTERVAL`
- ✅ Multi-condition queries combining all of the above

**In Lesson 2.3** we go deep on **Aggregations & Grouping**:
- Multi-column `GROUP BY`
- `HAVING` with complex conditions
- `ROLLUP` for subtotals
- `FILTER` clause with aggregates
- A first look at **window functions** (`ROW_NUMBER`, `RANK`, `SUM OVER`)
- All on CricketDB + ShopDB together
