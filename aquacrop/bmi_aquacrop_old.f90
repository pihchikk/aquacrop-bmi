module bmiaquacropf

use ac_global
use ac_run
use bmif_2_0
use, intrinsic :: iso_c_binding, only: c_ptr, c_loc, c_f_pointer
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
    generic :: get_value => &
        get_value_int, &
        get_value_float, &
        get_value_double
    
    procedure :: get_value_ptr_int => aquacrop_get_ptr_int
    procedure :: get_value_ptr_float => aquacrop_get_ptr_float
    procedure :: get_value_ptr_double => aquacrop_get_ptr_double
    generic :: get_value_ptr => &
        get_value_ptr_int, &
        get_value_ptr_float, &
        get_value_ptr_double
    
    procedure :: get_value_at_indices_int => aquacrop_get_at_indices_int
    procedure :: get_value_at_indices_float => aquacrop_get_at_indices_float
    procedure :: get_value_at_indices_double => aquacrop_get_at_indices_double
    generic :: get_value_at_indices => &
        get_value_at_indices_int, &
        get_value_at_indices_float, &
        get_value_at_indices_double
    
    procedure :: set_value_int => aquacrop_set_int
    procedure :: set_value_float => aquacrop_set_float
    procedure :: set_value_double => aquacrop_set_double
    generic :: set_value => &
        set_value_int, &
        set_value_float, &
        set_value_double
    
    procedure :: set_value_at_indices_int => aquacrop_set_at_indices_int
    procedure :: set_value_at_indices_float => aquacrop_set_at_indices_float
    procedure :: set_value_at_indices_double => aquacrop_set_at_indices_double
    generic :: set_value_at_indices => &
        set_value_at_indices_int, &
        set_value_at_indices_float, &
        set_value_at_indices_double
    
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
    
    ! Helper procedures
    procedure :: print_model_info
end type bmi_aquacrop

private
public :: bmi_aquacrop

! Model metadata
character(len=BMI_MAX_COMPONENT_NAME), target :: &
    component_name = "AquaCrop"

! Exchange items
integer, parameter :: input_item_count = 1
integer, parameter :: output_item_count = 4

character(len=BMI_MAX_VAR_NAME), target, dimension(input_item_count) :: &
    input_items = (/ &
    'crop__fertility_stress' &
    /)

character(len=BMI_MAX_VAR_NAME), target, dimension(output_item_count) :: &
    output_items = (/ &
    'crop__canopy_cover', &
    'crop__biomass     ', &
    'crop__yield       ', &
    'soil__moisture    ' &
    /)

contains

! ========================================================================
! BMI: Model Control Functions
! ========================================================================

function aquacrop_component_name(this, name) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), pointer, intent(out) :: name
integer :: bmi_status

name => component_name
bmi_status = BMI_SUCCESS
end function aquacrop_component_name

! ------------------------------------------------------------------------

function aquacrop_initialize(this, config_file) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: config_file
integer :: bmi_status

! TODO: Call AquaCrop initialization
! For now, just set up BMI state
this%current_time = 0.0d0
this%time_step = 1.0d0  ! Daily time step
this%end_time = 214.0d0  ! TODO: Get from project file
this%current_day = 0
this%current_season = 0
this%initialized = .true.
this%finalized = .false.

bmi_status = BMI_SUCCESS
end function aquacrop_initialize

! ------------------------------------------------------------------------

function aquacrop_update(this) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
integer :: bmi_status

if (.not. this%initialized) then
    bmi_status = BMI_FAILURE
    return
end if

! TODO: Call AquaCrop single-day simulation
this%current_time = this%current_time + this%time_step
this%current_day = this%current_day + 1

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

! TODO: Cleanup AquaCrop resources
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
character(*), pointer, intent(out) :: names(:)
integer :: bmi_status

names => input_items
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

function aquacrop_var_grid(this, var_name, grid_id) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
integer, intent(out) :: grid_id
integer :: bmi_status

! All variables on scalar grid (grid 0)
grid_id = 0
bmi_status = BMI_SUCCESS
end function aquacrop_var_grid

! ------------------------------------------------------------------------

function aquacrop_var_type(this, var_name, var_type) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
character(len=*), intent(out) :: var_type
integer :: bmi_status

! All our variables are double precision
var_type = "double"
bmi_status = BMI_SUCCESS
end function aquacrop_var_type

! ------------------------------------------------------------------------

function aquacrop_var_units(this, var_name, var_units) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
character(len=*), intent(out) :: var_units
integer :: bmi_status

select case(var_name)
case('crop__canopy_cover')
    var_units = "percent"
case('crop__biomass')
    var_units = "tonnes/ha"
case('crop__yield')
    var_units = "tonnes/ha"
case('soil__moisture')
    var_units = "mm"
case('crop__fertility_stress')
    var_units = "percent"
case default
    var_units = "-"
end select

bmi_status = BMI_SUCCESS
end function aquacrop_var_units

! ------------------------------------------------------------------------

function aquacrop_var_itemsize(this, var_name, var_size) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
integer, intent(out) :: var_size
integer :: bmi_status

! Size of double precision
var_size = c_sizeof(0.0d0)
bmi_status = BMI_SUCCESS
end function aquacrop_var_itemsize

! ------------------------------------------------------------------------

function aquacrop_var_nbytes(this, var_name, var_nbytes) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
integer, intent(out) :: var_nbytes
integer :: bmi_status
integer :: grid_size, item_size

! For scalar grid: nbytes = grid_size * item_size
grid_size = 1
item_size = c_sizeof(0.0d0)
var_nbytes = grid_size * item_size

bmi_status = BMI_SUCCESS
end function aquacrop_var_nbytes

! ------------------------------------------------------------------------

function aquacrop_var_location(this, var_name, var_loc) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
character(len=*), intent(out) :: var_loc
integer :: bmi_status

var_loc = "node"
bmi_status = BMI_SUCCESS
end function aquacrop_var_location

! ========================================================================
! BMI: Variable Getter and Setter Functions
! ========================================================================

! Get value functions (copy data)

function aquacrop_get_int(this, var_name, dest) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
integer, intent(inout) :: dest(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Integer values not used in AquaCrop BMI
end function aquacrop_get_int

! ------------------------------------------------------------------------

function aquacrop_get_float(this, var_name, dest) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
real(c_float), intent(inout) :: dest(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! We use double precision, not float
end function aquacrop_get_float

! ------------------------------------------------------------------------

function aquacrop_get_double(this, var_name, dest) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
real(c_double), intent(inout) :: dest(:)
integer :: bmi_status

! TODO: Get actual values from AquaCrop global state
select case(var_name)
case('crop__canopy_cover')
    dest(1) = 0.0d0  ! TODO: Get from GetCrop_CCx or similar
case('crop__biomass')
    dest(1) = 0.0d0  ! TODO: Get from biomass state
case('crop__yield')
    dest(1) = 0.0d0  ! TODO: Get from yield state
case('soil__moisture')
    dest(1) = 0.0d0  ! TODO: Get from soil water content
case default
    bmi_status = BMI_FAILURE
    return
end select

bmi_status = BMI_SUCCESS
end function aquacrop_get_double

! ------------------------------------------------------------------------
! Get value pointer functions (reference, no copy)

function aquacrop_get_ptr_int(this, var_name, dest_ptr) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
integer, pointer, intent(inout) :: dest_ptr(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not implemented - AquaCrop state not directly accessible
end function aquacrop_get_ptr_int

! ------------------------------------------------------------------------

function aquacrop_get_ptr_float(this, var_name, dest_ptr) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
real(c_float), pointer, intent(inout) :: dest_ptr(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not implemented
end function aquacrop_get_ptr_float

! ------------------------------------------------------------------------

function aquacrop_get_ptr_double(this, var_name, dest_ptr) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
real(c_double), pointer, intent(inout) :: dest_ptr(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not implemented - would need to expose AquaCrop global variables
end function aquacrop_get_ptr_double

! ------------------------------------------------------------------------
! Get value at indices

function aquacrop_get_at_indices_int(this, var_name, dest, inds) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
integer, intent(inout) :: dest(:)
integer, intent(in) :: inds(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_get_at_indices_int

! ------------------------------------------------------------------------

function aquacrop_get_at_indices_float(this, var_name, dest, inds) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
real(c_float), intent(inout) :: dest(:)
integer, intent(in) :: inds(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable
end function aquacrop_get_at_indices_float

! ------------------------------------------------------------------------

function aquacrop_get_at_indices_double(this, var_name, dest, inds) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
character(len=*), intent(in) :: var_name
real(c_double), intent(inout) :: dest(:)
integer, intent(in) :: inds(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_get_at_indices_double

! ------------------------------------------------------------------------
! Set value functions

function aquacrop_set_int(this, var_name, src) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: var_name
integer, intent(in) :: src(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Integer values not used
end function aquacrop_set_int

! ------------------------------------------------------------------------

function aquacrop_set_float(this, var_name, src) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: var_name
real(c_float), intent(in) :: src(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! We use double precision
end function aquacrop_set_float

! ------------------------------------------------------------------------

function aquacrop_set_double(this, var_name, src) result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: var_name
real(c_double), intent(in) :: src(:)
integer :: bmi_status

! TODO: Set values in AquaCrop state
select case(var_name)
case('crop__fertility_stress')
    ! TODO: Set fertility stress in management
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_set_double

! ------------------------------------------------------------------------
! Set value at indices

function aquacrop_set_at_indices_int(this, var_name, inds, src) &
    result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: var_name
integer, intent(in) :: inds(:)
integer, intent(in) :: src(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_set_at_indices_int

! ------------------------------------------------------------------------

function aquacrop_set_at_indices_float(this, var_name, inds, src) &
    result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: var_name
integer, intent(in) :: inds(:)
real(c_float), intent(in) :: src(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable
end function aquacrop_set_at_indices_float

! ------------------------------------------------------------------------

function aquacrop_set_at_indices_double(this, var_name, inds, src) &
    result(bmi_status)
class(bmi_aquacrop), intent(inout) :: this
character(len=*), intent(in) :: var_name
integer, intent(in) :: inds(:)
real(c_double), intent(in) :: src(:)
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_set_at_indices_double

! ========================================================================
! BMI: Grid Information Functions
! ========================================================================

function aquacrop_grid_type(this, grid_id, grid_type) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
character(len=*), intent(out) :: grid_type
integer :: bmi_status

select case(grid_id)
case(0)
    grid_type = "scalar"
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_type

! ------------------------------------------------------------------------

function aquacrop_grid_rank(this, grid_id, grid_rank) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
integer, intent(out) :: grid_rank
integer :: bmi_status

select case(grid_id)
case(0)
    grid_rank = 0  ! Scalar
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_rank

! ------------------------------------------------------------------------

function aquacrop_grid_size(this, grid_id, grid_size) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
integer, intent(out) :: grid_size
integer :: bmi_status

select case(grid_id)
case(0)
    grid_size = 1  ! Single point
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_size

! ------------------------------------------------------------------------

function aquacrop_grid_shape(this, grid_id, grid_shape) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
integer, dimension(:), intent(out) :: grid_shape
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_shape

! ------------------------------------------------------------------------

function aquacrop_grid_spacing(this, grid_id, grid_spacing) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
real(c_double), dimension(:), intent(out) :: grid_spacing
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_spacing

! ------------------------------------------------------------------------

function aquacrop_grid_origin(this, grid_id, grid_origin) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
real(c_double), dimension(:), intent(out) :: grid_origin
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_origin

! ------------------------------------------------------------------------

function aquacrop_grid_x(this, grid_id, grid_x) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
real(c_double), dimension(:), intent(out) :: grid_x
integer :: bmi_status

select case(grid_id)
case(0)
    ! TODO: Get from project longitude
    grid_x(1) = 0.0d0
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_x

! ------------------------------------------------------------------------

function aquacrop_grid_y(this, grid_id, grid_y) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
real(c_double), dimension(:), intent(out) :: grid_y
integer :: bmi_status

select case(grid_id)
case(0)
    ! TODO: Get from project latitude
    grid_y(1) = 0.0d0
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_y

! ------------------------------------------------------------------------

function aquacrop_grid_z(this, grid_id, grid_z) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
real(c_double), dimension(:), intent(out) :: grid_z
integer :: bmi_status

select case(grid_id)
case(0)
    ! TODO: Get from project altitude
    grid_z(1) = 0.0d0
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_z

! ------------------------------------------------------------------------

function aquacrop_grid_node_count(this, grid_id, count) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
integer, intent(out) :: count
integer :: bmi_status

select case(grid_id)
case(0)
    count = 1
    bmi_status = BMI_SUCCESS
case default
    bmi_status = BMI_FAILURE
end select
end function aquacrop_grid_node_count

! ------------------------------------------------------------------------

function aquacrop_grid_edge_count(this, grid_id, count) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
integer, intent(out) :: count
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_edge_count

! ------------------------------------------------------------------------

function aquacrop_grid_face_count(this, grid_id, count) result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
integer, intent(out) :: count
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_face_count

! ------------------------------------------------------------------------

function aquacrop_grid_edge_nodes(this, grid_id, edge_nodes) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
integer, dimension(:), intent(out) :: edge_nodes
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_edge_nodes

! ------------------------------------------------------------------------

function aquacrop_grid_face_edges(this, grid_id, face_edges) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
integer, dimension(:), intent(out) :: face_edges
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_face_edges

! ------------------------------------------------------------------------

function aquacrop_grid_face_nodes(this, grid_id, face_nodes) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
integer, dimension(:), intent(out) :: face_nodes
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_face_nodes

! ------------------------------------------------------------------------

function aquacrop_grid_nodes_per_face(this, grid_id, nodes_per_face) &
    result(bmi_status)
class(bmi_aquacrop), intent(in) :: this
integer, intent(in) :: grid_id
integer, dimension(:), intent(out) :: nodes_per_face
integer :: bmi_status

bmi_status = BMI_FAILURE
! Not applicable for scalar grid
end function aquacrop_grid_nodes_per_face

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

end module bmiaquacropf