import sqlite3
import datetime
import random
import os

db_path = 'backend/demo.db'

# Ensure directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Drop tables if they exist to refresh
cursor.execute("DROP TABLE IF EXISTS sales;")
cursor.execute("DROP TABLE IF EXISTS users;")

# Create tables
cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    region TEXT,
    segment INTEGER,
    acquisition_cost REAL,
    signup_date DATE
);
""")

cursor.execute("""
CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    date DATE,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
""")

# Seed users
regions = ["NA", "EU", "APAC", "LATAM", "MEA"]
segments = [1, 2, 3]

users_data = []
for i in range(1, 51):
    name = f"User {i}"
    email = f"user{i}@example.com"
    region = random.choice(regions)
    segment = random.choice(segments)
    acq_cost = random.uniform(50.0, 400.0)
    # Generate date within last 365 days
    signup_date = datetime.date.today() - datetime.timedelta(days=random.randint(10, 365))
    users_data.append((name, email, region, segment, acq_cost, signup_date.isoformat()))

cursor.executemany("""
INSERT INTO users (name, email, region, segment, acquisition_cost, signup_date)
VALUES (?, ?, ?, ?, ?, ?);
""", users_data)

# Seed sales
sales_data = []
for i in range(500):
    user_id = random.randint(1, 50)
    amount = random.uniform(20.0, 500.0)
    sale_date = datetime.date.today() - datetime.timedelta(days=random.randint(0, 360))
    sales_data.append((user_id, amount, sale_date.isoformat()))

cursor.executemany("""
INSERT INTO sales (user_id, amount, date)
VALUES (?, ?, ?);
""", sales_data)

conn.commit()
print("Successfully seeded backend/demo.db with 50 users and 500 sales.")

# Verify
cursor.execute("SELECT COUNT(*) FROM users;")
print("Users count:", cursor.fetchone()[0])
cursor.execute("SELECT COUNT(*) FROM sales;")
print("Sales count:", cursor.fetchone()[0])

conn.close()
