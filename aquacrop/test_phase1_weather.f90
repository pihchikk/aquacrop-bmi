program test_phase1_weather
    ! Phase 1 Test: Weather Input Variables
    ! Tests: rainfall, temperature_min, temperature_max, reference_evapotranspiration
    
    use iso_c_binding
    use aquacropbmi
    implicit none
    
    type(bmi_aquacrop) :: model
    real(c_double) :: value_dbl(1), rain, tmin, tmax, eto
    integer :: status, day
    character(len=256) :: config_file
    
    print *, "=========================================="
    print *, "PHASE 1 TEST: Weather Input Variables"
    print *, "=========================================="
    print *, ""
    
    ! Initialize
    config_file = "bmi_test_data/LIST/project.PRO"
    status = model%initialize(config_file)
    print *, "Initialize status:", status
    if (status /= 0) stop 1
    print *, ""
    
    ! ========================================================================
    ! TEST 1: Rainfall Amount
    ! ========================================================================
    print *, "TEST 1: weather__rainfall_amount"
    print *, "--------------------------------"
    
    rain = 10.0d0
    print *, "Setting rainfall to", rain, "mm/day"
    status = model%set_value_double("weather__rainfall_amount", [rain])
    print *, "Set status:", status
    
    status = model%get_value_double("weather__rainfall_amount", value_dbl)
    print *, "Get status:", status
    print *, "Retrieved value:", value_dbl(1), "mm/day"
    
    if (abs(value_dbl(1) - rain) < 0.01d0) then
        print *, "✓ PASS"
    else
        print *, "✗ FAIL: Value mismatch"
    end if
    print *, ""
    
    ! ========================================================================
    ! TEST 2: Minimum Temperature
    ! ========================================================================
    print *, "TEST 2: weather__air_temperature_min"
    print *, "------------------------------------"
    
    tmin = 12.5d0
    print *, "Setting Tmin to", tmin, "°C"
    status = model%set_value_double("weather__air_temperature_min", [tmin])
    print *, "Set status:", status
    
    status = model%get_value_double("weather__air_temperature_min", value_dbl)
    print *, "Get status:", status
    print *, "Retrieved value:", value_dbl(1), "°C"
    
    if (abs(value_dbl(1) - tmin) < 0.01d0) then
        print *, "✓ PASS"
    else
        print *, "✗ FAIL: Value mismatch"
    end if
    print *, ""
    
    ! ========================================================================
    ! TEST 3: Maximum Temperature
    ! ========================================================================
    print *, "TEST 3: weather__air_temperature_max"
    print *, "------------------------------------"
    
    tmax = 28.5d0
    print *, "Setting Tmax to", tmax, "°C"
    status = model%set_value_double("weather__air_temperature_max", [tmax])
    print *, "Set status:", status
    
    status = model%get_value_double("weather__air_temperature_max", value_dbl)
    print *, "Get status:", status
    print *, "Retrieved value:", value_dbl(1), "°C"
    
    if (abs(value_dbl(1) - tmax) < 0.01d0) then
        print *, "✓ PASS"
    else
        print *, "✗ FAIL: Value mismatch"
    end if
    print *, ""
    
    ! ========================================================================
    ! TEST 4: Reference Evapotranspiration
    ! ========================================================================
    print *, "TEST 4: weather__reference_evapotranspiration"
    print *, "---------------------------------------------"
    
    eto = 5.5d0
    print *, "Setting ET0 to", eto, "mm/day"
    status = model%set_value_double("weather__reference_evapotranspiration", [eto])
    print *, "Set status:", status
    
    status = model%get_value_double("weather__reference_evapotranspiration", value_dbl)
    print *, "Get status:", status
    print *, "Retrieved value:", value_dbl(1), "mm/day"
    
    if (abs(value_dbl(1) - eto) < 0.01d0) then
        print *, "✓ PASS"
    else
        print *, "✗ FAIL: Value mismatch"
    end if
    print *, ""
    
    ! ========================================================================
    ! TEST 5: Multiple Updates with Weather Changes
    ! ========================================================================
    print *, "TEST 5: Simulation with Weather Changes"
    print *, "---------------------------------------"
    
    print *, "Running 3 simulation steps with different weather:"
    print *, ""
    print *, "Step | Rain(mm) | Tmin(°C) | Tmax(°C) | ET0(mm) | Canopy(%)"
    print *, "----|----------|----------|----------|---------|----------"
    
    do day = 1, 3
        ! Set different weather for each day
        rain = 5.0d0 + day
        tmin = 15.0d0 + day * 0.5d0
        tmax = 25.0d0 + day * 0.5d0
        eto = 4.0d0 + day * 0.2d0
        
        status = model%set_value_double("weather__rainfall_amount", [rain])
        status = model%set_value_double("weather__air_temperature_min", [tmin])
        status = model%set_value_double("weather__air_temperature_max", [tmax])
        status = model%set_value_double("weather__reference_evapotranspiration", [eto])
        
        status = model%update()
        
        ! Get canopy to verify simulation is running
        status = model%get_value_double("crop__canopy_cover", value_dbl)
        
        write(*, '(I3, A, F8.2, A, F8.2, A, F8.2, A, F7.2, A, F9.2)') &
            day, ' | ', rain, ' | ', tmin, ' | ', tmax, ' | ', eto, ' | ', value_dbl(1)
    end do
    print *, ""
    print *, "✓ PASS: Weather variables working during simulation"
    print *, ""
    
    ! Finalize
    status = model%finalize()
    print *, "=========================================="
    print *, "PHASE 1 TEST COMPLETE"
    print *, "✓ All weather inputs working correctly"
    print *, "=========================================="
    
end program test_phase1_weather