#!/bin/bash
# ========================================================================
# QUICK DEBUG APPLICATION
# ========================================================================
# This temporarily adds debug output to see why get fails

cd /mnt/d/KNP/aquacrop-bmi/aquacrop

echo "========================================================================"
echo "  Applying Debug Version to aquacrop_get_double"
echo "========================================================================"
echo ""

# Backup current version
cp bmi_aquacrop.f90 bmi_aquacrop.f90.before_debug

echo "1. Backing up current version..."
echo "   ✅ Saved to: bmi_aquacrop.f90.before_debug"
echo ""

# Find the function and replace it
echo "2. Finding aquacrop_get_double function..."
LINE_START=$(grep -n "^function aquacrop_get_double" bmi_aquacrop.f90 | head -1 | cut -d: -f1)
LINE_END=$(grep -n "^end function aquacrop_get_double" bmi_aquacrop.f90 | head -1 | cut -d: -f1)

echo "   Function found at lines $LINE_START-$LINE_END"
echo ""

echo "3. Manual steps needed:"
echo "   a) Open bmi_aquacrop.f90 in your editor"
echo "   b) Go to line $LINE_START (function aquacrop_get_double)"
echo "   c) Replace the entire function (through line $LINE_END)"
echo "   d) With the debug version from: aquacrop_get_double_DEBUG.f90"
echo ""
echo "   OR use sed (risky):"
echo "   sed -i '${LINE_START},${LINE_END}d' bmi_aquacrop.f90"
echo "   Then manually insert debug version"
echo ""

echo "4. After editing, rebuild:"
echo "   make clean && make bmi"
echo ""

echo "5. Run minimal test again:"
echo "   ./run_minimal_test.sh"
echo ""

echo "6. The debug output will show EXACTLY where it fails!"
echo ""

echo "7. To revert:"
echo "   cp bmi_aquacrop.f90.before_debug bmi_aquacrop.f90"
echo "   make clean && make bmi"
echo ""

echo "========================================================================"
echo ""
echo "OR: Just manually edit bmi_aquacrop.f90:"
echo "  1. Find: function aquacrop_get_double (around line $LINE_START)"
echo "  2. Replace entire function with aquacrop_get_double_DEBUG.f90"
echo "  3. Rebuild: make clean && make bmi"
echo "  4. Test: ./run_minimal_test.sh"
echo ""
