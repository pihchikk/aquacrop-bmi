#!/bin/bash
# Comprehensive Fix for Input Count Issue

echo "================================================================================"
echo "           AQUACROP BMI - INPUT COUNT ISSUE DIAGNOSIS & FIX"
echo "================================================================================"
echo ""

# Step 1: Check current state
echo "STEP 1: Checking current installation state"
echo "============================================="
echo ""

echo "1.1 Checking if BMI library is installed system-wide..."
if [ -f "/usr/local/lib/libaquacropbmi.so" ]; then
    echo "  ✓ Library found: /usr/local/lib/libaquacropbmi.so"
    ls -lh /usr/local/lib/libaquacropbmi.so
else
    echo "  ✗ Library NOT found: /usr/local/lib/libaquacropbmi.so"
    echo "    This is likely the root cause!"
fi
echo ""

echo "1.2 Checking if module file exists..."
if [ -f "/usr/local/include/aquacropbmi.mod" ]; then
    echo "  ✓ Module found: /usr/local/include/aquacropbmi.mod"
else
    echo "  ✗ Module NOT found: /usr/local/include/aquacropbmi.mod"
fi
echo ""

echo "1.3 Checking pkg-config..."
if pkg-config --exists aquacropbmi 2>/dev/null; then
    VERSION=$(pkg-config --modversion aquacropbmi)
    echo "  ✓ pkg-config finds aquacropbmi (version $VERSION)"
else
    echo "  ✗ pkg-config cannot find aquacropbmi"
    echo "    This prevents babelizer from finding the library!"
fi
echo ""

# Step 2: Check source file
echo "STEP 2: Checking source file configuration"
echo "==========================================="
echo ""

if [ -f "bmi_aquacrop.f90" ]; then
    INPUT_LINE=$(grep "input_item_count.*="bmi_aquacrop.f90 | grep -v "procedure" | head -1)
    OUTPUT_LINE=$(grep "output_item_count.*="bmi_aquacrop.f90 | grep -v "procedure" | head -1)
    
    echo "Source file: bmi_aquacrop.f90"
    echo "  $INPUT_LINE"
    echo "  $OUTPUT_LINE"
    
    if echo "$INPUT_LINE" | grep -q "= 11"; then
        echo "  ✓ Source file has correct input count (11)"
    else
        echo "  ✗ Source file has WRONG input count (not 11)"
        echo "    Update the source file first!"
    fi
else
    echo "  ⚠ Cannot find source file at bmi_aquacrop.f90"
fi
echo ""

# Step 3: Diagnosis summary
echo "STEP 3: Diagnosis Summary"
echo "========================="
echo ""

ISSUE_FOUND=0

if [ ! -f "/usr/local/lib/libaquacropbmi.so" ]; then
    echo "❌ CRITICAL ISSUE: BMI library not installed system-wide"
    echo "   Location: /usr/local/lib/libaquacropbmi.so"
    echo "   Impact: Babelizer cannot find or is using wrong version"
    ISSUE_FOUND=1
fi

if ! pkg-config --exists aquacropbmi 2>/dev/null; then
    echo "❌ CRITICAL ISSUE: pkg-config cannot find aquacropbmi"
    echo "   Impact: Babelizer build will fail or use cached old version"
    ISSUE_FOUND=1
fi

if [ $ISSUE_FOUND -eq 0 ]; then
    echo "⚠️  Library IS installed but Python still reports wrong count"
    echo "   This suggests a build cache issue with babelizer"
fi

echo ""

# Step 4: Provide fix
echo "STEP 4: Recommended Fix"
echo "======================="
echo ""

if [ $ISSUE_FOUND -eq 1 ]; then
    echo "You need to install the BMI library system-wide:"
    echo ""
    echo "  cd /mnt/d/KNP/aquacrop-bmi/aquacrop/"
    echo "  make clean"
    echo "  make bmi"
    echo "  sudo make install"
    echo "  sudo ldconfig"
    echo ""
    echo "Then rebuild the Python wrapper:"
    echo ""
    echo "  cd aquacrop_bmi_babel"
    echo "  rm -rf build/ dist/ *.egg-info"
    echo "  uv pip uninstall aquacrop-bmi-babel"
    echo "  uv pip install ."
    echo ""
else
    echo "Library is installed, but babelizer may have cached old version."
    echo ""
    echo "Force a complete rebuild:"
    echo ""
    echo "  cd /mnt/d/KNP/aquacrop-bmi/aquacrop/aquacrop_bmi_babel"
    echo "  rm -rf build/ dist/ *.egg-info"
    echo "  uv pip uninstall aquacrop-bmi-babel"
    echo ""
    echo "  # Force rebuild of Meson build cache"
    echo "  cd .."
    echo "  sudo make clean"
    echo "  sudo make bmi"
    echo "  sudo make install"
    echo "  sudo ldconfig"
    echo ""
    echo "  # Now rebuild Python wrapper"
    echo "  cd aquacrop_bmi_babel"
    echo "  uv pip install . --no-cache-dir"
fi
echo ""

# Step 5: Verification commands
echo "STEP 5: Verification Commands"
echo "============================="
echo ""
echo "After applying the fix, run these to verify:"
echo ""
echo "1. Check library is installed:"
echo "   ls -l /usr/local/lib/libaquacropbmi.so"
echo ""
echo "2. Check pkg-config:"
echo "   pkg-config --modversion aquacropbmi"
echo ""
echo "3. Check Python reports correct count:"
echo "   python3 -c \"from aquacrop_bmi_babel import AquaCrop; m=AquaCrop(); m.initialize('/mnt/d/KNP/aquacrop-bmi/aquacrop/bmi_test_data/LIST/project.PRO'); print('Inputs:', m.get_input_item_count())\""
echo ""
echo "Expected output: 'Inputs: 11'"
echo ""

# Step 6: Check if we can auto-fix
echo "================================================================================"
echo "                           AUTO-FIX OPTION"
echo "================================================================================"
echo ""
echo "Would you like to automatically fix this? (requires sudo)"
echo ""
echo "This will:"
echo "  1. Rebuild the BMI library from source"
echo "  2. Install it system-wide to /usr/local"
echo "  3. Rebuild the Python wrapper"
echo "  4. Verify the fix"
echo ""
echo "Run with: $0 --auto-fix"
echo ""

if [ "$1" == "--auto-fix" ]; then
    echo "Starting auto-fix..."
    echo ""
    
    cd /mnt/d/KNP/aquacrop-bmi/aquacrop/ || exit 1
    
    echo "1. Cleaning previous build..."
    make clean
    
    echo "2. Building BMI library..."
    make bmi
    
    if [ ! -f "libaquacropbmi.so" ]; then
        echo "❌ Build failed - libaquacropbmi.so not created"
        exit 1
    fi
    
    echo "3. Installing system-wide (requires sudo)..."
    sudo make install
    sudo ldconfig
    
    echo "4. Verifying installation..."
    if pkg-config --exists aquacropbmi; then
        echo "  ✓ pkg-config finds library"
    else
        echo "  ✗ pkg-config still can't find library"
        exit 1
    fi
    
    echo "5. Rebuilding Python wrapper..."
    cd aquacrop_bmi_babel || exit 1
    rm -rf build/ dist/ *.egg-info
    uv pip uninstall -y aquacrop-bmi-babel 2>/dev/null || true
    uv pip install .
    
    echo "6. Testing..."
    cd ..
    python3 << 'EOFPYTHON'
from aquacrop_bmi_babel import AquaCrop
model = AquaCrop()
model.initialize('/mnt/d/KNP/aquacrop-bmi/aquacrop/bmi_test_data/LIST/project.PRO')
input_count = model.get_input_item_count()
print(f"\nResult: Input count = {input_count}")
if input_count == 11:
    print("✓ SUCCESS! Now reporting correct input count.")
else:
    print(f"✗ FAILED! Still reporting wrong count (expected 11, got {input_count})")
EOFPYTHON
    
    echo ""
    echo "Auto-fix complete!"
fi

echo "================================================================================"
