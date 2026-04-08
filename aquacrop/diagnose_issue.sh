#!/bin/bash
# ========================================================================
# DIAGNOSE WHY GET/SET STILL FAIL AFTER PATCH
# ========================================================================

echo "========================================================================"
echo "  DIAGNOSTIC: Why do get/set operations still fail?"
echo "========================================================================"
echo ""

cd /mnt/d/KNP/aquacrop-bmi/aquacrop

# 1. Verify patch is in the compiled code
echo "1. Checking if patch was applied:"
grep -n "EffectStress_init" bmi_aquacrop.f90 | head -2
echo ""

# 2. Check the get_value_double function
echo "2. Checking aquacrop_get_double function:"
echo "   (Looking for the fertility_stress case)"
grep -A 5 "case('crop__fertility_stress')" bmi_aquacrop.f90 | head -10
echo ""

# 3. Check the set_value_double function  
echo "3. Checking aquacrop_set_double function:"
echo "   (Looking for the fertility_stress case)"
grep -B 2 -A 10 "case('crop__fertility_stress')" bmi_aquacrop.f90 | tail -15
echo ""

# 4. Check variable name declarations
echo "4. Checking how input_items is declared:"
grep -A 3 "input_items = " bmi_aquacrop.f90
echo ""

# 5. Look for the actual string comparison
echo "5. Checking select case statements:"
grep -n "select case(trim(name))" bmi_aquacrop.f90
grep -n "select case(trim(adjustl(name)))" bmi_aquacrop.f90
echo ""

# 6. Compile and run string matching test
echo "6. Compiling string matching diagnostic..."
gfortran -I/usr/local/include test_string_matching.f90 -L. -laquacropbmi -o test_string_matching 2>&1 | head -20

if [ $? -eq 0 ]; then
    echo "   ✅ Compiled successfully"
    echo ""
    echo "========================================================================"
    echo "  RUNNING STRING MATCHING DIAGNOSTIC"
    echo "========================================================================"
    ./test_string_matching
else
    echo "   ❌ Compilation failed"
fi

echo ""
echo "========================================================================"
echo "  ANALYSIS"
echo "========================================================================"
echo "If tests 1-4 in string matching diagnostic show different results,"
echo "then we have a string comparison issue."
echo ""
echo "If all fail the same way, then the problem is in the BMI wrapper"
echo "logic itself, not the string matching."
echo ""
