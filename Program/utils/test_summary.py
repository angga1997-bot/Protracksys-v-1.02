# ============================================================
# FILE: test_summary.py
# ============================================================

import os
import sys

print("=" * 60)
print("🧪 Testing Summary Feature")
print("=" * 60)

# Test 1: Import config
print("\n1. Testing config import...")
try:
    from config import DEFAULT_DASHBOARD_CONFIG
    print("   ✅ DEFAULT_DASHBOARD_CONFIG imported")
    print(f"   Keys: {list(DEFAULT_DASHBOARD_CONFIG.keys())}")
    
    if "summary_columns" in DEFAULT_DASHBOARD_CONFIG:
        print("   ✅ summary_columns exists")
    else:
        print("   ❌ summary_columns MISSING!")
    
    if "summary_shift_column" in DEFAULT_DASHBOARD_CONFIG:
        print("   ✅ summary_shift_column exists")
    else:
        print("   ❌ summary_shift_column MISSING!")
        
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 2: Data Manager
print("\n2. Testing DataManager...")
try:
    from utils.data_manager import DataManager
    dm = DataManager()
    print("   ✅ DataManager initialized")
    
    # Check dashboard_config
    print(f"   Dashboard config keys: {list(dm.dashboard_config.keys())}")
    
    # Test get_column_names
    cols = dm.get_column_names()
    print(f"   ✅ Columns: {cols}")
    
    # Test summary methods if exists
    if hasattr(dm, 'get_summary_config'):
        print("   ✅ get_summary_config exists")
    else:
        print("   ⚠️ get_summary_config not found (optional)")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Dashboard Config Save/Load
print("\n3. Testing dashboard config save/load...")
try:
    # Add test summary config
    dm.dashboard_config["summary_columns"] = [
        {"column_name": "Test", "display_name": "Test Col", "operation": "SUM", "icon": "📊", "active": True}
    ]
    dm.dashboard_config["summary_shift_column"] = "Shift"
    dm.save_dashboard_config()
    print("   ✅ Config saved")
    
    # Reload
    dm2 = DataManager()
    if dm2.dashboard_config.get("summary_columns"):
        print("   ✅ Config loaded correctly")
        print(f"   Summary columns: {dm2.dashboard_config['summary_columns']}")
    else:
        print("   ⚠️ Config not persisted")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Import dashboard page
print("\n4. Testing dashboard page import...")
try:
    from pages.dashboard_page import DashboardPage, SummarySettingsDialog
    print("   ✅ DashboardPage imported")
    print("   ✅ SummarySettingsDialog imported")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ All tests completed!")
print("=" * 60)
print("\nRun: python main.py")