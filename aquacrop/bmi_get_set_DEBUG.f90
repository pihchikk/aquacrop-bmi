! ========================================================================
! DEBUGGING VERSION OF GET/SET FUNCTIONS
! Replace the aquacrop_get_double and aquacrop_set_double functions with these
! ========================================================================

function aquacrop_get_double(this, name, dest) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
real(c_double), intent(inout) :: dest(:)
integer :: bmi_status
character(len=100) :: debug_name

! DEBUG: Print what we're trying to get
debug_name = trim(adjustl(name))
print *, "DEBUG GET: Trying to get variable: '", trim(debug_name), "'"
print *, "DEBUG GET: Name length: ", len_trim(debug_name)
print *, "DEBUG GET: Comparing with 'crop__fertility_stress'"

! Get actual values from AquaCrop global state
select case(trim(adjustl(name)))
case('crop__fertility_stress')
    ! Get current fertility stress setting (0-100%)
    print *, "DEBUG GET: MATCHED fertility_stress case!"
    print *, "DEBUG GET: Calling GetManagement_FertilityStress()..."
    dest(1) = real(GetManagement_FertilityStress(), c_double)
    print *, "DEBUG GET: Got value: ", dest(1)
    print *, "DEBUG GET: SUCCESS"
case('crop__canopy_cover')
    dest(1) = real(GetCCiActual() * 100.0_dp, c_double)
case('crop__biomass')
    dest(1) = real(GetSumWaBal_Biomass(), c_double)
case('crop__yield')
    dest(1) = real(GetSumWaBal_YieldPart(), c_double)
case('soil__moisture')
    dest(1) = real(GetRootZoneWC_Actual(), c_double)
case default
    print *, "DEBUG GET: NO MATCH! Returning FAILURE"
    print *, "DEBUG GET: Name was: '", trim(debug_name), "'"
    bmi_status = BMI_FAILURE
    return
end select

bmi_status = BMI_SUCCESS
end function aquacrop_get_double

! ------------------------------------------------------------------------

function aquacrop_set_double(this, name, src) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: name
real(c_double), intent(in) :: src(:)
integer :: bmi_status
integer(int8) :: fertility_value
type(rep_EffectStress) :: EffectStress_temp
character(len=100) :: debug_name

! DEBUG: Print what we're trying to set
debug_name = trim(adjustl(name))
print *, "DEBUG SET: Trying to set variable: '", trim(debug_name), "'"
print *, "DEBUG SET: Value: ", src(1)
print *, "DEBUG SET: Comparing with 'crop__fertility_stress'"

! Currently only fertility stress can be set as input
select case(trim(adjustl(name)))
case('crop__fertility_stress')
    print *, "DEBUG SET: MATCHED fertility_stress case!"
    ! Set fertility stress (0-100%)
    ! Convert from double to int8, ensure it's in valid range
    fertility_value = int(max(0.0d0, min(100.0d0, src(1))), int8)
    print *, "DEBUG SET: Converted to int8: ", fertility_value
    
    print *, "DEBUG SET: Calling SetManagement_FertilityStress()..."
    ! Update AquaCrop's internal management state
    call SetManagement_FertilityStress(fertility_value)
    print *, "DEBUG SET: SetManagement_FertilityStress() done"
    
    print *, "DEBUG SET: Calling CropStressParametersSoilFertility()..."
    ! Recalculate stress parameters based on new fertility value
    EffectStress_temp = GetSimulation_EffectStress()
    call CropStressParametersSoilFertility( &
        GetCrop_StressResponse(), &
        fertility_value, &
        EffectStress_temp &
    )
    call SetSimulation_EffectStress(EffectStress_temp)
    print *, "DEBUG SET: CropStressParametersSoilFertility() done"
    
    print *, "DEBUG SET: SUCCESS"
    bmi_status = BMI_SUCCESS
    return
case default
    print *, "DEBUG SET: NO MATCH! Returning FAILURE"
    print *, "DEBUG SET: Name was: '", trim(debug_name), "'"
    bmi_status = BMI_FAILURE
    return
end select

end function aquacrop_set_double
