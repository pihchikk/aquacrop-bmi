#!/bin/bash

# Quick test - compile and run test_direct_access only
# This is the most important test

set -e

echo "========================================================================"
echo "  Quick Test: Direct Access to AquaCrop Functions"
echo "========================================================================"
echo ""

# Check if we have the necessary files
if [ ! -f "test_direct_access.f90" ]; then
    echo "ERROR: test_direct_access.f90 not found"
    exit 1
fi

# Make sure we have the object files
if [ ! -f "kinds.o" ]; then
    echo "Building AquaCrop objects first..."
    make lib
    echo ""
fi

echo "Compiling test_direct_access..."
gfortran -O2 -fPIC -J. -o test_direct_access test_direct_access.f90 \
    kinds.o project_input.o utils.o global.o initialsettings.o \
    defaultcropsoil.o rootunit.o simul.o tempprocessing.o \
    climprocessing.o inforesults.o run.o startunit.o

echo "✓ Compiled successfully"
echo ""

echo "========================================================================"
echo "  Running test..."
echo "========================================================================"
echo ""

./test_direct_access

echo ""
echo "========================================================================"
echo "  Analysis"
echo "========================================================================"
echo ""
echo "If you see:"
echo "  '✓ SUCCESS! Direct access works' → Problem is in BMI wrapper"
echo "  '✗ FAILURE! Direct access fails' → Problem is in AquaCrop init"
echo ""
