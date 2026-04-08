#!/bin/bash

# Simple test script for BMI setter debugging
# Run this after copying the debug files

set -e  # Exit on any error

echo "========================================================================"
echo "  BMI Setter Debug Test Script"
echo "========================================================================"
echo ""

# Check if we have the necessary files
if [ ! -f "bmi_aquacrop.f90" ]; then
    echo "ERROR: bmi_aquacrop.f90 not found in current directory"
    echo "Please copy it from the downloads first"
    exit 1
fi

if [ ! -f "test_setter_minimal.f90" ]; then
    echo "ERROR: test_setter_minimal.f90 not found"
    echo "Please copy it from the downloads first"
    exit 1
fi

echo "Step 1: Cleaning old build..."
make clean
echo ""

echo "Step 2: Building BMI library with debug version..."
make bmi
echo ""

echo "Step 3: Compiling minimal test..."
gfortran -O2 -fPIC -J. $(pkg-config --cflags bmif) \
    -o test_setter_minimal test_setter_minimal.f90 \
    -L. -laquacropbmi -Wl,-rpath,. $(pkg-config --libs bmif)
echo "✓ Test compiled"
echo ""

echo "========================================================================"
echo "  Running TEST 1: Setter immediately after initialization"
echo "========================================================================"
echo ""
./test_setter_minimal
echo ""

# Check if test_setter_after_update.f90 exists
if [ -f "test_setter_after_update.f90" ]; then
    echo "========================================================================"
    echo "  Compiling TEST 2: Setter after simulation updates"
    echo "========================================================================"
    echo ""
    gfortran -O2 -fPIC -J. $(pkg-config --cflags bmif) \
        -o test_setter_after_update test_setter_after_update.f90 \
        -L. -laquacropbmi -Wl,-rpath,. $(pkg-config --libs bmif)
    echo "✓ Test compiled"
    echo ""
    
    echo "========================================================================"
    echo "  Running TEST 2: Setter after simulation updates"
    echo "========================================================================"
    echo ""
    ./test_setter_after_update
    echo ""
fi

echo "========================================================================"
echo "  All tests complete!"
echo "========================================================================"
echo ""
echo "Check the output above for:"
echo "  - '✓ MATCHED' messages = string matching works"
echo "  - '✗ NO MATCH' messages = string matching failed (bug)"
echo "  - Any errors from AquaCrop functions"
echo ""