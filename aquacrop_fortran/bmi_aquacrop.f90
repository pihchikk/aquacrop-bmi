module aquacropbmi

use ac_kinds, only: dp, int32, int8, intEnum  ! Add intEnum to imports

use ac_global, only: GetCCiActual, GetSumWaBal_Biomass, &
                     GetSumWaBal_YieldPart, GetRootZoneWC_Actual, &
                     GetSimulation_FromDayNr, GetSimulation_ToDayNr, &
                     SetManagement_FertilityStress, GetManagement_FertilityStress, &
                     CropStressParametersSoilFertility, GetCrop_StressResponse, &
                     GetSimulation_EffectStress, SetSimulation_EffectStress, &
                     rep_EffectStress, rep_sim, &
                     ! Weather getters/setters for Phase 1
                     GetRain, SetRain, GetETo, SetETo, &
                     GetTmin, SetTmin, GetTmax, SetTmax, &
                     GetIrriMethod, SetIrriMethod, & ! handadded 19:59 11.11.25
                     GetSimulation, & ! Phase 5: Get simulation struct for DayAnaero
                     GetRootingDepth, & ! Phase 4: Rooting depth
                     GetSoilLayer_WaterContent, GetSoil_NrSoilLayers, & ! Phase 3: Soil layers
                     GetSoilLayerTheta, & ! Dynamic compartment-based soil moisture
                     ! Phase 6: Management inputs
                     GetManagement_Mulch, SetManagement_Mulch, &
                     GetManagement_BundHeight, SetManagement_BundHeight, &
                     GetManagement_WeedRC, SetManagement_WeedRC, &
                     ! Irrigation getters/setters
                     GetIrrigation, SetIrrigation, &
                    GetSumWaBal_Irrigation, SetSumWabal_Irrigation, &
                     ! BMI persistent weather overrides
                     BMI_has_Tmin_override, &
                     BMI_has_Tmax_override, &
                     BMI_has_Rain_override, &
                     BMI_has_ETo_override, &
                     BMI_Tmin_override_value, &
                     BMI_Tmax_override_value, &
                     BMI_Rain_override_value, &
                     BMI_ETo_override_value, &
                     SetZiAqua, SetECiAqua
use ac_run, only: BMI_SimulateOneDay, GetDayNri, &
                  GetStressTot_Temp, GetStressTot_Exp, GetStressTot_Sto, GetStressTot_Salt, &
                  GetSumWaBal_Tact, GetSumWaBal_Eact, GetSumWaBal_BiomassPot, & ! Phase 4
                  GetPreviousSum_Irrigation, SetPreviousSum_Irrigation, & ! Phase 2
                  GetCO2i, SetCO2i ! Phase 6: CO2 concentration
use ac_startunit, only: BMI_InitializeAquaCrop, BMI_FinalizeAquaCrop
use bmif_2_0
use, intrinsic :: iso_c_binding, only: c_ptr, c_loc, c_f_pointer, c_double, &
                                        c_int, c_float, c_char, c_sizeof
implicit none

type, extends (bmi) :: bmi_aquacrop
    private
    ! Model state
    real(c_double) :: current_time
    real(c_double) :: time_step
    real(c_double) :: end_time
    integer :: current_day
    integer :: current_season
    logical :: initialized
    logical :: finalized
contains
    ! BMI: Model Control Functions
    procedure :: get_component_name => aquacrop_component_name
    procedure :: initialize => aquacrop_initialize
    procedure :: finalize => aquacrop_finalize
    procedure :: update => aquacrop_update
    procedure :: update_until => aquacrop_update_until
    
    ! BMI: Model Information Functions
    procedure :: get_input_item_count => aquacrop_input_item_count
    procedure :: get_output_item_count => aquacrop_output_item_count
    procedure :: get_input_var_names => aquacrop_input_var_names
    procedure :: get_output_var_names => aquacrop_output_var_names
    
    ! BMI: Time Functions
    procedure :: get_start_time => aquacrop_start_time
    procedure :: get_end_time => aquacrop_end_time
    procedure :: get_current_time => aquacrop_current_time
    procedure :: get_time_step => aquacrop_time_step
    procedure :: get_time_units => aquacrop_time_units
    
    ! BMI: Variable Information Functions
    procedure :: get_var_type => aquacrop_var_type
    procedure :: get_var_units => aquacrop_var_units
    procedure :: get_var_itemsize => aquacrop_var_itemsize
    procedure :: get_var_nbytes => aquacrop_var_nbytes
    procedure :: get_var_location => aquacrop_var_location
    procedure :: get_var_grid => aquacrop_var_grid
    
    ! BMI: Variable Getter and Setter Functions
    procedure :: get_value_int => aquacrop_get_int
    procedure :: get_value_float => aquacrop_get_float
    procedure :: get_value_double => aquacrop_get_double
    
    ! Get value pointer (3 Ãƒâ€˜Ã¢â‚¬Å¾Ãƒâ€˜Ã†â€™ÃƒÂÃ‚Â½ÃƒÂÃ‚ÂºÃƒâ€˜Ã¢â‚¬Â ÃƒÂÃ‚Â¸ÃƒÂÃ‚Â¸ ÃƒÂÃ‚Â²ÃƒÂÃ‚Â¼ÃƒÂÃ‚ÂµÃƒâ€˜Ã‚ÂÃƒâ€˜Ã¢â‚¬Å¡ÃƒÂÃ‚Â¾ 1):
    procedure :: get_value_ptr_int => aquacrop_get_ptr_int
    procedure :: get_value_ptr_float => aquacrop_get_ptr_float  
    procedure :: get_value_ptr_double => aquacrop_get_ptr_double

    procedure :: get_value_at_indices_int => aquacrop_get_at_indices_int
    procedure :: get_value_at_indices_float => aquacrop_get_at_indices_float
    procedure :: get_value_at_indices_double => aquacrop_get_at_indices_double
    
    procedure :: set_value_int => aquacrop_set_int
    procedure :: set_value_float => aquacrop_set_float
    procedure :: set_value_double => aquacrop_set_double
    
    procedure :: set_value_at_indices_int => aquacrop_set_at_indices_int
    procedure :: set_value_at_indices_float => aquacrop_set_at_indices_float
    procedure :: set_value_at_indices_double => aquacrop_set_at_indices_double
    
    ! BMI: Grid Information Functions
    procedure :: get_grid_type => aquacrop_grid_type
    procedure :: get_grid_rank => aquacrop_grid_rank
    procedure :: get_grid_size => aquacrop_grid_size
    procedure :: get_grid_shape => aquacrop_grid_shape
    procedure :: get_grid_spacing => aquacrop_grid_spacing
    procedure :: get_grid_origin => aquacrop_grid_origin
    procedure :: get_grid_x => aquacrop_grid_x
    procedure :: get_grid_y => aquacrop_grid_y
    procedure :: get_grid_z => aquacrop_grid_z
    procedure :: get_grid_node_count => aquacrop_grid_node_count
    procedure :: get_grid_edge_count => aquacrop_grid_edge_count
    procedure :: get_grid_face_count => aquacrop_grid_face_count
    procedure :: get_grid_edge_nodes => aquacrop_grid_edge_nodes
    procedure :: get_grid_face_edges => aquacrop_grid_face_edges
    procedure :: get_grid_face_nodes => aquacrop_grid_face_nodes
    procedure :: get_grid_nodes_per_face => aquacrop_grid_nodes_per_face
    
    ! Generic interfaces for babelizer compatibility
    generic :: get_value => get_value_int, get_value_float, get_value_double
    generic :: get_value_ptr => get_value_ptr_int, get_value_ptr_float, get_value_ptr_double
    generic :: get_value_at_indices => get_value_at_indices_int, get_value_at_indices_float, get_value_at_indices_double
    generic :: set_value => set_value_int, set_value_float, set_value_double
    generic :: set_value_at_indices => set_value_at_indices_int, set_value_at_indices_float, set_value_at_indices_double

    ! Helper procedures
    procedure :: print_model_info
end type bmi_aquacrop

private
public :: bmi_aquacrop

! Model metadata
character(len=BMI_MAX_COMPONENT_NAME), target :: &
    component_name = "AquaCrop"

! Exchange items
integer, parameter :: input_item_count = 14
integer, parameter :: output_item_count = 23

character(len=BMI_MAX_VAR_NAME), target, dimension(input_item_count) :: &
    input_items = (/ &
    'plant_fertility-stress               ', &
    'air_precipitation                    ', &
    'air_temperature_minimum~day          ', &
    'air_temperature_maximal~day          ', &
    'air_evapotranspiration~reference     ', &
    'management_irrigation_method         ', &
    'management_irrigation_amount         ', &
    'atmosphere_co2-concentration         ', &
    'management_mulch-cover               ', &
    'management_bund-height               ', &
    'management_weed-cover                ', &
    'bmi__clear_weather_overrides         ', &
    'groundwater__depth                   ', &
    'groundwater__ec                      ' &
    /)

character(len=BMI_MAX_VAR_NAME), target, dimension(output_item_count) :: &
    output_items = (/ &
    'plant_cover~projective       ', &
    'plant_biomass~above-ground   ', &
    'plant_yield~standard         ', &
    'soil_water_actual            ', &
    'plant_stress_water           ', &
    'plant_stress_temperature     ', &
    'plant_stress_aeration        ', &
    'plant_stress_salinity        ', &
    'plant_root_depth             ', &
    'air_transpiration            ', &
    'air_evapotranspiration~plants', &
    'plant_biomass_potential      ', &
    'soil_water_actual_layer-1    ', &
    'soil_water_actual_layer-2    ', &
    'soil_water_actual_layer-3    ', &
    'soil_water_actual_layer-4    ', &
    'soil_water_actual_layer-5    ', &
    'soil_water_actual_layer-6    ', &
    'soil_water_actual_layer-7    ', &
    'soil_water_actual_layer-8    ', &
    'soil_water_actual_layer-9    ', &
    'soil_water_actual_layer-10   ', &
    'soil__water_content_in_layers' &
    /)

contains

! ========================================================================
! Alias resolver: maps old CSDMS names to canonical ESoil names
! ========================================================================

function resolve_var_alias(name) result(canonical)
    character(len=*), intent(in) :: name
    character(len=BMI_MAX_VAR_NAME) :: canonical

    select case(trim(name))
    case('crop__yield');                    canonical = 'plant_yield~standard'
    case('crop__biomass');                  canonical = 'plant_biomass~above-ground'
    case('crop__biomass_potential');        canonical = 'plant_biomass_potential'
    case('crop__canopy_cover');             canonical = 'plant_cover~projective'
    case('crop__rooting_depth');            canonical = 'plant_root_depth'
    case('crop__transpiration');            canonical = 'air_transpiration'
    case('crop__evapotranspiration');       canonical = 'air_evapotranspiration~plants'
    case('crop__water_stress');             canonical = 'plant_stress_water'
    case('crop__temperature_stress');       canonical = 'plant_stress_temperature'
    case('crop__aeration_stress');          canonical = 'plant_stress_aeration'
    case('crop__salinity_stress');          canonical = 'plant_stress_salinity'
    case('soil__moisture');                 canonical = 'soil_water_actual'
    case('soil__moisture_layer_1');         canonical = 'soil_water_actual_layer-1'
    case('soil__moisture_layer_2');         canonical = 'soil_water_actual_layer-2'
    case('soil__moisture_layer_3');         canonical = 'soil_water_actual_layer-3'
    case('soil__moisture_layer_4');         canonical = 'soil_water_actual_layer-4'
    case('soil__moisture_layer_5');         canonical = 'soil_water_actual_layer-5'
    case('soil__moisture_layer_6');         canonical = 'soil_water_actual_layer-6'
    case('soil__moisture_layer_7');         canonical = 'soil_water_actual_layer-7'
    case('soil__moisture_layer_8');         canonical = 'soil_water_actual_layer-8'
    case('soil__moisture_layer_9');         canonical = 'soil_water_actual_layer-9'
    case('soil__moisture_layer_10');        canonical = 'soil_water_actual_layer-10'
    case('weather__rainfall_amount');               canonical = 'air_precipitation'
    case('weather__air_temperature_max');           canonical = 'air_temperature_maximal~day'
    case('weather__air_temperature_min');           canonical = 'air_temperature_minimum~day'
    case('weather__reference_evapotranspiration');  canonical = 'air_evapotranspiration~reference'
    case('management__irrigation_amount');          canonical = 'management_irrigation_amount'
    case('management__irrigation_method');          canonical = 'management_irrigation_method'
    case('management__mulch_cover');                canonical = 'management_mulch-cover'
    case('management__bund_height');                canonical = 'management_bund-height'
    case('management__weed_cover');                 canonical = 'management_weed-cover'
    case('management__surface_storage');            canonical = 'management_surface-storage'
    case('atmosphere__co2_concentration');          canonical = 'atmosphere_co2-concentration'
    case('crop__fertility_stress');                 canonical = 'plant_fertility-stress'
    case default
        canonical = name
    end select
end function resolve_var_alias

! ========================================================================
! BMI: Model Control Functions
! ========================================================================

function aquacrop_component_name(this, name) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), pointer, intent(out) :: name
character(len=BMI_MAX_COMPONENT_NAME), target, save :: component_name = "AquaCrop"
integer :: bmi_status

name => component_name
bmi_status = BMI_SUCCESS
end function aquacrop_component_name

! ------------------------------------------------------------------------

function aquacrop_initialize(this, config_file) result(bmi_status)
use ac_global, only: SetPathNameOutp, SetOutputName  
class(bmi_aquacrop), intent(out) :: this
character(len=*), intent(in) :: config_file
integer :: bmi_status
integer :: aquacrop_status
integer(int32) :: from_day, to_day

!call SetPathNameOutp('')
!call SetOutputName('')     

! Call AquaCrop initialization
! This loads the project file and sets up the simulation
call BMI_InitializeAquaCrop(config_file, aquacrop_status)

! Check if initialization succeeded
if (aquacrop_status /= 0) then
    print *, "ERROR: AquaCrop initialization failed with status:", aquacrop_status
    bmi_status = BMI_FAILURE
    return
end if

! Get actual simulation period from AquaCrop
from_day = GetSimulation_FromDayNr()
to_day = GetSimulation_ToDayNr()

! Set up BMI state variables
this%current_time = 0.0d0  ! Start at day 0 (relative time)
this%time_step = 1.0d0     ! Daily time step (AquaCrop is daily only)
this%end_time = real(to_day - from_day, c_double)  ! Duration in days
this%current_day = from_day
this%current_season = 0
this%initialized = .true.
this%finalized = .false.

print *, "  Simulation period: Day", from_day, "to", to_day
print *, "  Duration:", int(this%end_time), "days"

bmi_status = BMI_SUCCESS
end function aquacrop_initialize

! ------------------------------------------------------------------------

function aquacrop_update(this) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
integer :: bmi_status
integer :: aquacrop_status

if (.not. this%initialized) then
    bmi_status = BMI_FAILURE
    return
end if

! Call AquaCrop to simulate one day
call BMI_SimulateOneDay(aquacrop_status)

! Check status
select case(aquacrop_status)
case(0)
    ! Normal - continue
    this%current_time = this%current_time + this%time_step
    bmi_status = BMI_SUCCESS
case(1)
    ! Simulation complete
    this%current_time = this%current_time + this%time_step
    bmi_status = BMI_SUCCESS
    ! Note: Caller should check end_time to know simulation is done
case default
    ! Error
    bmi_status = BMI_FAILURE
    return
end select

! Sync day counter with AquaCrop's internal state
this%current_day = GetDayNri()

bmi_status = BMI_SUCCESS
end function aquacrop_update

! ------------------------------------------------------------------------

function aquacrop_update_until(this, time) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
real(c_double), intent(in) :: time
integer :: bmi_status

do while (this%current_time < time)
    bmi_status = this%update()
    if (bmi_status /= BMI_SUCCESS) return
end do

bmi_status = BMI_SUCCESS
end function aquacrop_update_until

! ------------------------------------------------------------------------

function aquacrop_finalize(this) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
integer :: bmi_status
integer :: aquacrop_status

! Call AquaCrop cleanup
! This closes files, deallocates memory, writes final outputs
call BMI_FinalizeAquaCrop(aquacrop_status)

! Update BMI state
this%finalized = .true.
this%initialized = .false.

bmi_status = BMI_SUCCESS
end function aquacrop_finalize

! ========================================================================
! BMI: Model Information Functions
! ========================================================================

function aquacrop_input_item_count(this, count) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(out) :: count
integer :: bmi_status

count = input_item_count
bmi_status = BMI_SUCCESS
end function aquacrop_input_item_count

! ------------------------------------------------------------------------

function aquacrop_output_item_count(this, count) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(out) :: count
integer :: bmi_status

count = output_item_count
bmi_status = BMI_SUCCESS
end function aquacrop_output_item_count

! ------------------------------------------------------------------------

function aquacrop_input_var_names(this, names) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: this
    character(len=*), pointer, intent(out) :: names(:)
    integer :: bmi_status

    names => input_items   ! â† Point to the full array with 11 variables
    bmi_status = BMI_SUCCESS
end function aquacrop_input_var_names

! ------------------------------------------------------------------------

function aquacrop_output_var_names(this, names) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(*), pointer, intent(out) :: names(:)
integer :: bmi_status

names => output_items
bmi_status = BMI_SUCCESS
end function aquacrop_output_var_names

! ========================================================================
! BMI: Time Functions
! ========================================================================

function aquacrop_start_time(this, time) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
real(c_double), intent(out) :: time
integer :: bmi_status

time = 0.0d0
bmi_status = BMI_SUCCESS
end function aquacrop_start_time

! ------------------------------------------------------------------------

function aquacrop_end_time(this, time) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
real(c_double), intent(out) :: time
integer :: bmi_status

time = this%end_time
bmi_status = BMI_SUCCESS
end function aquacrop_end_time

! ------------------------------------------------------------------------

function aquacrop_current_time(this, time) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
real(c_double), intent(out) :: time
integer :: bmi_status

time = this%current_time
bmi_status = BMI_SUCCESS
end function aquacrop_current_time

! ------------------------------------------------------------------------

function aquacrop_time_step(this, time_step) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
real(c_double), intent(out) :: time_step
integer :: bmi_status

time_step = this%time_step
bmi_status = BMI_SUCCESS
end function aquacrop_time_step

! ------------------------------------------------------------------------

function aquacrop_time_units(this, units) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(out) :: units
integer :: bmi_status

units = "days"
bmi_status = BMI_SUCCESS
end function aquacrop_time_units

! ========================================================================
! BMI: Variable Information Functions
! ========================================================================

function aquacrop_var_grid(this, name, grid) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
integer, intent(out) :: grid
integer :: bmi_status
character(len=BMI_MAX_VAR_NAME) :: resolved

resolved = resolve_var_alias(name)
select case(trim(resolved))
case('soil__water_content_in_layers')
    grid = 1
case default
    grid = 0
end select
bmi_status = BMI_SUCCESS
end function aquacrop_var_grid

! ------------------------------------------------------------------------

function aquacrop_var_type(this, name, type) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
character(len=*), intent(out) :: type
integer :: bmi_status

character(len=BMI_MAX_VAR_NAME) :: resolved

resolved = resolve_var_alias(name)
select case(trim(resolved))
case('management_irrigation_method')
    type = "real*8"
case default
    type = "real*8"
end select

bmi_status = BMI_SUCCESS
end function aquacrop_var_type

! ------------------------------------------------------------------------

function aquacrop_var_units(this, name, units) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
character(len=*), intent(out) :: units
integer :: bmi_status
character(len=BMI_MAX_VAR_NAME) :: resolved

resolved = resolve_var_alias(name)
select case(trim(resolved))
case('plant_cover~projective')
    units = "percent"
case('plant_biomass~above-ground')
    units = "tonnes/ha"
case('plant_yield~standard')
    units = "tonnes/ha"
case('soil_water_actual')
    units = "mm"
case('plant_fertility-stress')
    units = "percent"
case('air_precipitation')
    units = "mm/day"
case('air_temperature_minimum~day')
    units = "degrees_Celsius"
case('air_temperature_maximal~day')
    units = "degrees_Celsius"
case('air_evapotranspiration~reference')
    units = "mm/day"
case('management_irrigation_method')
    units = "enumeration"
case('plant_stress_water')
    units = "days"
case('plant_stress_temperature')
    units = "days"
case('plant_stress_aeration')
    units = "days"
case('plant_stress_salinity')
    units = "days"
case('plant_root_depth')
    units = "m"
case('air_transpiration')
    units = "mm"
case('air_evapotranspiration~plants')
    units = "mm"
case('plant_biomass_potential')
    units = "tonnes/ha"
case('management_irrigation_amount')
    units = "mm"
case('soil_water_actual_layer-1','soil_water_actual_layer-2','soil_water_actual_layer-3', &
     'soil_water_actual_layer-4','soil_water_actual_layer-5','soil_water_actual_layer-6', &
     'soil_water_actual_layer-7','soil_water_actual_layer-8','soil_water_actual_layer-9', &
     'soil_water_actual_layer-10','soil__water_content_in_layers')
    units = 'm3 m-3'
case('atmosphere_co2-concentration')
    units = "ppm"
case('management_mulch-cover')
    units = "%"
case('management_bund-height')
    units = "m"
case('management_weed-cover')
    units = "%"
case('groundwater__depth')
    units = 'm'
case('groundwater__ec')
    units = 'dS m-1'
case default
    units = "-"
end select

bmi_status = BMI_SUCCESS
end function aquacrop_var_units

! ------------------------------------------------------------------------

function aquacrop_var_itemsize(this, name, size) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
integer, intent(out) :: size
integer :: bmi_status
character(len=BMI_MAX_VAR_NAME) :: resolved

resolved = resolve_var_alias(name)
select case(trim(resolved))
case('management_irrigation_method')
    size = c_sizeof(0)  ! Integer size (4 bytes)
case default
    size = c_sizeof(0.0d0)  ! Double precision (8 bytes)
end select

bmi_status = BMI_SUCCESS
end function aquacrop_var_itemsize

! ------------------------------------------------------------------------

function aquacrop_var_nbytes(this, name, nbytes) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
integer, intent(out) :: nbytes
integer :: bmi_status
integer :: grid, gsize

bmi_status = this%get_var_grid(name, grid)
bmi_status = this%get_grid_size(grid, gsize)
nbytes = gsize * int(c_sizeof(0.0d0))

bmi_status = BMI_SUCCESS
end function aquacrop_var_nbytes

! ------------------------------------------------------------------------

function aquacrop_var_location(this, name, location) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
character(len=*), intent(out) :: location
integer :: bmi_status

location = "node"
bmi_status = BMI_SUCCESS
end function aquacrop_var_location

! ========================================================================
! BMI: Variable Getter and Setter Functions
! ========================================================================

! Get value functions (copy data)

function aquacrop_get_int(this, name, dest) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
integer, intent(inout) :: dest(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Integer values not used in AquaCrop BMI
end function aquacrop_get_int

! ------------------------------------------------------------------------

function aquacrop_get_float(this, name, dest) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
real(c_float), intent(inout) :: dest(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! We use double precision, not float
end function aquacrop_get_float

! ------------------------------------------------------------------------

function aquacrop_get_double(this, name, dest) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
real(c_double), intent(inout) :: dest(:)
integer :: bmi_status, i
type(rep_sim) :: sim_temp
character(len=BMI_MAX_VAR_NAME) :: resolved

resolved = resolve_var_alias(name)
select case(trim(resolved))
case('plant_fertility-stress')
    ! Get current fertility stress setting (0-100%)
    ! This is an input variable that affects crop growth
    dest(1) = real(GetManagement_FertilityStress(), c_double)
case('air_precipitation')
    ! Get current day's rainfall in mm/day
    dest(1) = real(GetRain(), c_double)
case('air_temperature_minimum~day')
    ! Get current day's minimum air temperature in degrees Celsius
    dest(1) = real(GetTmin(), c_double)
case('air_temperature_maximal~day')
    ! Get current day's maximum air temperature in degrees Celsius
    dest(1) = real(GetTmax(), c_double)
case('air_evapotranspiration~reference')
    ! Get current day's reference evapotranspiration (ET0) in mm/day
    dest(1) = real(GetETo(), c_double) ! hand added 20:02 11.11.25
case('management_irrigation_method')
    ! Get current irrigation method
    ! 0=Basin, 1=Border, 2=Drip, 3=Furrow, 4=Sprinkler
    dest(1) = real(GetIrriMethod(), c_double)
case('management_irrigation_amount')
    ! Get cumulative irrigation amount applied
    ! Phase 2 addition: Dynamic irrigation tracking
    ! Units: mm (cumulative)
    dest(1) = real(GetIrrigation(), c_double)  
case('atmosphere_co2-concentration')
    ! Get current atmospheric CO2 concentration
    ! Phase 6 addition: Climate change scenarios
    ! Units: ppm
    dest(1) = real(GetCO2i(), c_double)
case('management_mulch-cover')
    ! Get soil mulch cover percentage
    ! Phase 6 addition: Field management
    ! Units: percent (0-100)
    dest(1) = real(GetManagement_Mulch(), c_double)
case('management_bund-height')
    ! Get water retention bund height
    ! Phase 6 addition: Field management
    ! Units: meters
    dest(1) = real(GetManagement_BundHeight(), c_double)
case('management_weed-cover')
    ! Get weed relative cover percentage
    ! Phase 6 addition: Field management
    ! Units: percent (0-100)
    dest(1) = real(GetManagement_WeedRC(), c_double)
case('plant_cover~projective')
    ! Get CURRENT actual canopy cover (CCiActual), not CCini
    ! CCiActual is updated during simulation and represents the actual canopy cover
    ! Returns as percentage (0-100)
    dest(1) = real(GetCCiActual() * 100.0_dp, c_double)
case('plant_biomass~above-ground')
    ! Get cumulative biomass production in tonnes/ha
    ! This is the total above-ground dry biomass produced
    dest(1) = real(GetSumWaBal_Biomass(), c_double)
case('plant_yield~standard')
    ! Get cumulative yield in tonnes/ha
    ! This is the harvestable yield (grain, tubers, etc.)
    dest(1) = real(GetSumWaBal_YieldPart(), c_double)
case('soil_water_actual')
    ! Get root zone water content in mm
    ! Returns actual water content in the active root zone only
    ! (not the full soil profile, only where roots are extracting water)
    dest(1) = real(GetRootZoneWC_Actual(), c_double)
case('plant_stress_water')
    ! Get water stress (stomatal + expansion) - cumulative stress from storage and leaf expansion
    ! Phase 5 addition: Returns stress from water stress on stomata (GetStressTot_Sto)
    ! Value range: 0-100+ (cumulative days or percentage)
    dest(1) = real(GetStressTot_Sto(), c_double)
case('plant_stress_temperature')
    ! Get temperature stress - cumulative temperature stress days
    ! Phase 5 addition: Temperature stress factor
    ! Value range: 0-100+ (cumulative)
    dest(1) = real(GetStressTot_Temp(), c_double)
case('plant_stress_aeration')
    ! Get aeration stress - days under anaerobic conditions
    ! Phase 5 addition: Aeration/oxygen stress indicator
    ! Value: number of days with waterlogging
    sim_temp = GetSimulation()
    dest(1) = real(sim_temp%DayAnaero, c_double)
case('plant_stress_salinity')
    ! Get salinity stress - cumulative salt stress
    ! Phase 5 addition: Salt stress indicator
    ! Value range: 0-100+ (cumulative)
    dest(1) = real(GetStressTot_Salt(), c_double)
case('plant_root_depth')
    ! Get current rooting depth in meters
    ! Phase 4 addition: Crop root development indicator
    ! Value range: 0-3+ (meters)
    dest(1) = real(GetRootingDepth(), c_double)
case('air_transpiration')
    ! Get cumulative actual crop transpiration
    ! Phase 4 addition: Water use by crop
    ! Value: Cumulative mm of water transpired
    dest(1) = real(GetSumWaBal_Tact(), c_double)
case('air_evapotranspiration~plants')
    ! Get cumulative actual evapotranspiration (E + Tr)
    ! Phase 4 addition: Total water loss from field
    ! Value: Cumulative mm (soil evaporation + crop transpiration)
    dest(1) = real(GetSumWaBal_Eact(), c_double)
case('plant_biomass_potential')
    ! Get potential biomass without stress
    ! Phase 4 addition: Biomass production if no stress
    ! Value: t/ha
    dest(1) = real(GetSumWaBal_BiomassPot(), c_double)
case('soil_water_actual_layer-1')
    if (GetSoil_NrSoilLayers() >= 1) then
        dest(1) = real(GetSoilLayerTheta(1), c_double)
    else
        dest(1) = -999.0d0  ! Layer doesn't exist
    end if
case('soil_water_actual_layer-2')
    if (GetSoil_NrSoilLayers() >= 2) then
        dest(1) = real(GetSoilLayerTheta(2), c_double)
    else
        dest(1) = -999.0d0
    end if
case('soil_water_actual_layer-3')
    if (GetSoil_NrSoilLayers() >= 3) then
        dest(1) = real(GetSoilLayerTheta(3), c_double)
    else
        dest(1) = -999.0d0
    end if
case('soil_water_actual_layer-4')
    if (GetSoil_NrSoilLayers() >= 4) then
        dest(1) = real(GetSoilLayerTheta(4), c_double)
    else
        dest(1) = -999.0d0
    end if
case('soil_water_actual_layer-5')
    if (GetSoil_NrSoilLayers() >= 5) then
        dest(1) = real(GetSoilLayerTheta(5), c_double)
    else
        dest(1) = -999.0d0
    end if
case('soil_water_actual_layer-6')
    if (GetSoil_NrSoilLayers() >= 6) then
        dest(1) = real(GetSoilLayerTheta(6), c_double)
    else
        dest(1) = -999.0d0
    end if
case('soil_water_actual_layer-7')
    if (GetSoil_NrSoilLayers() >= 7) then
        dest(1) = real(GetSoilLayerTheta(7), c_double)
    else
        dest(1) = -999.0d0
    end if
case('soil_water_actual_layer-8')
    if (GetSoil_NrSoilLayers() >= 8) then
        dest(1) = real(GetSoilLayerTheta(8), c_double)
    else
        dest(1) = -999.0d0
    end if
case('soil_water_actual_layer-9')
    if (GetSoil_NrSoilLayers() >= 9) then
        dest(1) = real(GetSoilLayerTheta(9), c_double)
    else
        dest(1) = -999.0d0
    end if
case('soil_water_actual_layer-10')
    if (GetSoil_NrSoilLayers() >= 10) then
        dest(1) = real(GetSoilLayerTheta(10), c_double)
    else
        dest(1) = -999.0d0
    end if
case('soil__water_content_in_layers')
    do i = 1, GetSoil_NrSoilLayers()
        dest(i) = real(GetSoilLayerTheta(i), c_double)
    end do
case default
    bmi_status = BMI_FAILURE
    return
end select

bmi_status = BMI_SUCCESS
end function aquacrop_get_double

! ------------------------------------------------------------------------
! Set value functions (copy data in)

function aquacrop_set_int(this, name, src) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: name
integer, intent(in) :: src(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Integer values not used in AquaCrop BMI
end function aquacrop_set_int

! ------------------------------------------------------------------------

function aquacrop_set_float(this, name, src) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: name
real(c_float), intent(in) :: src(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! We use double precision, not float
end function aquacrop_set_float

! ------------------------------------------------------------------------

function aquacrop_set_double(this, name, src) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: name
real(c_double), intent(in) :: src(:)
integer :: bmi_status
integer(int8) :: fertility_value
type(rep_EffectStress) :: EffectStress_temp
character(len=BMI_MAX_VAR_NAME) :: resolved

resolved = resolve_var_alias(name)
select case(trim(resolved))
case('plant_fertility-stress')
    ! Set fertility stress (0-100%)
    ! Convert from double to int8, ensure it's in valid range
    fertility_value = int(max(0.0d0, min(100.0d0, src(1))), int8)
    
    ! Update AquaCrop's internal management state
    call SetManagement_FertilityStress(fertility_value)
    
    ! Recalculate stress parameters based on new fertility value
    ! This follows the pattern used in global.f90 when loading management files
    EffectStress_temp = GetSimulation_EffectStress()
    call CropStressParametersSoilFertility( &
        GetCrop_StressResponse(), &
        fertility_value, &
        EffectStress_temp &
    )
    call SetSimulation_EffectStress(EffectStress_temp)
    
    bmi_status = BMI_SUCCESS
    return
case('air_precipitation')
    ! Set current day's rainfall in mm/day
    ! Phase 7: Use persistent override system
    BMI_Rain_override_value = real(max(0.0d0, src(1)), dp)
    BMI_has_Rain_override = .true.
    call SetRain(BMI_Rain_override_value)
    bmi_status = BMI_SUCCESS
    return
case('air_temperature_minimum~day')
    ! Set current day's minimum air temperature in degrees Celsius
    ! Phase 7: Use persistent override system
    BMI_Tmin_override_value = real(src(1), dp)
    BMI_has_Tmin_override = .true.
    call SetTmin(BMI_Tmin_override_value)
    bmi_status = BMI_SUCCESS
    return
case('air_temperature_maximal~day')
    ! Set current day's maximum air temperature in degrees Celsius
    ! Phase 7: Use persistent override system
    BMI_Tmax_override_value = real(src(1), dp)
    BMI_has_Tmax_override = .true.
    call SetTmax(BMI_Tmax_override_value)
    bmi_status = BMI_SUCCESS
    return
case('management_irrigation_method') ! hand added 20:02 11.11.25
    ! Set irrigation method (0=Basin, 1=Border, 2=Drip, 3=Furrow, 4=Sprinkler)
    ! Clamp to valid range [0, 4]
    call SetIrriMethod(int(nint(max(0.0d0, min(4.0d0, src(1)))), kind=int8))
    bmi_status = BMI_SUCCESS
    return
case('air_evapotranspiration~reference')
    ! Set current day's reference evapotranspiration (ET0) in mm/day
    ! Phase 7: Use persistent override system
    BMI_ETo_override_value = real(max(0.0d0, src(1)), dp)
    BMI_has_ETo_override = .true.
    call SetETo(BMI_ETo_override_value)
    bmi_status = BMI_SUCCESS
    return
case('management_irrigation_amount')
    ! Set daily irrigation amount in mm/day
    ! Phase 2 addition: Allows dynamic irrigation scheduling
    ! *** CRITICAL FIX: Must set both current irrigation AND update sum ***
    call SetIrrigation(real(max(0.0d0, src(1)), dp))  ! Set TODAY's irrigation
    ! Also update sum for proper accounting
    call SetSumWabal_Irrigation(GetSumWaBal_Irrigation() + real(max(0.0d0, src(1)), dp))
    bmi_status = BMI_SUCCESS
    return
case('atmosphere_co2-concentration')
    ! Set atmospheric CO2 concentration
    ! Phase 6 addition: Climate change scenarios
    ! Units: ppm (parts per million)
    call SetCO2i(real(max(280.0d0, src(1)), dp))  ! Clamp to realistic min
    bmi_status = BMI_SUCCESS
    return
case('management_mulch-cover')
    ! Set mulch soil cover percentage
    ! Phase 6 addition: Field management
    ! Units: percent (0-100)
    call SetManagement_Mulch(int(max(0.0d0, min(100.0d0, src(1))), int8))
    bmi_status = BMI_SUCCESS
    return
case('management_bund-height')
    ! Set water retention bund height
    ! Phase 6 addition: Field management
    ! Units: meters
    call SetManagement_BundHeight(real(max(0.0d0, src(1)), dp))
    bmi_status = BMI_SUCCESS
    return
case('management_weed-cover')
    ! Set weed relative cover percentage
    ! Phase 6 addition: Field management
    ! Units: percent (0-100)
    call SetManagement_WeedRC(int(max(0.0d0, min(100.0d0, src(1))), int8))
    bmi_status = BMI_SUCCESS
    return
case('bmi__clear_weather_overrides')
    ! Clear all weather overrides, return to file-based values
    ! Phase 7: Reset all persistent weather overrides
    ! Any non-zero value will clear all overrides
    if (src(1) /= 0.0d0) then
        BMI_has_Tmin_override = .false.
        BMI_has_Tmax_override = .false.
        BMI_has_Rain_override = .false.
        BMI_has_ETo_override = .false.
    end if
    bmi_status = BMI_SUCCESS
    return
case('groundwater__depth')
    call SetZiAqua(int(src(1) * 100.0d0))
    bmi_status = BMI_SUCCESS
    return
case('groundwater__ec')
    call SetECiAqua(src(1))
    bmi_status = BMI_SUCCESS
    return
case default
    bmi_status = BMI_FAILURE
    return
end select

end function aquacrop_set_double

! ========================================================================
! BMI: Grid Information Functions
! ========================================================================

function aquacrop_grid_type(this, grid, type) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
character(len=*), intent(out) :: type
integer :: bmi_status

select case(grid)
case(0)
    type = "scalar"
    bmi_status = BMI_SUCCESS
case(1)
    type = 'uniform_rectilinear'
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_type

! ------------------------------------------------------------------------

function aquacrop_grid_rank(this, grid, rank) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
integer, intent(out) :: rank
integer :: bmi_status

select case(grid)
case(0)
    rank = 0
    bmi_status = BMI_SUCCESS
case(1)
    rank = 1
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_rank

! ------------------------------------------------------------------------

function aquacrop_grid_size(this, grid, size) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
integer, intent(out) :: size
integer :: bmi_status

select case(grid)
case(0)
    size = 1
    bmi_status = BMI_SUCCESS
case(1)
    size = int(GetSoil_NrSoilLayers())
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_size

! ------------------------------------------------------------------------

function aquacrop_grid_shape(this, grid, shape) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
integer, dimension(:), intent(out) :: shape
integer :: bmi_status

select case(grid)
case(1)
    shape(1) = int(GetSoil_NrSoilLayers())
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_shape

! ------------------------------------------------------------------------

function aquacrop_grid_spacing(this, grid, spacing) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
real(c_double), dimension(:), intent(out) :: spacing
integer :: bmi_status

select case(grid)
case(1)
    spacing(1) = 1.0d0
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_spacing

! ------------------------------------------------------------------------

function aquacrop_grid_origin(this, grid, origin) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
real(c_double), dimension(:), intent(out) :: origin
integer :: bmi_status

select case(grid)
case(1)
    origin(1) = 0.0d0
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_origin

! ------------------------------------------------------------------------

function aquacrop_grid_x(this, grid, x) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
real(c_double), dimension(:), intent(out) :: x
integer :: bmi_status

select case(grid)
case(0)
    ! TODO: Get from project longitude
    x(1) = 0.0d0
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_x

! ------------------------------------------------------------------------

function aquacrop_grid_y(this, grid, y) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
real(c_double), dimension(:), intent(out) :: y
integer :: bmi_status

select case(grid)
case(0)
    ! TODO: Get from project latitude
    y(1) = 0.0d0
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_y

! ------------------------------------------------------------------------

function aquacrop_grid_z(this, grid, z) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
real(c_double), dimension(:), intent(out) :: z
integer :: bmi_status

select case(grid)
case(0)
    ! TODO: Get from project altitude
    z(1) = 0.0d0
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_z

! ------------------------------------------------------------------------

function aquacrop_grid_node_count(this, grid, count) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
integer, intent(out) :: count
integer :: bmi_status

select case(grid)
case(0)
    count = 1
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_node_count

! ------------------------------------------------------------------------

function aquacrop_grid_edge_count(this, grid, count) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
integer, intent(out) :: count
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_edge_count

! ------------------------------------------------------------------------

function aquacrop_grid_face_count(this, grid, count) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
integer, intent(out) :: count
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_face_count

! ------------------------------------------------------------------------

function aquacrop_grid_edge_nodes(this, grid, edge_nodes) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
integer, dimension(:), intent(out) :: edge_nodes
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_edge_nodes

! ------------------------------------------------------------------------

function aquacrop_grid_face_edges(this, grid, face_edges) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
integer, dimension(:), intent(out) :: face_edges
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_face_edges

! ------------------------------------------------------------------------

function aquacrop_grid_face_nodes(this, grid, face_nodes) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
integer, dimension(:), intent(out) :: face_nodes
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_face_nodes

! ------------------------------------------------------------------------

function aquacrop_grid_nodes_per_face(this, grid, nodes_per_face) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid
integer, dimension(:), intent(out) :: nodes_per_face
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_nodes_per_face

! ========================================================================
! Get value pointer functions - typed versions
! ========================================================================

function aquacrop_get_ptr_int(this, name, dest_ptr) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
integer, pointer, intent(inout) :: dest_ptr(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not implemented - AquaCrop state not directly accessible as pointers
end function aquacrop_get_ptr_int

! ------------------------------------------------------------------------

function aquacrop_get_ptr_float(this, name, dest_ptr) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
real, pointer, intent(inout) :: dest_ptr(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not implemented
end function aquacrop_get_ptr_float

! ------------------------------------------------------------------------

function aquacrop_get_ptr_double(this, name, dest_ptr) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
double precision, pointer, intent(inout) :: dest_ptr(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not implemented - would need to expose AquaCrop global variables
end function aquacrop_get_ptr_double

! ========================================================================
! Get value at indices - typed versions
! ========================================================================

function aquacrop_get_at_indices_int(this, name, dest, inds) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
integer, intent(inout) :: dest(:)
integer, intent(in) :: inds(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_get_at_indices_int

! ------------------------------------------------------------------------

function aquacrop_get_at_indices_float(this, name, dest, inds) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
real, intent(inout) :: dest(:)
integer, intent(in) :: inds(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable
end function aquacrop_get_at_indices_float

! ------------------------------------------------------------------------

function aquacrop_get_at_indices_double(this, name, dest, inds) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: name
double precision, intent(inout) :: dest(:)
integer, intent(in) :: inds(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_get_at_indices_double

! ========================================================================
! Set value at indices - typed versions
! ========================================================================

function aquacrop_set_at_indices_int(this, name, inds, src) &
    result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: name
integer, intent(in) :: inds(:)
integer, intent(in) :: src(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_set_at_indices_int

! ------------------------------------------------------------------------

function aquacrop_set_at_indices_float(this, name, inds, src) &
    result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: name
integer, intent(in) :: inds(:)
real, intent(in) :: src(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable
end function aquacrop_set_at_indices_float

! ------------------------------------------------------------------------

function aquacrop_set_at_indices_double(this, name, inds, src) &
    result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: name
integer, intent(in) :: inds(:)
double precision, intent(in) :: src(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_set_at_indices_double

! ========================================================================
! Helper Functions
! ========================================================================

subroutine print_model_info(this)
class(bmi_aquacrop), intent(in) :: this

print *, "Model name:      ", component_name
print *, "Input items:     ", input_item_count
print *, "Output items:    ", output_item_count
print *, "Time step:       ", this%time_step, " days"
print *, "Start time:      ", 0.0d0, " days"
print *, "End time:        ", this%end_time, " days"
end subroutine print_model_info

end module aquacropbmi