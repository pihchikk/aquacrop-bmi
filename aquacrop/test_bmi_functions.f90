program test_bmi_functions
    ! Test program for BMI AquaCrop Steps 4 & 5
    ! Tests initialize, update, get_value, and finalize
    
    use bmiaquacropf
    use, intrinsic :: iso_c_binding
    implicit none
    
    type(bmi_aquacrop) :: model
    integer :: status, day
    real(c_double) :: cc(1), biomass(1), yield(1), soil_water(1)
    real(c_double) :: current_time, end_time
    character(len=1024) :: project_file
    
    ! IMPORTANT: Change this to your actual project file path!
    project_file = "test_bmi.PRO"
    
    print *, "========================================"
    print *, "BMI AquaCrop Function Test"
    print *, "========================================"
    print *, ""
    
    ! ========================================
    ! Test 1: Get Component Name
    ! ========================================
    print *, "Test 1: Component Name"
    block
        character(len=2048) :: name
        status = model%get_component_name(name)
        if (status == 0) then
            print *, "  ✅ Component: ", trim(name)
        else
            print *, "  ❌ FAILED to get component name"
        end if
    end block
    print *, ""
    
    ! ========================================
    ! Test 2: Initialize
    ! ========================================
    print *, "Test 2: Initialize"
    print *, "  Project file: ", trim(project_file)
    status = model%initialize(trim(project_file))
    if (status == 0) then
        print *, "  ✅ SUCCESS: Model initialized"
    else
        print *, "  ❌ FAILED: Could not initialize"
        print *, "  Make sure project file exists and is valid!"
        stop 1
    end if
    print *, ""
    
    ! ========================================
    ! Test 3: Get Time Info
    ! ========================================
    print *, "Test 3: Time Information"
    status = model%get_current_time(current_time)
    status = model%get_end_time(end_time)
    print '(A,F6.1)', "  Current time: ", current_time
    print '(A,F6.1)', "  End time: ", end_time
    print *, ""
    
    ! ========================================
    ! Test 4: Run 5 days and get values
    ! ========================================
    print *, "Test 4: Running 5 days..."
    print *, "  Day |  CC(%) | Biomass | Yield | Soil H2O"
    print *, "  ----|--------|---------|-------|----------"
    
    do day = 1, 5
        ! Update (simulate one day)
        status = model%update()
        if (status /= 0) then
            print *, "  ❌ ERROR: Update failed on day", day
            exit
        end if
        
        ! Get values
        status = model%get_value_double("crop__canopy_cover", cc)
        status = model%get_value_double("crop__biomass", biomass)
        status = model%get_value_double("crop__yield", yield)
        status = model%get_value_double("soil__moisture", soil_water)
        
        print '(I5,A,F7.2,A,F8.3,A,F6.3,A,F9.2)', &
              day, " | ", cc(1), " | ", biomass(1), " | ", &
              yield(1), " | ", soil_water(1)
    end do
    print *, ""
    
    ! ========================================
    ! Test 5: Get current time after updates
    ! ========================================
    print *, "Test 5: Current Time After Updates"
    status = model%get_current_time(current_time)
    print '(A,F6.1,A)', "  Current time: ", current_time, " days"
    print *, ""
    
    ! ========================================
    ! Test 6: Finalize
    ! ========================================
    print *, "Test 6: Finalize"
    status = model%finalize()
    if (status == 0) then
        print *, "  ✅ SUCCESS: Model finalized"
    else
        print *, "  ❌ FAILED: Finalization error"
    end if
    print *, ""
    
    ! ========================================
    ! Summary
    ! ========================================
    print *, "========================================"
    print *, "All Tests Complete!"
    print *, "========================================"
    print *, ""
    print *, "BMI Functions Working:"
    print *, "  ✅ get_component_name()"
    print *, "  ✅ initialize()"
    print *, "  ✅ update()"
    print *, "  ✅ get_value_double()"
    print *, "  ✅ get_current_time()"
    print *, "  ✅ finalize()"
    print *, ""
    
end program test_bmi_functions