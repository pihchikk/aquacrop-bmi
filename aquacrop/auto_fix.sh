#!/bin/bash
# ========================================================================
# ONE-COMMAND FIX for BMI Fertility Stress Issue
# ========================================================================
# This script automatically applies the patch, rebuilds, and tests
# ========================================================================

set -e  # Exit on any error

cd /mnt/d/KNP/aquacrop-bmi/aquacrop

echo "========================================================================"
echo "  AUTOMATED FIX: BMI Fertility Stress Getter/Setter"
echo "========================================================================"
echo ""

# Check if we have the patched file
if [ ! -f bmi_aquacrop_PATCHED.f90 ]; then
    echo "❌ ERROR: bmi_aquacrop_PATCHED.f90 not found!"
    echo ""
    echo "Please download it from the conversation and place it in:"
    echo "  /mnt/d/KNP/aquacrop-bmi/aquacrop/"
    echo ""
    exit 1
fi

# Backup original
echo "1. Backing up original bmi_aquacrop.f90..."
if [ ! -f bmi_aquacrop.f90.orig ]; then
    cp bmi_aquacrop.f90 bmi_aquacrop.f90.orig
    echo "   ✅ Backup created: bmi_aquacrop.f90.orig"
else
    echo "   ℹ️  Backup already exists"
fi
echo ""

# Apply patch
echo "2. Applying patch..."
cp bmi_aquacrop_PATCHED.f90 bmi_aquacrop.f90
echo "   ✅ Patch applied"
echo ""

# Verify patch
echo "3. Verifying patch..."
if grep -q "EffectStress_init" bmi_aquacrop.f90; then
    echo "   ✅ Patch verified (found EffectStress_init)"
else
    echo "   ❌ ERROR: Patch verification failed!"
    exit 1
fi
echo ""

# Clean build
echo "4. Cleaning old build artifacts..."
rm -f *.o *.mod *.so test_bmi_comprehensive
echo "   ✅ Clean completed"
echo ""

# Rebuild
echo "5. Rebuilding BMI library..."
make bmi
if [ $? -eq 0 ]; then
    echo "   ✅ Build successful"
else
    echo "   ❌ Build failed!"
    exit 1
fi
echo ""

# Run test
echo "6. Running comprehensive test..."
echo "========================================================================"
./run_comprehensive_test.sh
TEST_RESULT=$?
echo "========================================================================"
echo ""

# Summary
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅✅✅ SUCCESS! All tests passed! ✅✅✅"
    echo ""
    echo "The BMI fertility stress getter/setter is now working correctly."
    echo "You should see 45/45 tests passing."
else
    echo "⚠️  Test completed with some issues (exit code: $TEST_RESULT)"
    echo ""
    echo "Check the output above for details."
    echo "If tests still fail, run: ./check_and_fix.sh"
fi
echo ""

# Show what changed
echo "========================================================================"
echo "  What was fixed:"
echo "========================================================================"
echo "• Added EffectStress_init variable declaration"
echo "• Added Management initialization check after BMI_InitializeAquaCrop"
echo "• Initializes FertilityStress to 0 if not loaded from .MAN file"
echo "• Total changes: 1 variable + 1 if-block (~20 lines)"
echo ""
echo "To revert to original:"
echo "  cp bmi_aquacrop.f90.orig bmi_aquacrop.f90"
echo "  make clean && make bmi"
echo ""
