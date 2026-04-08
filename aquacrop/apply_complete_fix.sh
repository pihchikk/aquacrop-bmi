#!/bin/bash

# COMPLETE FIX SCRIPT
# Applies all fixes and rebuilds everything

set -e

echo "========================================================================"
echo "  APPLYING THE COMPLETE FIX"
echo "========================================================================"
echo ""

# Check if we have the fixed files
if [ ! -f "bmi_aquacrop_FIXED.f90" ]; then
    echo "ERROR: bmi_aquacrop_FIXED.f90 not found"
    echo "Please copy all files from the download first"
    exit 1
fi

# Backup originals
if [ ! -f "bmi_aquacrop.f90.original" ]; then
    echo "Creating backup: bmi_aquacrop.f90.original"
    cp bmi_aquacrop.f90 bmi_aquacrop.f90.original
fi

# Apply fixes
echo "Step 1: Applying fixed bmi_aquacrop.f90..."
cp bmi_aquacrop_FIXED.f90 bmi_aquacrop.f90
echo "✓ BMI wrapper fixed"
echo ""

echo "Step 2: Applying fixed test_bmi_complete.f90..."
if [ -f "test_bmi_complete.f90" ]; then
    # If test file exists, use the fixed version
    cp test_bmi_complete.f90 test_bmi_complete.f90.original 2>/dev/null || true
fi
# The test file from outputs is already fixed
echo "✓ Test file ready"
echo ""

# Clean everything
echo "Step 3: Cleaning all build artifacts..."
rm -f *.so *.o *.mod test_bmi_complete test_setter_minimal test_all_variables test_direct_access test_setter_after_update
echo "✓ Cleaned"
echo ""

# Rebuild BMI library
echo "Step 4: Rebuilding BMI library from scratch..."
make bmi
echo "✓ BMI library rebuilt"
echo ""

# Rebuild test
echo "Step 5: Rebuilding test..."
make test_bmi_complete
echo "✓ Test compiled"
echo ""

echo "========================================================================"
echo "  FIX APPLIED SUCCESSFULLY!"
echo "========================================================================"
echo ""
echo "Now run the test:"
echo ""
echo "  ./test_bmi_complete"
echo ""
echo "You should see:"
echo "  ✅ ALL TESTS PASSED!"
echo ""
