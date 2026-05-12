#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mobile App Analytics Pipeline - Data Cleaning Layer (Bronze -> Silver)
Handles: duplicates, null values, format inconsistencies, invalid data
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCleaner:
    """Cleans mobile app event data"""
    
    def __init__(self, raw_data_dir="data/raw", processed_data_dir="data/processed"):
        self.raw_dir = Path(raw_data_dir)
        self.processed_dir = Path(processed_data_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.users_df = None
        self.features_df = None
    
    def load_users(self):
        """Load user master data"""
        logger.info("Loading users.json...")
        with open(self.raw_dir / "users.json", encoding='utf-8') as f:
            users = json.load(f)
        self.users_df = pd.DataFrame(users)
        logger.info(f"Loaded {len(self.users_df)} users")
        return self.users_df
    
    def load_features(self):
        """Load features master data"""
        logger.info("Loading features.json...")
        with open(self.raw_dir / "features.json", encoding='utf-8') as f:
            features = json.load(f)
        self.features_df = pd.DataFrame(features)
        logger.info(f"Loaded {len(self.features_df)} features")
        return self.features_df
    
    def load_events(self):
        """Load events from JSONL file"""
        logger.info("Loading events.jsonl...")
        events = []
        with open(self.raw_dir / "events.jsonl", encoding='utf-8') as f:
            for line in f:
                events.append(json.loads(line))
        df = pd.DataFrame(events)
        logger.info(f"Loaded {len(df)} raw events")
        return df
    
    def clean_timestamps(self, df):
        """
        Clean and standardize timestamp formats
        Handles: ISO format, MM/DD/YYYY, invalid formats
        """
        logger.info("Cleaning timestamps...")
        initial_count = len(df)
        
        def parse_timestamp(ts):
            if pd.isna(ts) or ts == '':
                return pd.NaT
            try:
                return pd.to_datetime(ts, format='ISO8601')
            except Exception:
                try:
                    return pd.to_datetime(ts)
                except Exception:
                    return pd.NaT
        
        df = df.copy()
        df['timestamp'] = df['timestamp'].apply(parse_timestamp)
        
        # Remove invalid timestamps
        df = df[df['timestamp'].notna()]
        
        # Remove future dates (data quality issue)
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        df = df[df['timestamp'] <= pd.Timestamp.now(tz='UTC')]
        
        removed = initial_count - len(df)
        logger.info(f"Cleaned timestamps: removed {removed} invalid records")
        return df
    
    def standardize_ids(self, df):
        """Standardize user_id, event_id formats"""
        logger.info("Standardizing IDs...")
        initial_count = len(df)
        
        df = df.copy()
        # Standardize user_id to USER_XXX format
        df['user_id'] = df['user_id'].str.upper().str.strip()
        df['user_id'] = df['user_id'].replace('', np.nan)
        
        # Remove rows with missing user_id
        df = df[df['user_id'].notna()]
        
        # Ensure user_id matches pattern USER_XXX (remove if not)
        df = df[df['user_id'].str.match(r'^USER_\d+$', na=False)]
        
        removed = initial_count - len(df)
        logger.info(f"Standardized IDs: removed {removed} invalid records")
        return df
    
    def clean_event_types(self, df):
        """Clean event_type field"""
        logger.info("Cleaning event types...")
        initial_count = len(df)
        
        df = df.copy()
        # Remove empty event_types
        df = df[df['event_type'].notna()]
        df = df[df['event_type'] != '']
        
        # Standardize to lowercase
        df['event_type'] = df['event_type'].str.lower().str.strip()
        
        removed = initial_count - len(df)
        logger.info(f"Cleaned event types: removed {removed} invalid records")
        return df
    
    def clean_os(self, df):
        """Clean operating system field"""
        logger.info("Cleaning OS field...")
        initial_count = len(df)
        
        valid_os = ['iOS', 'Android', 'Web']
        df = df[df['os'].isin(valid_os)]
        
        removed = initial_count - len(df)
        logger.info(f"Cleaned OS: removed {removed} invalid records")
        return df
    
    def clean_country(self, df):
        """Clean country codes"""
        logger.info("Cleaning country codes...")
        initial_count = len(df)
        
        valid_countries = ['ID', 'SG', 'MY', 'TH', 'PH', 'VN']
        df = df[df['country'].isin(valid_countries)]
        
        removed = initial_count - len(df)
        logger.info(f"Cleaned country: removed {removed} invalid records")
        return df
    
    def clean_app_version(self, df):
        """Clean app version format (should be X.Y.Z)"""
        logger.info("Cleaning app_version...")
        initial_count = len(df)
        
        # Check if version matches X.Y.Z pattern
        df = df[df['app_version'].str.match(r'^\d+\.\d+\.\d+$', na=False)]
        
        removed = initial_count - len(df)
        logger.info(f"Cleaned app_version: removed {removed} invalid records")
        return df
    
    def clean_properties(self, df):
        """Clean event properties (amounts should be positive)"""
        logger.info("Cleaning event properties...")
        initial_count = len(df)
        
        def check_properties(props):
            if not isinstance(props, dict):
                return False
            if 'amount' in props:
                try:
                    amount = float(props['amount'])
                    return amount > 0
                except Exception:
                    return False
            return True
        
        df = df[df['properties'].apply(check_properties)]
        
        removed = initial_count - len(df)
        logger.info(f"Cleaned properties: removed {removed} invalid records")
        return df
    
    def remove_duplicates(self, df):
        """Remove duplicate events"""
        logger.info("Removing duplicates...")
        initial_count = len(df)
        
        # Duplicates: same event_id + user_id + timestamp
        df = df.drop_duplicates(subset=['event_id', 'user_id', 'timestamp'], keep='first')
        
        removed = initial_count - len(df)
        logger.info(f"Removed {removed} duplicate events")
        return df
    
    def add_derived_columns(self, df):
        """Add useful derived columns for analytics"""
        logger.info("Adding derived columns...")
        
        df = df.copy()
        df['event_date'] = df['timestamp'].dt.date
        df['event_hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        df['week_of_year'] = df['timestamp'].dt.isocalendar().week
        df['year_month'] = df['timestamp'].dt.to_period('M')
        
        # Extract major version
        df['major_version'] = df['app_version'].str.split('.').str[0].astype(int)
        
        logger.info("Added derived columns")
        return df
    
    def save_bronze_layer(self, df):
        """Save bronze layer (raw combined data)"""
        filepath = self.processed_dir / "bronze_events.parquet"
        df.to_parquet(filepath, index=False)
        logger.info(f"Saved bronze layer: {filepath} ({len(df)} records)")
        return df
    
    def save_silver_layer(self, df):
        """Save silver layer (cleaned data)"""
        filepath = self.processed_dir / "silver_events.parquet"
        
        columns_to_keep = [
            'event_id', 'user_id', 'event_type', 'timestamp',
            'app_version', 'major_version', 'os', 'country', 'session_id',
            'properties', 'event_date', 'event_hour', 'day_of_week',
            'week_of_year', 'year_month'
        ]
        df = df[columns_to_keep]
        
        df.to_parquet(filepath, index=False)
        logger.info(f"Saved silver layer: {filepath} ({len(df)} records)")
        return df
    
    def generate_cleaning_report(self, bronze_df, silver_df):
        """Generate summary report of cleaning process"""
        print("\n" + "="*60)
        print("DATA CLEANING REPORT")
        print("="*60)
        
        initial = len(bronze_df)
        final = len(silver_df)
        removed = initial - final
        retention = (final / initial * 100) if initial > 0 else 0
        
        print(f"\nRecords Summary:")
        print(f"  Initial records (bronze):  {initial:,}")
        print(f"  Final records (silver):    {final:,}")
        print(f"  Records removed:           {removed:,}")
        print(f"  Data retention rate:       {retention:.1f}%")
        
        print(f"\nData Quality Improvements:")
        print(f"  [OK] Duplicate events removed")
        print(f"  [OK] Invalid timestamps fixed")
        print(f"  [OK] User IDs standardized")
        print(f"  [OK] Event types validated")
        print(f"  [OK] OS values validated")
        print(f"  [OK] Country codes validated")
        print(f"  [OK] App versions validated")
        print(f"  [OK] Event properties cleaned")
        
        print(f"\nNull Values (Silver Layer):")
        for col in silver_df.columns:
            null_count = silver_df[col].isna().sum()
            null_pct = (null_count / len(silver_df) * 100) if len(silver_df) > 0 else 0
            if null_count > 0:
                print(f"  {col}: {null_count} ({null_pct:.2f}%)")
        
        print(f"\nEvent Type Distribution:")
        event_type_counts = silver_df['event_type'].value_counts().head(10)
        for event_type, count in event_type_counts.items():
            print(f"  {event_type}: {count} ({count/len(silver_df)*100:.1f}%)")
        
        print("\n" + "="*60 + "\n")
    
    def run(self):
        """Execute complete cleaning pipeline"""
        print("\n" + "="*60)
        print("MOBILE APP ANALYTICS - DATA CLEANING PIPELINE")
        print("="*60 + "\n")
        
        # Load all data
        self.load_users()
        self.load_features()
        events_df = self.load_events()
        
        # Save bronze layer (raw combined)
        bronze_df = events_df.copy()
        self.save_bronze_layer(bronze_df)
        
        # Execute cleaning steps
        events_df = self.remove_duplicates(events_df)
        events_df = self.clean_timestamps(events_df)
        events_df = self.standardize_ids(events_df)
        events_df = self.clean_event_types(events_df)
        events_df = self.clean_os(events_df)
        events_df = self.clean_country(events_df)
        events_df = self.clean_app_version(events_df)
        events_df = self.clean_properties(events_df)
        events_df = self.add_derived_columns(events_df)
        
        # Save silver layer (cleaned)
        silver_df = self.save_silver_layer(events_df)
        
        # Generate report
        self.generate_cleaning_report(bronze_df, silver_df)
        
        return silver_df

if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaned_data = cleaner.run()