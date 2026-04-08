! ========================================================================
! REVISED SETTER - Handles missing crop data gracefully
! ========================================================================
! Replace the aquacrop_set_double function with this version

function aquacrop_set_double(this, name, src) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: name
real(c_double), intent(in) :: src(:)
integer :: bmi_status
integer(int8) :: fertility_value
type(rep_EffectStress) :: EffectStress_temp
real(dp) :: crop_ccx

! Currently only fertility stress can be set as input
select case(trim(name))
case('crop__fertility_stress')
    ! Set fertility stress (0-100%)
    ! Convert from double to int8, ensure it's in valid range
    fertility_value = int(max(0.0d0, min(100.0d0, src(1))), int8)
    
    ! Update AquaCrop's internal management state
    call SetManagement_FertilityStress(fertility_value)
    
    ! Only recalculate stress parameters if crop data is loaded
    ! Check if crop is initialized by testing if CCx > 0
    crop_ccx = GetCrop_CCx()
    if (crop_ccx > 0.0_dp) then
        ! Crop is loaded, can recalculate stress parameters
        EffectStress_temp = GetSimulation_EffectStress()
        call CropStressParametersSoilFertility( &
            GetCrop_StressResponse(), &
            fertility_value, &
            EffectStress_temp &
        )
        call SetSimulation_EffectStress(EffectStress_temp)
    end if
    ! If crop not loaded, just setting FertilityStress is enough
    ! It will be used when/if crop gets loaded later
    
    bmi_status = BMI_SUCCESS
    return
case default
    bmi_status = BMI_FAILURE
    return
end select

end function aquacrop_set_double
