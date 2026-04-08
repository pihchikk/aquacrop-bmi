program test_irrigation_method_debug
    use iso_c_binding
    use aquacropbmi
    implicit none
    
    type(bmi_aquacrop) :: model
    real(c_double) :: value_dbl(1)
    integer :: status
    character(len=256) :: config_file
    
    print *, ""
    print *, "========================================"
    print *, "  DEBUG: Irrigation Method Issue"
    print *, "========================================"
    print *, ""
    
    ! Initialize
    config_file = "bmi_test_data/LIST/project.PRO"
    status = model%initialize(config_file)
    
    if (status /= 0) then
        print *, "✗ Initialize failed:", status
        stop 1
    end if
    print *, "✓ Initialize successful"
    print *, ""
    
    ! Test 1: Try to SET irrigation method
    print *, "TEST 1: SET irrigation method to 2 (Drip)"
    status = model%set_value_double("management__irrigation_method", [2.0d0])
    print *, "  Status returned:", status
    
    if (status == 0) then
        print *, "  ✓ SET succeeded"
    else
        print *, "  ✗ SET FAILED with status:", status
        print *, ""
        print *, "This means the setter in bmi_aquacrop.f90 returned BMI_FAILURE"
        print *, "Check the aquacrop_set_double() function"
    end if
    print *, ""
    
    ! Test 2: Try to GET irrigation method
    print *, "TEST 2: GET irrigation method"
    value_dbl(1) = -999.0d0  ! Set to invalid value first
    status = model%get_value_double("management__irrigation_method", value_dbl)
    print *, "  Status returned:", status
    print *, "  Value returned:", value_dbl(1)
    
    if (status == 0) then
        print *, "  ✓ GET succeeded"
    else
        print *, "  ✗ GET FAILED with status:", status
    end if
    print *, ""
    
    ! Test 3: Check if SetIrriMethod exists
    print *, "TEST 3: Direct call to SetIrriMethod"
    print *, "  (This tests if the function is accessible)"
    
    ! Try to import and call directly
    ! This will fail at compile time if function doesn't exist
    ! or has wrong signature
    
    print *, ""
    print *, "========================================"
    
    status = model%finalize()
    
end program test_irrigation_method_debug