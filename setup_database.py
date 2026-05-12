#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mobile App Analytics Pipeline - Database Setup
Loads cleaned silver layer data into SQLite star schema
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_database(db_path="analytics.db"):
    """Create SQLite database with star schema"""
    logger.info(f"Creating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # ── DIMENSION TABLES ──────────────────────────────────────

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_date (
        date_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        full_date   TEXT UNIQUE NOT NULL,
        year        INTEGER,
        month       INTEGER,
        month_name  TEXT,
        day         INTEGER,
        day_of_week TEXT,
        week_of_year INTEGER,
        quarter     INTEGER,
        is_weekend  INTEGER
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_user (
        user_id           TEXT PRIMARY KEY,
        user_name         TEXT,
        email             TEXT,
        signup_date       TEXT,
        country           TEXT,
        subscription_tier TEXT,
        is_active         INTEGER DEFAULT 1
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_event_type (
        event_type_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type_name TEXT UNIQUE NOT NULL,
        category        TEXT,
        description     TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_os (
        os_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        os_name     TEXT UNIQUE NOT NULL,
        description TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_country (
        country_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        country_code TEXT UNIQUE NOT NULL,
        country_name TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_app_version (
        app_version_id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_version    TEXT UNIQUE NOT NULL,
        major_version  INTEGER,
        minor_version  INTEGER,
        patch_version  INTEGER
    )""")

    # ── FACT TABLE ────────────────────────────────────────────

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_events (
        event_id       TEXT PRIMARY KEY,
        date_id        INTEGER REFERENCES dim_date(date_id),
        user_id        TEXT    REFERENCES dim_user(user_id),
        event_type_id  INTEGER REFERENCES dim_event_type(event_type_id),
        os_id          INTEGER REFERENCES dim_os(os_id),
        country_id     INTEGER REFERENCES dim_country(country_id),
        app_version_id INTEGER REFERENCES dim_app_version(app_version_id),
        session_id     TEXT,
        event_timestamp TEXT,
        amount         REAL
    )""")

    conn.commit()
    logger.info("Schema created successfully")
    return conn

def load_dimensions(conn, df):
    """Load all dimension tables"""
    cursor = conn.cursor()

    # dim_date
    logger.info("Loading dim_date...")
    dates = df['event_date'].dropna().unique()
    for d in dates:
        import datetime
        dt = datetime.date.fromisoformat(str(d))
        cursor.execute("""
            INSERT OR IGNORE INTO dim_date
            (full_date, year, month, month_name, day, day_of_week, week_of_year, quarter, is_weekend)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(d), dt.year, dt.month,
            dt.strftime('%B'), dt.day,
            dt.strftime('%A'),
            dt.isocalendar()[1],
            (dt.month - 1) // 3 + 1,
            1 if dt.weekday() >= 5 else 0
        ))

    # dim_user
    logger.info("Loading dim_user...")
    users_path = Path("data/raw/users.json")
    with open(users_path, encoding='utf-8') as f:
        users = json.load(f)
    for u in users:
        cursor.execute("""
            INSERT OR IGNORE INTO dim_user
            (user_id, user_name, email, signup_date, country, subscription_tier)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (u['user_id'], u['user_name'], u['email'],
              u['signup_date'], u['country'], u['subscription_tier']))

    # dim_event_type
    logger.info("Loading dim_event_type...")
    event_type_map = {
        'app_open': ('Engagement', 'User opened the app'),
        'app_close': ('Engagement', 'User closed the app'),
        'screen_view': ('Engagement', 'User viewed a screen'),
        'button_click': ('Engagement', 'User clicked a button'),
        'search': ('Discovery', 'User performed a search'),
        'item_view': ('Discovery', 'User viewed an item'),
        'add_to_cart': ('Commerce', 'User added item to cart'),
        'remove_from_cart': ('Commerce', 'User removed item from cart'),
        'checkout': ('Commerce', 'User started checkout'),
        'purchase': ('Monetization', 'User completed purchase'),
        'payment_success': ('Monetization', 'Payment processed successfully'),
        'payment_failed': ('Monetization', 'Payment failed'),
        'wishlist_add': ('Engagement', 'User added to wishlist'),
        'wishlist_remove': ('Engagement', 'User removed from wishlist'),
        'review_submitted': ('Social', 'User submitted a review'),
        'rating_submitted': ('Social', 'User submitted a rating'),
        'share_clicked': ('Social', 'User shared content'),
        'download_started': ('Engagement', 'User started downloading'),
        'error': ('Technical', 'Application error occurred'),
        'crash': ('Technical', 'Application crashed')
    }
    for name, (cat, desc) in event_type_map.items():
        cursor.execute("""
            INSERT OR IGNORE INTO dim_event_type (event_type_name, category, description)
            VALUES (?, ?, ?)
        """, (name, cat, desc))

    # dim_os
    logger.info("Loading dim_os...")
    for os_name in ['iOS', 'Android', 'Web']:
        cursor.execute("INSERT OR IGNORE INTO dim_os (os_name) VALUES (?)", (os_name,))

    # dim_country
    logger.info("Loading dim_country...")
    country_map = {
        'ID': 'Indonesia', 'SG': 'Singapore', 'MY': 'Malaysia',
        'TH': 'Thailand', 'PH': 'Philippines', 'VN': 'Vietnam'
    }
    for code, name in country_map.items():
        cursor.execute("""
            INSERT OR IGNORE INTO dim_country (country_code, country_name)
            VALUES (?, ?)
        """, (code, name))

    # dim_app_version
    logger.info("Loading dim_app_version...")
    for version in df['app_version'].unique():
        parts = version.split('.')
        cursor.execute("""
            INSERT OR IGNORE INTO dim_app_version
            (app_version, major_version, minor_version, patch_version)
            VALUES (?, ?, ?, ?)
        """, (version, int(parts[0]), int(parts[1]), int(parts[2])))

    conn.commit()
    logger.info("All dimensions loaded")

def load_facts(conn, df):
    """Load fact_events table"""
    logger.info("Loading fact_events...")
    cursor = conn.cursor()

    # Build lookup dicts
    cursor.execute("SELECT full_date, date_id FROM dim_date")
    date_map = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute("SELECT event_type_name, event_type_id FROM dim_event_type")
    event_type_map = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute("SELECT os_name, os_id FROM dim_os")
    os_map = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute("SELECT country_code, country_id FROM dim_country")
    country_map = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute("SELECT app_version, app_version_id FROM dim_app_version")
    version_map = {r[0]: r[1] for r in cursor.fetchall()}

    # Insert facts
    inserted = 0
    skipped = 0
    for _, row in df.iterrows():
        try:
            date_key = str(row['event_date'])
            amount = None
            if isinstance(row['properties'], dict) and 'amount' in row['properties']:
                try:
                    amount = float(row['properties']['amount'])
                except Exception:
                    pass

            cursor.execute("""
                INSERT OR IGNORE INTO fact_events
                (event_id, date_id, user_id, event_type_id, os_id,
                 country_id, app_version_id, session_id, event_timestamp, amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['event_id'],
                date_map.get(date_key),
                row['user_id'],
                event_type_map.get(row['event_type']),
                os_map.get(row['os']),
                country_map.get(row['country']),
                version_map.get(row['app_version']),
                row['session_id'],
                str(row['timestamp']),
                amount
            ))
            inserted += 1
        except Exception as e:
            skipped += 1

    conn.commit()
    logger.info(f"Loaded {inserted} fact records ({skipped} skipped)")

def print_summary(conn):
    """Print database summary"""
    cursor = conn.cursor()
    print("\n" + "="*60)
    print("DATABASE SUMMARY")
    print("="*60)

    tables = ['dim_date', 'dim_user', 'dim_event_type', 'dim_os',
              'dim_country', 'dim_app_version', 'fact_events']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:<25} {count:>6} rows")

    print("\n--- Sample Query: Event Type Breakdown ---")
    cursor.execute("""
        SELECT et.event_type_name, et.category, COUNT(*) as total
        FROM fact_events fe
        JOIN dim_event_type et ON fe.event_type_id = et.event_type_id
        GROUP BY et.event_type_name, et.category
        ORDER BY total DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:<25} {row[1]:<15} {row[2]} events")

    print("\n--- Sample Query: Events by Country ---")
    cursor.execute("""
        SELECT dc.country_name, COUNT(*) as total
        FROM fact_events fe
        JOIN dim_country dc ON fe.country_id = dc.country_id
        GROUP BY dc.country_name
        ORDER BY total DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]:<20} {row[1]} events")

    print("="*60 + "\n")

def main():
    print("\n" + "="*60)
    print("MOBILE APP ANALYTICS - DATABASE SETUP")
    print("="*60 + "\n")

    # Load silver layer
    logger.info("Loading silver_events.parquet...")
    df = pd.read_parquet("data/processed/silver_events.parquet")
    logger.info(f"Loaded {len(df)} records")

    # Create and populate database
    conn = create_database("analytics.db")
    load_dimensions(conn, df)
    load_facts(conn, df)
    print_summary(conn)
    conn.close()

    print("[OK] Database created: analytics.db")
    print("[OK] Star schema loaded with fact + dimension tables")
    print("[OK] Ready for SQL queries!\n")

if __name__ == "__main__":
    main()