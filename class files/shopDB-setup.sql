-- ============================================================
-- Lesson 2.2 — ShopDB Setup Script
-- Indian E-commerce Database
-- ============================================================
-- HOW TO USE:
--   1. Open pgAdmin and connect to your PostgreSQL server
--   2. Run: CREATE DATABASE shopdb;
--   3. Connect to shopdb (right-click → Query Tool)
--   4. Paste this entire file and press F5 (Run All)
--   5. You should see: CREATE TABLE x5, INSERT 0 n for each table
-- ============================================================


-- ============================================================
-- STEP 1: DROP tables if they already exist (safe re-run)
-- Drop in reverse dependency order: children before parents
-- ============================================================

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS customers;


-- ============================================================
-- STEP 2: CREATE tables
-- ============================================================

CREATE TABLE customers (
    id          SERIAL          PRIMARY KEY,
    name        VARCHAR(100)    NOT NULL,
    email       VARCHAR(150)    NOT NULL UNIQUE,
    city        VARCHAR(50)     NOT NULL,
    state       VARCHAR(50)     NOT NULL,
    joined_on   DATE            NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE categories (
    id          SERIAL          PRIMARY KEY,
    name        VARCHAR(50)     NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE products (
    id              SERIAL          PRIMARY KEY,
    name            VARCHAR(150)    NOT NULL,
    category_id     INT             NOT NULL REFERENCES categories(id),
    price_inr       NUMERIC(10,2)   NOT NULL CHECK (price_inr > 0),
    stock_quantity  INT             NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    is_available    BOOLEAN         NOT NULL DEFAULT TRUE
);

CREATE TABLE orders (
    id              SERIAL          PRIMARY KEY,
    customer_id     INT             NOT NULL REFERENCES customers(id),
    order_date      DATE            NOT NULL DEFAULT CURRENT_DATE,
    status          VARCHAR(20)     NOT NULL DEFAULT 'Pending'
                                    CHECK (status IN ('Pending','Shipped','Delivered','Cancelled')),
    payment_method  VARCHAR(20)     NOT NULL
                                    CHECK (payment_method IN ('UPI','Card','COD','NetBanking'))
);

CREATE TABLE order_items (
    id          SERIAL          PRIMARY KEY,
    order_id    INT             NOT NULL REFERENCES orders(id),
    product_id  INT             NOT NULL REFERENCES products(id),
    quantity    INT             NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10,2)   NOT NULL CHECK (unit_price > 0)
    -- unit_price is snapshotted at time of order
    -- so price changes don't affect historical orders
);


-- ============================================================
-- STEP 3: INSERT data
-- ============================================================

-- 20 customers from across India
INSERT INTO customers (name, email, city, state, joined_on) VALUES
('Aarav Mehta',        'aarav.mehta@gmail.com',      'Mumbai',      'Maharashtra',  '2023-01-15'),
('Diya Sharma',        'diya.sharma@gmail.com',       'Delhi',       'Delhi',        '2023-02-20'),
('Rohan Iyer',         'rohan.iyer@gmail.com',        'Bengaluru',   'Karnataka',    '2023-03-10'),
('Priya Patel',        'priya.patel@gmail.com',       'Ahmedabad',   'Gujarat',      '2023-03-25'),
('Kabir Singh',        'kabir.singh@gmail.com',       'Chandigarh',  'Punjab',       '2023-04-05'),
('Ananya Nair',        'ananya.nair@gmail.com',       'Kochi',       'Kerala',       '2023-04-18'),
('Vikram Rao',         'vikram.rao@gmail.com',        'Hyderabad',   'Telangana',    '2023-05-02'),
('Sneha Joshi',        'sneha.joshi@gmail.com',       'Pune',        'Maharashtra',  '2023-05-14'),
('Arjun Reddy',        'arjun.reddy@gmail.com',       'Chennai',     'Tamil Nadu',   '2023-06-01'),
('Meera Gupta',        'meera.gupta@gmail.com',       'Lucknow',     'Uttar Pradesh','2023-06-20'),
('Ravi Kumar',         'ravi.kumar@gmail.com',        'Patna',       'Bihar',        '2023-07-08'),
('Ishaan Verma',       'ishaan.verma@gmail.com',      'Jaipur',      'Rajasthan',    '2023-07-22'),
('Kavya Pillai',       'kavya.pillai@gmail.com',      'Thiruvananthapuram','Kerala', '2023-08-05'),
('Aditya Banerjee',    'aditya.banerjee@gmail.com',   'Kolkata',     'West Bengal',  '2023-08-19'),
('Pooja Desai',        'pooja.desai@gmail.com',       'Surat',       'Gujarat',      '2023-09-03'),
('Nikhil Mishra',      'nikhil.mishra@gmail.com',     'Bhopal',      'Madhya Pradesh','2023-09-17'),
('Shreya Kapoor',      'shreya.kapoor@gmail.com',     'Delhi',       'Delhi',        '2023-10-01'),
('Rahul Nair',         'rahul.nair@gmail.com',        'Mangalore',   'Karnataka',    '2023-10-15'),
('Tanvi Shah',         'tanvi.shah@gmail.com',        'Vadodara',    'Gujarat',      '2023-11-02'),
('Harsh Tiwari',       'harsh.tiwari@gmail.com',      'Varanasi',    'Uttar Pradesh','2023-11-20');


-- 6 categories
INSERT INTO categories (name, description) VALUES
('Electronics',   'Phones, laptops, tablets, accessories'),
('Clothing',      'Men and women traditional and western wear'),
('Books',         'Fiction, non-fiction, textbooks, guides'),
('Home & Kitchen','Appliances, cookware, decor'),
('Sports',        'Cricket, football, fitness equipment'),
('Beauty',        'Skincare, haircare, personal care products');


-- 25 products
INSERT INTO products (name, category_id, price_inr, stock_quantity, is_available) VALUES
-- Electronics (category 1)
('Samsung Galaxy S23',          1, 74999.00,  30, TRUE),
('Apple iPhone 15',             1, 79999.00,  20, TRUE),
('OnePlus Nord CE 3',           1, 24999.00,  50, TRUE),
('boAt Rockerz 450 Headphones', 1,  1499.00, 200, TRUE),
('Lenovo IdeaPad Slim 3',       1, 45999.00,  15, TRUE),
('Mi Smart TV 43 inch',         1, 28999.00,  25, TRUE),

-- Clothing (category 2)
('Fabindia Kurta Set',          2,  2499.00, 100, TRUE),
('Raymond Suit Length',         2,  5999.00,  40, TRUE),
('Biba Anarkali Dress',         2,  3299.00,  60, TRUE),
('Allen Solly Formal Shirt',    2,  1799.00, 150, TRUE),

-- Books (category 3)
('The White Tiger - Aravind Adiga', 3,  299.00, 500, TRUE),
('Wings of Fire - APJ Abdul Kalam', 3,  199.00, 800, TRUE),
('Ikigai',                          3,  350.00, 400, TRUE),
('RD Sharma Class 12 Maths',        3,  650.00, 300, TRUE),

-- Home & Kitchen (category 4)
('Prestige Pressure Cooker 5L', 4,  2199.00,  80, TRUE),
('Bajaj Mixer Grinder 500W',    4,  2999.00,  60, TRUE),
('Milton Thermosteel Flask 1L', 4,   799.00, 250, TRUE),
('Cello Mattress Single',       4, 12999.00,  10, TRUE),

-- Sports (category 5)
('SG Cricket Bat English Willow', 5, 3499.00,  45, TRUE),
('Nivia Football',                5,  799.00, 120, TRUE),
('Cosco Badminton Racket Set',    5,  999.00,  90, TRUE),
('Boldfit Resistance Bands Set',  5,  699.00, 180, TRUE),

-- Beauty (category 6)
('Himalaya Face Wash 200ml',      6,  149.00, 600, TRUE),
('Mamaearth Vitamin C Serum',     6,  599.00, 300, TRUE),
('Biotique Bio Sunscreen SPF 50', 6,  299.00,  0,  FALSE); -- out of stock


-- 15 orders
INSERT INTO orders (customer_id, order_date, status, payment_method) VALUES
( 1, '2024-01-05', 'Delivered',  'UPI'),
( 3, '2024-01-12', 'Delivered',  'Card'),
( 5, '2024-01-18', 'Delivered',  'COD'),
( 2, '2024-02-02', 'Delivered',  'UPI'),
( 7, '2024-02-14', 'Delivered',  'NetBanking'),
( 4, '2024-02-28', 'Delivered',  'UPI'),
( 9, '2024-03-07', 'Shipped',    'Card'),
(12, '2024-03-15', 'Delivered',  'UPI'),
( 6, '2024-03-22', 'Cancelled',  'COD'),
(15, '2024-04-03', 'Delivered',  'UPI'),
( 8, '2024-04-10', 'Shipped',    'Card'),
(17, '2024-04-18', 'Pending',    'UPI'),
(10, '2024-05-02', 'Delivered',  'NetBanking'),
( 1, '2024-05-15', 'Delivered',  'UPI'),     -- Aarav orders again
(20, '2024-05-28', 'Pending',    'COD');


-- 30 order items (2-3 items per order)
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
-- Order 1 (Aarav, Jan)
(1,  1, 1, 74999.00),   -- Samsung Galaxy S23
(1,  4, 2,  1499.00),   -- boAt Headphones x2

-- Order 2 (Rohan, Jan)
(2, 11, 1,   299.00),   -- The White Tiger
(2, 12, 1,   199.00),   -- Wings of Fire
(2, 13, 2,   350.00),   -- Ikigai x2

-- Order 3 (Kabir, Jan)
(3, 19, 1,  3499.00),   -- SG Cricket Bat
(3, 20, 1,   799.00),   -- Nivia Football

-- Order 4 (Diya, Feb)
(4,  9, 1,  3299.00),   -- Biba Dress
(4,  7, 2,  2499.00),   -- Fabindia Kurta x2

-- Order 5 (Vikram, Feb)
(5,  5, 1, 45999.00),   -- Lenovo IdeaPad
(5,  4, 1,  1499.00),   -- boAt Headphones

-- Order 6 (Priya, Feb)
(6, 15, 1,  2199.00),   -- Pressure Cooker
(6, 16, 1,  2999.00),   -- Mixer Grinder
(6, 17, 2,   799.00),   -- Flask x2

-- Order 7 (Arjun, Mar)
(7,  2, 1, 79999.00),   -- iPhone 15
(7, 23, 1,   149.00),   -- Himalaya Face Wash

-- Order 8 (Ishaan, Mar)
(8, 14, 2,   650.00),   -- RD Sharma Maths x2
(8, 12, 3,   199.00),   -- Wings of Fire x3

-- Order 9 (Ananya, Mar — CANCELLED)
(9, 24, 1,   599.00),   -- Serum (cancelled)

-- Order 10 (Pooja, Apr)
(10, 21, 1,  999.00),   -- Badminton Racket
(10, 22, 1,  699.00),   -- Resistance Bands
(10, 20, 2,  799.00),   -- Football x2

-- Order 11 (Sneha, Apr)
(11,  6, 1, 28999.00),  -- Mi Smart TV
(11, 17, 1,   799.00),  -- Flask

-- Order 12 (Shreya, Apr)
(12,  3, 1, 24999.00),  -- OnePlus Nord
(12, 10, 2,  1799.00),  -- Allen Solly Shirt x2

-- Order 13 (Meera, May)
(13, 18, 1, 12999.00),  -- Cello Mattress
(13, 15, 1,  2199.00),  -- Pressure Cooker

-- Order 14 (Aarav again, May)
(14,  8, 1,  5999.00),  -- Raymond Suit
(14, 25, 1,   299.00),  -- Biotique Sunscreen

-- Order 15 (Harsh, May)
(15, 13, 1,   350.00),  -- Ikigai
(15, 23, 2,   149.00);  -- Himalaya Face Wash x2


-- ============================================================
-- VERIFY: Run these to confirm data loaded correctly
-- ============================================================

SELECT 'customers'  AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'categories',                COUNT(*)               FROM categories
UNION ALL
SELECT 'products',                  COUNT(*)               FROM products
UNION ALL
SELECT 'orders',                    COUNT(*)               FROM orders
UNION ALL
SELECT 'order_items',               COUNT(*)               FROM order_items;

-- Expected output:
--  table_name  | row_count
-- -------------+-----------
--  customers   |        20
--  categories  |         6
--  products    |        25
--  orders      |        15
--  order_items |        30
