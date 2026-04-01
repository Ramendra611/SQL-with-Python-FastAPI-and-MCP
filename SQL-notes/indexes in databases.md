# SQL Indexing — A Hands-On Demo
### See the problem first. Then understand why.

---

## Table of Contents

- [What We Are Building](#what-we-are-building)
- [Step 1 — Generate the Data](#step-1--generate-the-data-python)
- [Step 2 — Load Into PostgreSQL](#step-2--load-into-postgresql)
- [Step 3 — Query Without an Index](#step-3--query-without-an-index)
- [Step 4 — What Just Happened? (The Theory)](#step-4--what-just-happened-the-theory)
- [Step 5 — The B-tree Index (Interactive)](#step-5--the-b-tree-index-interactive-demo)
- [Step 6 — Create the Index](#step-6--create-the-index)
- [Step 7 — Query Again and Compare](#step-7--query-again-and-compare)
- [Step 8 — Reading EXPLAIN ANALYZE Line by Line](#step-8--reading-explain-analyze-line-by-line)
- [Step 9 — Clustered vs Non-Clustered Indexes](#step-9--clustered-vs-non-clustered-indexes)
- [Key Takeaways](#key-takeaways)

---

## What We Are Building

We are going to:
1. Create a table with **2 million rows** of fake user data
2. Run a query on it **without an index** and measure how long it takes
3. Understand *why* it is slow — the storage and search model
4. See how a B-tree index works using an interactive visualiser
5. Create an index and run the same query again
6. Read the EXPLAIN ANALYZE output together and understand every line
7. Learn about clustered vs non-clustered indexes

By the end, you will have a concrete, measurable understanding of what
an index actually does — not just "it makes queries faster."

---

---

## Step 1 — Generate the Data (Python)

We are using a Python script to generate the data rather than SQL
because it gives us full control over the data shape and lets us
inspect the CSV before loading it.

### Run the script

Make sure you have Python 3 installed. No external libraries needed —
only the built-in `csv`, `random`, and `datetime` modules.

```bash
python generate_data.py
```

You will see progress printed every 50,000 rows:

```
Generating 2,000,000 rows → users.csv
This will take about 30–60 seconds...
      50,000 rows written...
     100,000 rows written...
     ...
   2,000,000 rows written...

Done! File saved as: users.csv
```

### Inspect the file before loading

Open `users.csv` in Excel or a text editor. The first few rows should
look like this:

```
id,first_name,last_name,age,email,city,signup_date
1,Arjun,Sharma,34,arjun.sharma123@gmail.com,Mumbai,2021-03-14
2,Priya,Nair,27,priya4521@yahoo.com,Delhi,2019-08-22
3,Rohit,Verma,45,r.verma56@outlook.com,Bengaluru,2022-11-30
...
```

**What the data looks like:**
- `id` — sequential integer 1 to 2,000,000
- `first_name` / `last_name` — random from a pool of 40 first names and 35 last names
- `age` — random integer between 18 and 70
- `email` — generated from name + id, guaranteed unique
- `city` — random from 20 Indian cities
- `signup_date` — random date between 2018 and 2024

The file will be approximately **80MB**. That is a lot of data for a demo
table — and that is intentional. We want the timing difference to be
real and visible.

---

---

## Step 2 — Load Into PostgreSQL

### Create the database and table

Open pgAdmin, connect to your PostgreSQL server, and run:

```sql
CREATE DATABASE indexing_demo;
```

Connect to `indexing_demo`, then create the table:

```sql
CREATE TABLE users (
    id          INT,
    first_name  VARCHAR(50),
    last_name   VARCHAR(50),
    age         INT,
    email       VARCHAR(150),
    city        VARCHAR(50),
    signup_date DATE
);
```

> **Notice:** We have deliberately NOT created a primary key or any
> index yet. This is important — we want to see what queries look like
> with zero indexes before adding any.

### Import the CSV

In pgAdmin:
1. Right-click the `users` table in the left panel
2. Click **Import/Export Data**
3. Set Format: **CSV** | Header: **Yes** | Delimiter: **,**
4. Browse to `users.csv` and select it
5. Click **OK**

The import will take 30–60 seconds for 2 million rows.

### Verify the data loaded correctly

```sql
-- Count the rows
SELECT COUNT(*) FROM users;
-- Expected: 2,000,000
```

```sql
-- See the first 5 rows
SELECT * FROM users LIMIT 5;
```

```sql
-- Check the spread of ages
SELECT
    MIN(age)   AS youngest,
    MAX(age)   AS oldest,
    ROUND(AVG(age), 1) AS avg_age
FROM users;
-- Expected: youngest=18, oldest=70, avg_age≈44
```

```sql
-- Check city distribution
SELECT city, COUNT(*) AS count
FROM   users
GROUP BY city
ORDER BY count DESC;
-- Each of the 20 cities should have roughly 100,000 rows (5% each)
```

```sql
-- Update table statistics so the planner has accurate info
ANALYZE users;
```

Everything looks good. Now we have a 2 million row table with no indexes
other than what we explicitly create. Let's see how it performs.

---

---

## Step 3 — Query Without an Index

### What we are doing

We are going to search for a specific person by name — a very common
operation in any real application. We want to measure how long it takes
with zero indexes.

### Run the query

```sql
-- Find all users named 'Arjun Sharma'
-- No index exists on any column — watch the timing at the bottom of pgAdmin
EXPLAIN ANALYZE
SELECT *
FROM   users
WHERE  first_name = 'Arjun'
  AND  last_name  = 'Sharma';
```

### What you will see

The EXPLAIN ANALYZE output will look something like this:

```
Seq Scan on users
  (cost=0.00..43695.00 rows=147 width=76)
  (actual time=0.412..521.834 rows=156 loops=1)
  Filter: (((first_name)::text = 'Arjun') AND ((last_name)::text = 'Sharma'))
  Rows Removed by Filter: 1999844
Planning Time: 0.5 ms
Execution Time: 522.4 ms
```

> Your exact numbers will differ — but the shape will be the same.

### What to notice right now

Just look at these three lines for now. Don't worry about the rest:

```
Seq Scan on users                        ← type of scan
Rows Removed by Filter: 1,999,844        ← how many rows were checked and discarded
Execution Time: 522 ms                   ← how long it took
```

PostgreSQL:
- Read **every single row** in the 2 million row table
- Checked each one: "is this Arjun Sharma?"
- Kept 156, discarded 1,999,844
- The whole thing took over **half a second**

For finding 156 rows.

Now let's understand *why* this happens before we fix it.

---

---

## Step 4 — What Just Happened? (The Theory)

### How PostgreSQL stores data

PostgreSQL stores all data in fixed-size blocks called **pages**.
Each page is 8KB. Think of pages like the physical pages of a printed book —
you can only read one page at a time, and reading takes time.

```
Table: users (2 million rows)

Each page holds roughly 40–50 rows
2,000,000 ÷ 45 ≈ 44,000 pages in total

Page 1   │ row 1  │ row 2  │ row 3  │ ... │ row 45  │
Page 2   │ row 46 │ row 47 │ row 48 │ ... │ row 90  │
Page 3   │ row 91 │ row 92 │ ...                     │
...
Page 44000│ row 1,999,960 │ ... │ row 2,000,000      │
```

**The key point:** Rows are stored in the order they were inserted.
There is no automatic sorting by name, age, or any column. An Arjun
inserted in 2018 and an Arjun inserted in 2023 could be on completely
different pages — pages 3 and 41,000.

### What a sequential scan actually does

When you search `WHERE first_name = 'Arjun'` with no index,
PostgreSQL has no choice but to:

```
Load page 1    → check all 45 rows → is any first_name = 'Arjun'? → keep matches, discard rest
Load page 2    → check all 45 rows → same check
Load page 3    → check all 45 rows → same check
...
Load page 44000 → check remaining rows → done
```

Every page is loaded. Every row is inspected. Even if your name appears
in the first 10 rows, PostgreSQL still reads all 44,000 pages because
it does not know where else your name might appear.

This is called a **Sequential Scan** — and it is why the query took 522ms.

**The cost scales linearly:**
- 2M rows → ~500ms
- 20M rows → ~5 seconds
- 200M rows → ~50 seconds

Clearly not acceptable for a production application.

### The solution: an index

An index is a **separate data structure** that sits alongside your table.
It stores column values in a sorted, searchable structure — so PostgreSQL
can find the rows you want in milliseconds, not seconds.

The most common index type in PostgreSQL is a **B-tree** (Balanced Tree).

Let's understand how it works before we create one.

---

---

## Step 5 — The B-tree Index (Interactive Demo)

### What a B-tree is

A B-tree is a sorted tree structure where:
- Values are stored in **sorted order**
- The tree is always **balanced** — every path from root to leaf is the same length
- Each node can have multiple keys and multiple children
- The bottom level (**leaf nodes**) contains the actual index entries — each one stores the value AND a pointer back to the row in the table

```
Example: B-tree index on first_name (simplified)

                    ┌─────────┐
                    │  "Meera" │   ← root node (split point)
                    └────┬────┘
              ┌──────────┴──────────┐
         ┌────▼────┐           ┌────▼────┐
         │"Arjun"  │           │ "Priya" │   ← internal nodes
         └────┬────┘           └────┬────┘
     ┌────────┴────────┐           ...
┌────▼────┐       ┌────▼────┐
│"Aditya" │       │"Arjun"  │   ← leaf nodes: value + row pointer
│ → row 5 │       │ → row 1 │
│"Amit"   │       │"Arjun"  │
│ → row 9 │       │ → row 7 │
│"Ananya" │       │"Kabir"  │
│ → row 3 │       │ → row 2 │
└─────────┘       └─────────┘
    ↕ linked          ↕ linked    ← leaf nodes linked to each other
```

### How a lookup works

**Query:** `WHERE first_name = 'Arjun'`

1. Start at the **root** node — compare 'Arjun' against 'Meera'
2. 'Arjun' comes before 'Meera' alphabetically → go left
3. Reach internal node 'Arjun' → go to the correct child
4. Reach the **leaf node** containing all 'Arjun' entries
5. Each leaf entry has a **row pointer** (CTID) → fetch those exact rows from the table

For 2 million rows, this traversal takes about **21 steps**.
Compare that to reading 2,000,000 rows in a sequential scan.

### See it live — interactive B-tree visualiser

**Go to this URL:**
**https://www.cs.usfca.edu/~galles/visualization/BTree.html**

This is a free interactive B-tree visualiser from the University of
San Francisco. You can insert values and watch the tree build and
balance in real time.

**Guided exercise — do this:**

1. Set the **Order** to 3 (default) using the slider at the top
2. Insert these values one by one using the Insert button:

```
Insert in this order: 50, 25, 75, 10, 30, 60, 80, 5, 15, 28, 35
```

**Watch what happens at each insert:**

| Insert | What to observe |
|---|---|
| 50 | Root node created with one value |
| 25, 75 | Root now has three values — full |
| 10 | Tree splits — root becomes internal node, children created |
| 30, 60, 80 | Leaf nodes fill up |
| 5 | Another split occurs — tree grows taller |
| 15, 28, 35 | Watch the tree stay balanced — all leaf nodes at same depth |

**Key observations:**
- The tree is always balanced — every leaf is at the same depth
- Values in leaf nodes are always sorted left to right
- When a node gets full, it splits and promotes a value upward
- The tree height grows slowly — millions of values still need only ~20 levels

**Now try a search:**

Click the **Find** button and search for value `28`.
Watch how the algorithm traverses from root to leaf — left or right at
each node based on comparison. Count the steps. Then search for `5`.
Then `80`. Notice it always takes the same number of steps regardless
of which value you search for — because the tree is balanced.

**This is exactly what PostgreSQL does** when you query a column with
a B-tree index. The column values are the keys. The row pointers are
the CTID links back to the actual data in the table.

---

---

## Step 6 — Create the Index

Now that we understand what an index does internally, let's create one
and see the difference.

### What we are doing

We are creating a B-tree index on `first_name` and `last_name` together
(a composite index) because our query filters on both columns.

```sql
-- Create the index
-- Naming convention: idx_tablename_column(s)
CREATE INDEX idx_users_name
ON users (first_name, last_name);
```

**What is happening while this runs:**
PostgreSQL is scanning the entire `users` table, extracting the
`first_name` and `last_name` values from every row, sorting them, and
building the B-tree structure on disk. This takes 15–30 seconds for
2 million rows — you only pay this cost once.

```sql
-- Verify the index was created
SELECT indexname, indexdef
FROM   pg_indexes
WHERE  tablename = 'users';
```

You should see two indexes: one is `idx_users_name` that we just created.
(If you see only one, the index is still building — wait a moment.)

---

---

## Step 7 — Query Again and Compare

Now we run the **same query** on the same table. The only thing that
has changed is that we created an index in Step 6.

---

### Query 1 — Searching on an INDEXED column (first_name + last_name)

We created `idx_users_name` on `(first_name, last_name)` in Step 6.
Let's query those columns and observe what happens.

```sql
-- Searching on an indexed column
EXPLAIN ANALYZE
SELECT *
FROM   users
WHERE  first_name = 'Arjun'
  AND  last_name  = 'Sharma';
```

**Output:**

```
Index Scan using idx_users_name on users
  (cost=0.43..830.22 rows=147 width=76)
  (actual time=0.052..1.842 rows=156 loops=1)
  Index Cond: (((first_name)::text = 'Arjun') AND ((last_name)::text = 'Sharma'))
Planning Time: 0.4 ms
Execution Time: 1.9 ms
```

**What to notice:**
- `Index Scan` — PostgreSQL used the index
- `Index Cond` — filtering happened inside the index (no rows wasted)
- `actual time=0.052..1.842` — found first row in 0.05ms, all done in 1.8ms
- `Execution Time: 1.9 ms` — under 2 milliseconds for 2 million rows

---

### Query 2 — Searching on a NON-INDEXED column (age)

We have no index on the `age` column. Let's search on it and compare.

```sql
-- Searching on a non-indexed column
EXPLAIN ANALYZE
SELECT *
FROM   users
WHERE  age = 25;
```

**Output:**

```
Seq Scan on users
  (cost=0.00..43695.00 rows=37800 width=76)
  (actual time=0.118..498.234 rows=37892 loops=1)
  Filter: (age = 25)
  Rows Removed by Filter: 1962108
Planning Time: 0.1 ms
Execution Time: 498.7 ms
```

**What to notice:**
- `Seq Scan` — no index available, every page must be read
- `Filter` — filtering happened AFTER fetching rows from the heap
- `Rows Removed by Filter: 1,962,108` — nearly 2 million rows read and discarded
- `Execution Time: 498.7 ms` — almost 500 milliseconds

---

### The direct comparison

Here are both outputs side by side. Same table, same 2 million rows,
same machine. Only difference: one column has an index, the other does not.

```
INDEXED COLUMN (first_name + last_name)    NON-INDEXED COLUMN (age)
────────────────────────────────────────   ─────────────────────────────────────
Index Scan using idx_users_name            Seq Scan on users
  actual time=0.052..1.842                   actual time=0.118..498.234
  rows=156                                   rows=37892
  Index Cond: (first_name = 'Arjun'...)      Filter: (age = 25)
                                             Rows Removed by Filter: 1,962,108
Execution Time: 1.9 ms                     Execution Time: 498.7 ms
```

| | Indexed column | Non-indexed column |
|---|---|---|
| Scan type | Index Scan | Seq Scan |
| How rows are found | Directly in the index | Read every row, filter after |
| Rows wasted | 0 | 1,962,108 |
| Execution time | **1.9 ms** | **498.7 ms** |
| Speed difference | — | **~260× slower** |

---

### Now fix it — add an index on age and compare again

```sql
-- Create an index on the age column
CREATE INDEX idx_users_age ON users (age);
```

```sql
-- Run the same query again
EXPLAIN ANALYZE
SELECT *
FROM   users
WHERE  age = 25;
```

**What you will see:**

```
Index Scan using idx_users_age on users
  (cost=0.43..95123.43 rows=37800 width=76)
  (actual time=0.061..28.432 rows=37892 loops=1)
  Index Cond: (age = 25)
Planning Time: 0.2 ms
Execution Time: 28.9 ms
```

**What to notice:**
- `Index Scan` — now using the index
- `Execution Time: 28.9 ms` — much better than 498ms

But notice it is **not as fast as the name search (1.9ms)**.
Why? Because `age = 25` matches ~37,000 rows (about 1.9% of the table).
After finding those 37,000 entries in the index, PostgreSQL must jump
to 37,000 different locations in the heap to fetch the full rows. That
heap jumping takes time.

The name search only matched 156 rows — far fewer heap lookups.

**This illustrates an important lesson:**

> The fewer rows a condition matches, the more an index helps.
> This is called **selectivity** — and it is the most important factor
> in deciding whether an index will actually speed up your query.

| Query | Rows matched | % of table | Time with index |
|---|---|---|---|
| `first_name = 'Arjun' AND last_name = 'Sharma'` | ~156 | 0.008% | 1.9 ms |
| `age = 25` | ~37,000 | 1.9% | 28.9 ms |
| `city = 'Mumbai'` (if indexed) | ~100,000 | 5% | likely Seq Scan still |

The more selective the condition, the bigger the benefit of indexing.

---

### Try it yourself — three more experiments

Run each of these and observe the EXPLAIN ANALYZE output.
Before running each one, predict what you expect to see.

```sql
-- Experiment 1: Range query on indexed column (first_name)
-- How does a range perform vs an equality lookup?
EXPLAIN ANALYZE
SELECT * FROM users
WHERE first_name BETWEEN 'Arjun' AND 'Kabir';
```

```sql
-- Experiment 2: Search on last_name only (non-leading column of composite index)
-- Will the index be used?
EXPLAIN ANALYZE
SELECT * FROM users
WHERE last_name = 'Sharma';
```

```sql
-- Experiment 3: Search on city (not indexed)
-- What happens with a low-selectivity column even if we add an index?
EXPLAIN ANALYZE
SELECT * FROM users
WHERE city = 'Mumbai';
-- Then: CREATE INDEX idx_users_city ON users (city);
-- Then run the EXPLAIN ANALYZE again
-- Does the index get used? Why or why not?
```

**Expected findings:**
- Experiment 1: Index Scan — range queries work on B-tree indexes
- Experiment 2: Seq Scan — non-leading column cannot use the composite index
- Experiment 3: Seq Scan even WITH an index — city has only 20 values, each matching 5% of the table. The planner decides a sequential scan is faster than jumping to 100,000 scattered heap pages.

**What to observe on the last query:**
You should see `Seq Scan` again. The index is sorted by first_name
first, then last_name within each first_name group. Without knowing
the first_name, there is no contiguous block of 'Sharma' entries in
the index to scan — they are scattered across every first_name group.

This is the **leading column rule** of composite indexes — the index
can only be used if the query filters on the leftmost column(s).

---

---

## Step 8 — Reading EXPLAIN ANALYZE Line by Line

Let us take the output from Step 7 and go through every part of it carefully.

### The full output

```
Index Scan using idx_users_name on users
  (cost=0.43..830.22 rows=147 width=76)
  (actual time=0.052..1.842 rows=156 loops=1)
  Index Cond: (((first_name)::text = 'Arjun') AND ((last_name)::text = 'Sharma'))
Planning Time: 0.4 ms
Execution Time: 1.9 ms
```

### Line by line

**Line 1: `Index Scan using idx_users_name on users`**

This tells you:
- The type of scan: `Index Scan` (good — it used our index)
- Which index: `idx_users_name` (the one we just created)
- Which table: `users`

If you saw `Seq Scan on users` here, the index is not being used.

---

**Line 2: `(cost=0.43..830.22 rows=147 width=76)`**

This is the **planner's estimate** before the query runs.

- `cost=0.43` — startup cost: how much work before the first row is returned
- `cost=..830.22` — total cost: arbitrary units the planner uses to compare plans
- `rows=147` — planner estimated 147 matching rows
- `width=76` — estimated average row size in bytes

The `cost` numbers are not milliseconds. They are internal units the
planner uses to compare different execution strategies. Smaller is better,
but only compare costs within the same query.

---

**Line 3: `(actual time=0.052..1.842 rows=156 loops=1)`**

This is the **real measured result** after the query ran.

- `actual time=0.052` — real time in milliseconds to return the first row
- `actual time=..1.842` — real total time in milliseconds to return all rows
- `rows=156` — actual rows returned (vs estimate of 147 — very close)
- `loops=1` — this node ran once (>1 in nested loops)

**This is the most important line for performance analysis.**
The `actual time` values tell you exactly how long this step took.
If you have a slow query, find the node with the highest `actual time`.

---

**Line 4: `Index Cond: (((first_name)::text = 'Arjun') AND ...)`**

This tells you what condition was applied **inside the index** to find
the matching entries. This is different from a `Filter` line — an
`Index Cond` means the filtering happened in the index itself, not
after fetching rows from the heap.

`Filter` = rows fetched then discarded (expensive)
`Index Cond` = rows found directly in the index (cheap)

---

**Line 5: `Planning Time: 0.4 ms`**

Time to build the execution plan — how long the planner spent deciding
*how* to run the query. Usually negligible. Can be high for very complex
queries with many tables.

---

**Line 6: `Execution Time: 1.9 ms`**

The total wall-clock time for the entire query including planning.
This is what you report when someone asks "how long does this query take?"

---

### The before and after side by side

Here is the key difference in the two query plans annotated:

```
WITHOUT INDEX                          WITH INDEX
──────────────────────────────────     ──────────────────────────────────────
Seq Scan on users                      Index Scan using idx_users_name
  ↑ reads every page                     ↑ jumps to matching entries

actual time=0.412..521.834               actual time=0.052..1.842
  ↑ 522 ms total                           ↑ 1.9 ms total

rows=156                                 rows=156
  ↑ same result                             ↑ same result

Rows Removed by Filter: 1,999,844        (no Filter line)
  ↑ 2M rows read, 1.99M thrown away        ↑ 0 rows wasted
```

Same answer. 275× faster.

---

---

## Step 9 — Clustered vs Non-Clustered Indexes

### The concept

Now that you have seen how a B-tree index works, there is an important
distinction to understand: the relationship between the index and the
physical table data.

### Non-Clustered Index (what we just built)

In a non-clustered index, the index is a **completely separate structure**
from the table. The table (heap) stores rows in insertion order. The
index stores values in sorted order with pointers (CTIDs) back to the
heap.

```
HEAP (table — rows in insertion order):
┌────────────────────────────────────────────────────────┐
│ Page 1: Arjun(34), Priya(27), Rohit(45), Sneha(22)... │
│ Page 2: Kabir(31), Meera(29), Vikram(55), Ananya(19)...│
│ Page 3: ...                                            │
└────────────────────────────────────────────────────────┘
                          ↑
                     CTIDs point here

NON-CLUSTERED INDEX (separate structure — sorted):
┌─────────────────────────────────────┐
│ Aditya  → Page 4, slot 3           │
│ Amit    → Page 7, slot 1           │
│ Ananya  → Page 2, slot 4  ←────────┼── pointer back to heap
│ Arjun   → Page 1, slot 1           │
│ Arjun   → Page 9, slot 2           │
│ Arjun   → Page 15, slot 4          │
│ ...                                 │
└─────────────────────────────────────┘
```

**How a lookup works:**
1. Find 'Arjun' entries in the index → get CTIDs (Page 1 slot 1, Page 9 slot 2, Page 15 slot 4)
2. Jump to those specific pages in the heap and fetch the rows

The heap is unordered. The index is ordered. They are separate.

**This is what ALL PostgreSQL indexes are** — non-clustered by default.

---

### Clustered Index (the concept)

In a clustered index, the **table rows are physically stored in the
same sorted order as the index**. The index and the table are one
structure — not two separate ones.

```
CLUSTERED (index + table merged — rows sorted by first_name):
┌────────────────────────────────────────────────────────┐
│ Page 1: Aditya(45), Aditya(23), Amit(38), Ananya(19)  │
│ Page 2: Ananya(27), Arjun(34), Arjun(52), Arjun(29)   │
│ Page 3: Arjun(41), Arjun(22), Arjun(31), Arjun(18)    │
│ ...all Arjun rows are on consecutive pages...          │
│ Page 50: Diya(22), Diya(35), Divya(41), Geeta(29)     │
└────────────────────────────────────────────────────────┘
```

**How a lookup works:**
1. Find 'Arjun' in the index
2. Read consecutive pages — all Arjun rows are together physically
3. No jumping around the heap — all matches are in one place

**The benefit:** For range queries, all matching rows are physically
adjacent on disk. Much faster disk I/O.

**The limitation:** A table can only have ONE physical row order.
You can only cluster on one column (or set of columns) at a time.

---

### How PostgreSQL handles this

PostgreSQL does not have a traditional clustered index in the SQL Server
sense. Every PostgreSQL table uses a heap — rows are stored in insertion
order, unordered.

However, PostgreSQL has the `CLUSTER` command which **reorders the table
rows** according to an index:

```sql
-- Reorder the users table so rows are physically sorted by first_name, last_name
CLUSTER users USING idx_users_name;
```

**The catch:** This is a **one-time reorder**. As new rows are inserted
after the CLUSTER command, they go back into insertion order. Over time
the table drifts back to being unsorted. You would need to run CLUSTER
periodically to maintain the physical order.

This is why PostgreSQL developers say: **"PostgreSQL has no clustered
indexes — only clustered tables."**

```sql
-- After clustering, verify with EXPLAIN ANALYZE
-- Range queries should be significantly faster on the clustered data
EXPLAIN ANALYZE
SELECT * FROM users
WHERE first_name BETWEEN 'Arjun' AND 'Kabir';
```

---

### Clustered vs Non-Clustered — Side by Side

| | Non-Clustered (default PostgreSQL) | Clustered (SQL Server / MySQL InnoDB) |
|---|---|---|
| Data storage | Heap — rows in insertion order | Rows physically sorted by index key |
| Index structure | Separate from table | Table IS the index |
| How many per table | Many | Only one |
| Range query speed | Good (index + heap jumps) | Excellent (sequential disk read) |
| INSERT speed | Fast (append to heap) | Slower (must insert in sorted position) |
| PostgreSQL equivalent | Default index | `CLUSTER` command (one-time reorder) |
| Maintained automatically | N/A | Yes (SQL Server) / No (PostgreSQL CLUSTER) |

---

### The practical takeaway

For PostgreSQL:
- All your indexes are non-clustered. That is fine — they are very fast.
- If you have a table where you very frequently query large date ranges
  (like log tables or time-series data), `CLUSTER` can help — but budget
  time for running it periodically.
- The performance difference between clustered and non-clustered is
  most visible on **range queries that return many rows** — not point
  lookups like our name search.

---

---

## Key Takeaways

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Without an index, PostgreSQL reads EVERY ROW               │
│     → Sequential scan, O(n), scales badly with table size      │
│                                                                 │
│  2. An index is a separate sorted data structure (B-tree)       │
│     → Lookup takes ~21 steps for 2M rows instead of 2M steps  │
│                                                                 │
│  3. The B-tree stores values in sorted order                    │
│     → Equality lookups: traverse root to leaf                  │
│     → Range lookups: traverse to start, scan along leaf level  │
│                                                                 │
│  4. All PostgreSQL indexes are non-clustered by default         │
│     → Index is separate from heap                               │
│     → A lookup fetches from index, then jumps to heap rows     │
│                                                                 │
│  5. Composite index: column order matters                       │
│     → Leading column can always be used                        │
│     → Non-leading column alone cannot use the index            │
│                                                                 │
│  6. EXPLAIN ANALYZE is your best friend                         │
│     → Seq Scan = no index (or index not helpful)               │
│     → Index Scan = index used, fetches from heap               │
│     → actual time= shows real milliseconds                     │
│     → Rows Removed by Filter = wasted work                     │
└─────────────────────────────────────────────────────────────────┘
```

### What to explore next

- **Partial indexes** — index only a subset of rows for even faster queries
- **Covering indexes (INCLUDE)** — add columns so PostgreSQL never needs to touch the heap
- **EXPLAIN ANALYZE in depth** — Bitmap scans, hash joins, nested loops
- **Index types** — Hash, GIN (for full-text and JSONB), BRIN (for huge time-series tables)


