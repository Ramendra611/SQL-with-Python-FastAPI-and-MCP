-- ============================================================
-- Lesson 2.1 — CricketDB Setup Script
-- Indian Cricket Players, Matches & Performances
-- ============================================================
-- HOW TO USE:
--   1. Open pgAdmin and connect to your PostgreSQL server
--   2. Run: CREATE DATABASE cricketdb;
--   3. Connect to cricketdb (right-click → Query Tool)
--   4. Paste this entire file and press F5 (Run All)
--   5. Verify with the check query at the bottom
-- ============================================================


-- ============================================================
-- STEP 1: DROP tables (safe re-run, child before parent)
-- ============================================================

DROP TABLE IF EXISTS performances;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS players;


-- ============================================================
-- STEP 2: CREATE tables
-- ============================================================

CREATE TABLE players (
    id              SERIAL          PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    role            VARCHAR(20)     NOT NULL
                                    CHECK (role IN ('Batsman', 'Bowler', 'All-rounder', 'Wicket-keeper')),
    batting_style   VARCHAR(20)     NOT NULL
                                    CHECK (batting_style IN ('Right-hand', 'Left-hand')),
    bowling_style   VARCHAR(30),    -- NULL for pure batsmen and wicket-keepers
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE
);

CREATE TABLE matches (
    id          SERIAL          PRIMARY KEY,
    opponent    VARCHAR(60)     NOT NULL,
    venue       VARCHAR(80)     NOT NULL,
    format      VARCHAR(10)     NOT NULL
                                CHECK (format IN ('Test', 'ODI', 'T20')),
    match_date  DATE            NOT NULL,
    result      VARCHAR(10)     NOT NULL
                                CHECK (result IN ('Won', 'Lost', 'Draw', 'No Result'))
);

CREATE TABLE performances (
    id              SERIAL  PRIMARY KEY,
    match_id        INT     NOT NULL REFERENCES matches(id)  ON DELETE CASCADE,
    player_id       INT     NOT NULL REFERENCES players(id)  ON DELETE CASCADE,
    runs            INT     NOT NULL DEFAULT 0 CHECK (runs >= 0),
    wickets         INT     NOT NULL DEFAULT 0 CHECK (wickets >= 0),
    catches         INT     NOT NULL DEFAULT 0 CHECK (catches >= 0),
    UNIQUE (match_id, player_id)   -- one performance row per player per match
);


-- ============================================================
-- STEP 3: INSERT data
-- ============================================================

-- 15 players (all-time Indian greats + current stars)
INSERT INTO players (name, role, batting_style, bowling_style, is_active) VALUES
('Virat Kohli',         'Batsman',          'Right-hand', NULL,                   TRUE),
('Rohit Sharma',        'Batsman',          'Right-hand', NULL,                   TRUE),
('Jasprit Bumrah',      'Bowler',           'Right-hand', 'Right-arm Fast',       TRUE),
('Ravindra Jadeja',     'All-rounder',      'Left-hand',  'Left-arm Spin',        TRUE),
('Ravichandran Ashwin', 'All-rounder',      'Right-hand', 'Right-arm Off-spin',   TRUE),
('MS Dhoni',            'Wicket-keeper',    'Right-hand', NULL,                   FALSE),
('Sachin Tendulkar',    'Batsman',          'Right-hand', 'Right-arm Medium',     FALSE),
('Anil Kumble',         'Bowler',           'Right-hand', 'Right-arm Leg-spin',   FALSE),
('Shikhar Dhawan',      'Batsman',          'Left-hand',  NULL,                   FALSE),
('Hardik Pandya',       'All-rounder',      'Right-hand', 'Right-arm Fast-medium',TRUE),
('KL Rahul',            'Batsman',          'Right-hand', NULL,                   TRUE),
('Mohammed Shami',      'Bowler',           'Right-hand', 'Right-arm Fast',       TRUE),
('Suryakumar Yadav',    'Batsman',          'Right-hand', NULL,                   TRUE),
('Yuzvendra Chahal',    'Bowler',           'Right-hand', 'Right-arm Leg-spin',   TRUE),
('Shreyas Iyer',        'Batsman',          'Right-hand', NULL,                   TRUE);


-- 8 matches across three formats and multiple opponents
INSERT INTO matches (opponent, venue, format, match_date, result) VALUES
('Australia',   'Melbourne Cricket Ground, Melbourne',  'Test',  '2024-01-05',  'Won'),
('England',     'Narendra Modi Stadium, Ahmedabad',     'Test',  '2024-02-15',  'Won'),
('Pakistan',    'Nassau County International, New York','T20',   '2024-06-09',  'Won'),
('Australia',   'MA Chidambaram Stadium, Chennai',      'ODI',   '2023-10-08',  'Won'),
('South Africa','Eden Gardens, Kolkata',                'T20',   '2024-06-15',  'Lost'),
('New Zealand', 'Wankhede Stadium, Mumbai',             'ODI',   '2023-11-22',  'Won'),
('England',     'Edgbaston, Birmingham',                'Test',  '2022-07-01',  'Lost'),
('West Indies', 'Rajiv Gandhi International, Hyderabad','T20',   '2024-02-02',  'Won');


-- 30 performances — each row is one player in one match
INSERT INTO performances (match_id, player_id, runs, wickets, catches) VALUES
-- Match 1: Test vs Australia at MCG (Won)
(1,  1,  76, 0, 1),   -- Kohli: 76 runs
(1,  2,  52, 0, 0),   -- Rohit: 52 runs
(1,  3,   8, 5, 0),   -- Bumrah: 5 wickets
(1,  4,  31, 2, 1),   -- Jadeja: 31 runs + 2 wickets
(1,  5,  12, 3, 0),   -- Ashwin: 3 wickets

-- Match 2: Test vs England in Ahmedabad (Won)
(2,  1, 121, 0, 0),   -- Kohli: 121 runs (century)
(2,  5,  22, 5, 1),   -- Ashwin: 5 wickets
(2,  4,  48, 3, 2),   -- Jadeja: 48 runs + 3 wickets
(2,  3,   4, 3, 0),   -- Bumrah: 3 wickets
(2, 15,  64, 0, 0),   -- Shreyas: 64 runs

-- Match 3: T20 vs Pakistan in New York (Won)
(3,  2,  57, 0, 0),   -- Rohit: 57 runs
(3, 13,  44, 0, 1),   -- Surya: 44 runs
(3,  3,   2, 2, 0),   -- Bumrah: 2 wickets
(3, 14,   0, 2, 1),   -- Chahal: 2 wickets
(3, 10,  27, 1, 0),   -- Pandya: 27 runs + 1 wicket

-- Match 4: ODI vs Australia in Chennai (Won)
(4,  2, 119, 0, 0),   -- Rohit: 119 runs (century)
(4,  1,  85, 0, 0),   -- Kohli: 85 runs
(4, 12,   5, 3, 0),   -- Shami: 3 wickets
(4, 10,  35, 2, 1),   -- Pandya: 35 runs + 2 wickets
(4, 11,  62, 0, 0),   -- KL Rahul: 62 runs

-- Match 5: T20 vs South Africa in Kolkata (Lost)
(5,  1,  23, 0, 0),   -- Kohli: 23 runs
(5,  2,  15, 0, 0),   -- Rohit: 15 runs
(5,  3,   0, 1, 0),   -- Bumrah: 1 wicket
(5, 14,   0, 1, 0),   -- Chahal: 1 wicket
(5, 13,  41, 0, 1),   -- Surya: 41 runs

-- Match 6: ODI vs New Zealand in Mumbai (Won)
(6, 11,  97, 0, 2),   -- KL Rahul: 97 runs
(6,  4,  55, 2, 0),   -- Jadeja: 55 runs + 2 wickets
(6, 12,   8, 4, 0),   -- Shami: 4 wickets
(6,  1,  72, 0, 0),   -- Kohli: 72 runs

-- Match 7: Test vs England at Edgbaston (Lost)
(7,  1,  11, 0, 0),   -- Kohli: 11 runs (famous duck series)
(7,  5,  14, 2, 0);   -- Ashwin: 2 wickets


-- ============================================================
-- VERIFY: Run this to confirm everything loaded correctly
-- ============================================================

SELECT 'players'      AS table_name, COUNT(*) AS row_count FROM players
UNION ALL
SELECT 'matches',                    COUNT(*)               FROM matches
UNION ALL
SELECT 'performances',               COUNT(*)               FROM performances;

-- Expected:
--  table_name   | row_count
-- --------------+-----------
--  players      |        15
--  matches      |         8
--  performances |        30
