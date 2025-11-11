! ========================================================================
! DEBUG VERSION of aquacrop_get_double
! Replace lines 489-525 in bmi_aquacrop.f90 with this
! ========================================================================

function aquacrop_get_double(this, name, dest) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
real(c_double), intent(inout) :: dest(:)
integer :: bmi_status
integer(int8) :: fert_val_debug

! DEBUG: Print what we're doing
print *, "=== DEBUG aquacrop_get_double ==="
print *, "Input name: '", trim(name), "'"
print *, "Name length: ", len_trim(name)

! Get actual values from AquaCrop global state
select case(trim(name))
case('crop__fertility_stress')
    print *, "  MATCHED case: crop__fertility_stress"
    ! Get current fertility stress setting (0-100%)
    ! This is an input variable that affects crop growth
    print *, "  Calling GetManagement_FertilityStress()..."
    fert_val_debug = GetManagement_FertilityStress()
    print *, "  Got value (int8):", fert_val_debug
    dest(1) = real(fert_val_debug, c_double)
    print *, "  Converted to double:", dest(1)
    print *, "  Setting bmi_status = BMI_SUCCESS"
case('crop__canopy_cover')
    print *, "  MATCHED case: crop__canopy_cover"
    ! Get CURRENT actual canopy cover (CCiActual), not CCini
    ! CCiActual is updated during simulation and represents the actual canopy cover
    ! Returns as percentage (0-100)
    dest(1) = real(GetCCiActual() * 100.0_dp, c_double)
case('crop__biomass')
    print *, "  MATCHED case: crop__biomass"
    ! Get cumulative biomass production in tonnes/ha
    ! This is the total above-ground dry biomass produced
    dest(1) = real(GetSumWaBal_Biomass(), c_double)
case('crop__yield')
    print *, "  MATCHED case: crop__yield"
    ! Get cumulative yield in tonnes/ha
    ! This is the harvestable yield (grain, tubers, etc.)
    dest(1) = real(GetSumWaBal_YieldPart(), c_double)
case('soil__moisture')
    print *, "  MATCHED case: soil__moisture"
    ! Get root zone water content in mm
    ! Returns actual water content in the active root zone only
    ! (not the full soil profile, only where roots are extracting water)
    dest(1) = real(GetRootZoneWC_Actual(), c_double)
case default
    print *, "  NO MATCH! Hit default case - returning FAILURE"
    bmi_status = BMI_FAILURE
    return
end select

print *, "  After select case, setting bmi_status = BMI_SUCCESS"
bmi_status = BMI_SUCCESS
print *, "=== END DEBUG ==="
end function aquacrop_get_double
