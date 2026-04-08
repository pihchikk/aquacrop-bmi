#!/bin/bash

# Build script for all diagnostic tests
# Run this to compile all tests at once

set -e

echo "========================================================================"
echo "  Building All Diagnostic Tests"
echo "========================================================================"
echo ""

# Check prerequisites
if [ ! -f "bmi_aquacrop.f90" ]; then
    echo "ERROR: bmi_aquacrop.f90 not found"
    echo "Please copy it from downloads first"
    exit 1
fi

# Clean and rebuild BMI library
echo "Step 1: Rebuilding BMI library with debug version..."
make clean
make bmi
echo "✓ BMI library built"
echo ""

# Test 1: Direct access
if [ -f "test_direct_access.f90" ]; then
    echo "Step 2: Compiling test_direct_access..."
    gfortran -O2 -fPIC -J. -o test_direct_access test_direct_access.f90 \
        kinds.o project_input.o utils.o global.o initialsettings.o \
        defaultcropsoil.o rootunit.o simul.o tempprocessing.o \
        climprocessing.o inforesults.o run.o startunit.o
    echo "✓ test_direct_access compiled"
else
    echo "⚠ test_direct_access.f90 not found, skipping"
fi
echo ""

# Test 2: All variables  
if [ -f "test_all_variables.f90" ]; then
    echo "Step 3: Compiling test_all_variables..."
    gfortran -O2 -fPIC -J. $(pkg-config --cflags bmif) \
        -o test_all_variables test_all_variables.f90 \
        -L. -laquacropbmi -Wl,-rpath,. $(pkg-config --libs bmif)
    echo "✓ test_all_variables compiled"
else
    echo "⚠ test_all_variables.f90 not found, skipping"
fi
echo ""

# Test 3: Setter minimal
if [ -f "test_setter_minimal.f90" ]; then
    echo "Step 4: Compiling test_setter_minimal..."
    gfortran -O2 -fPIC -J. $(pkg-config --cflags bmif) \
        -o test_setter_minimal test_setter_minimal.f90 \
        -L. -laquacropbmi -Wl,-rpath,. $(pkg-config --libs bmif)
    echo "✓ test_setter_minimal compiled"
else
    echo "⚠ test_setter_minimal.f90 not found, skipping"
fi
echo ""

# Test 4: Setter after update
if [ -f "test_setter_after_update.f90" ]; then
    echo "Step 5: Compiling test_setter_after_update..."
    gfortran -O2 -fPIC -J. $(pkg-config --cflags bmif) \
        -o test_setter_after_update test_setter_after_update.f90 \
        -L. -laquacropbmi -Wl,-rpath,. $(pkg-config --libs bmif)
    echo "✓ test_setter_after_update compiled"
else
    echo "⚠ test_setter_after_update.f90 not found, skipping"
fi
echo ""

echo "========================================================================"
echo "  All Tests Compiled Successfully!"
echo "========================================================================"
echo ""
echo "Run them in this order:"
echo ""
echo "  1. ./test_direct_access"
echo "     Tests if AquaCrop functions work directly (bypass BMI)"
echo ""
echo "  2. ./test_all_variables"  
echo "     Tests which BMI variables work"
echo ""
echo "  3. ./test_setter_minimal"
echo "     Tests setter immediately after init"
echo ""
echo "  4. ./test_setter_after_update"
echo "     Tests setter after simulation starts"
echo ""
echo "The output will show exactly where the problem is."
echo ""
