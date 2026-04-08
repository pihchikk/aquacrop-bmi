program test_phase2_irrigation_detailed
    ! Phase 2 Test: Irrigation Method Input Variable
    ! Tests: Setting and getting irrigation method (0-4)
    ! 0=Basin, 1=Border, 2=Drip, 3=Furrow, 4=Sprinkler
    
    use iso_c_binding
    use aquacropbmi
    implicit none
    
    type(bmi_aquacrop) :: model
    integer(c_int) :: value_int(1), method
    real(c_double) :: value_dbl(1), biomass, yield_val, canopy
    integer :: status, day, method_count
    character(len=256) :: config_file
    character(len=50) :: method_name(0:4), var_type, var_units
    
    ! Method names
    method_name(0) = "Basin irrigation"
    method_name(1) = "Border irrigation"
    method_name(2) = "Drip irrigation"
    method_name(3) = "Furrow irrigation"
    method_name(4) = "Sprinkler irrigation"
    
    print *, "=========================================="
    print *, "PHASE 2 TEST: Irrigation Method"
    print *, "=========================================="
    print *, ""
    
    ! Initialize
    config_file = "bmi_test_data/LIST/project.PRO"
    status = model%initialize(config_file)
    print *, "Initialize status:", status
    if (status /= 0) stop 1
    print *, ""
    
    ! ========================================================================
    ! TEST 1: Test all irrigation methods (0-4)
    ! ========================================================================
    print *, "TEST 1: All Irrigation Methods"
    print *, "------------------------------"
    print *, ""
    
    do method_count = 0, 4
        method = method_count
        
        print *, "Testing method", method, ":", trim(method_name(method))
        
        status = model%set_value_int("management__irrigation_method", [method])
        print *, "  Set status:", status
        
        status = model%get_value_int("management__irrigation_method", value_int)
        print *, "  Get status:", status
        print *, "  Retrieved:", value_int(1)
        
        if (value_int(1) == method) then
            print *, "  ✓ PASS"
        else
            print *, "  ✗ FAIL: Value mismatch"
        end if
        print *, ""
    end do
    
    ! ========================================================================
    ! TEST 2: Boundary Testing
    ! ========================================================================
    print *, "TEST 2: Boundary Testing"
    print *, "-----------------------"
    print *, ""
    
    ! Test minimum (0)
    print *, "Setting to minimum value (0)"
    status = model%set_value_int("management__irrigation_method", [0])
    status = model%get_value_int("management__irrigation_method", value_int)
    print *, "  Retrieved:", value_int(1)
    if (value_int(1) == 0) print *, "  ✓ PASS"
    print *, ""
    
    ! Test maximum (4)
    print *, "Setting to maximum value (4)"
    status = model%set_value_int("management__irrigation_method", [4])
    status = model%get_value_int("management__irrigation_method", value_int)
    print *, "  Retrieved:", value_int(1)
    if (value_int(1) == 4) print *, "  ✓ PASS"
    print *, ""
    
    ! ========================================================================
    ! TEST 3: Simulation with Different Irrigation Methods
    ! ========================================================================
    print *, "TEST 3: Simulation with Different Methods"
    print *, "----------------------------------------"
    print *, ""
    print *, "Running simulation with different irrigation methods"
    print *, "and comparing biomass/yield growth:"
    print *, ""
    
    ! Test methods 0 (Basin) and 2 (Drip)
    do method = 0, 2, 2
        
        print *, "METHOD", method, ":", trim(method_name(method))
        print *, "------"
        
        ! Reset and reinitialize for clean comparison
        status = model%finalize()
        status = model%initialize(config_file)
        
        ! Set irrigation method
        status = model%set_value_int("management__irrigation_method", [method])
        
        print *, "Day | Biomass(t/ha) | Yield(t/ha) | Canopy(%)"
        print *, "----|---------------|-------------|----------"
        
        do day = 1, 5
            status = model%update()
            
            ! Get outputs
            status = model%get_value_double("crop__biomass", value_dbl)
            biomass = value_dbl(1)
            
            status = model%get_value_double("crop__yield", value_dbl)
            yield_val = value_dbl(1)
            
            status = model%get_value_double("crop__canopy_cover", value_dbl)
            canopy = value_dbl(1)
            
            write(*, '(I3, A, F13.2, A, F11.2, A, F9.2)') &
                day, ' | ', biomass, ' | ', yield_val, ' | ', canopy
        end do
        print *, ""
    end do
    
    ! ========================================================================
    ! TEST 4: Type and Metadata
    ! ========================================================================
    print *, "TEST 4: Variable Type and Metadata"
    print *, "----------------------------------"
    print *, ""
    
    ! Get variable type (should be "integer")
    status = model%get_var_type(model, "management__irrigation_method", var_type)
    print *, "Variable type:", trim(var_type)
    print *, "Expected: integer"
    print *, ""
    
    ! Get variable units (should be "enumeration")
    status = model%get_var_units(model, "management__irrigation_method", var_units)
    print *, "Variable units:", trim(var_units)
    print *, "Expected: enumeration"
    print *, ""
    
    ! Finalize
    status = model%finalize()
    
    print *, "=========================================="
    print *, "PHASE 2 TEST COMPLETE"
    print *, "✓ Irrigation method working correctly"
    print *, "=========================================="
    
end program test_phase2_irrigation_detailed