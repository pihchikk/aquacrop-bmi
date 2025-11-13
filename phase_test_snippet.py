# ========================================================================
# PHASE 2: IRRIGATION MANAGEMENT (2 variables)
# ========================================================================
print_test_header("PHASE 2", "Irrigation Management Variables (2)")

# Test irrigation method (enumeration: 0-4)
# NOTE: This variable has special handling because it's an integer enum
total_tests += 2
var = "management__irrigation_method"

# Try SET
try:
    src = np.array([2.0], dtype=np.float64)
    model.set_value(var, src)
    print(f"  ✓ SET {var:45s} = 2 (Drip)")
    passed_tests += 1
except Exception as e:
    print(f"  ✗ SET {var} FAILED: {e}")
    print(f"      (Known issue: babelizer wrapper may not handle integer enums correctly)")
    # Don't fail the whole test for this known issue

# Try GET regardless of whether SET worked
try:
    dest = np.empty(1, dtype=np.float64)
    model.get_value(var, dest)
    method_names = ["Basin", "Border", "Drip", "Furrow", "Sprinkler"]
    method_idx = int(dest[0])
    if 0 <= method_idx <= 4:
        print(f"  ✓ GET {var:45s} = {method_idx} ({method_names[method_idx]})")
        passed_tests += 1
    else:
        print(f"  ⚠ GET {var:45s} = {method_idx} (out of range 0-4)")
except Exception as e:
    print(f"  ✗ GET {var} FAILED: {e}")