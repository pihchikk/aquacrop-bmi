!> The Basic Model Interface (BMI) version 2.0 for Fortran
!> 
!> This module provides the abstract interface definition for BMI 2.0
!> Reference: https://bmi.readthedocs.io/
module bmif_2_0

  use, intrinsic :: iso_c_binding, only: c_double, c_int, c_char, c_ptr, c_float

  implicit none

  ! BMI status codes
  integer, parameter :: BMI_SUCCESS = 0
  integer, parameter :: BMI_FAILURE = 1

  ! Maximum string lengths
  integer, parameter :: BMI_MAX_COMPONENT_NAME = 2048
  integer, parameter :: BMI_MAX_VAR_NAME = 2048
  integer, parameter :: BMI_MAX_TYPE_NAME = 2048
  integer, parameter :: BMI_MAX_UNITS_NAME = 2048

  !> The Basic Model Interface
  type, abstract :: bmi
   contains
     ! Model control functions
     procedure(bmif_get_component_name), deferred :: get_component_name
     procedure(bmif_initialize), deferred :: initialize
     procedure(bmif_finalize), deferred :: finalize
     procedure(bmif_update), deferred :: update
     procedure(bmif_update_until), deferred :: update_until

     ! Model information functions
     procedure(bmif_get_input_item_count), deferred :: get_input_item_count
     procedure(bmif_get_output_item_count), deferred :: get_output_item_count
     procedure(bmif_get_input_var_names), deferred :: get_input_var_names
     procedure(bmif_get_output_var_names), deferred :: get_output_var_names

     ! Time functions
     procedure(bmif_get_start_time), deferred :: get_start_time
     procedure(bmif_get_end_time), deferred :: get_end_time
     procedure(bmif_get_current_time), deferred :: get_current_time
     procedure(bmif_get_time_step), deferred :: get_time_step
     procedure(bmif_get_time_units), deferred :: get_time_units

     ! Variable information functions
     procedure(bmif_get_var_grid), deferred :: get_var_grid
     procedure(bmif_get_var_type), deferred :: get_var_type
     procedure(bmif_get_var_units), deferred :: get_var_units
     procedure(bmif_get_var_itemsize), deferred :: get_var_itemsize
     procedure(bmif_get_var_nbytes), deferred :: get_var_nbytes
     procedure(bmif_get_var_location), deferred :: get_var_location

     ! Variable getter and setter functions
     procedure(bmif_get_value_int), deferred :: get_value_int
     procedure(bmif_get_value_float), deferred :: get_value_float
     procedure(bmif_get_value_double), deferred :: get_value_double
     procedure(bmif_get_value_ptr), deferred :: get_value_ptr
     procedure(bmif_get_value_at_indices), deferred :: get_value_at_indices

     procedure(bmif_set_value_int), deferred :: set_value_int
     procedure(bmif_set_value_float), deferred :: set_value_float
     procedure(bmif_set_value_double), deferred :: set_value_double
     procedure(bmif_set_value_at_indices), deferred :: set_value_at_indices

     ! Grid information functions
     procedure(bmif_get_grid_type), deferred :: get_grid_type
     procedure(bmif_get_grid_rank), deferred :: get_grid_rank
     procedure(bmif_get_grid_size), deferred :: get_grid_size
     procedure(bmif_get_grid_shape), deferred :: get_grid_shape
     procedure(bmif_get_grid_spacing), deferred :: get_grid_spacing
     procedure(bmif_get_grid_origin), deferred :: get_grid_origin
     procedure(bmif_get_grid_x), deferred :: get_grid_x
     procedure(bmif_get_grid_y), deferred :: get_grid_y
     procedure(bmif_get_grid_z), deferred :: get_grid_z
     procedure(bmif_get_grid_node_count), deferred :: get_grid_node_count
     procedure(bmif_get_grid_edge_count), deferred :: get_grid_edge_count
     procedure(bmif_get_grid_face_count), deferred :: get_grid_face_count
     procedure(bmif_get_grid_edge_nodes), deferred :: get_grid_edge_nodes
     procedure(bmif_get_grid_face_edges), deferred :: get_grid_face_edges
     procedure(bmif_get_grid_face_nodes), deferred :: get_grid_face_nodes
     procedure(bmif_get_grid_nodes_per_face), deferred :: get_grid_nodes_per_face
  end type bmi

  ! Abstract interface definitions
  abstract interface

     ! Model control functions
     function bmif_get_component_name(this, name) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(out) :: name
       integer :: bmi_status
     end function bmif_get_component_name

     function bmif_initialize(this, config_file) result(bmi_status)
       import :: bmi
       class(bmi), intent(inout) :: this
       character(len=*), intent(in) :: config_file
       integer :: bmi_status
     end function bmif_initialize

     function bmif_finalize(this) result(bmi_status)
       import :: bmi
       class(bmi), intent(inout) :: this
       integer :: bmi_status
     end function bmif_finalize

     function bmif_update(this) result(bmi_status)
       import :: bmi
       class(bmi), intent(inout) :: this
       integer :: bmi_status
     end function bmif_update

     function bmif_update_until(this, time) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(inout) :: this
       real(c_double), intent(in) :: time
       integer :: bmi_status
     end function bmif_update_until

     ! Model information functions
     function bmif_get_input_item_count(this, count) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(out) :: count
       integer :: bmi_status
     end function bmif_get_input_item_count

     function bmif_get_output_item_count(this, count) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(out) :: count
       integer :: bmi_status
     end function bmif_get_output_item_count

     function bmif_get_input_var_names(this, names) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(*), pointer, intent(out) :: names(:)
       integer :: bmi_status
     end function bmif_get_input_var_names

     function bmif_get_output_var_names(this, names) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(*), pointer, intent(out) :: names(:)
       integer :: bmi_status
     end function bmif_get_output_var_names

     ! Time functions
     function bmif_get_start_time(this, time) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       real(c_double), intent(out) :: time
       integer :: bmi_status
     end function bmif_get_start_time

     function bmif_get_end_time(this, time) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       real(c_double), intent(out) :: time
       integer :: bmi_status
     end function bmif_get_end_time

     function bmif_get_current_time(this, time) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       real(c_double), intent(out) :: time
       integer :: bmi_status
     end function bmif_get_current_time

     function bmif_get_time_step(this, time_step) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       real(c_double), intent(out) :: time_step
       integer :: bmi_status
     end function bmif_get_time_step

     function bmif_get_time_units(this, units) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(out) :: units
       integer :: bmi_status
     end function bmif_get_time_units

     ! Variable information functions
     function bmif_get_var_grid(this, var_name, grid_id) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: var_name
       integer(c_int), intent(out) :: grid_id
       integer :: bmi_status
     end function bmif_get_var_grid

     function bmif_get_var_type(this, var_name, var_type) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: var_name
       character(len=*), intent(out) :: var_type
       integer :: bmi_status
     end function bmif_get_var_type

     function bmif_get_var_units(this, var_name, var_units) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: var_name
       character(len=*), intent(out) :: var_units
       integer :: bmi_status
     end function bmif_get_var_units

     function bmif_get_var_itemsize(this, var_name, var_size) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: var_name
       integer(c_int), intent(out) :: var_size
       integer :: bmi_status
     end function bmif_get_var_itemsize

     function bmif_get_var_nbytes(this, var_name, var_nbytes) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: var_name
       integer(c_int), intent(out) :: var_nbytes
       integer :: bmi_status
     end function bmif_get_var_nbytes

     function bmif_get_var_location(this, var_name, var_loc) result(bmi_status)
       import :: bmi
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: var_name
       character(len=*), intent(out) :: var_loc
       integer :: bmi_status
     end function bmif_get_var_location

     ! Variable getter functions
     function bmif_get_value_int(this, var_name, dest) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: var_name
       integer(c_int), intent(inout) :: dest(:)
       integer :: bmi_status
     end function bmif_get_value_int

     function bmif_get_value_float(this, var_name, dest) result(bmi_status)
       import :: bmi, c_float
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: var_name
       real(c_float), intent(inout) :: dest(:)
       integer :: bmi_status
     end function bmif_get_value_float

     function bmif_get_value_double(this, var_name, dest) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: var_name
       real(c_double), intent(inout) :: dest(:)
       integer :: bmi_status
     end function bmif_get_value_double

     function bmif_get_value_ptr(this, var_name, dest_ptr) result(bmi_status)
       import :: bmi, c_ptr
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: var_name
       type(c_ptr), intent(inout) :: dest_ptr
       integer :: bmi_status
     end function bmif_get_value_ptr

     function bmif_get_value_at_indices(this, var_name, dest, indices) result(bmi_status)
       import :: bmi, c_double, c_int
       class(bmi), intent(in) :: this
       character(len=*), intent(in) :: var_name
       real(c_double), intent(inout) :: dest(:)
       integer(c_int), intent(in) :: indices(:)
       integer :: bmi_status
     end function bmif_get_value_at_indices

     ! Variable setter functions
     function bmif_set_value_int(this, var_name, src) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(inout) :: this
       character(len=*), intent(in) :: var_name
       integer(c_int), intent(in) :: src(:)
       integer :: bmi_status
     end function bmif_set_value_int

     function bmif_set_value_float(this, var_name, src) result(bmi_status)
       import :: bmi, c_float
       class(bmi), intent(inout) :: this
       character(len=*), intent(in) :: var_name
       real(c_float), intent(in) :: src(:)
       integer :: bmi_status
     end function bmif_set_value_float

     function bmif_set_value_double(this, var_name, src) result(bmi_status)
       import :: bmi, c_double
       class(bmi), intent(inout) :: this
       character(len=*), intent(in) :: var_name
       real(c_double), intent(in) :: src(:)
       integer :: bmi_status
     end function bmif_set_value_double

     function bmif_set_value_at_indices(this, var_name, indices, src) result(bmi_status)
       import :: bmi, c_int, c_double
       class(bmi), intent(inout) :: this
       character(len=*), intent(in) :: var_name
       integer(c_int), intent(in) :: indices(:)
       real(c_double), intent(in) :: src(:)
       integer :: bmi_status
     end function bmif_set_value_at_indices

     ! Grid information functions
     function bmif_get_grid_type(this, grid_id, grid_type) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       character(len=*), intent(out) :: grid_type
       integer :: bmi_status
     end function bmif_get_grid_type

     function bmif_get_grid_rank(this, grid_id, grid_rank) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       integer(c_int), intent(out) :: grid_rank
       integer :: bmi_status
     end function bmif_get_grid_rank

     function bmif_get_grid_size(this, grid_id, grid_size) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       integer(c_int), intent(out) :: grid_size
       integer :: bmi_status
     end function bmif_get_grid_size

     function bmif_get_grid_shape(this, grid_id, grid_shape) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       integer(c_int), dimension(:), intent(out) :: grid_shape
       integer :: bmi_status
     end function bmif_get_grid_shape

     function bmif_get_grid_spacing(this, grid_id, grid_spacing) result(bmi_status)
       import :: bmi, c_int, c_double
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       real(c_double), dimension(:), intent(out) :: grid_spacing
       integer :: bmi_status
     end function bmif_get_grid_spacing

     function bmif_get_grid_origin(this, grid_id, grid_origin) result(bmi_status)
       import :: bmi, c_int, c_double
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       real(c_double), dimension(:), intent(out) :: grid_origin
       integer :: bmi_status
     end function bmif_get_grid_origin

     function bmif_get_grid_x(this, grid_id, grid_x) result(bmi_status)
       import :: bmi, c_int, c_double
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       real(c_double), dimension(:), intent(out) :: grid_x
       integer :: bmi_status
     end function bmif_get_grid_x

     function bmif_get_grid_y(this, grid_id, grid_y) result(bmi_status)
       import :: bmi, c_int, c_double
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       real(c_double), dimension(:), intent(out) :: grid_y
       integer :: bmi_status
     end function bmif_get_grid_y

     function bmif_get_grid_z(this, grid_id, grid_z) result(bmi_status)
       import :: bmi, c_int, c_double
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       real(c_double), dimension(:), intent(out) :: grid_z
       integer :: bmi_status
     end function bmif_get_grid_z

     function bmif_get_grid_node_count(this, grid_id, count) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       integer(c_int), intent(out) :: count
       integer :: bmi_status
     end function bmif_get_grid_node_count

     function bmif_get_grid_edge_count(this, grid_id, count) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       integer(c_int), intent(out) :: count
       integer :: bmi_status
     end function bmif_get_grid_edge_count

     function bmif_get_grid_face_count(this, grid_id, count) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       integer(c_int), intent(out) :: count
       integer :: bmi_status
     end function bmif_get_grid_face_count

     function bmif_get_grid_edge_nodes(this, grid_id, edge_nodes) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       integer(c_int), dimension(:), intent(out) :: edge_nodes
       integer :: bmi_status
     end function bmif_get_grid_edge_nodes

     function bmif_get_grid_face_edges(this, grid_id, face_edges) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       integer(c_int), dimension(:), intent(out) :: face_edges
       integer :: bmi_status
     end function bmif_get_grid_face_edges

     function bmif_get_grid_face_nodes(this, grid_id, face_nodes) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       integer(c_int), dimension(:), intent(out) :: face_nodes
       integer :: bmi_status
     end function bmif_get_grid_face_nodes

     function bmif_get_grid_nodes_per_face(this, grid_id, nodes_per_face) result(bmi_status)
       import :: bmi, c_int
       class(bmi), intent(in) :: this
       integer(c_int), intent(in) :: grid_id
       integer(c_int), dimension(:), intent(out) :: nodes_per_face
       integer :: bmi_status
     end function bmif_get_grid_nodes_per_face

  end interface

end module bmif_2_0
