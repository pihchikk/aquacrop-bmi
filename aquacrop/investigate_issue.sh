#!/bin/bash

echo "=========================================================================="
echo "  INVESTIGATING THE REAL PROBLEM"
echo "=========================================================================="
echo ""

cd /mnt/d/KNP/aquacrop-bmi/aquacrop

# Check if the patch was applied
echo "1. Check if patch was applied:"
echo "   Looking for 'EffectStress_init' in bmi_aquacrop.f90..."
if grep -q "EffectStress_init" bmi_aquacrop.f90; then
    echo "   ✅ Found! Patch WAS applied"
    grep -n "EffectStress_init" bmi_aquacrop.f90 | head -2
else
    echo "   ❌ NOT FOUND! Patch was NOT applied"
    echo ""
    echo "   TO APPLY PATCH:"
    echo "   cp bmi_aquacrop_PATCHED.f90 bmi_aquacrop.f90"
    echo "   make clean && make bmi"
fi
echo ""

# Check what files are actually missing
echo "2. Check what files are missing according to AquaCrop:"
echo "   (This tells us WHY Management isn't initialized)"
if [ -f bmi_test_data/OUTP/ListProjectsLoaded.OUT ]; then
    echo ""
    cat bmi_test_data/OUTP/ListProjectsLoaded.OUT
else
    echo "   File not found. Run the test first."
fi
echo ""

# Check the actual test data structure
echo "3. What test data files DO exist:"
find bmi_test_data -type f | sort
echo ""

# Compile and run diagnostic
echo "4. Would you like to compile and run diagnostic test?"
echo "   This will show EXACTLY what GetManagement_FertilityStress() returns"
echo ""
echo "   To run diagnostic:"
echo "   gfortran -I/usr/local/include test_diagnostic.f90 -L. -laquacropbmi -lbmi_fortran -o test_diagnostic"
echo "   ./test_diagnostic"
echo ""

