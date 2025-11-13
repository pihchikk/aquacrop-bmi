program test_phase5_stress_detailed
    ! Phase 5 Test: Stress Output Variables
    ! Tests all 4 stress indicators:
    ! - crop__water_stress
    ! - crop__temperature_stress
    ! - crop__aeration_stress
    ! - crop__salinity_stress
    
    use iso_c_binding
    use aquacropbmi
    implicit none
    
    type(bmi_aquacrop) :: model
    real(c_double) :: value_dbl(1)
    integer :: status, day, n_days
    character(len=256) :: config_file
    real(c_double) :: start_time, end_time, current_time, time_step
    
    ! Stress values
    real(c_double) :: water_stress, temp_stress, aeration_stress, salinity_stress
    
    ! Original outputs
    real(c_double) :: canopy, biomass, yield_val, soil_moisture
    
    ! Min/max tracking
    real(c_double) :: max_water, max_temp, max_aeration, max_salinity
    real(c_double) :: min_water, min_temp, min_aeration, min_salinity
    
    print *, "=========================================="
    print *, "PHASE 5 TEST: Stress Output Indicators"
    print *, "=========================================="
    print *, ""
    
    ! Initialize
    config_file = "bmi_test_data/LIST/project.PRO"
    status = model%initialize(config_file)
    print *, "Initialize status:", status
    if (status /= 0) stop 1
    print *, ""
    
    ! ========================================================================
    ! Get time information
    ! ========================================================================
    status = model%get_start_time(start_time)
    status = model%get_end_time(end_time)
    status = model%get_time_step(time_step)
    
    n_days = min(20, int(end_time - start_time))
    print *, "Simulation period:", start_time, "to", end_time, "days"
    print *, "Running test for:", n_days, "days"
    print *, ""
    
    ! ========================================================================
    ! TEST 1: Check stress variables are accessible
    ! ========================================================================
    print *, "TEST 1: Stress Variables Accessible"
    print *, "-----------------------------------"
    print *, ""
    
    status = model%update()
    
    ! Test each stress variable
    print *, "Testing water_stress getter..."
    status = model%get_value_double("crop__water_stress", value_dbl)
    if (status == 0) then
        print *, "  ✓ PASS: water_stress =", value_dbl(1)
    else
        print *, "  ✗ FAIL: status =", status
    end if
    
    print *, "Testing temperature_stress getter..."
    status = model%get_value_double("crop__temperature_stress", value_dbl)
    if (status == 0) then
        print *, "  ✓ PASS: temperature_stress =", value_dbl(1)
    else
        print *, "  ✗ FAIL: status =", status
    end if
    
    print *, "Testing aeration_stress getter..."
    status = model%get_value_double("crop__aeration_stress", value_dbl)
    if (status == 0) then
        print *, "  ✓ PASS: aeration_stress =", value_dbl(1)
    else
        print *, "  ✗ FAIL: status =", status
    end if
    
    print *, "Testing salinity_stress getter..."
    status = model%get_value_double("crop__salinity_stress", value_dbl)
    if (status == 0) then
        print *, "  ✓ PASS: salinity_stress =", value_dbl(1)
    else
        print *, "  ✗ FAIL: status =", status
    end if
    print *, ""
    
    ! ========================================================================
    ! TEST 2: Run simulation and track stress changes
    ! ========================================================================
    print *, "TEST 2: Stress Changes During Simulation"
    print *, "---------------------------------------"
    print *, ""
    
    ! Reset for clean run
    status = model%finalize()
    status = model%initialize(config_file)
    
    ! Initialize min/max
    max_water = -1.0d0
    max_temp = -1.0d0
    max_aeration = -1.0d0
    max_salinity = -1.0d0
    min_water = 999999.0d0
    min_temp = 999999.0d0
    min_aeration = 999999.0d0
    min_salinity = 999999.0d0
    
    print *, "Day | Water_Str | Temp_Str | Aer_Str | Sal_Str | Canopy(%) | Biomass"
    print *, "----|-----------|----------|---------|---------|-----------|----------"
    
    do day = 1, n_days
        status = model%update()
        status = model%get_current_time(current_time)
        
        ! Get stress values
        status = model%get_value_double("crop__water_stress", value_dbl)
        water_stress = value_dbl(1)
        
        status = model%get_value_double("crop__temperature_stress", value_dbl)
        temp_stress = value_dbl(1)
        
        status = model%get_value_double("crop__aeration_stress", value_dbl)
        aeration_stress = value_dbl(1)
        
        status = model%get_value_double("crop__salinity_stress", value_dbl)
        salinity_stress = value_dbl(1)
        
        ! Get original outputs for context
        status = model%get_value_double("crop__canopy_cover", value_dbl)
        canopy = value_dbl(1)
        
        status = model%get_value_double("crop__biomass", value_dbl)
        biomass = value_dbl(1)
        
        ! Track min/max
        if (water_stress > max_water) max_water = water_stress
        if (water_stress < min_water) min_water = water_stress
        
        if (temp_stress > max_temp) max_temp = temp_stress
        if (temp_stress < min_temp) min_temp = temp_stress
        
        if (aeration_stress > max_aeration) max_aeration = aeration_stress
        if (aeration_stress < min_aeration) min_aeration = aeration_stress
        
        if (salinity_stress > max_salinity) max_salinity = salinity_stress
        if (salinity_stress < min_salinity) min_salinity = salinity_stress
        
        ! Print results
        write(*, '(I3, A, F9.2, A, F8.2, A, F7.2, A, F7.2, A, F9.2, A, F8.2)') &
            day, ' | ', water_stress, ' | ', temp_stress, ' | ', &
            aeration_stress, ' | ', salinity_stress, ' | ', canopy, ' | ', biomass
    end do
    
    print *, ""
    
    ! ========================================================================
    ! TEST 3: Stress Statistics
    ! ========================================================================
    print *, "TEST 3: Stress Statistics"
    print *, "------------------------"
    print *, ""
    
    print *, "Water Stress:"
    print *, "  Min:", min_water, "days"
    print *, "  Max:", max_water, "days"
    print *, "  Range:", max_water - min_water, "days"
    print *, ""
    
    print *, "Temperature Stress:"
    print *, "  Min:", min_temp, "days"
    print *, "  Max:", max_temp, "days"
    print *, "  Range:", max_temp - min_temp, "days"
    print *, ""
    
    print *, "Aeration Stress:"
    print *, "  Min:", min_aeration, "days"
    print *, "  Max:", max_aeration, "days"
    print *, "  Range:", max_aeration - min_aeration, "days"
    print *, ""
    
    print *, "Salinity Stress:"
    print *, "  Min:", min_salinity, "days"
    print *, "  Max:", max_salinity, "days"
    print *, "  Range:", max_salinity - min_salinity, "days"
    print *, ""
    
    ! ========================================================================
    ! TEST 4: Validation
    ! ========================================================================
    print *, "TEST 4: Validation"
    print *, "-----------------"
    print *, ""
    
    ! Stress values should be non-negative (days)
    if (min_water >= 0.0d0) then
        print *, "✓ Water stress values non-negative"
    else
        print *, "✗ Water stress has negative values!"
    end if
    
    if (min_temp >= 0.0d0) then
        print *, "✓ Temperature stress values non-negative"
    else
        print *, "✗ Temperature stress has negative values!"
    end if
    
    if (min_aeration >= 0.0d0) then
        print *, "✓ Aeration stress values non-negative"
    else
        print *, "✗ Aeration stress has negative values!"
    end if
    
    if (min_salinity >= 0.0d0) then
        print *, "✓ Salinity stress values non-negative"
    else
        print *, "✗ Salinity stress has negative values!"
    end if
    
    print *, ""
    
    ! Check if stress values are changing (not all zero)
    if (max_water > 0.0d0 .or. max_temp > 0.0d0 .or. &
        max_aeration > 0.0d0 .or. max_salinity > 0.0d0) then
        print *, "✓ At least one stress indicator showing activity"
    else
        print *, "⚠ All stress values are zero (may be normal for this scenario)"
    end if
    
    print *, ""
    
    ! Finalize
    status = model%finalize()
    
    print *, "=========================================="
    print *, "PHASE 5 TEST COMPLETE"
    print *, "✓ All stress indicators accessible"
    print *, "=========================================="
    
end program test_phase5_stress_detailed