# MANUAL BMI TESTING GUIDE FOR AQUACROP FORTRAN

This guide provides step-by-step instructions for manually testing the AquaCrop Fortran BMI implementation.

## ✅ CURRENT STATUS

### What's Working
- ✅ **Fortran BMI Library**: `libaquacropbmi.so` compiles successfully (1.1 MB)
- ✅ **All 40+ BMI Functions**: Fully implemented in `bmi_aquacrop.f90`
- ✅ **Test Programs**: Complete test programs provided
- ✅ **Build System**: Makefile works correctly

### What Needs Attention
- ⚠️ **Data Files**: Require proper AquaCrop-format climate/crop/soil files
- ⚠️ **Testing**: Needs validation with known-good AquaCrop project

---

## 📁 DIRECTORY STRUCTURE

Your repository should have this structure:

```
aquacrop-bmi/
├── aquacrop/
│   ├── bmi_aquacrop.f90           # BMI implementation (919 lines)
│   ├── bmif_2_0.f90                # BMI 2.0 interface
│   ├── libaquacropbmi.so           # Compiled BMI library ✅
│   ├── test_bmi_complete.f90       # Comprehensive test program
│   ├── Makefile                    # Build configuration
│   └── bmi_test_data/              # Test data directory (NEEDS VALID DATA)
│       ├── LIST/
│       │   └── project.PRO
│       ├── OUTP/
│       ├── SIMUL/
│       │   ├── MaunaLoa.CO2
│       │   └── DailyResults.SIM
│       ├── project.CLI
│       ├── project.Tnx
│       ├── project.ETo
│       ├── project.PLU
│       ├── project.CRO
│       ├── project.SOL
│       ├── project.SW0
│       ├── project.GWT
│       ├── project.MAN
│       └── project.CAL
└── src/
    └── aquacrop_bmi/
        ├── data/                   # Example data files
        │   ├── crops/              # .CRO files
        │   └── default/            # Default project files
        └── sync.py                 # Shows how Python creates data

```

---

## 🔧 STEP 1: BUILD THE BMI LIBRARY

```bash
cd /path/to/aquacrop-bmi/aquacrop

# Clean previous builds
make clean

# Build the BMI library
make bmi

# Verify it was created
ls -lh libaquacropbmi.so
# Should show: libaquacropbmi.so (about 1.1 MB)
```

**Expected output:**
```
-rwxr-xr-x 1 user user 1.1M libaquacropbmi.so
```

---

## 🧪 STEP 2: COMPILE THE TEST PROGRAM

```bash
# Compile the comprehensive test program
gfortran -o test_bmi_complete test_bmi_complete.f90 \
    -L. -laquacropbmi -Wl,-rpath,.

# Verify compilation
ls -lh test_bmi_complete
```

---

## 📊 STEP 3: PREPARE TEST DATA

### Option A: Use Python-Generated Data (RECOMMENDED)

The easiest way is to let the Python code generate proper data files:

```bash
cd /path/to/aquacrop-bmi

# Install Python dependencies
pip install -e .

# Run Python to generate test data
python3 << 'EOF'
from aquacrop_bmi.project import AquaCropProject
from aquacrop_bmi.models import Season, Point
from datetime import date

# Create test data
with AquaCropProject(with_default=False) as project:
    # This creates all necessary files in a temp directory
    # Copy them to bmi_test_data/ for BMI testing
    print(f"Data created in: {project.root}")
    # Copy files from project.root to your bmi_test_data/
EOF
```

### Option B: Use Existing AquaCrop Project

If you have an existing working AquaCrop project:

```bash
# Copy your working project to bmi_test_data/
cp -r /path/to/working/aquacrop/project/* aquacrop/bmi_test_data/

# Verify structure
ls aquacrop/bmi_test_data/LIST/project.PRO
```

### Critical Data Requirements

Your data files must:

1. **Date Format**: Use AquaCrop epoch days (days since 1900-12-31)
   ```python
   from datetime import date
   epoch = date(1900, 12, 31).toordinal()
   day_number = date(2024, 4, 1).toordinal() - epoch
   ```

2. **Climate Files**: Must have correct number of data lines
   - Header: 8 lines
   - Data: Exactly (end_day - start_day + 1) lines

3. **File Paths**: In `LIST/project.PRO`, use `./'` for files in root:
   ```
   project.CLI
   './'
   ```

---

## ▶️ STEP 4: RUN THE BMI TEST

```bash
cd /path/to/aquacrop-bmi/aquacrop

# Run the comprehensive test
./test_bmi_complete

# Or with output redirection
./test_bmi_complete 2>&1 | tee test_output.log
```

---

## ✅ EXPECTED OUTPUT

If everything works correctly, you should see:

```
============================================================================
           COMPREHENSIVE BMI AQUACROP TEST PROGRAM
============================================================================

This program tests ALL major BMI functions with real AquaCrop data

----------------------------------------------------------------------------
TEST 1: Get Component Name
----------------------------------------------------------------------------
  ✅ Component Name: AquaCrop

----------------------------------------------------------------------------
TEST 2: Initialize Model
----------------------------------------------------------------------------
  Project file: bmi_test_data/LIST/project.PRO

  ✅ SUCCESS: Model initialized

----------------------------------------------------------------------------
TEST 3: Model Information
----------------------------------------------------------------------------
  Input variables:  1
  Output variables: 4
  Input variable names:
    1. crop__fertility_stress
  Output variable names:
    1. crop__canopy_cover
    2. crop__biomass
    3. crop__yield
    4. soil__moisture

----------------------------------------------------------------------------
TEST 4: Time Information
----------------------------------------------------------------------------
  Start time:      0.0 days
  Current time:    0.0 days
  End time:      121.0 days
  Time step:       1.0 days
  Total simulation days:      121 days

... (more output) ...

----------------------------------------------------------------------------
TEST 10: Final Results
----------------------------------------------------------------------------
  Simulation completed at day    121 days

  FINAL VALUES:
    Canopy Cover:     XX.XX %
    Biomass:         XX.XXX tonnes/ha
    Yield:           XX.XXX tonnes/ha
    Soil Moisture:   XXX.XX mm

============================================================================
                         TEST SUMMARY
============================================================================

  ALL TESTS PASSED! ✅

  BMI Functions Tested:
    ✅ get_component_name()
    ✅ initialize()
    ✅ get_input_item_count() / get_output_item_count()
    ✅ get_input_var_names() / get_output_var_names()
    ✅ get_start/current/end_time()
    ✅ get_time_step() / get_time_units()
    ✅ get_var_type/units/itemsize/nbytes/location/grid()
    ✅ get_grid_type/rank/size/node_count/x/y/z()
    ✅ update()
    ✅ get_value_double() (4 variables tested)
    ✅ finalize()
```

---

## 🐛 TROUBLESHOOTING

### Error: "Segmentation fault"

**Cause**: BMI initialization failed, usually due to missing/invalid data files

**Solutions**:
1. Verify all data files exist in `bmi_test_data/`
2. Check `.PRO` file paths are correct
3. Ensure climate files have enough data lines
4. Use Python-generated data instead

### Error: "Cannot open file"

**Cause**: File paths in `.PRO` file are incorrect

**Solution**: Check file paths in `LIST/project.PRO`:
```
-- Correct:
project.CLI
'./'

-- Incorrect:
project.CLI
'../'
```

### Error: "Bad real number" or "End of file"

**Cause**: Data file format issues or insufficient data lines

**Solutions**:
1. Check climate files have (end_day - start_day + 1) data lines
2. Verify dates are in numeric format (not text)
3. Use Python-generated data files

### Error: Library not found

**Cause**: `libaquacropbmi.so` not in search path

**Solution**:
```bash
export LD_LIBRARY_PATH=/path/to/aquacrop:$LD_LIBRARY_PATH
./test_bmi_complete
```

---

## 📝 CREATING YOUR OWN TEST

Here's a minimal BMI test program you can customize:

```fortran
program minimal_bmi_test
    use bmiaquacropf
    use, intrinsic :: iso_c_binding
    implicit none

    type(bmi_aquacrop) :: model
    integer :: status
    real(c_double) :: yield_val(1), current_time, end_time
    character(len=1024) :: project_file

    ! Set your project file path
    project_file = "bmi_test_data/LIST/project.PRO"

    ! Initialize
    print *, "Initializing AquaCrop BMI..."
    status = model%initialize(trim(project_file))
    if (status /= 0) then
        print *, "ERROR: Initialization failed"
        stop 1
    end if

    ! Get time info
    status = model%get_end_time(end_time)
    print *, "Simulation duration:", int(end_time), "days"

    ! Run simulation
    print *, "Running simulation..."
    do while (current_time < end_time)
        status = model%update()
        if (status /= 0) exit
        status = model%get_current_time(current_time)
    end do

    ! Get final yield
    status = model%get_value_double("crop__yield", yield_val)
    print *, "Final yield:", yield_val(1), "tonnes/ha"

    ! Finalize
    status = model%finalize()
    print *, "Done!"

end program minimal_bmi_test
```

**Compile and run:**
```bash
gfortran -o minimal_test minimal_bmi_test.f90 -L. -laquacropbmi -Wl,-rpath,.
./minimal_test
```

---

## 📚 BMI FUNCTIONS REFERENCE

### Initialization & Finalization
```fortran
status = model%get_component_name(name)          ! Get model name
status = model%initialize(config_file)           ! Initialize with .PRO file
status = model%finalize()                        ! Clean up
```

### Model Information
```fortran
status = model%get_input_item_count(count)       ! Number of input vars
status = model%get_output_item_count(count)      ! Number of output vars
status = model%get_input_var_names(names)        ! Input variable names
status = model%get_output_var_names(names)       ! Output variable names
```

### Time Management
```fortran
status = model%get_start_time(time)              ! Start time (0.0)
status = model%get_current_time(time)            ! Current time
status = model%get_end_time(time)                ! End time
status = model%get_time_step(step)               ! Time step (1.0 day)
status = model%get_time_units(units)             ! Time units ("days")
status = model%update()                          ! Advance one day
status = model%update_until(time)                ! Run until time
```

### Variable Access
```fortran
! Get values (copy)
status = model%get_value_double(var_name, dest)

! Available output variables:
! - "crop__canopy_cover" (percent)
! - "crop__biomass" (tonnes/ha)
! - "crop__yield" (tonnes/ha)
! - "soil__moisture" (mm)

! Set values
status = model%set_value_double(var_name, src)
! - "crop__fertility_stress" (percent, 0-100)
```

### Variable Information
```fortran
status = model%get_var_type(var_name, type)      ! Variable type
status = model%get_var_units(var_name, units)    ! Variable units
status = model%get_var_itemsize(var_name, size)  ! Item size (bytes)
status = model%get_var_nbytes(var_name, bytes)   ! Total bytes
status = model%get_var_location(var_name, loc)   ! Location ("node")
status = model%get_var_grid(var_name, grid_id)   ! Grid ID (0=scalar)
```

### Grid Information (Scalar Grid)
```fortran
status = model%get_grid_type(0, type)            ! "scalar"
status = model%get_grid_rank(0, rank)            ! 0
status = model%get_grid_size(0, size)            ! 1
status = model%get_grid_node_count(0, count)     ! 1
status = model%get_grid_x(0, x)                  ! Longitude
status = model%get_grid_y(0, y)                  ! Latitude
status = model%get_grid_z(0, z)                  ! Altitude
```

---

## 🎯 SUCCESS CRITERIA

Your BMI implementation is working correctly if:

1. ✅ Test program compiles without errors
2. ✅ `initialize()` returns status = 0
3. ✅ `update()` runs without segfaults for all days
4. ✅ Output values are reasonable:
   - Canopy cover: 0-100%
   - Biomass: 0-30 tonnes/ha (typically)
   - Yield: 0-20 tonnes/ha (typically)
   - Soil moisture: positive mm value
5. ✅ `finalize()` returns status = 0
6. ✅ No memory leaks or crashes

---

## 📞 SUPPORT

If you encounter issues:

1. **Check the example data**: Look at `/src/aquacrop_bmi/examples/` for JSON examples
2. **Use Python sync.py**: See how it creates data files correctly
3. **Verify data format**: Run Python AquaCropProject to generate known-good files
4. **Test standalone**: Try running `./aquacrop` executable first
5. **Enable debug**: Compile with `-g -fcheck=all` for detailed errors

---

## 📖 FILES IN THIS DIRECTORY

| File | Purpose |
|------|---------|
| `bmi_aquacrop.f90` | BMI implementation (919 lines) |
| `bmif_2_0.f90` | BMI 2.0 interface definition |
| `libaquacropbmi.so` | Compiled BMI library |
| `test_bmi_complete.f90` | Comprehensive test program |
| `test_bmi_functions.f90` | Simple test program |
| `Makefile` | Build configuration |
| `bmi_test_data/` | Test data directory |

---

## ✨ NEXT STEPS

Once BMI testing is successful:

1. Create Python wrapper using babelizer or ctypes
2. Write unit tests for each BMI function
3. Create integration tests with real crop/climate data
4. Document expected input/output ranges
5. Add error handling and validation
6. Create user documentation

---

**Last Updated**: 2025-11-04
**Status**: Fortran BMI complete, awaiting proper test data
**Contact**: See repository README
