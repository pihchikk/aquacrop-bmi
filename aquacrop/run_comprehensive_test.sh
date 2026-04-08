#!/bin/bash

# Compile and run the comprehensive BMI test suite

set -e

echo "========================================================================"
echo "  Comprehensive BMI Getter/Setter Test"
echo "========================================================================"
echo ""

# Check if we have the fixed BMI library
if [ ! -f "libaquacropbmi.so" ]; then
    echo "ERROR: libaquacropbmi.so not found"
    echo "Please run ./apply_complete_fix.sh first to build the fixed BMI library"
    exit 1
fi

# Compile the comprehensive test
echo "Compiling test_bmi_comprehensive..."
gfortran -fPIC -fall-intrinsics -O2 -march=native -funroll-loops \
    -I/usr/local/include -o test_bmi_comprehensive test_bmi_comprehensive.f90 \
    -L. -laquacropbmi -Wl,-rpath,. -L/usr/local/lib -lbmif

echo "✓ Test compiled"
echo ""

# Run the test
echo "========================================================================"
echo "  Running 45 comprehensive tests..."
echo "========================================================================"
echo ""

./test_bmi_comprehensive

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "  ✅ COMPREHENSIVE TEST SUITE PASSED!"
    echo "========================================================================"
    echo ""
    echo "Your BMI implementation is production-ready:"
    echo "  • All getters work correctly"
    echo "  • All setters work correctly"
    echo "  • Boundary conditions are handled properly"
    echo "  • Error conditions are handled correctly"
    echo "  • State consistency is maintained"
    echo ""
    exit 0
else
    echo ""
    echo "========================================================================"
    echo "  ❌ SOME TESTS FAILED"
    echo "========================================================================"
    echo ""
    echo "Review the output above to see which tests failed."
    echo "Common issues:"
    echo "  • Missing trim() in select case statements"
    echo "  • Incorrect variable names"
    echo "  • Missing variables in input_items or output_items"
    echo ""
    exit 1
fi
