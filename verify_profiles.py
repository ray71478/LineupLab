#!/usr/bin/env python3
"""
Script to verify that "ray" and "base" (default) profiles have different weights.
"""

import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cortex:cortex@localhost:5432/cortex"
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def compare_profiles():
    """Compare weights between 'ray' and 'base' (default) profiles."""
    session = SessionLocal()
    
    try:
        # Query for ray profile
        ray_result = session.execute(
            text("""
                SELECT id, name, weights, config, is_default
                FROM weight_profiles
                WHERE LOWER(name) = 'ray'
            """)
        )
        ray_row = ray_result.fetchone()
        
        # Query for default (base) profile
        base_result = session.execute(
            text("""
                SELECT id, name, weights, config, is_default
                FROM weight_profiles
                WHERE is_default = true
                LIMIT 1
            """)
        )
        base_row = base_result.fetchone()
        
        if not ray_row:
            print("❌ ERROR: 'ray' profile not found in database")
            return False
        
        if not base_row:
            print("❌ ERROR: Default profile not found in database")
            return False
        
        ray_id, ray_name, ray_weights_json, ray_config_json, ray_is_default = ray_row
        base_id, base_name, base_weights_json, base_config_json, base_is_default = base_row
        
        # Parse JSONB fields (they might be strings or already dicts)
        if isinstance(ray_weights_json, str):
            ray_weights = json.loads(ray_weights_json)
        else:
            ray_weights = ray_weights_json
            
        if isinstance(base_weights_json, str):
            base_weights = json.loads(base_weights_json)
        else:
            base_weights = base_weights_json
        
        if isinstance(ray_config_json, str):
            ray_config = json.loads(ray_config_json)
        else:
            ray_config = ray_config_json
            
        if isinstance(base_config_json, str):
            base_config = json.loads(base_config_json)
        else:
            base_config = base_config_json
        
        print("=" * 80)
        print("PROFILE COMPARISON: 'ray' vs 'base' (default)")
        print("=" * 80)
        print()
        
        print(f"📊 Profile: {ray_name}")
        print(f"   ID: {ray_id}")
        print(f"   Is Default: {ray_is_default}")
        print()
        
        print(f"📊 Profile: {base_name}")
        print(f"   ID: {base_id}")
        print(f"   Is Default: {base_is_default}")
        print()
        
        print("=" * 80)
        print("WEIGHTS COMPARISON")
        print("=" * 80)
        print()
        
        # Compare weights
        weights_different = False
        for key in ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8']:
            ray_val = ray_weights.get(key, 0)
            base_val = base_weights.get(key, 0)
            diff = ray_val - base_val
            
            if abs(diff) > 0.0001:  # Account for floating point precision
                weights_different = True
                status = "✓ DIFFERENT"
            else:
                status = "  same"
            
            print(f"{key:3s} | Ray: {ray_val:8.5f} | Base: {base_val:8.5f} | Diff: {diff:10.5f} | {status}")
        
        print()
        print("=" * 80)
        print("CONFIG COMPARISON")
        print("=" * 80)
        print()
        
        # Compare config
        config_different = False
        for key in ['projection_source', 'eighty_twenty_enabled', 'eighty_twenty_threshold']:
            ray_val = ray_config.get(key)
            base_val = base_config.get(key)
            
            if ray_val != base_val:
                config_different = True
                status = "✓ DIFFERENT"
            else:
                status = "  same"
            
            print(f"{key:25s} | Ray: {str(ray_val):15s} | Base: {str(base_val):15s} | {status}")
        
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        
        if weights_different:
            print("✅ CONFIRMED: 'ray' and 'base' profiles have DIFFERENT weights")
        else:
            print("⚠️  WARNING: 'ray' and 'base' profiles have IDENTICAL weights")
        
        if config_different:
            print("✅ CONFIRMED: 'ray' and 'base' profiles have DIFFERENT config")
        else:
            print("ℹ️  INFO: 'ray' and 'base' profiles have IDENTICAL config")
        
        print()
        print("=" * 80)
        
        # Show full JSON for debugging
        print()
        print("Full 'ray' weights JSON:")
        print(json.dumps(ray_weights, indent=2))
        print()
        print("Full 'base' weights JSON:")
        print(json.dumps(base_weights, indent=2))
        
        return weights_different
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    compare_profiles()

