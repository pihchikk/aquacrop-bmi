#!/bin/bash
cd /mnt/d/KNP/aquacrop-bmi/aquacrop

echo "========================================================================"
echo "  VERIFICATION: What version of bmi_aquacrop.f90 do we have?"
echo "========================================================================"
echo ""

echo "1. Check if patch was applied (looking for EffectStress_init):"
if grep -q "EffectStress_init" bmi_aquacrop.f90; then
    echo "   ✅ Found EffectStress_init - patch WAS applied"
    grep -n "EffectStress_init" bmi_aquacrop.f90 | head -3
else
    echo "   ❌ NOT found - patch was NOT applied"
fi
echo ""

echo "2. Check GetManagement_FertilityStress in USE statement:"
if grep -q "GetManagement_FertilityStress" bmi_aquacrop.f90 | head -5; then
    echo "   ✅ Found in USE statement"
    grep "GetManagement_FertilityStress" bmi_aquacrop.f90 | head -2
else
    echo "   ❌ NOT in USE statement"
fi
echo ""

echo "3. Check aquacrop_get_double has fertility_stress case:"
if grep -q "case('crop__fertility_stress')" bmi_aquacrop.f90; then
    echo "   ✅ Found case statement"
    grep -A 3 "case('crop__fertility_stress')" bmi_aquacrop.f90 | head -15
else
    echo "   ❌ Case NOT found"
fi
echo ""

echo "4. Count how many times 'crop__fertility_stress' appears:"
COUNT=$(grep -c "crop__fertility_stress" bmi_aquacrop.f90)
echo "   Found $COUNT occurrences"
if [ $COUNT -lt 3 ]; then
    echo "   ⚠️  Should be at least 3 times (input_items, getter, setter)"
fi
echo ""

echo "5. Check the library modification time:"
if [ -f libaquacropbmi.so ]; then
    echo "   Library: $(ls -lh libaquacropbmi.so | awk '{print $6, $7, $8, $9}')"
    echo "   Source:  $(ls -lh bmi_aquacrop.f90 | awk '{print $6, $7, $8, $9}')"
    if [ bmi_aquacrop.f90 -nt libaquacropbmi.so ]; then
        echo "   ⚠️  Source is NEWER than library - need to rebuild!"
    else
        echo "   ✅ Library is up to date"
    fi
else
    echo "   ❌ Library not found!"
fi
echo ""

echo "6. Verify the actual getter function structure:"
echo "   (Showing lines around the fertility_stress case)"
grep -n "case('crop__fertility_stress')" bmi_aquacrop.f90 | while read line; do
    LINE_NUM=$(echo $line | cut -d: -f1)
    echo "   At line $LINE_NUM:"
    sed -n "$((LINE_NUM-1)),$((LINE_NUM+4))p" bmi_aquacrop.f90 | sed 's/^/      /'
    echo ""
done

echo "========================================================================"
echo ""
