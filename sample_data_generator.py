#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mobile App Analytics Pipeline - Data Generator
Generates realistic but messy mobile app event data with intentional quality issues
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Set random seed for reproducibility
random.seed(42)

def generate_users(num_users=250):
    """Generate user master data with realistic information"""
    countries = ['ID', 'SG', 'MY', 'TH', 'PH', 'VN']
    devices = ['iOS', 'Android']
    tiers = ['free', 'basic', 'premium']
    
    users = []
    base_date = datetime(2023, 1, 1)
    
    for i in range(1, num_users + 1):
        user_id = f"USER_{i:03d}"
        signup_date = base_date + timedelta(days=random.randint(0, 365))
        
        users.append({
            "user_id": user_id,
            "user_name": f"User{i}",
            "email": f"user{i}@example.com",
            "signup_date": signup_date.strftime('%Y-%m-%d'),
            "country": random.choice(countries),
            "device_type": random.choice(devices),
            "subscription_tier": random.choice(tiers)
        })
    
    return users

def generate_features(num_features=25):
    """Generate feature catalog"""
    categories = ['Discovery', 'Engagement', 'Monetization', 'Social', 'Settings']
    features = []
    base_date = datetime(2023, 1, 1)
    
    feature_names = [
        'Search', 'Browse', 'Wishlist', 'Checkout', 'Payment',
        'Share', 'Review', 'Rating', 'Recommendation', 'Cart',
        'Profile', 'Settings', 'Notification', 'Filter', 'Sort',
        'Download', 'Upload', 'Bookmark', 'Subscribe', 'Unsubscribe',
        'Login', 'Logout', 'Register', 'Password Reset', 'Two Factor'
    ]
    
    for i, feature_name in enumerate(feature_names[:num_features]):
        feature_id = f"FEAT_{i+1:02d}"
        launch_date = base_date + timedelta(days=random.randint(0, 300))
        
        features.append({
            "feature_id": feature_id,
            "feature_name": feature_name,
            "category": random.choice(categories),
            "launch_date": launch_date.strftime('%Y-%m-%d')
        })
    
    return features

def generate_events(num_events=7000, users=None):
    """
    Generate mobile app events with intentional messiness
    Includes: duplicates, missing values, invalid formats, future dates, etc.
    """
    if users is None:
        users = generate_users()
    
    user_ids = [u['user_id'] for u in users]
    event_types = [
        'app_open', 'app_close', 'screen_view', 'button_click',
        'search', 'item_view', 'add_to_cart', 'remove_from_cart',
        'checkout', 'purchase', 'payment_success', 'payment_failed',
        'wishlist_add', 'wishlist_remove', 'review_submitted', 'rating_submitted',
        'share_clicked', 'download_started', 'error', 'crash'
    ]
    
    os_list = ['iOS', 'Android', 'Web']
    valid_countries = ['ID', 'SG', 'MY', 'TH', 'PH', 'VN']
    
    events = []
    base_date = datetime(2024, 1, 1)
    event_id_counter = 1
    
    for _ in range(num_events):
        timestamp = base_date + timedelta(
            days=random.randint(0, 14),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        
        user_id = random.choice(user_ids)
        event_type = random.choice(event_types)
        session_id = f"SESSION_{random.randint(1000, 9999)}"
        app_version = f"{random.randint(1, 2)}.{random.randint(0, 5)}.{random.randint(0, 9)}"
        os = random.choice(os_list)
        country = random.choice(valid_countries)
        
        event = {
            "event_id": f"EVT_{event_id_counter:06d}",
            "user_id": user_id,
            "event_type": event_type,
            "timestamp": timestamp.isoformat() + "Z",
            "app_version": app_version,
            "os": os,
            "country": country,
            "session_id": session_id,
            "properties": {}
        }
        
        # Add properties based on event type
        if event_type == 'purchase':
            event["properties"] = {
                "item_id": f"ITEM_{random.randint(100, 999)}",
                "amount": round(random.uniform(10, 500), 2)
            }
        elif event_type == 'item_view':
            event["properties"] = {
                "item_id": f"ITEM_{random.randint(100, 999)}"
            }
        elif event_type == 'screen_view':
            event["properties"] = {
                "screen_name": random.choice(['home', 'search', 'product', 'cart', 'checkout'])
            }
        elif event_type == 'search':
            event["properties"] = {
                "query": f"search_term_{random.randint(1, 100)}"
            }
        
        events.append(event)
        event_id_counter += 1
    
    # ===== INTENTIONAL MESSINESS =====
    
    # 1. Add duplicate events (same event_id, same timestamp)
    num_duplicates = int(num_events * 0.03)
    for i in range(num_duplicates):
        events.append(events[i].copy())
    
    # 2. Add events with missing user_id
    num_missing_user = int(num_events * 0.02)
    for i in range(num_missing_user):
        events[random.randint(0, len(events)-1)]["user_id"] = ""
    
    # 3. Add events with inconsistent user_id format
    num_inconsistent_user = int(num_events * 0.02)
    for i in range(num_inconsistent_user):
        event = events[random.randint(0, len(events)-1)]
        if event["user_id"]:
            if random.choice([True, False]):
                event["user_id"] = event["user_id"].lower()
            else:
                event["user_id"] = event["user_id"].replace("_", "")
    
    # 4. Add events with future timestamps
    num_future = int(num_events * 0.01)
    for i in range(num_future):
        future_date = datetime.now() + timedelta(days=random.randint(1, 30))
        events[random.randint(0, len(events)-1)]["timestamp"] = future_date.isoformat() + "Z"
    
    # 5. Add events with invalid timestamp format
    num_bad_timestamp = int(num_events * 0.015)
    for i in range(num_bad_timestamp):
        event = events[random.randint(0, len(events)-1)]
        event["timestamp"] = "01/15/2024 10:30:00"
    
    # 6. Add events with invalid OS
    num_bad_os = int(num_events * 0.01)
    for i in range(num_bad_os):
        events[random.randint(0, len(events)-1)]["os"] = random.choice(['Windows', 'Linux', 'Unknown'])
    
    # 7. Add events with invalid app_version format
    num_bad_version = int(num_events * 0.015)
    for i in range(num_bad_version):
        event = events[random.randint(0, len(events)-1)]
        event["app_version"] = random.choice(['1.2', '2', 'latest', '1.2.3.4'])
    
    # 8. Add events with negative amounts
    num_negative_amounts = int(num_events * 0.01)
    for i in range(num_negative_amounts):
        event = events[random.randint(0, len(events)-1)]
        if "properties" in event and "amount" in event["properties"]:
            event["properties"]["amount"] = -abs(event["properties"]["amount"])
    
    # 9. Add invalid country codes
    num_bad_country = int(num_events * 0.01)
    for i in range(num_bad_country):
        events[random.randint(0, len(events)-1)]["country"] = random.choice(['XX', 'ZZ', 'US', 'GB'])
    
    # 10. Add missing event_type
    num_missing_type = int(num_events * 0.005)
    for i in range(num_missing_type):
        events[random.randint(0, len(events)-1)]["event_type"] = ""
    
    return events

def save_events_jsonl(events, filepath):
    """Save events as JSONL (JSON Lines format)"""
    with open(filepath, 'w', encoding='utf-8') as f:
        for event in events:
            f.write(json.dumps(event) + '\n')
    print(f"[OK] Saved {len(events)} events to {filepath}")

def save_users_json(users, filepath):
    """Save users as JSON array"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2)
    print(f"[OK] Saved {len(users)} users to {filepath}")

def save_features_json(features, filepath):
    """Save features as JSON array"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(features, f, indent=2)
    print(f"[OK] Saved {len(features)} features to {filepath}")

def main():
    """Main function to generate all data"""
    print("\n" + "="*60)
    print("Mobile App Analytics Pipeline - Data Generator")
    print("="*60 + "\n")
    
    # Create data directory
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating data sources...\n")
    
    # Generate users
    print("1. Generating users...")
    users = generate_users(num_users=250)
    save_users_json(users, data_dir / "users.json")
    
    # Generate features
    print("2. Generating features...")
    features = generate_features(num_features=25)
    save_features_json(features, data_dir / "features.json")
    
    # Generate events
    print("3. Generating events (with intentional messiness)...")
    events = generate_events(num_events=7000, users=users)
    save_events_jsonl(events, data_dir / "events.jsonl")
    
    print("\n" + "="*60)
    print("Data Generation Summary:")
    print("="*60)
    print(f"Users: {len(users)}")
    print(f"Features: {len(features)}")
    print(f"Events: {len(events)} (with ~{int(len(events)*0.1)} intentional errors)")
    print(f"\nOutput directory: {data_dir}")
    print("\nData quality issues introduced:")
    print("  - ~3% duplicate events")
    print("  - ~2% missing user_id")
    print("  - ~2% inconsistent user_id format")
    print("  - ~1% future timestamps")
    print("  - ~1.5% invalid timestamp format")
    print("  - ~1% invalid OS values")
    print("  - ~1.5% invalid app_version format")
    print("  - ~1% negative amounts in properties")
    print("  - ~1% invalid country codes")
    print("  - ~0.5% missing event_type")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()