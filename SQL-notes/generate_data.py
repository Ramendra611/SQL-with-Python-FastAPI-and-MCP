"""
generate_data.py
----------------
Generates a large CSV file of fake user records for the SQL indexing demo.

Output: users.csv (~2 million rows, ~80MB)
Columns: id, first_name, last_name, age, email, city, signup_date

Run this script once before starting the indexing guide.
It will take about 30-60 seconds depending on your machine.
"""

import csv
import random
from datetime import date, timedelta

# ── Configuration ──────────────────────────────────────────────────────────────
OUTPUT_FILE  = "users.csv"
NUM_ROWS     = 2_000_000   # 2 million rows

# Sample data pools — realistic Indian names and cities
FIRST_NAMES = [
    "Arjun", "Priya", "Rohit", "Sneha", "Kabir", "Meera", "Vikram", "Ananya",
    "Aditya", "Kavya", "Harsh", "Pooja", "Rahul", "Divya", "Nikhil", "Shreya",
    "Tanvi", "Ishaan", "Riya", "Karan", "Neha", "Varun", "Simran", "Aarav",
    "Diya", "Siddharth", "Anjali", "Manish", "Swati", "Rajesh", "Sunita",
    "Amit", "Nisha", "Suresh", "Geeta", "Deepak", "Rekha", "Vijay", "Usha"
]

LAST_NAMES = [
    "Sharma", "Verma", "Iyer", "Nair", "Singh", "Patel", "Mehta", "Gupta",
    "Reddy", "Pillai", "Rao", "Joshi", "Mishra", "Tiwari", "Banerjee",
    "Chakraborty", "Desai", "Shah", "Kapoor", "Malhotra", "Kulkarni",
    "Bhat", "Shetty", "Menon", "Naidu", "Agarwal", "Saxena", "Pandey",
    "Chaudhary", "Dubey", "Tripathi", "Yadav", "Kumar", "Das", "Roy"
]

CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat",
    "Lucknow", "Kanpur", "Nagpur", "Visakhapatnam", "Indore",
    "Bhopal", "Patna", "Vadodara", "Coimbatore", "Nashik"
]

# ── Helper functions ────────────────────────────────────────────────────────────

def random_date(start_year=2018, end_year=2024):
    """Generate a random date between start_year and end_year."""
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def generate_email(first, last, uid):
    """Generate a realistic email address."""
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "mail.com"]
    pattern = random.randint(0, 3)
    if pattern == 0:
        return f"{first.lower()}.{last.lower()}{uid % 1000}@{random.choice(domains)}"
    elif pattern == 1:
        return f"{first.lower()}{uid % 10000}@{random.choice(domains)}"
    elif pattern == 2:
        return f"{last.lower()}.{first.lower()}@{random.choice(domains)}"
    else:
        return f"{first.lower()[0]}{last.lower()}{uid % 100}@{random.choice(domains)}"


# ── Main generation loop ────────────────────────────────────────────────────────

def main():
    print(f"Generating {NUM_ROWS:,} rows → {OUTPUT_FILE}")
    print("This will take about 30–60 seconds...")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(["id", "first_name", "last_name", "age", "email", "city", "signup_date"])

        # Write rows in batches (faster than row-by-row flush)
        BATCH_SIZE = 50_000
        batch = []

        for i in range(1, NUM_ROWS + 1):
            first = random.choice(FIRST_NAMES)
            last  = random.choice(LAST_NAMES)

            row = [
                i,                                          # id
                first,                                      # first_name
                last,                                       # last_name
                random.randint(18, 70),                     # age
                generate_email(first, last, i),             # email
                random.choice(CITIES),                      # city
                random_date(),                              # signup_date
            ]
            batch.append(row)

            if len(batch) == BATCH_SIZE:
                writer.writerows(batch)
                batch.clear()
                print(f"  {i:>10,} rows written...")

        # Write remaining rows
        if batch:
            writer.writerows(batch)

    print(f"\nDone! File saved as: {OUTPUT_FILE}")
    print(f"Open it in Excel or any text editor to inspect the data before loading.")


if __name__ == "__main__":
    main()
