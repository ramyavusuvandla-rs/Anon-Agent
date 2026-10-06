import sqlite3
import uuid


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return sqlite3.connect("anonsense.db")


# ============================================================
# CREATE ANONYMOUS USER TABLE
# ============================================================

def create_user_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anonymous_users (
            user_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# CREATE ANONYMOUS USER
# ============================================================

def create_anonymous_user():

    user_id = "user_" + str(uuid.uuid4())[:8]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO anonymous_users (user_id) VALUES (?)",
        (user_id,)
    )

    connection.commit()
    connection.close()

    return user_id


# ============================================================
# CREATE ACTIVITY TABLE
# ============================================================

def create_activity_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            activity TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# SAVE USER ACTIVITY
# ============================================================

def save_activity(user_id, activity):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO activities (user_id, activity)
        VALUES (?, ?)
        """,
        (user_id, activity)
    )

    connection.commit()
    connection.close()


# ============================================================
# GET ALL USER ACTIVITIES
# ============================================================

def get_user_activities(user_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT activity, timestamp
        FROM activities
        WHERE user_id = ?
        ORDER BY timestamp DESC
        """,
        (user_id,)
    )

    activities = cursor.fetchall()

    connection.close()

    return activities


# ============================================================
# GET RECENT USER ACTIVITIES
# ============================================================

def get_recent_activities(user_id, limit=10):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT activity, timestamp
        FROM activities
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_id, limit)
    )

    activities = cursor.fetchall()

    connection.close()

    return activities


# ============================================================
# GET TODAY'S ACTIVITIES
# ============================================================

def get_today_activities(user_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT activity, timestamp
        FROM activities
        WHERE user_id = ?
        AND DATE(timestamp) = DATE('now', 'localtime')
        ORDER BY timestamp DESC
        """,
        (user_id,)
    )

    activities = cursor.fetchall()

    connection.close()

    return activities


# ============================================================
# GET YESTERDAY'S ACTIVITIES
# ============================================================

def get_yesterday_activities(user_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT activity, timestamp
        FROM activities
        WHERE user_id = ?
        AND DATE(timestamp) = DATE('now', 'localtime', '-1 day')
        ORDER BY timestamp DESC
        """,
        (user_id,)
    )

    activities = cursor.fetchall()

    connection.close()

    return activities


# ============================================================
# CREATE REMINDER TABLE
# ============================================================

def create_reminder_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            task TEXT NOT NULL,
            reminder_time TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()
# ============================================================
# CALENDAR TABLE
# ============================================================

def create_calendar_table():

    import sqlite3

    conn = sqlite3.connect("anonsense.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
# ============================================================
# CREATE BUS BOOKING TABLE
# ============================================================

def create_bus_booking_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bus_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            travel_date TEXT NOT NULL,
            bus_name TEXT NOT NULL,
            departure TEXT NOT NULL,
            bus_type TEXT NOT NULL,
            price INTEGER NOT NULL,
            booking_status TEXT DEFAULT 'CONFIRMED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()
    
# ============================================================
# SAVE BUS BOOKING
# ============================================================

def save_bus_booking(
    user_id,
    source,
    destination,
    travel_date,
    bus_name,
    departure,
    bus_type,
    price
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO bus_bookings (
            user_id,
            source,
            destination,
            travel_date,
            bus_name,
            departure,
            bus_type,
            price
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            source,
            destination,
            travel_date,
            bus_name,
            departure,
            bus_type,
            price
        )
    )

    connection.commit()
    connection.close()
    
# ============================================================
# GET BUS BOOKING HISTORY
# ============================================================

def get_bus_bookings(user_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            source,
            destination,
            travel_date,
            bus_name,
            departure,
            bus_type,
            price,
            booking_status,
            created_at
        FROM bus_bookings
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    bookings = cursor.fetchall()

    connection.close()

    return bookings
# ============================================================
# SAVE REMINDER
# ============================================================

def save_reminder(user_id, task, reminder_time):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO reminders (user_id, task, reminder_time)
        VALUES (?, ?, ?)
        """,
        (user_id, task, reminder_time)
    )

    connection.commit()
    connection.close()


# ============================================================
# GET USER REMINDERS
# ============================================================

def get_user_reminders(user_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT task, reminder_time, created_at
        FROM reminders
        WHERE user_id = ?
        ORDER BY reminder_time ASC
        """,
        (user_id,)
    )

    reminders = cursor.fetchall()

    connection.close()

    return reminders



