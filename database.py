import sqlite3
from datetime import datetime, timedelta

from config import FREE_LIMIT, LIMIT_HOURS

db = sqlite3.connect("db.sqlite")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS premium (
    username TEXT PRIMARY KEY,
    until_date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS limits (
    username TEXT PRIMARY KEY,
    requests INTEGER,
    reset_time TEXT
)
""")

db.commit()

# ---------------- PREMIUM ----------------

def has_premium(username):
    cursor.execute(
        "SELECT until_date FROM premium WHERE username=?",
        (username,)
    )

    data = cursor.fetchone()

    if not data:
        return False

    until_date = datetime.fromisoformat(data[0])

    if datetime.now() > until_date:
        cursor.execute(
            "DELETE FROM premium WHERE username=?",
            (username,)
        )

        db.commit()
        return False

    return True

def get_premium_date(username):
    cursor.execute(
        "SELECT until_date FROM premium WHERE username=?",
        (username,)
    )

    data = cursor.fetchone()

    if not data:
        return "Нет"

    return data[0][:10]

def give_premium(username, days):
    until_date = datetime.now() + timedelta(days=days)

    cursor.execute("""
    INSERT OR REPLACE INTO premium
    VALUES (?, ?)
    """, (
        username,
        until_date.isoformat()
    ))

    db.commit()

# ---------------- LIMITS ----------------

def check_limit(username):
    cursor.execute("""
    SELECT requests, reset_time
    FROM limits
    WHERE username=?
    """, (username,))

    data = cursor.fetchone()

    now = datetime.now()

    if not data:
        reset = now + timedelta(hours=LIMIT_HOURS)

        cursor.execute("""
        INSERT INTO limits
        VALUES (?, ?, ?)
        """, (
            username,
            0,
            reset.isoformat()
        ))

        db.commit()

        return True

    requests, reset_time = data
    reset_time = datetime.fromisoformat(reset_time)

    if now >= reset_time:
        new_reset = now + timedelta(hours=LIMIT_HOURS)

        cursor.execute("""
        UPDATE limits
        SET requests=?, reset_time=?
        WHERE username=?
        """, (
            0,
            new_reset.isoformat(),
            username
        ))

        db.commit()

        return True

    return requests < FREE_LIMIT

def add_request(username):
    cursor.execute("""
    UPDATE limits
    SET requests = requests + 1
    WHERE username=?
    """, (username,))

    db.commit()

def remaining_requests(username):
    cursor.execute("""
    SELECT requests
    FROM limits
    WHERE username=?
    """, (username,))

    data = cursor.fetchone()

    if not data:
        return FREE_LIMIT

    return FREE_LIMIT - data[0]
