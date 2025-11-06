#!/bin/bash
#
# verify_bmi_test_setup.sh
# 
# Verification script for BMI AquaCrop test data setup
# Run this before executing test_bmi_complete to ensure everything is correct
#

set -e  # Exit on any error

echo ""
echo "========================================================================"
echo "  BMI AQUACROP TEST DATA VERIFICATION"
echo "========================================================================"
echo ""

ERRORS=0
WARNINGS=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $description"
        return 0
    else
        echo -e "${RED}❌${NC} $description - MISSING: $file"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

function check_dir() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅${NC} $description"
        return 0
    else
        echo -e "${RED}❌${NC} $description - MISSING: $dir"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

function warn() {
    local message=$1
    echo -e "${YELLOW}⚠️${NC}  $message"
    WARNINGS=$((WARNINGS + 1))
}

function info() {
    local message=$1
    echo "   $message"
}

# Check current directory
echo "Current directory: $(pwd)"
echo ""

# Check if bmi_test_data exists
if [ ! -d "bmi_test_data" ]; then
    echo -e "${RED}❌ FATAL: bmi_test_data directory not found!${NC}"
    echo ""
    echo "Please extract the test data first:"
    echo "  tar -xzf bmi_test_data.tar.gz"
    echo ""
    echo "Or generate it:"
    echo "  python3 generate_bmi_test_data.py"
    echo ""
    exit 1
fi

# Check directory structure
echo "1. Checking Directory Structure"
echo "────────────────────────────────────────"
check_dir "bmi_test_data" "Root directory"
check_dir "bmi_test_data/LIST" "LIST directory (for project files)"
check_dir "bmi_test_data/OUTP" "OUTP directory (for outputs)"
check_dir "bmi_test_data/SIMUL" "SIMUL directory (for simulation config)"
echo ""

# Check critical project files
echo "2. Checking Project Configuration Files"
echo "────────────────────────────────────────"
check_file "bmi_test_data/LIST/project.PRO" "Main project file (LIST/project.PRO)"
check_file "bmi_test_data/LIST/ListProjects.txt" "Project list file"

# Additional check: Make sure project.PRO is NOT in root
if [ -f "bmi_test_data/project.PRO" ]; then
    warn "Found project.PRO in root directory - should be in LIST/ instead!"
    info "The file in root will be ignored by AquaCrop"
fi
echo ""

# Check climate data files
echo "3. Checking Climate Data Files"
echo "────────────────────────────────────────"
check_file "bmi_test_data/project.CLI" "Climate configuration"
check_file "bmi_test_data/project.Tnx" "Temperature data"
check_file "bmi_test_data/project.PLU" "Precipitation data"
check_file "bmi_test_data/project.ETo" "Evapotranspiration data"
echo ""

# Check crop and soil files
echo "4. Checking Crop and Soil Files"
echo "────────────────────────────────────────"
check_file "bmi_test_data/project.CRO" "Crop parameters"
check_file "bmi_test_data/project.SOL" "Soil profile"
check_file "bmi_test_data/project.SW0" "Initial water content"
check_file "bmi_test_data/project.GWT" "Groundwater table"
echo ""

# Check management and calendar files
echo "5. Checking Management Files"
echo "────────────────────────────────────────"
check_file "bmi_test_data/project.MAN" "Field management"
check_file "bmi_test_data/project.CAL" "Crop calendar"
echo ""

# Check simulation configuration files
echo "6. Checking Simulation Configuration"
echo "────────────────────────────────────────"
check_file "bmi_test_data/SIMUL/MaunaLoa.CO2" "CO2 concentration data"
check_file "bmi_test_data/SIMUL/DailyResults.SIM" "Daily output configuration"
check_file "bmi_test_data/SIMUL/DEFAULT.CRO" "Default crop parameters"
check_file "bmi_test_data/SIMUL/DEFAULT.SOL" "Default soil parameters"
echo ""

# Check for executable
echo "7. Checking Test Executable"
echo "────────────────────────────────────────"
if [ -f "test_bmi_complete" ]; then
    if [ -x "test_bmi_complete" ]; then
        echo -e "${GREEN}✅${NC} test_bmi_complete executable found"
    else
        warn "test_bmi_complete exists but is not executable"
        info "Run: chmod +x test_bmi_complete"
    fi
else
    warn "test_bmi_complete not found in current directory"
    info "Make sure you compiled it and are in the correct directory"
fi
echo ""

# Validate project.PRO content
echo "8. Validating project.PRO Content"
echo "────────────────────────────────────────"
if [ -f "bmi_test_data/LIST/project.PRO" ]; then
    # Check if file has the expected relative paths
    if grep -q "^\.\./project\.CLI" bmi_test_data/LIST/project.PRO; then
        echo -e "${GREEN}✅${NC} project.PRO contains correct relative paths (../)"
    else
        echo -e "${RED}❌${NC} project.PRO missing expected relative paths"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Check for required references
    local required_refs=("CLI" "Tnx" "ETo" "PLU" "CRO" "SOL" "SW0" "GWT" "MAN")
    for ref in "${required_refs[@]}"; do
        if grep -q "project\.$ref" bmi_test_data/LIST/project.PRO; then
            echo -e "${GREEN}✅${NC} project.$ref referenced in project.PRO"
        else
            echo -e "${RED}❌${NC} project.$ref NOT referenced in project.PRO"
            ERRORS=$((ERRORS + 1))
        fi
    done
    
    # Check for SIMUL references
    if grep -q "SIMUL/MaunaLoa.CO2" bmi_test_data/LIST/project.PRO; then
        echo -e "${GREEN}✅${NC} CO2 file referenced in project.PRO"
    else
        echo -e "${RED}❌${NC} CO2 file NOT referenced in project.PRO"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}❌${NC} Cannot validate - project.PRO not found"
fi
echo ""

# Check file sizes (basic sanity check)
echo "9. Checking File Sizes"
echo "────────────────────────────────────────"
for file in bmi_test_data/project.{Tnx,PLU,ETo}; do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
        if [ "$size" -gt 1000 ]; then
            echo -e "${GREEN}✅${NC} $(basename $file) has reasonable size ($size bytes)"
        else
            warn "$(basename $file) seems too small ($size bytes)"
            info "Climate files should be ~3-5 KB for 120 days of data"
        fi
    fi
done
echo ""

# Summary
echo "========================================================================"
echo "  VERIFICATION SUMMARY"
echo "========================================================================"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 PERFECT! All checks passed!${NC}"
    echo ""
    echo "Your test data is correctly set up and ready to use."
    echo ""
    echo "You can now run:"
    echo "  ./test_bmi_complete"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}✅ Setup is OK with $WARNINGS warning(s)${NC}"
    echo ""
    echo "The warnings above are minor issues that probably won't prevent"
    echo "the test from running, but you may want to address them."
    echo ""
    echo "You can try running:"
    echo "  ./test_bmi_complete"
    echo ""
    exit 0
else
    echo -e "${RED}❌ ERRORS FOUND: $ERRORS error(s), $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before running test_bmi_complete."
    echo ""
    echo "Common fixes:"
    echo "  1. Extract test data:  tar -xzf bmi_test_data.tar.gz"
    echo "  2. Generate fresh:     python3 generate_bmi_test_data.py"
    echo "  3. Check permissions:  chmod +x test_bmi_complete"
    echo ""
    exit 1
fi
