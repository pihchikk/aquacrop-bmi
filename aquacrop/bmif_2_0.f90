!===============================================================================
! Basic Model Interface (BMI) 2.0 Fortran specification
! Based on CSDMS BMI 2.0 standard
!===============================================================================

module bmif_2_0
  use, intrinsic :: iso_c_binding, only: c_int, c_double, c_float, c_char
  implicit none

  integer, parameter :: BMI_MAX_COMPONENT_NAME = 2048
  integer, parameter :: BMI_MAX_VAR_NAME = 2048
  integer, parameter :: BMI_MAX_TYPE_NAME = 2048
  integer, parameter :: BMI_MAX_UNITS_NAME = 2048

  integer, parameter :: BMI_SUCCESS = 0
  integer, parameter :: BMI_FAILURE = 1

  ! BMI abstract base type
  type, abstract :: bmi
   contains
     ! Model control functions
     procedure(bmi_get_component_name), deferred :: get_component_name
     procedure(bmi_initialize), deferred :: initialize
     procedure(bmi_finalize), deferred :: finalize
     procedure(bmi_update), deferred :: update
     procedure(bmi_update_until), deferred :: update_until

     ! Model information functions
     procedure(bmi_get_input_item_count), deferred :: get_input_item_count
     procedure(bmi_get_output_item_count), deferred :: get_output_item_count
     procedure(bmi_get_input_var_names), deferred :: get_input_var_names
     procedure(bmi_get_output_var_names), deferred :: get_output_var_names

     ! Time functions
     procedure(bmi_get_start_time), deferred :: get_start_time
     procedure(bmi_get_end_time), deferred :: get_end_time
     procedure(bmi_get_current_time), deferred :: get_current_time
     procedure(bmi_get_time_step), deferred :: get_time_step
     procedure(bmi_get_time_units), deferred :: get_time_units

     ! Variable information functions
     procedure(bmi_get_var_type), deferred :: get_var_type
     procedure(bmi_get_var_units), deferred :: get_var_units
     procedure(bmi_get_var_itemsize), deferred :: get_var_itemsize
     procedure(bmi_get_var_nbytes), deferred :: get_var_nbytes
     procedure(bmi_get_var_location), deferred :: get_var_location
     procedure(bmi_get_var_grid), deferred :: get_var_grid

     ! Grid information functions
     procedure(bmi_get_grid_type), deferred :: get_grid_type
     procedure(bmi_get_grid_rank), deferred :: get_grid_rank
     procedure(bmi_get_grid_size), deferred :: get_grid_size
     procedure(bmi_get_grid_shape), deferred :: get_grid_shape
     procedure(bmi_get_grid_spacing), deferred :: get_grid_spacing
     procedure(bmi_get_grid_origin), deferred :: get_grid_origin
     procedure(bmi_get_grid_x), deferred :: get_grid_x
     procedure(bmi_get_grid_y), deferred :: get_grid_y
     procedure(bmi_get_grid_z), deferred :: get_grid_z
     procedure(bmi_get_grid_node_count), deferred :: get_grid_node_count
     procedure(bmi_get_grid_edge_count), deferred :: get_grid_edge_count
     procedure(bmi_get_grid_face_count), deferred :: get_grid_face_count
     procedure(bmi_get_grid_edge_nodes), deferred :: get_grid_edge_nodes
     procedure(bmi_get_grid_face_edges), deferred :: get_grid_face_edges
     procedure(bmi_get_grid_face_nodes), deferred :: get_grid_face_nodes
     procedure(bmi_get_grid_nodes_per_face), deferred :: get_grid_nodes_per_face

     ! Variable getter functions
     procedure(bmi_get_value_int), deferred :: get_value_int
     procedure(bmi_get_value_float), deferred :: get_value_float
     procedure(bmi_get_value_double), deferred :: get_value_double
     procedure(bmi_get_value_ptr_int), deferred :: get_value_ptr_int
     procedure(bmi_get_value_ptr_float), deferred :: get_value_ptr_float
     procedure(bmi_get_value_ptr_double), deferred :: get_value_ptr_double
     procedure(bmi_get_value_at_indices_int), deferred :: get_value_at_indices_int
     procedure(bmi_get_value_at_indices_float), deferred :: get_value_at_indices_float
     procedure(bmi_get_value_at_indices_double), deferred :: get_value_at_indices_double

     ! Variable setter functions
     procedure(bmi_set_value_int), deferred :: set_value_int
     procedure(bmi_set_value_float), deferred :: set_value_float
     procedure(bmi_set_value_double), deferred :: set_value_double
     procedure(bmi_set_value_at_indices_int), deferred :: set_value_at_indices_int
     procedure(bmi_set_value_at_indices_float), deferred :: set_value_at_indices_float
     procedure(bmi_set_value_at_indices_double), deferred :: set_value_at_indices_double
  end type bmi

  ! Abstract interfaces for BMI procedures
  abstract interface

     ! Model control functions
     function bmi_get_component_name(this, name) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), pointer, intent(out) :: name
       integer :: bmi_status
     end function bmi_get_component_name

     function bmi_initialize(this, config_file) result(bmi_status)
       import :: bmi
       class(bmi), intent(out) :: this
       character(len=*), intent(in) :: config_file
       integer :: bmi_status
     end function bmi_initialize

     function bmi_finalize(this) result(bmi_status)
       import :: bmi
       class(bmi), intent(inout) :: this
       integer :: bmi_status
     end function bmi_finalize

     function bmi_update(this) result(bmi_status)
       import :: bmi
       class(bmi), intent(inout) :: this
       integer :: bmi_status
     end function bmi_update

     function bmi_update_until(this, time) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(inout) :: this
       real(c_double), intent(in) :: time
       integer :: bmi_status
     end function bmi_update_until

     ! Model information functions
     function bmi_get_input_item_count(this, count) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(out) :: count
       integer :: bmi_status
     end function bmi_get_input_item_count

     function bmi_get_output_item_count(this, count) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(out) :: count
       integer :: bmi_status
     end function bmi_get_output_item_count

     function bmi_get_input_var_names(this, names) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), pointer, intent(out) :: names(:)
       integer :: bmi_status
     end function bmi_get_input_var_names

     function bmi_get_output_var_names(this, names) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), pointer, intent(out) :: names(:)
       integer :: bmi_status
     end function bmi_get_output_var_names

     ! Time functions
     function bmi_get_start_time(this, time) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       real(c_double), intent(out) :: time
       integer :: bmi_status
     end function bmi_get_start_time

     function bmi_get_end_time(this, time) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       real(c_double), intent(out) :: time
       integer :: bmi_status
     end function bmi_get_end_time

     function bmi_get_current_time(this, time) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       real(c_double), intent(out) :: time
       integer :: bmi_status
     end function bmi_get_current_time

     function bmi_get_time_step(this, time_step) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       real(c_double), intent(out) :: time_step
       integer :: bmi_status
     end function bmi_get_time_step

     function bmi_get_time_units(this, units) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(out) :: units
       integer :: bmi_status
     end function bmi_get_time_units

     ! Variable information functions
     function bmi_get_var_type(this, name, type) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       character(len=*), intent(out) :: type
       integer :: bmi_status
     end function bmi_get_var_type

     function bmi_get_var_units(this, name, units) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       character(len=*), intent(out) :: units
       integer :: bmi_status
     end function bmi_get_var_units

     function bmi_get_var_itemsize(this, name, size) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       integer, intent(out) :: size
       integer :: bmi_status
     end function bmi_get_var_itemsize

     function bmi_get_var_nbytes(this, name, nbytes) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       integer, intent(out) :: nbytes
       integer :: bmi_status
     end function bmi_get_var_nbytes

     function bmi_get_var_location(this, name, location) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       character(len=*), intent(out) :: location
       integer :: bmi_status
     end function bmi_get_var_location

     function bmi_get_var_grid(this, name, grid) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       integer, intent(out) :: grid
       integer :: bmi_status
     end function bmi_get_var_grid

     ! Grid information functions
     function bmi_get_grid_type(this, grid, type) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       character(len=*), intent(out) :: type
       integer :: bmi_status
     end function bmi_get_grid_type

     function bmi_get_grid_rank(this, grid, rank) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       integer, intent(out) :: rank
       integer :: bmi_status
     end function bmi_get_grid_rank

     function bmi_get_grid_size(this, grid, size) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       integer, intent(out) :: size
       integer :: bmi_status
     end function bmi_get_grid_size

     function bmi_get_grid_shape(this, grid, shape) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       integer, dimension(:), intent(out) :: shape
       integer :: bmi_status
     end function bmi_get_grid_shape

     function bmi_get_grid_spacing(this, grid, spacing) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       real(c_double), dimension(:), intent(out) :: spacing
       integer :: bmi_status
     end function bmi_get_grid_spacing

     function bmi_get_grid_origin(this, grid, origin) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       real(c_double), dimension(:), intent(out) :: origin
       integer :: bmi_status
     end function bmi_get_grid_origin

     function bmi_get_grid_x(this, grid, x) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       real(c_double), dimension(:), intent(out) :: x
       integer :: bmi_status
     end function bmi_get_grid_x

     function bmi_get_grid_y(this, grid, y) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       real(c_double), dimension(:), intent(out) :: y
       integer :: bmi_status
     end function bmi_get_grid_y

     function bmi_get_grid_z(this, grid, z) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       real(c_double), dimension(:), intent(out) :: z
       integer :: bmi_status
     end function bmi_get_grid_z

     function bmi_get_grid_node_count(this, grid, count) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       integer, intent(out) :: count
       integer :: bmi_status
     end function bmi_get_grid_node_count

     function bmi_get_grid_edge_count(this, grid, count) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       integer, intent(out) :: count
       integer :: bmi_status
     end function bmi_get_grid_edge_count

     function bmi_get_grid_face_count(this, grid, count) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       integer, intent(out) :: count
       integer :: bmi_status
     end function bmi_get_grid_face_count

     function bmi_get_grid_edge_nodes(this, grid, edge_nodes) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       integer, dimension(:), intent(out) :: edge_nodes
       integer :: bmi_status
     end function bmi_get_grid_edge_nodes

     function bmi_get_grid_face_edges(this, grid, face_edges) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       integer, dimension(:), intent(out) :: face_edges
       integer :: bmi_status
     end function bmi_get_grid_face_edges

     function bmi_get_grid_face_nodes(this, grid, face_nodes) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       integer, dimension(:), intent(out) :: face_nodes
       integer :: bmi_status
     end function bmi_get_grid_face_nodes

     function bmi_get_grid_nodes_per_face(this, grid, nodes_per_face) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       integer, intent(in) :: grid
       integer, dimension(:), intent(out) :: nodes_per_face
       integer :: bmi_status
     end function bmi_get_grid_nodes_per_face

     ! Variable getter functions
     function bmi_get_value_int(this, name, dest) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       integer, intent(inout) :: dest(:)
       integer :: bmi_status
     end function bmi_get_value_int

     function bmi_get_value_float(this, name, dest) result(bmi_status)
       import :: bmi, c_float
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       real(c_float), intent(inout) :: dest(:)
       integer :: bmi_status
     end function bmi_get_value_float

     function bmi_get_value_double(this, name, dest) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       real(c_double), intent(inout) :: dest(:)
       integer :: bmi_status
     end function bmi_get_value_double

     function bmi_get_value_ptr_int(this, name, dest_ptr) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       integer, pointer, intent(inout) :: dest_ptr(:)
       integer :: bmi_status
     end function bmi_get_value_ptr_int

     function bmi_get_value_ptr_float(this, name, dest_ptr) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       real, pointer, intent(inout) :: dest_ptr(:)
       integer :: bmi_status
     end function bmi_get_value_ptr_float

     function bmi_get_value_ptr_double(this, name, dest_ptr) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       double precision, pointer, intent(inout) :: dest_ptr(:)
       integer :: bmi_status
     end function bmi_get_value_ptr_double

     function bmi_get_value_at_indices_int(this, name, dest, inds) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       integer, intent(inout) :: dest(:)
       integer, intent(in) :: inds(:)
       integer :: bmi_status
     end function bmi_get_value_at_indices_int

     function bmi_get_value_at_indices_float(this, name, dest, inds) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       real, intent(inout) :: dest(:)
       integer, intent(in) :: inds(:)
       integer :: bmi_status
     end function bmi_get_value_at_indices_float

     function bmi_get_value_at_indices_double(this, name, dest, inds) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: name
       double precision, intent(inout) :: dest(:)
       integer, intent(in) :: inds(:)
       integer :: bmi_status
     end function bmi_get_value_at_indices_double

     ! Variable setter functions
     function bmi_set_value_int(this, name, src) result(bmi_status)
       import :: bmi
       class(bmi), intent(inout) :: this
       character(len=*), intent(in) :: name
       integer, intent(in) :: src(:)
       integer :: bmi_status
     end function bmi_set_value_int

     function bmi_set_value_float(this, name, src) result(bmi_status)
       import :: bmi, c_float
       class(bmi), intent(inout) :: this
       character(len=*), intent(in) :: name
       real(c_float), intent(in) :: src(:)
       integer :: bmi_status
     end function bmi_set_value_float

     function bmi_set_value_double(this, name, src) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(inout) :: this
       character(len=*), intent(in) :: name
       real(c_double), intent(in) :: src(:)
       integer :: bmi_status
     end function bmi_set_value_double

     function bmi_set_value_at_indices_int(this, name, inds, src) result(bmi_status)
       import :: bmi
       class(bmi), intent(inout) :: this
       character(len=*), intent(in) :: name
       integer, intent(in) :: inds(:)
       integer, intent(in) :: src(:)
       integer :: bmi_status
     end function bmi_set_value_at_indices_int

     function bmi_set_value_at_indices_float(this, name, inds, src) result(bmi_status)
       import :: bmi
       class(bmi), intent(inout) :: this
       character(len=*), intent(in) :: name
       integer, intent(in) :: inds(:)
       real, intent(in) :: src(:)
       integer :: bmi_status
     end function bmi_set_value_at_indices_float

     function bmi_set_value_at_indices_double(this, name, inds, src) result(bmi_status)
       import :: bmi
       class(bmi), intent(inout) :: this
       character(len=*), intent(in) :: name
       integer, intent(in) :: inds(:)
       double precision, intent(in) :: src(:)
       integer :: bmi_status
     end function bmi_set_value_at_indices_double

  end interface

end module bmif_2_0
