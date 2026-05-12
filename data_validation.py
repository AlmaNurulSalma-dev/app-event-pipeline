#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mobile App Analytics Pipeline - Data Validation Layer
Validates data quality rules against the cleaned silver layer
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataValidator:
    """Validates mobile app event data against quality rules"""
    
    def __init__(self, cleaned_data_path="data/processed/silver_events.parquet"):
        self.data_path = cleaned_data_path
        self.df = None
        self.validation_results = {}
    
    def load_data(self):
        """Load cleaned data"""
        logger.info(f"Loading data from {self.data_path}...")
        self.df = pd.read_parquet(self.data_path)
        logger.info(f"Loaded {len(self.df)} records")
        return self.df
    
    def validate_completeness(self):
        """Check for null/missing values"""
        logger.info("Validating completeness...")
        results = {}
        
        critical_columns = ['event_id', 'user_id', 'event_type', 'timestamp']
        
        for col in critical_columns:
            null_count = self.df[col].isna().sum()
            passed = null_count == 0
            results[f"no_nulls_in_{col}"] = {
                "passed": bool(passed),
                "failed_count": int(null_count),
                "failed_pct": float((null_count / len(self.df) * 100) if len(self.df) > 0 else 0)
            }
        
        self.validation_results.update(results)
        return results
    
    def validate_format(self):
        """Check data format compliance"""
        logger.info("Validating formats...")
        results = {}
        
        # Check user_id format (USER_XXX)
        valid_user_ids = self.df['user_id'].str.match(r'^USER_\d+$', na=False).sum()
        total_users = len(self.df)
        results["user_id_format"] = {
            "passed": bool(valid_user_ids == total_users),
            "failed_count": int(total_users - valid_user_ids),
            "failed_pct": float(((total_users - valid_user_ids) / total_users * 100) if total_users > 0 else 0)
        }
        
        # Check timestamp format
        valid_timestamps = pd.to_datetime(self.df['timestamp'], errors='coerce').notna().sum()
        results["timestamp_format"] = {
            "passed": bool(valid_timestamps == len(self.df)),
            "failed_count": int(len(self.df) - valid_timestamps),
            "failed_pct": float(((len(self.df) - valid_timestamps) / len(self.df) * 100) if len(self.df) > 0 else 0)
        }
        
        # Check app_version format (X.Y.Z)
        valid_versions = self.df['app_version'].str.match(r'^\d+\.\d+\.\d+$', na=False).sum()
        results["app_version_format"] = {
            "passed": bool(valid_versions == len(self.df)),
            "failed_count": int(len(self.df) - valid_versions),
            "failed_pct": float(((len(self.df) - valid_versions) / len(self.df) * 100) if len(self.df) > 0 else 0)
        }
        
        self.validation_results.update(results)
        return results
    
    def validate_business_rules(self):
        """Check business logic constraints"""
        logger.info("Validating business rules...")
        results = {}
        
        # Event type should be from known set
        valid_event_types = {
            'app_open', 'app_close', 'screen_view', 'button_click', 'search',
            'item_view', 'add_to_cart', 'remove_from_cart', 'checkout', 'purchase',
            'payment_success', 'payment_failed', 'wishlist_add', 'wishlist_remove',
            'review_submitted', 'rating_submitted', 'share_clicked', 'download_started',
            'error', 'crash'
        }
        
        valid_events = self.df['event_type'].isin(valid_event_types).sum()
        results["valid_event_types"] = {
            "passed": bool(valid_events == len(self.df)),
            "failed_count": int(len(self.df) - valid_events),
            "failed_pct": float(((len(self.df) - valid_events) / len(self.df) * 100) if len(self.df) > 0 else 0)
        }
        
        # OS should be valid
        valid_os = {'iOS', 'Android', 'Web'}
        valid_os_count = self.df['os'].isin(valid_os).sum()
        results["valid_os"] = {
            "passed": bool(valid_os_count == len(self.df)),
            "failed_count": int(len(self.df) - valid_os_count),
            "failed_pct": float(((len(self.df) - valid_os_count) / len(self.df) * 100) if len(self.df) > 0 else 0)
        }
        
        # Country should be valid 2-letter code
        valid_countries = {'ID', 'SG', 'MY', 'TH', 'PH', 'VN'}
        valid_country_count = self.df['country'].isin(valid_countries).sum()
        results["valid_country_code"] = {
            "passed": bool(valid_country_count == len(self.df)),
            "failed_count": int(len(self.df) - valid_country_count),
            "failed_pct": float(((len(self.df) - valid_country_count) / len(self.df) * 100) if len(self.df) > 0 else 0)
        }
        
        # Event ID should be unique
        unique_events = self.df['event_id'].nunique()
        results["unique_event_ids"] = {
            "passed": bool(unique_events == len(self.df)),
            "failed_count": int(len(self.df) - unique_events),
            "failed_pct": float(((len(self.df) - unique_events) / len(self.df) * 100) if len(self.df) > 0 else 0)
        }
        
        # No future timestamps (timezone-aware comparison)
        now = pd.Timestamp.now(tz='UTC')
        future_count = (self.df['timestamp'] > now).sum()
        results["no_future_timestamps"] = {
            "passed": bool(future_count == 0),
            "failed_count": int(future_count),
            "failed_pct": float((future_count / len(self.df) * 100) if len(self.df) > 0 else 0)
        }
        
        # Purchase events should have positive amounts
        purchase_events = self.df[self.df['event_type'] == 'purchase']
        if len(purchase_events) > 0:
            valid_amounts = 0
            for _, row in purchase_events.iterrows():
                if isinstance(row['properties'], dict) and 'amount' in row['properties']:
                    try:
                        amount = float(row['properties']['amount'])
                        if amount > 0:
                            valid_amounts += 1
                    except Exception:
                        pass
            
            results["purchase_amounts_positive"] = {
                "passed": bool(valid_amounts == len(purchase_events)),
                "failed_count": int(len(purchase_events) - valid_amounts),
                "failed_pct": float(((len(purchase_events) - valid_amounts) / len(purchase_events) * 100) if len(purchase_events) > 0 else 0)
            }
        
        self.validation_results.update(results)
        return results
    
    def validate_statistics(self):
        """Check statistical anomalies"""
        logger.info("Validating statistics...")
        results = {}
        
        major_versions = self.df['major_version'].value_counts()
        results["major_version_distribution"] = {
            "passed": bool(len(major_versions) > 0),
            "summary": {str(k): int(v) for k, v in major_versions.to_dict().items()}
        }
        
        os_distribution = self.df['os'].value_counts()
        results["os_distribution"] = {
            "passed": bool(len(os_distribution) > 0),
            "summary": {str(k): int(v) for k, v in os_distribution.to_dict().items()}
        }
        
        event_distribution = self.df['event_type'].value_counts().head(10)
        results["event_type_distribution"] = {
            "top_10": {str(k): int(v) for k, v in event_distribution.to_dict().items()}
        }
        
        self.validation_results.update(results)
        return results
    
    def generate_validation_report(self):
        """Generate detailed validation report"""
        Path("data/validation").mkdir(parents=True, exist_ok=True)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_records": len(self.df),
            "validation_results": self.validation_results,
            "summary": self._create_summary()
        }
        
        report_path = Path("data/validation/validation_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Saved validation report: {report_path}")
        return report
    
    def _create_summary(self):
        """Create summary statistics"""
        total_validations = 0
        passed_validations = 0
        
        for rule, result in self.validation_results.items():
            if isinstance(result, dict) and "passed" in result:
                total_validations += 1
                if result["passed"]:
                    passed_validations += 1
        
        pass_rate = (passed_validations / total_validations * 100) if total_validations > 0 else 0
        
        return {
            "total_validation_rules": total_validations,
            "rules_passed": passed_validations,
            "rules_failed": total_validations - passed_validations,
            "overall_pass_rate_pct": round(pass_rate, 2)
        }
    
    def print_validation_report(self):
        """Print validation report to console"""
        print("\n" + "="*70)
        print("DATA QUALITY VALIDATION REPORT")
        print("="*70)
        
        print(f"\nTotal Records Validated: {len(self.df):,}")
        
        print("\n--- COMPLETENESS ---")
        for rule, result in self.validation_results.items():
            if "no_nulls" in rule:
                status = "[PASS]" if result["passed"] else "[FAIL]"
                print(f"{status}: {rule}")
                if result["failed_count"] > 0:
                    print(f"       {result['failed_count']} records ({result['failed_pct']:.2f}%)")
        
        print("\n--- FORMAT VALIDATION ---")
        for rule, result in self.validation_results.items():
            if "format" in rule or "ids" in rule:
                status = "[PASS]" if result["passed"] else "[FAIL]"
                print(f"{status}: {rule}")
                if result["failed_count"] > 0:
                    print(f"       {result['failed_count']} records ({result['failed_pct']:.2f}%)")
        
        print("\n--- BUSINESS RULES ---")
        for rule, result in self.validation_results.items():
            if "valid_" in rule or "unique_" in rule or "future" in rule or "positive" in rule:
                if isinstance(result, dict) and "passed" in result:
                    status = "[PASS]" if result["passed"] else "[FAIL]"
                    print(f"{status}: {rule}")
                    if result["failed_count"] > 0:
                        print(f"       {result['failed_count']} records ({result['failed_pct']:.2f}%)")
        
        print("\n--- DATA DISTRIBUTION ---")
        if "os_distribution" in self.validation_results:
            print("\nOS Distribution:")
            for os, count in self.validation_results["os_distribution"]["summary"].items():
                pct = (count / len(self.df) * 100)
                print(f"  {os}: {count} ({pct:.1f}%)")
        
        if "event_type_distribution" in self.validation_results:
            print("\nTop 10 Event Types:")
            for event_type, count in self.validation_results["event_type_distribution"]["top_10"].items():
                pct = (count / len(self.df) * 100)
                print(f"  {event_type}: {count} ({pct:.1f}%)")
        
        summary = self._create_summary()
        print("\n" + "-"*70)
        print("SUMMARY")
        print("-"*70)
        print(f"Total Validation Rules: {summary.get('total_validation_rules', 0)}")
        print(f"Rules Passed:           {summary.get('rules_passed', 0)}")
        print(f"Rules Failed:           {summary.get('rules_failed', 0)}")
        print(f"Overall Pass Rate:      {summary.get('overall_pass_rate_pct', 0):.2f}%")
        print("="*70 + "\n")
    
    def run(self):
        """Execute complete validation pipeline"""
        self.load_data()
        self.validate_completeness()
        self.validate_format()
        self.validate_business_rules()
        self.validate_statistics()
        self.generate_validation_report()
        self.print_validation_report()
        return self.validation_results

if __name__ == "__main__":
    validator = DataValidator()
    results = validator.run()