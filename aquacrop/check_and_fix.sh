#!/bin/bash
# ========================================================================
# COMPREHENSIVE FIX SCRIPT
# ========================================================================

cd /mnt/d/KNP/aquacrop-bmi/aquacrop

echo "========================================================================"
echo "  BMI Fertility Stress Fix - Diagnostic and Repair"
echo "========================================================================"
echo ""

# Step 1: Check if patch was applied
echo "STEP 1: Checking if patch was applied to bmi_aquacrop.f90..."
if grep -q "EffectStress_init" bmi_aquacrop.f90; then
    echo "  ✅ Patch WAS applied (found 'EffectStress_init')"
    grep -n "EffectStress_init" bmi_aquacrop.f90 | head -2
    PATCH_APPLIED=1
else
    echo "  ❌ Patch NOT applied yet"
    PATCH_APPLIED=0
fi
echo ""

# Step 2: Check if library is up to date
echo "STEP 2: Checking library compilation date..."
if [ -f libaquacropbmi.so ]; then
    LIB_DATE=$(stat -c %y libaquacropbmi.so | cut -d'.' -f1)
    SRC_DATE=$(stat -c %y bmi_aquacrop.f90 | cut -d'.' -f1)
    echo "  Library compiled: $LIB_DATE"
    echo "  Source modified:  $SRC_DATE"
    
    if [ bmi_aquacrop.f90 -nt libaquacropbmi.so ]; then
        echo "  ⚠️  Source is NEWER than library - need to rebuild!"
        NEED_REBUILD=1
    else
        echo "  ✅ Library is up to date"
        NEED_REBUILD=0
    fi
else
    echo "  ❌ Library not found - need to build!"
    NEED_REBUILD=1
fi
echo ""

# Step 3: Compile and run simple test
echo "STEP 3: Compiling simple diagnostic test..."
gfortran -c -I. kinds.f90 utils.f90 global.f90 2>/dev/null
gfortran -c -I. startunit.F90 2>/dev/null
gfortran test_simple.f90 kinds.o utils.o global.o startunit.o \
    project_input.o rootunit.o simul.o tempprocessing.o climprocessing.o \
    defaultcropsoil.o initialsettings.o inforesults.o run.o \
    -o test_simple 2>/dev/null

if [ $? -eq 0 ]; then
    echo "  ✅ Simple test compiled successfully"
    echo ""
    echo "========================================================================"
    echo "  Running simple diagnostic..."
    echo "========================================================================"
    ./test_simple
    echo ""
else
    echo "  ❌ Simple test failed to compile"
    echo "  Let's try a different approach..."
    echo ""
fi

# Step 4: Check what files are missing from test data
echo "STEP 4: Checking test data completeness..."
if [ -f bmi_test_data/OUTP/ListProjectsLoaded.OUT ]; then
    echo "  Contents of ListProjectsLoaded.OUT:"
    echo "  ----------------------------------------"
    cat bmi_test_data/OUTP/ListProjectsLoaded.OUT
    echo "  ----------------------------------------"
else
    echo "  ⚠️  ListProjectsLoaded.OUT not found"
fi
echo ""

echo "  Files in test data:"
find bmi_test_data -type f | sort | sed 's/^/    /'
echo ""

# Step 5: Recommendations
echo "========================================================================"
echo "  RECOMMENDATIONS"
echo "========================================================================"

if [ $PATCH_APPLIED -eq 0 ]; then
    echo "  1. ⚠️  APPLY THE PATCH:"
    echo "     cp bmi_aquacrop_PATCHED.f90 bmi_aquacrop.f90"
    echo ""
fi

if [ $NEED_REBUILD -eq 1 ] || [ $PATCH_APPLIED -eq 0 ]; then
    echo "  2. ⚠️  REBUILD THE LIBRARY:"
    echo "     make clean"
    echo "     make bmi"
    echo ""
fi

echo "  3. ✓ RE-RUN THE TEST:"
echo "     ./run_comprehensive_test.sh"
echo ""

echo "========================================================================"
echo ""
