# DEBUGGING STRATEGY - Find the Real Problem

## The Issue
Your tests show all get/set operations on `crop__fertility_stress` fail, but:
- ✅ Output variable getters work (canopy_cover, biomass, yield, soil_moisture)
- ✅ Variable metadata queries work
- ✅ Error handling works (rejects invalid variables)
- ❌ ONLY fertility_stress get/set fails

This suggests the problem is:
1. Either the string comparison is failing (name mismatch)
2. Or GetManagement_FertilityStress()/SetManagement_FertilityStress() are crashing
3. Or CropStressParametersSoilFertility() is crashing

## Step-by-Step Debugging

### Option A: Apply debug version (RECOMMENDED)

1. Replace the get/set functions in `bmi_aquacrop.f90`:
   ```bash
   # Find lines containing "function aquacrop_get_double" and 
   # "function aquacrop_set_double" 
   # Replace them with the DEBUG versions from bmi_get_set_DEBUG.f90
   ```

2. Rebuild and test:
   ```bash
   make clean && make bmi
   ./run_comprehensive_test.sh 2>&1 | tee debug_output.txt
   ```

3. The debug version will print:
   - What variable name it's trying to match
   - Whether the case statement matches
   - What function calls it's making
   - Where it fails (if it fails)

### Option B: Use diagnostic test

1. Compile diagnostic test:
   ```bash
   cd /mnt/d/KNP/aquacrop-bmi/aquacrop
   gfortran -I/usr/local/include test_diagnostic.f90 -L. -laquacropbmi -lbmi_fortran -o test_diagnostic
   ```

2. Run it:
   ```bash
   ./test_diagnostic
   ```

3. This will show:
   - What GetManagement_FertilityStress() actually returns
   - Whether the BMI wrapper fails even with valid data
   - Exactly where the failure occurs

### Option C: Check what files are actually missing

```bash
cd /mnt/d/KNP/aquacrop-bmi/aquacrop

# See what AquaCrop thinks is missing
cat bmi_test_data/OUTP/ListProjectsLoaded.OUT

# See what files you actually have
find bmi_test_data -type f | sort

# Common missing files:
# - .MAN (Management) - fertility stress lives here
# - .CRO (Crop) - needed for CropStressParametersSoilFertility
# - .SOL (Soil) - soil parameters
# - .CLI (Climate) - weather data
```

## Most Likely Causes

Based on the error pattern, I suspect ONE of these:

### Cause 1: String comparison failing
**Symptom**: All fertility_stress operations fail, but other variables work
**Test**: Use debug version to see if case statement matches
**Fix**: Use `trim(adjustl(name))` instead of `trim(name)`

### Cause 2: Crop data not initialized
**Symptom**: Set operation fails when calling CropStressParametersSoilFertility()
**Test**: Check if .CRO file exists and loads
**Fix**: Ensure test data includes a proper .CRO file, or skip CropStressParameters call

### Cause 3: Management structure completely uninitialized
**Symptom**: Both get and set fail
**Test**: Run diagnostic to see what GetManagement_FertilityStress() returns
**Fix**: Add explicit Management initialization in BMI_InitializeAquaCrop

## Quick Fixes to Try

### Fix 1: Use adjustl in string comparison
In `bmi_aquacrop.f90`, change:
```fortran
select case(trim(name))
```
to:
```fortran
select case(trim(adjustl(name)))
```

### Fix 2: Skip CropStressParameters if Crop not loaded
In the setter, wrap the CropStressParameters call:
```fortran
call SetManagement_FertilityStress(fertility_value)

! Only recalculate stress parameters if Crop is loaded
if (GetCrop_CCo() > 0.0_dp) then  ! Check if crop data exists
    EffectStress_temp = GetSimulation_EffectStress()
    call CropStressParametersSoilFertility( &
        GetCrop_StressResponse(), &
        fertility_value, &
        EffectStress_temp &
    )
    call SetSimulation_EffectStress(EffectStress_temp)
end if
```

### Fix 3: Initialize Management explicitly
In `aquacrop_initialize`, after BMI_InitializeAquaCrop:
```fortran
! Ensure Management has safe defaults
call SetManagement_FertilityStress(0_int8)
```

## What to Send Me

For me to help debug further, please send:
1. Output of `grep "EffectStress_init" bmi_aquacrop.f90` (to confirm patch status)
2. Contents of `bmi_test_data/OUTP/ListProjectsLoaded.OUT` (to see what's missing)
3. Output of debug version or diagnostic test
4. List of files in your test data: `find bmi_test_data -type f`

Then I can pinpoint the exact issue!
