# Mobile App Analytics Pipeline

An end-to-end data engineering pipeline for mobile app event analytics, built with Python, SQL, SQLite, and Power BI.

**Author:** Alma Nurul Salma  
**GitHub:** https://github.com/AlmaNurulSalma-dev/app-event-pipeline  
**Status:** Production Ready  
**Last Updated:** May 2026  

---

## Overview

This project demonstrates a complete data engineering pipeline that ingests messy real-world mobile app event data, cleans it, validates quality, models it into a star schema, and visualizes insights in Power BI dashboards.

### The Problem

Mobile apps generate millions of events daily, but raw data is full of problems:
- **Duplicates** from network retries
- **Missing user IDs** from app crashes
- **Invalid formats** across iOS/Android/Web
- **Inconsistent timestamps** from offline sync

This pipeline solves all of these.

---

## Architecture

```
Raw Data Sources (JSONL + JSON)
        |
        v
Bronze Layer  ->  Load + combine all sources (no transformation)
        |
        v
Silver Layer  ->  Clean, deduplicate, standardize, validate
        |
        v
Validation    ->  20+ quality rules, generate quality report
        |
        v
SQL Schema    ->  Star schema (1 fact + 6 dimension tables)
        |
        v
Power BI      ->  Engagement + Data Quality dashboards
```

---

## Actual Results

| Metric | Value |
|--------|-------|
| Raw events generated | 7,210 |
| Duplicates removed | 190 (2.6%) |
| Invalid timestamps removed | 69 (1.0%) |
| Invalid user IDs removed | 203 (2.8%) |
| Invalid OS removed | 62 (0.9%) |
| Invalid countries removed | 66 (0.9%) |
| Invalid app versions removed | 99 (1.4%) |
| Final clean records | 6,486 |
| Data retention rate | 90.0% |
| Validation rules checked | 15 |
| Validation pass rate | 93.33% |
| Star schema tables | 7 (1 fact + 6 dims) |

---

## Project Structure

```
app-event-pipeline/
|
|-- README.md
|-- requirements.txt
|-- schema.sql                     # Star schema DDL (PostgreSQL)
|-- setup_database.py              # SQLite database setup script
|
|-- sample_data_generator.py       # Generate 7,210 messy events
|-- data_cleaning.py               # Clean data (Bronze -> Silver)
|-- data_validation.py             # Validate 20+ quality rules
|
|-- data/
|   |-- raw/
|   |   |-- events.jsonl           # 7,210 raw events (messy)
|   |   |-- users.json             # 250 user profiles
|   |   |-- features.json          # 25 app features
|   |
|   |-- processed/
|   |   |-- bronze_events.parquet  # Raw combined (7,210 records)
|   |   |-- silver_events.parquet  # Cleaned data (6,486 records)
|   |   |-- silver_events.csv      # CSV export for Power BI
|   |
|   |-- validation/
|       |-- validation_report.json # Quality report (93.33% pass)
|
|-- mobile_app_analytics.pbix      # Power BI dashboard file
```

---

## Data Model (Star Schema)

### Fact Table: `fact_events`
One row = one user event

```
fact_events (6,481 rows)
|-- event_id (PK)
|-- date_id (FK -> dim_date)
|-- user_id (FK -> dim_user)
|-- event_type_id (FK -> dim_event_type)
|-- os_id (FK -> dim_os)
|-- country_id (FK -> dim_country)
|-- app_version_id (FK -> dim_app_version)
|-- session_id
|-- event_timestamp
|-- amount
```

### Dimension Tables

| Table | Rows | Purpose |
|-------|------|---------|
| `dim_date` | 15 | Time analysis (day, week, quarter) |
| `dim_user` | 250 | User profiles (tier, country, signup) |
| `dim_event_type` | 20 | Event classification (engagement, commerce) |
| `dim_os` | 3 | Platform analysis (iOS, Android, Web) |
| `dim_country` | 6 | Geographic analysis (SE Asia) |
| `dim_app_version` | 120 | App version tracking |

---

## Getting Started

### Prerequisites
- Python 3.9+
- Power BI Desktop (free)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/AlmaNurulSalma-dev/app-event-pipeline.git
cd app-event-pipeline

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate messy test data
python sample_data_generator.py

# 5. Clean the data
python data_cleaning.py

# 6. Validate data quality
python data_validation.py

# 7. Setup SQLite database
python setup_database.py
```

### Expected Output

```
Step 4 - Data Generator:
  [OK] Saved 250 users
  [OK] Saved 25 features
  [OK] Saved 7,210 events with ~721 intentional errors

Step 5 - Data Cleaning:
  Removed 190 duplicates
  Removed 69 invalid timestamps
  Removed 203 invalid user IDs
  Final: 6,486 clean records (90.0% retention)

Step 6 - Data Validation:
  15 rules checked
  14 rules passed
  Overall pass rate: 93.33%

Step 7 - Database Setup:
  dim_date:          15 rows
  dim_user:         250 rows
  dim_event_type:    20 rows
  dim_os:             3 rows
  dim_country:        6 rows
  dim_app_version:  120 rows
  fact_events:    6,481 rows
```

---

## Data Quality Rules (15 Validations)

### Completeness
- No NULLs in: event_id, user_id, event_type, timestamp

### Format
- user_id matches USER_XXX pattern
- timestamp is valid datetime
- app_version is X.Y.Z format

### Business Rules
- event_type from known set (20 types)
- OS is iOS, Android, or Web only
- country is valid 2-letter code (SE Asia)
- event_id is unique (no duplicates)
- No future timestamps
- Purchase amounts are positive

### Statistical
- Major version distribution
- OS distribution
- Event type distribution

---

## Power BI Dashboards

### Page 1: Engagement
- Events by Type (clustered column chart)
- Events by OS (pie chart — iOS 33.9%, Android 33.4%, Web 32.8%)
- Events by Country (clustered column chart — 6 SE Asian countries)

### Page 2: Data Quality
- Total Records KPI card (6,486)
- Events by Day of Week (column chart)
- Events by Major Version (column chart — v1 vs v2)
- Events by Hour of Day (line chart — 24-hour activity pattern)

---

## Technology Stack

| Layer | Tools |
|-------|-------|
| Data Generation | Python |
| Data Cleaning | Python, Pandas |
| Data Validation | Python, custom rules |
| Data Storage | Parquet, CSV, SQLite |
| Data Modeling | SQL (star schema) |
| Data Visualization | Power BI Desktop |
| Version Control | Git, GitHub |

---

## Data Quality Issues Simulated

The generator intentionally introduces realistic data problems:

| Issue | Rate | Description |
|-------|------|-------------|
| Duplicate events | ~3% | Same event sent twice (network retry) |
| Missing user ID | ~2% | App crash before ID assignment |
| Inconsistent ID format | ~2% | USER_001 vs user_001 vs USER001 |
| Future timestamps | ~1% | Clock sync issues |
| Invalid timestamp format | ~1.5% | MM/DD/YYYY instead of ISO 8601 |
| Invalid OS | ~1% | Windows/Linux instead of iOS/Android/Web |
| Invalid app version | ~1.5% | "latest" instead of X.Y.Z |
| Negative amounts | ~1% | Refund events misclassified |
| Invalid country | ~1% | US/GB instead of SE Asia codes |
| Missing event type | ~0.5% | Incomplete event tracking |

---

## FAQ

**Q: Why JSONL for events?**
Events stream continuously. JSONL (one JSON per line) is the industry standard for event data — easy to append and process line by line.

**Q: Why star schema instead of flat table?**
Storage efficiency (user info stored once, not 6,486 times), query performance (small dimension joins), and maintainability (update once, reflected everywhere).

**Q: Why SQLite instead of PostgreSQL?**
SQLite is zero-setup and built into Python — perfect for local development and portfolio projects. The same schema.sql works with PostgreSQL for production.

**Q: Why 90% retention rate?**
Real-world data is messy. A 90% retention rate after cleaning is realistic and shows the pipeline handles quality issues properly without being too aggressive.

---

## License

Open source — free to use for educational and portfolio purposes.