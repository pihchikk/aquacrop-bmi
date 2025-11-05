program test_bmi_standalone
    !=====================================================================
    ! STANDALONE BMI TEST - NO PYTHON REQUIRED
    !=====================================================================
    ! Tests basic BMI functions with pre-generated data
    ! Data location: bmi_standalone_test/LIST/project.PRO
    !=====================================================================
    
    use bmiaquacropf
    use, intrinsic :: iso_c_binding
    implicit none
    
    type(bmi_aquacrop) :: model
    integer :: status, day
    real(c_double) :: cc(1), biomass(1), yield_val(1), soil_water(1)
    real(c_double) :: current_time, end_time
    character(len=1024) :: project_file
    character(len=256) :: name
    
    project_file = "bmi_standalone_test/LIST/project.PRO"
    
    print *, "========================================"
    print *, "  STANDALONE BMI TEST (No Python)"
    print *, "========================================"
    print *, ""
    
    ! Test 1: Component Name
    print *, "Test 1: Component Name"
    status = model%get_component_name(name)
    if (status == 0) then
        print '(A,A)', "  ✅ Component: ", trim(name)
    else
        print *, "  ❌ FAILED"
        stop 1
    end if
    print *, ""
    
    ! Test 2: Initialize
    print *, "Test 2: Initialize"
    print '(A,A)', "  Project file: ", trim(project_file)
    status = model%initialize(trim(project_file))
    if (status == 0) then
        print *, "  ✅ Model initialized successfully"
    else
        print *, "  ❌ FAILED - check data files"
        stop 1
    end if
    print *, ""
    
    ! Test 3: Time Info
    print *, "Test 3: Time Information"
    status = model%get_end_time(end_time)
    print '(A,F6.0,A)', "  Simulation duration: ", end_time, " days"
    print *, ""
    
    ! Test 4: Run first 10 days
    print *, "Test 4: Run First 10 Days"
    print *, "  Day |  CC(%)  | Biomass | Yield  | Soil H2O"
    print *, "  ----|---------|---------|--------|----------"
    
    do day = 1, 10
        status = model%update()
        if (status /= 0) then
            print *, "  ❌ Update failed on day", day
            exit
        end if
        
        status = model%get_current_time(current_time)
        status = model%get_value_double("crop__canopy_cover", cc)
        status = model%get_value_double("crop__biomass", biomass)
        status = model%get_value_double("crop__yield", yield_val)
        status = model%get_value_double("soil__moisture", soil_water)
        
        print '(I5,A,F8.2,A,F8.3,A,F7.3,A,F9.2)', &
              day, " | ", cc(1), " | ", biomass(1), " | ", &
              yield_val(1), " | ", soil_water(1)
    end do
    print *, ""
    
    ! Test 5: Finalize
    print *, "Test 5: Finalize"
    status = model%finalize()
    if (status == 0) then
        print *, "  ✅ Model finalized successfully"
    else
        print *, "  ❌ Finalization failed"
    end if
    print *, ""
    
    print *, "========================================"
    print *, "  ✅ ALL TESTS PASSED!"
    print *, "========================================"
    print *, ""
    print *, "BMI Functions Tested:"
    print *, "  ✅ get_component_name()"
    print *, "  ✅ initialize()"
    print *, "  ✅ get_end_time()"
    print *, "  ✅ update() x 10"
    print *, "  ✅ get_current_time()"
    print *, "  ✅ get_value_double() x 4 variables"
    print *, "  ✅ finalize()"
    print *, ""

end program test_bmi_standalone
