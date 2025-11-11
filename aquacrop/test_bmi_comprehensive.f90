program test_bmi_comprehensive
    !===========================================================================
    ! COMPREHENSIVE BMI GETTER/SETTER TEST SUITE
    !===========================================================================
    ! Tests all BMI getter/setter functionality thoroughly
    !===========================================================================

    use bmif
    use bmif_2_0
    use, intrinsic :: iso_c_binding
    implicit none

    type(bmi_aquacrop) :: model
    integer :: status
    character(len=1024) :: config_file
    real(c_double) :: val(1), retrieved_val(1)
    integer :: i, passed, failed

    config_file = "bmi_test_data/LIST/project.PRO"
    passed = 0
    failed = 0

    print *, ""
    print *, "========================================================================"
    print *, "          COMPREHENSIVE BMI GETTER/SETTER TEST SUITE"
    print *, "========================================================================"
    print *, ""
    print *, "This test validates:"
    print *, "  ✓ All getter functions"
    print *, "  ✓ All setter functions"
    print *, "  ✓ Boundary conditions"
    print *, "  ✓ Variable metadata"
    print *, "  ✓ Error handling"
    print *, "  ✓ State consistency"
    print *, ""
    print *, "========================================================================"
    print *, ""

    ! Initialize
    print *, "Initializing AquaCrop BMI..."
    print *, ""
    status = model%initialize(config_file)
    if (status /= BMI_SUCCESS) then
        print *, "ERROR: Initialization failed!"
        stop 1
    end if
    print *, "✓ Model initialized"
    print *, ""

    ! ========================================================================
    ! TEST CATEGORY 1: Variable Metadata
    ! ========================================================================
    print *, "========================================================================"
    print *, "TEST CATEGORY 1: Variable Metadata"
    print *, "========================================================================"
    print *, ""

    ! Test 1.1: Input item count
    block
        integer :: count
        status = model%get_input_item_count(count)
        if (status == BMI_SUCCESS .and. count == 1) then
            print *, " ✅ 1.1 Input item count:", count
            passed = passed + 1
        else
            print *, " ❌ 1.1 Input item count FAILED"
            failed = failed + 1
        end if
    end block

    ! Test 1.2: Output item count
    block
        integer :: count
        status = model%get_output_item_count(count)
        if (status == BMI_SUCCESS .and. count == 4) then
            print *, " ✅ 1.2 Output item count:", count
            passed = passed + 1
        else
            print *, " ❌ 1.2 Output item count FAILED"
            failed = failed + 1
        end if
    end block

    print *, ""

    ! ========================================================================
    ! TEST CATEGORY 2: Input Variable Getters (Initial State)
    ! ========================================================================
    print *, "========================================================================"
    print *, "TEST CATEGORY 2: Input Variable Getters (Initial State)"
    print *, "========================================================================"
    print *, ""

    ! Test 2.1: Get fertility stress
    status = model%get_value_double("crop__fertility_stress", val)
    if (status == BMI_SUCCESS) then
        print '(A,F6.1)', "  ✅ 2.1 Initial fertility_stress:", val(1)
        passed = passed + 1
    else
        print *, "  ❌ 2.1 get_value_double(fertility_stress) FAILED"
        failed = failed + 1
    end if

    print *, ""

    ! ========================================================================
    ! TEST CATEGORY 3: Output Variable Getters (Initial State)
    ! ========================================================================
    print *, "========================================================================"
    print *, "TEST CATEGORY 3: Output Variable Getters (Initial State)"
    print *, "========================================================================"
    print *, ""

    ! Test 3.1: Canopy cover
    status = model%get_value_double("crop__canopy_cover", val)
    if (status == BMI_SUCCESS) then
        print '(A,F6.2,A)', " ✅ 3.1 Initial canopy_cover:", val(1), "%"
        passed = passed + 1
    else
        print *, " ❌ 3.1 canopy_cover FAILED"
        failed = failed + 1
    end if

    ! Test 3.2: Biomass
    status = model%get_value_double("crop__biomass", val)
    if (status == BMI_SUCCESS) then
        print '(A,F8.3,A)', " ✅ 3.2 Initial biomass:", val(1), " t/ha"
        passed = passed + 1
    else
        print *, " ❌ 3.2 biomass FAILED"
        failed = failed + 1
    end if

    ! Test 3.3: Yield
    status = model%get_value_double("crop__yield", val)
    if (status == BMI_SUCCESS) then
        print '(A,F8.3,A)', " ✅ 3.3 Initial yield:", val(1), " t/ha"
        passed = passed + 1
    else
        print *, " ❌ 3.3 yield FAILED"
        failed = failed + 1
    end if

    ! Test 3.4: Soil moisture
    status = model%get_value_double("soil__moisture", val)
    if (status == BMI_SUCCESS) then
        print '(A,F6.2,A)', " ✅ 3.4 Initial soil_moisture:", val(1), " mm"
        passed = passed + 1
    else
        print *, " ❌ 3.4 soil_moisture FAILED"
        failed = failed + 1
    end if

    print *, ""

    ! ========================================================================
    ! TEST CATEGORY 4: Input Variable Setters (Basic Functionality)
    ! ========================================================================
    print *, "========================================================================"
    print *, "TEST CATEGORY 4: Input Variable Setters (Basic Functionality)"
    print *, "========================================================================"
    print *, ""

    ! Test 4.1: Set to 25
    val(1) = 25.0d0
    status = model%set_value_double("crop__fertility_stress", val)
    if (status == BMI_SUCCESS) then
        status = model%get_value_double("crop__fertility_stress", retrieved_val)
        if (status == BMI_SUCCESS .and. abs(retrieved_val(1) - 25.0d0) < 0.1d0) then
            print '(A,F6.1)', "  ✅ 4.1 Set/Get 25.0:", retrieved_val(1)
            passed = passed + 1
        else
            print *, "  ❌ 4.1 Set succeeded but get failed"
            failed = failed + 1
        end if
    else
        print *, "  ❌ 4.1 set_value_double FAILED"
        failed = failed + 1
    end if

    ! Test 4.2: Set to 50
    val(1) = 50.0d0
    status = model%set_value_double("crop__fertility_stress", val)
    if (status == BMI_SUCCESS) then
        status = model%get_value_double("crop__fertility_stress", retrieved_val)
        if (status == BMI_SUCCESS .and. abs(retrieved_val(1) - 50.0d0) < 0.1d0) then
            print '(A,F6.1)', "  ✅ 4.2 Set/Get 50.0:", retrieved_val(1)
            passed = passed + 1
        else
            print *, "  ❌ 4.2 Get mismatch"
            failed = failed + 1
        end if
    else
        print *, "  ❌ 4.2 set_value_double FAILED"
        failed = failed + 1
    end if

    ! Test 4.3: Set to 75
    val(1) = 75.0d0
    status = model%set_value_double("crop__fertility_stress", val)
    if (status == BMI_SUCCESS) then
        status = model%get_value_double("crop__fertility_stress", retrieved_val)
        if (status == BMI_SUCCESS .and. abs(retrieved_val(1) - 75.0d0) < 0.1d0) then
            print '(A,F6.1)', "  ✅ 4.3 Set/Get 75.0:", retrieved_val(1)
            passed = passed + 1
        else
            print *, "  ❌ 4.3 Get mismatch"
            failed = failed + 1
        end if
    else
        print *, "  ❌ 4.3 set_value_double FAILED"
        failed = failed + 1
    end if

    print *, ""

    ! ========================================================================
    ! TEST CATEGORY 5: Input Variable Setters (Boundary Conditions)
    ! ========================================================================
    print *, "========================================================================"
    print *, "TEST CATEGORY 5: Input Variable Setters (Boundary Conditions)"
    print *, "========================================================================"
    print *, ""

    ! Test 5.1: Set to 0
    val(1) = 0.0d0
    status = model%set_value_double("crop__fertility_stress", val)
    if (status == BMI_SUCCESS) then
        print '(A,F6.1)', "  ✅ 5.1 Set to 0.0:", val(1)
        passed = passed + 1
    else
        print *, "  ❌ 5.1 set_value_double(0) FAILED"
        failed = failed + 1
    end if

    ! Test 5.2: Set to 100
    val(1) = 100.0d0
    status = model%set_value_double("crop__fertility_stress", val)
    if (status == BMI_SUCCESS) then
        print '(A,F6.1)', "  ✅ 5.2 Set to 100.0:", val(1)
        passed = passed + 1
    else
        print *, "  ❌ 5.2 set_value_double(100) FAILED"
        failed = failed + 1
    end if

    ! Test 5.3: Set to negative (should clamp to 0)
    val(1) = -10.0d0
    status = model%set_value_double("crop__fertility_stress", val)
    if (status == BMI_SUCCESS) then
        status = model%get_value_double("crop__fertility_stress", retrieved_val)
        if (status == BMI_SUCCESS .and. retrieved_val(1) >= 0.0d0) then
            print '(A,F6.1,A)', "  ✅ 5.3 Negative clamped to:", retrieved_val(1), " (expected >= 0)"
            passed = passed + 1
        else
            print *, "  ❌ 5.3 Clamping failed"
            failed = failed + 1
        end if
    else
        print *, "  ❌ 5.3 set_value_double(-10) FAILED"
        failed = failed + 1
    end if

    ! Test 5.4: Set above 100 (should clamp to 100)
    val(1) = 150.0d0
    status = model%set_value_double("crop__fertility_stress", val)
    if (status == BMI_SUCCESS) then
        status = model%get_value_double("crop__fertility_stress", retrieved_val)
        if (status == BMI_SUCCESS .and. retrieved_val(1) <= 100.0d0) then
            print '(A,F6.1,A)', "  ✅ 5.4 Above 100 clamped to:", retrieved_val(1), " (expected <= 100)"
            passed = passed + 1
        else
            print *, "  ❌ 5.4 Clamping failed"
            failed = failed + 1
        end if
    else
        print *, "  ❌ 5.4 set_value_double(150) FAILED"
        failed = failed + 1
    end if

    print *, ""

    ! ========================================================================
    ! TEST CATEGORY 6: Error Handling
    ! ========================================================================
    print *, "========================================================================"
    print *, "TEST CATEGORY 6: Error Handling"
    print *, "========================================================================"
    print *, ""

    ! Test 6.1: Invalid variable name
    status = model%get_value_double("invalid__variable", val)
    if (status == BMI_FAILURE) then
        print *, "  ✅ 6.1 Invalid variable name rejected (as expected)"
        passed = passed + 1
    else
        print *, "  ❌ 6.1 Should have rejected invalid name"
        failed = failed + 1
    end if

    ! Test 6.2: Try to set output variable
    status = model%set_value_double("crop__canopy_cover", val)
    if (status == BMI_FAILURE) then
        print *, "  ✅ 6.2 Output variable rejected for setting (as expected)"
        passed = passed + 1
    else
        print *, "  ❌ 6.2 Should have rejected setting output var"
        failed = failed + 1
    end if

    print *, ""

    ! ========================================================================
    ! Summary
    ! ========================================================================
    print *, ""
    print *, "========================================================================"
    print *, "                        TEST SUMMARY"
    print *, "========================================================================"
    print *, ""
    print '(A,I3)', "  Total tests: ", passed + failed
    print '(A,I3)', "  Passed:      ", passed
    print '(A,I3)', "  Failed:      ", failed
    print *, ""

    if (failed == 0) then
        print *, "  ✅ ALL TESTS PASSED"
        print *, ""
    else
        print *, "  ❌ SOME TESTS FAILED"
        print *, ""
        print '(A,F5.1,A)', "  Success rate: ", (100.0 * passed) / (passed + failed), "%"
        print *, ""
        stop 1
    end if

    ! Finalize
    status = model%finalize()

end program test_bmi_comprehensive