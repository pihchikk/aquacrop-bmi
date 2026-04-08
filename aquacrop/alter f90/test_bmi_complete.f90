program test_bmi_complete
    !===========================================================================
    ! COMPREHENSIVE BMI AQUACROP TEST SUITE
    !===========================================================================
    ! Based on CSDMS bmi-example-fortran test patterns
    ! Tests ALL BMI 2.0 functions systematically
    !
    ! Project file: bmi_test_data/LIST/project.PRO
    !===========================================================================

    use bmiaquacropf
    use bmif_2_0
    use, intrinsic :: iso_c_binding
    implicit none

    type(bmi_aquacrop) :: model
    integer :: status
    integer :: total_tests, passed_tests, failed_tests
    character(len=1024) :: config_file

    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    config_file = "bmi_test_data/LIST/project.PRO"

    print *, ""
    print *, "========================================================================"
    print *, "          BMI AQUACROP COMPREHENSIVE TEST SUITE"
    print *, "========================================================================"
    print *, ""

    ! Run all test categories
    call test_control_functions(model, config_file, total_tests, passed_tests)
    call test_info_functions(model, total_tests, passed_tests)
    call test_time_functions(model, total_tests, passed_tests)
    call test_variable_info(model, total_tests, passed_tests)
    call test_getter_functions(model, total_tests, passed_tests)
    call test_setter_functions(model, total_tests, passed_tests)
    call test_grid_functions(model, total_tests, passed_tests)
    call test_simulation(model, total_tests, passed_tests)

    ! Final results
    failed_tests = total_tests - passed_tests
    
    print *, ""
    print *, "========================================================================"
    print *, "                        TEST SUMMARY"
    print *, "========================================================================"
    print *, ""
    print '(A,I0)', "  Total tests:  ", total_tests
    print '(A,I0)', "  Passed:       ", passed_tests
    print '(A,I0)', "  Failed:       ", failed_tests
    
    if (failed_tests == 0) then
        print *, ""
        print *, "  ✅ ALL TESTS PASSED!"
        print *, ""
    else
        print *, ""
        print *, "  ❌ SOME TESTS FAILED"
        print *, ""
        stop 1
    end if

contains

    !===========================================================================
    ! TEST CATEGORY 1: Control Functions
    !===========================================================================
    subroutine test_control_functions(m, cfg, total, passed)
        type(bmi_aquacrop), intent(inout) :: m
        character(len=*), intent(in) :: cfg
        integer, intent(inout) :: total, passed
        integer :: s
        character(len=BMI_MAX_COMPONENT_NAME), pointer :: name
        
        print *, "------------------------------------------------------------------------"
        print *, "TEST CATEGORY 1: Control Functions"
        print *, "------------------------------------------------------------------------"
        
        ! Test 1.1: get_component_name
        total = total + 1
        s = m%get_component_name(name)
        if (s == BMI_SUCCESS .and. associated(name)) then
            print '(A,A)', "  ✅ 1.1 get_component_name: ", trim(name)
            passed = passed + 1
        else
            print *, "  ❌ 1.1 get_component_name FAILED"
        end if
        
        ! Test 1.2: initialize
        total = total + 1
        s = m%initialize(cfg)
        if (s == BMI_SUCCESS) then
            print *, "  ✅ 1.2 initialize"
            passed = passed + 1
        else
            print *, "  ❌ 1.2 initialize FAILED"
            print *, "     Check that config file exists:", trim(cfg)
            return
        end if
        
        print *, ""
    end subroutine test_control_functions

    !===========================================================================
    ! TEST CATEGORY 2: Model Information Functions
    !===========================================================================
    subroutine test_info_functions(m, total, passed)
        type(bmi_aquacrop), intent(in) :: m
        integer, intent(inout) :: total, passed
        integer :: s, count, i
        character(len=BMI_MAX_VAR_NAME), dimension(:), pointer :: names
        
        print *, "------------------------------------------------------------------------"
        print *, "TEST CATEGORY 2: Model Information Functions"
        print *, "------------------------------------------------------------------------"
        
        ! Test 2.1: get_input_item_count
        total = total + 1
        s = m%get_input_item_count(count)
        if (s == BMI_SUCCESS) then
            print '(A,I0)', "  ✅ 2.1 get_input_item_count: ", count
            passed = passed + 1
        else
            print *, "  ❌ 2.1 get_input_item_count FAILED"
        end if
        
        ! Test 2.2: get_output_item_count
        total = total + 1
        s = m%get_output_item_count(count)
        if (s == BMI_SUCCESS) then
            print '(A,I0)', "  ✅ 2.2 get_output_item_count: ", count
            passed = passed + 1
        else
            print *, "  ❌ 2.2 get_output_item_count FAILED"
        end if
        
        ! Test 2.3: get_input_var_names
        total = total + 1
        s = m%get_input_var_names(names)
        if (s == BMI_SUCCESS .and. associated(names)) then
            print *, "  ✅ 2.3 get_input_var_names:"
            do i = 1, size(names)
                print '(A,I0,A,A)', "       ", i, ": ", trim(names(i))
            end do
            passed = passed + 1
        else
            print *, "  ❌ 2.3 get_input_var_names FAILED"
        end if
        
        ! Test 2.4: get_output_var_names
        total = total + 1
        s = m%get_output_var_names(names)
        if (s == BMI_SUCCESS .and. associated(names)) then
            print *, "  ✅ 2.4 get_output_var_names:"
            do i = 1, size(names)
                print '(A,I0,A,A)', "       ", i, ": ", trim(names(i))
            end do
            passed = passed + 1
        else
            print *, "  ❌ 2.4 get_output_var_names FAILED"
        end if
        
        print *, ""
    end subroutine test_info_functions

    !===========================================================================
    ! TEST CATEGORY 3: Time Functions
    !===========================================================================
    subroutine test_time_functions(m, total, passed)
        type(bmi_aquacrop), intent(in) :: m
        integer, intent(inout) :: total, passed
        integer :: s
        real(c_double) :: time_val
        character(len=BMI_MAX_UNITS_NAME) :: units
        
        print *, "------------------------------------------------------------------------"
        print *, "TEST CATEGORY 3: Time Functions"
        print *, "------------------------------------------------------------------------"
        
        ! Test 3.1: get_start_time
        total = total + 1
        s = m%get_start_time(time_val)
        if (s == BMI_SUCCESS) then
            print '(A,F10.2)', "  ✅ 3.1 get_start_time: ", time_val
            passed = passed + 1
        else
            print *, "  ❌ 3.1 get_start_time FAILED"
        end if
        
        ! Test 3.2: get_current_time
        total = total + 1
        s = m%get_current_time(time_val)
        if (s == BMI_SUCCESS) then
            print '(A,F10.2)', "  ✅ 3.2 get_current_time: ", time_val
            passed = passed + 1
        else
            print *, "  ❌ 3.2 get_current_time FAILED"
        end if
        
        ! Test 3.3: get_end_time
        total = total + 1
        s = m%get_end_time(time_val)
        if (s == BMI_SUCCESS) then
            print '(A,F10.2)', "  ✅ 3.3 get_end_time: ", time_val
            passed = passed + 1
        else
            print *, "  ❌ 3.3 get_end_time FAILED"
        end if
        
        ! Test 3.4: get_time_step
        total = total + 1
        s = m%get_time_step(time_val)
        if (s == BMI_SUCCESS) then
            print '(A,F10.2)', "  ✅ 3.4 get_time_step: ", time_val
            passed = passed + 1
        else
            print *, "  ❌ 3.4 get_time_step FAILED"
        end if
        
        ! Test 3.5: get_time_units
        total = total + 1
        s = m%get_time_units(units)
        if (s == BMI_SUCCESS) then
            print '(A,A)', "  ✅ 3.5 get_time_units: ", trim(units)
            passed = passed + 1
        else
            print *, "  ❌ 3.5 get_time_units FAILED"
        end if
        
        print *, ""
    end subroutine test_time_functions

    !===========================================================================
    ! TEST CATEGORY 4: Variable Information Functions
    !===========================================================================
    subroutine test_variable_info(m, total, passed)
        type(bmi_aquacrop), intent(in) :: m
        integer, intent(inout) :: total, passed
        integer :: s, itemsize, nbytes, grid
        character(len=*), parameter :: test_var = "crop__canopy_cover"
        character(len=BMI_MAX_TYPE_NAME) :: var_type
        character(len=BMI_MAX_UNITS_NAME) :: units
        character(len=BMI_MAX_VAR_NAME) :: location
        
        print *, "------------------------------------------------------------------------"
        print *, "TEST CATEGORY 4: Variable Information Functions"
        print *, "------------------------------------------------------------------------"
        print '(A,A)', "  Testing variable: ", test_var
        print *, ""
        
        ! Test 4.1: get_var_type
        total = total + 1
        s = m%get_var_type(test_var, var_type)
        if (s == BMI_SUCCESS) then
            print '(A,A)', "  ✅ 4.1 get_var_type: ", trim(var_type)
            passed = passed + 1
        else
            print *, "  ❌ 4.1 get_var_type FAILED"
        end if
        
        ! Test 4.2: get_var_units
        total = total + 1
        s = m%get_var_units(test_var, units)
        if (s == BMI_SUCCESS) then
            print '(A,A)', "  ✅ 4.2 get_var_units: ", trim(units)
            passed = passed + 1
        else
            print *, "  ❌ 4.2 get_var_units FAILED"
        end if
        
        ! Test 4.3: get_var_itemsize
        total = total + 1
        s = m%get_var_itemsize(test_var, itemsize)
        if (s == BMI_SUCCESS) then
            print '(A,I0,A)', "  ✅ 4.3 get_var_itemsize: ", itemsize, " bytes"
            passed = passed + 1
        else
            print *, "  ❌ 4.3 get_var_itemsize FAILED"
        end if
        
        ! Test 4.4: get_var_nbytes
        total = total + 1
        s = m%get_var_nbytes(test_var, nbytes)
        if (s == BMI_SUCCESS) then
            print '(A,I0,A)', "  ✅ 4.4 get_var_nbytes: ", nbytes, " bytes"
            passed = passed + 1
        else
            print *, "  ❌ 4.4 get_var_nbytes FAILED"
        end if
        
        ! Test 4.5: get_var_location
        total = total + 1
        s = m%get_var_location(test_var, location)
        if (s == BMI_SUCCESS) then
            print '(A,A)', "  ✅ 4.5 get_var_location: ", trim(location)
            passed = passed + 1
        else
            print *, "  ❌ 4.5 get_var_location FAILED"
        end if
        
        ! Test 4.6: get_var_grid
        total = total + 1
        s = m%get_var_grid(test_var, grid)
        if (s == BMI_SUCCESS) then
            print '(A,I0)', "  ✅ 4.6 get_var_grid: ", grid
            passed = passed + 1
        else
            print *, "  ❌ 4.6 get_var_grid FAILED"
        end if
        
        print *, ""
    end subroutine test_variable_info

    !===========================================================================
    ! TEST CATEGORY 5: Variable Getter Functions
    !===========================================================================
    subroutine test_getter_functions(m, total, passed)
        type(bmi_aquacrop), intent(in) :: m
        integer, intent(inout) :: total, passed
        integer :: s
        real(c_double) :: val(1)
        character(len=*), parameter :: vars(4) = [ &
            "crop__canopy_cover", &
            "crop__biomass     ", &
            "crop__yield       ", &
            "soil__moisture    " ]
        integer :: i
        
        print *, "------------------------------------------------------------------------"
        print *, "TEST CATEGORY 5: Variable Getter Functions"
        print *, "------------------------------------------------------------------------"
        
        do i = 1, size(vars)
            ! Test get_value_double for each output variable
            total = total + 1
            s = m%get_value_double(trim(vars(i)), val)
            if (s == BMI_SUCCESS) then
                print '(A,I0,A,A,A,F10.3)', "  ✅ 5.", i, " get_value_double(", &
                    trim(vars(i)), "): ", val(1)
                passed = passed + 1
            else
                print '(A,I0,A,A)', "  ❌ 5.", i, " get_value_double(", &
                    trim(vars(i)), ") FAILED"
            end if
        end do
        
        print *, ""
    end subroutine test_getter_functions

    !===========================================================================
    ! TEST CATEGORY 6: Variable Setter Functions (Expected to Fail)
    !===========================================================================
    subroutine test_setter_functions(m, total, passed)
        type(bmi_aquacrop), intent(inout) :: m
        integer, intent(inout) :: total, passed
        integer :: s
        real(c_double) :: val(1)
        
        print *, "------------------------------------------------------------------------"
        print *, "TEST CATEGORY 6: Variable Setter Functions"
        print *, "------------------------------------------------------------------------"
        print *, "  Note: Setters are not yet implemented (expected to return FAILURE)"
        print *, ""
        
        ! Test 6.1: set_value_double (expected to fail)
        total = total + 1
        val(1) = 50.0d0
        s = m%set_value_double("crop__fertility_stress", val)
        if (s == BMI_FAILURE) then
            print *, "  ✅ 6.1 set_value_double returns FAILURE (as expected)"
            passed = passed + 1
        else
            print *, "  ❌ 6.1 set_value_double should return FAILURE"
        end if
        
        print *, ""
    end subroutine test_setter_functions

    !===========================================================================
    ! TEST CATEGORY 7: Grid Information Functions
    !===========================================================================
    subroutine test_grid_functions(m, total, passed)
        type(bmi_aquacrop), intent(in) :: m
        integer, intent(inout) :: total, passed
        integer :: s, grid_id, rank_val, size_val, node_count
        character(len=BMI_MAX_TYPE_NAME) :: grid_type
        real(c_double) :: x(1), y(1), z(1)
        
        print *, "------------------------------------------------------------------------"
        print *, "TEST CATEGORY 7: Grid Information Functions"
        print *, "------------------------------------------------------------------------"
        
        grid_id = 0  ! AquaCrop uses scalar grid (grid 0)
        
        ! Test 7.1: get_grid_type
        total = total + 1
        s = m%get_grid_type(grid_id, grid_type)
        if (s == BMI_SUCCESS) then
            print '(A,A)', "  ✅ 7.1 get_grid_type: ", trim(grid_type)
            passed = passed + 1
        else
            print *, "  ❌ 7.1 get_grid_type FAILED"
        end if
        
        ! Test 7.2: get_grid_rank
        total = total + 1
        s = m%get_grid_rank(grid_id, rank_val)
        if (s == BMI_SUCCESS) then
            print '(A,I0)', "  ✅ 7.2 get_grid_rank: ", rank_val
            passed = passed + 1
        else
            print *, "  ❌ 7.2 get_grid_rank FAILED"
        end if
        
        ! Test 7.3: get_grid_size
        total = total + 1
        s = m%get_grid_size(grid_id, size_val)
        if (s == BMI_SUCCESS) then
            print '(A,I0)', "  ✅ 7.3 get_grid_size: ", size_val
            passed = passed + 1
        else
            print *, "  ❌ 7.3 get_grid_size FAILED"
        end if
        
        ! Test 7.4: get_grid_x
        total = total + 1
        s = m%get_grid_x(grid_id, x)
        if (s == BMI_SUCCESS) then
            print '(A,F10.2)', "  ✅ 7.4 get_grid_x: ", x(1)
            passed = passed + 1
        else
            print *, "  ❌ 7.4 get_grid_x FAILED"
        end if
        
        ! Test 7.5: get_grid_y
        total = total + 1
        s = m%get_grid_y(grid_id, y)
        if (s == BMI_SUCCESS) then
            print '(A,F10.2)', "  ✅ 7.5 get_grid_y: ", y(1)
            passed = passed + 1
        else
            print *, "  ❌ 7.5 get_grid_y FAILED"
        end if
        
        ! Test 7.6: get_grid_z
        total = total + 1
        s = m%get_grid_z(grid_id, z)
        if (s == BMI_SUCCESS) then
            print '(A,F10.2)', "  ✅ 7.6 get_grid_z: ", z(1)
            passed = passed + 1
        else
            print *, "  ❌ 7.6 get_grid_z FAILED"
        end if
        
        ! Test 7.7: get_grid_node_count
        total = total + 1
        s = m%get_grid_node_count(grid_id, node_count)
        if (s == BMI_SUCCESS) then
            print '(A,I0)', "  ✅ 7.7 get_grid_node_count: ", node_count
            passed = passed + 1
        else
            print *, "  ❌ 7.7 get_grid_node_count FAILED"
        end if
        
        print *, ""
    end subroutine test_grid_functions

    !===========================================================================
    ! TEST CATEGORY 8: Simulation (Update) Functions
    !===========================================================================
    subroutine test_simulation(m, total, passed)
        type(bmi_aquacrop), intent(inout) :: m
        integer, intent(inout) :: total, passed
        integer :: s, day
        real(c_double) :: current_time, end_time, cc(1)
        
        print *, "------------------------------------------------------------------------"
        print *, "TEST CATEGORY 8: Simulation (Update) Functions"
        print *, "------------------------------------------------------------------------"
        
        s = m%get_end_time(end_time)
        
        ! Test 8.1: update() for 10 days
        total = total + 1
        print *, "  Running simulation for 10 days..."
        do day = 1, 10
            s = m%update()
            if (s /= BMI_SUCCESS) exit
        end do
        
        if (s == BMI_SUCCESS) then
            s = m%get_current_time(current_time)
            s = m%get_value_double("crop__canopy_cover", cc)
            print '(A,F6.0,A,F8.2,A)', "  ✅ 8.1 update (10 days): Day ", &
                current_time, ", CC=", cc(1), "%"
            passed = passed + 1
        else
            print *, "  ❌ 8.1 update FAILED"
        end if
        
        ! Test 8.2: update_until
        total = total + 1
        s = m%get_current_time(current_time)
        s = m%update_until(current_time + 10.0d0)
        if (s == BMI_SUCCESS) then
            s = m%get_current_time(current_time)
            print '(A,F6.0,A)', "  ✅ 8.2 update_until: Day ", current_time, ""
            passed = passed + 1
        else
            print *, "  ❌ 8.2 update_until FAILED"
        end if
        
        ! Test 8.3: finalize
        total = total + 1
        s = m%finalize()
        if (s == BMI_SUCCESS) then
            print *, "  ✅ 8.3 finalize"
            passed = passed + 1
        else
            print *, "  ❌ 8.3 finalize FAILED"
        end if
        
        print *, ""
    end subroutine test_simulation

end program test_bmi_complete