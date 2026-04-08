module aquacropbmi
  use bmif_2_0
  use iso_c_binding, only: c_ptr, c_loc, c_f_pointer, c_char, c_null_char
  implicit none

  ! Module-level constants for array dimensions
  integer, parameter :: MAX_DAYS = 1000
  integer, parameter :: MAX_COLS = 98

  type, extends(bmi) :: bmi_aquacrop
    private
    character(len=2048) :: config_dir = ""
    character(len=2048) :: pro_file = ""
    integer :: current_day = 0
    integer :: total_days = 0
    integer :: simulation_start = 0
    integer :: simulation_end = 0
    
    ! Model state variables (cached from output files)
    real(kind=8) :: canopy_cover = 0.0d0
    real(kind=8) :: biomass = 0.0d0
    real(kind=8) :: yield_value = 0.0d0
    real(kind=8) :: soil_moisture = 0.0d0
    
    ! Input variables (can be modified via set_value)
    real(kind=8) :: fertility_stress = 9.0d0
    real(kind=8) :: mulch_coverage = 0.0d0
    real(kind=8) :: weed_coverage = 0.0d0
    integer :: irrigation_day = -1
    real(kind=8) :: irrigation_amount = 0.0d0
    
    ! Flag to track if simulation needs to be re-run
    logical :: simulation_complete = .false.
    
    ! Storage for daily output data (for stepwise access)
    real(kind=8), dimension(MAX_DAYS, MAX_COLS) :: daily_data
    integer :: n_daily_records = 0
    
  contains
    procedure :: get_component_name => aquacrop_component_name
    procedure :: get_input_item_count => aquacrop_input_item_count
    procedure :: get_output_item_count => aquacrop_output_item_count
    procedure :: get_input_var_names => aquacrop_input_var_names
    procedure :: get_output_var_names => aquacrop_output_var_names
    
    procedure :: initialize => aquacrop_initialize
    procedure :: finalize => aquacrop_finalize
    procedure :: get_start_time => aquacrop_start_time
    procedure :: get_end_time => aquacrop_end_time
    procedure :: get_current_time => aquacrop_current_time
    procedure :: get_time_step => aquacrop_time_step
    procedure :: get_time_units => aquacrop_time_units
    procedure :: update => aquacrop_update
    procedure :: update_until => aquacrop_update_until
    
    procedure :: get_var_grid => aquacrop_var_grid
    procedure :: get_var_type => aquacrop_var_type
    procedure :: get_var_units => aquacrop_var_units
    procedure :: get_var_itemsize => aquacrop_var_itemsize
    procedure :: get_var_nbytes => aquacrop_var_nbytes
    procedure :: get_var_location => aquacrop_var_location
    
    procedure :: get_grid_rank => aquacrop_grid_rank
    procedure :: get_grid_size => aquacrop_grid_size
    procedure :: get_grid_type => aquacrop_grid_type
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
    
    ! Internal helper procedures
    procedure, private :: run_aquacrop_simulation
    procedure, private :: read_daily_output
    procedure, private :: update_man_file
    procedure, private :: update_irr_file
    procedure, private :: read_pro_file
  end type bmi_aquacrop

  private
  public :: bmi_aquacrop

  character(len=BMI_MAX_COMPONENT_NAME), target :: &
       component_name = "AquaCrop"

  ! Variable names
  integer, parameter :: input_item_count = 6
  integer, parameter :: output_item_count = 4
  
  character(len=BMI_MAX_VAR_NAME), target, dimension(input_item_count) :: &
       input_var_names = (/ &
       "crop__fertility_stress  ", &
       "management__mulch_cover ", &
       "management__weed_cover  ", &
       "irrigation__day         ", &
       "irrigation__amount      ", &
       "soil__initial_moisture  " /)

  character(len=BMI_MAX_VAR_NAME), target, dimension(output_item_count) :: &
       output_var_names = (/ &
       "crop__canopy_cover      ", &
       "crop__biomass           ", &
       "crop__yield             ", &
       "soil__moisture          " /)

contains

  ! ===================================================================
  ! Model Control Functions
  ! ===================================================================

  function aquacrop_component_name(self, name) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), pointer, intent(out) :: name
    integer :: bmi_status
    
    name => component_name
    bmi_status = BMI_SUCCESS
  end function aquacrop_component_name

  function aquacrop_initialize(self, config_file) result(bmi_status)
    class(bmi_aquacrop), intent(inout) :: self
    character(len=*), intent(in) :: config_file
    integer :: bmi_status
    integer :: stat
    
    bmi_status = BMI_SUCCESS
    
    ! Extract directory from config file
    if (index(config_file, '.PRO') > 0 .or. index(config_file, '.pro') > 0) then
      self%pro_file = trim(config_file)
      stat = index(config_file, '/', .true.)
      if (stat > 0) then
        self%config_dir = config_file(1:stat-1)
      else
        self%config_dir = '.'
      end if
    else
      self%config_dir = trim(config_file)
      self%pro_file = trim(self%config_dir) // '/LIST/project.PRO'
    end if
    
    ! Read PRO file to get simulation start/end dates
    call self%read_pro_file(stat)
    if (stat /= 0) then
      bmi_status = BMI_FAILURE
      return
    end if
    
    ! Calculate total days
    self%total_days = self%simulation_end - self%simulation_start + 1
    self%current_day = 0
    self%simulation_complete = .false.
    
    ! Initialize state variables
    self%canopy_cover = 0.0d0
    self%biomass = 0.0d0
    self%yield_value = 0.0d0
    self%soil_moisture = 0.0d0
    
  end function aquacrop_initialize

  subroutine read_pro_file(self, stat)
    class(bmi_aquacrop), intent(inout) :: self
    integer, intent(out) :: stat
    integer :: iounit
    character(len=256) :: line
    
    stat = 0
    open(newunit=iounit, file=trim(self%pro_file), status='old', action='read', iostat=stat)
    if (stat /= 0) return
    
    ! Skip first 3 lines
    read(iounit, '(A)', iostat=stat) line
    read(iounit, '(A)', iostat=stat) line
    read(iounit, '(A)', iostat=stat) line
    
    ! Read simulation start (line 4)
    read(iounit, *, iostat=stat) self%simulation_start
    if (stat /= 0) then
      close(iounit)
      return
    end if
    
    ! Read simulation end (line 5)
    read(iounit, *, iostat=stat) self%simulation_end
    
    close(iounit)
  end subroutine read_pro_file

  function aquacrop_update(self) result(bmi_status)
    class(bmi_aquacrop), intent(inout) :: self
    integer :: bmi_status
    integer :: stat
    
    bmi_status = BMI_SUCCESS
    
    ! Check if we need to run the full simulation
    if (.not. self%simulation_complete) then
      ! Update MAN file with current parameters
      call self%update_man_file()
      
      ! Run full AquaCrop simulation
      call self%run_aquacrop_simulation(stat)
      if (stat /= 0) then
        bmi_status = BMI_FAILURE
        return
      end if
      
      ! Read all daily outputs
      call self%read_daily_output(stat)
      if (stat /= 0) then
        bmi_status = BMI_FAILURE
        return
      end if
      
      self%simulation_complete = .true.
    end if
    
    ! Advance to next day
    self%current_day = self%current_day + 1
    
    ! Check bounds
    if (self%current_day > self%total_days) then
      self%current_day = self%total_days
      return
    end if
    
    ! Update state variables from cached daily data
    if (self%current_day <= self%n_daily_records) then
      ! Column indices from DAILY_OUT_HEADER
      ! 29: CC (Canopy Cover %)
      ! 38: Biomass (tonnes/ha)
      ! 40: Y(dry) (Yield tonnes/ha)
      ! 45: WC (Soil Water Content mm)
      self%canopy_cover = self%daily_data(self%current_day, 29)
      self%biomass = self%daily_data(self%current_day, 38)
      self%yield_value = self%daily_data(self%current_day, 40)
      self%soil_moisture = self%daily_data(self%current_day, 45)
      
      ! Handle -9 (no data) values
      if (self%canopy_cover < 0) self%canopy_cover = 0.0d0
      if (self%biomass < 0) self%biomass = 0.0d0
      if (self%yield_value < 0) self%yield_value = 0.0d0
      if (self%soil_moisture < 0) self%soil_moisture = 0.0d0
    end if
    
  end function aquacrop_update

  function aquacrop_update_until(self, time) result(bmi_status)
    class(bmi_aquacrop), intent(inout) :: self
    double precision, intent(in) :: time
    integer :: bmi_status
    double precision :: current_time
    
    bmi_status = BMI_SUCCESS
    current_time = dble(self%current_day)
    
    do while (current_time < time)
      bmi_status = self%update()
      if (bmi_status /= BMI_SUCCESS) return
      current_time = dble(self%current_day)
    end do
  end function aquacrop_update_until

  function aquacrop_finalize(self) result(bmi_status)
    class(bmi_aquacrop), intent(inout) :: self
    integer :: bmi_status
    
    self%current_day = 0
    self%total_days = 0
    self%simulation_complete = .false.
    bmi_status = BMI_SUCCESS
  end function aquacrop_finalize

  ! ===================================================================
  ! Time Functions
  ! ===================================================================

  function aquacrop_start_time(self, time) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    double precision, intent(out) :: time
    integer :: bmi_status
    
    time = 0.0d0
    bmi_status = BMI_SUCCESS
  end function aquacrop_start_time

  function aquacrop_end_time(self, time) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    double precision, intent(out) :: time
    integer :: bmi_status
    
    time = dble(self%total_days)
    bmi_status = BMI_SUCCESS
  end function aquacrop_end_time

  function aquacrop_current_time(self, time) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    double precision, intent(out) :: time
    integer :: bmi_status
    
    time = dble(self%current_day)
    bmi_status = BMI_SUCCESS
  end function aquacrop_current_time

  function aquacrop_time_step(self, time_step) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    double precision, intent(out) :: time_step
    integer :: bmi_status
    
    time_step = 1.0d0
    bmi_status = BMI_SUCCESS
  end function aquacrop_time_step

  function aquacrop_time_units(self, time_units) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(out) :: time_units
    integer :: bmi_status
    
    time_units = "days"
    bmi_status = BMI_SUCCESS
  end function aquacrop_time_units

  ! ===================================================================
  ! Variable Info Functions
  ! ===================================================================

  function aquacrop_input_item_count(self, count) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(out) :: count
    integer :: bmi_status
    
    count = input_item_count
    bmi_status = BMI_SUCCESS
  end function aquacrop_input_item_count

  function aquacrop_output_item_count(self, count) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(out) :: count
    integer :: bmi_status
    
    count = output_item_count
    bmi_status = BMI_SUCCESS
  end function aquacrop_output_item_count

  function aquacrop_input_var_names(self, names) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(*), pointer, intent(out) :: names(:)
    integer :: bmi_status
    
    names => input_var_names
    bmi_status = BMI_SUCCESS
  end function aquacrop_input_var_names

  function aquacrop_output_var_names(self, names) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(*), pointer, intent(out) :: names(:)
    integer :: bmi_status
    
    names => output_var_names
    bmi_status = BMI_SUCCESS
  end function aquacrop_output_var_names

  function aquacrop_var_grid(self, var_name, grid_id) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    integer, intent(out) :: grid_id
    integer :: bmi_status
    
    grid_id = 0  ! Scalar grid
    bmi_status = BMI_SUCCESS
  end function aquacrop_var_grid

  function aquacrop_var_type(self, var_name, var_type) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    character(len=*), intent(out) :: var_type
    integer :: bmi_status
    
    var_type = "double"
    bmi_status = BMI_SUCCESS
  end function aquacrop_var_type

  function aquacrop_var_units(self, var_name, var_units) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    character(len=*), intent(out) :: var_units
    integer :: bmi_status
    
    select case(trim(var_name))
    case("crop__canopy_cover")
      var_units = "percent"
    case("crop__biomass")
      var_units = "tonnes/ha"
    case("crop__yield")
      var_units = "tonnes/ha"
    case("soil__moisture")
      var_units = "mm"
    case("crop__fertility_stress")
      var_units = "percent"
    case("management__mulch_cover")
      var_units = "percent"
    case("management__weed_cover")
      var_units = "percent"
    case("irrigation__day")
      var_units = "days"
    case("irrigation__amount")
      var_units = "mm"
    case("soil__initial_moisture")
      var_units = "percent"
    case default
      var_units = ""
    end select
    
    bmi_status = BMI_SUCCESS
  end function aquacrop_var_units

  function aquacrop_var_itemsize(self, var_name, var_itemsize) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    integer, intent(out) :: var_itemsize
    integer :: bmi_status
    
    var_itemsize = 8  ! double precision
    bmi_status = BMI_SUCCESS
  end function aquacrop_var_itemsize

  function aquacrop_var_nbytes(self, var_name, var_nbytes) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    integer, intent(out) :: var_nbytes
    integer :: bmi_status
    
    var_nbytes = 8  ! 1 value * 8 bytes
    bmi_status = BMI_SUCCESS
  end function aquacrop_var_nbytes

  function aquacrop_var_location(self, var_name, var_location) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    character(len=*), intent(out) :: var_location
    integer :: bmi_status
    
    var_location = "node"
    bmi_status = BMI_SUCCESS
  end function aquacrop_var_location

  ! ===================================================================
  ! Getter Functions (Following official BMI pattern)
  ! ===================================================================

  function aquacrop_get_double(self, var_name, dest) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    double precision, intent(inout) :: dest(:)
    integer :: bmi_status
    
    bmi_status = BMI_SUCCESS
    
    select case(trim(var_name))
    case("crop__canopy_cover")
      dest(1) = self%canopy_cover
    case("crop__biomass")
      dest(1) = self%biomass
    case("crop__yield")
      dest(1) = self%yield_value
    case("soil__moisture")
      dest(1) = self%soil_moisture
    case("crop__fertility_stress")
      dest(1) = self%fertility_stress
    case("management__mulch_cover")
      dest(1) = self%mulch_coverage
    case("management__weed_cover")
      dest(1) = self%weed_coverage
    case("irrigation__day")
      dest(1) = dble(self%irrigation_day)
    case("irrigation__amount")
      dest(1) = self%irrigation_amount
    case default
      bmi_status = BMI_FAILURE
    end select
  end function aquacrop_get_double

  function aquacrop_get_float(self, var_name, dest) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    real, intent(inout) :: dest(:)
    integer :: bmi_status
    double precision :: temp(1)
    
    bmi_status = self%get_value_double(var_name, temp)
    dest(1) = real(temp(1))
  end function aquacrop_get_float

  function aquacrop_get_int(self, var_name, dest) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    integer, intent(inout) :: dest(:)
    integer :: bmi_status
    double precision :: temp(1)
    
    bmi_status = self%get_value_double(var_name, temp)
    dest(1) = int(temp(1))
  end function aquacrop_get_int

  ! ===================================================================
  ! Setter Functions (Following official BMI pattern)
  ! ===================================================================

  function aquacrop_set_double(self, var_name, src) result(bmi_status)
    class(bmi_aquacrop), intent(inout) :: self
    character(len=*), intent(in) :: var_name
    double precision, intent(in) :: src(:)
    integer :: bmi_status
    
    bmi_status = BMI_SUCCESS
    
    select case(trim(var_name))
    case("crop__fertility_stress")
      self%fertility_stress = src(1)
      self%simulation_complete = .false.
      
    case("management__mulch_cover")
      self%mulch_coverage = src(1)
      self%simulation_complete = .false.
      
    case("management__weed_cover")
      self%weed_coverage = src(1)
      self%simulation_complete = .false.
      
    case("irrigation__day")
      self%irrigation_day = int(src(1))
      
    case("irrigation__amount")
      self%irrigation_amount = src(1)
      if (self%irrigation_day > 0 .and. self%irrigation_amount > 0) then
        call self%update_irr_file()
        self%simulation_complete = .false.
      end if
      
    case default
      bmi_status = BMI_FAILURE
    end select
  end function aquacrop_set_double

  function aquacrop_set_float(self, var_name, src) result(bmi_status)
    class(bmi_aquacrop), intent(inout) :: self
    character(len=*), intent(in) :: var_name
    real, intent(in) :: src(:)
    integer :: bmi_status
    double precision :: temp(1)
    
    temp(1) = dble(src(1))
    bmi_status = self%set_value_double(var_name, temp)
  end function aquacrop_set_float

  function aquacrop_set_int(self, var_name, src) result(bmi_status)
    class(bmi_aquacrop), intent(inout) :: self
    character(len=*), intent(in) :: var_name
    integer, intent(in) :: src(:)
    integer :: bmi_status
    double precision :: temp(1)
    
    temp(1) = dble(src(1))
    bmi_status = self%set_value_double(var_name, temp)
  end function aquacrop_set_int

  ! ===================================================================
  ! Pointer and Index Functions (Following official BMI pattern)
  ! ===================================================================

  function aquacrop_get_ptr_double(self, var_name, dest_ptr) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    double precision, pointer, intent(out) :: dest_ptr(:)
    integer :: bmi_status
    
    select case(trim(var_name))
    case default
      bmi_status = BMI_FAILURE
    end select
  end function aquacrop_get_ptr_double

  function aquacrop_get_ptr_float(self, var_name, dest_ptr) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    real, pointer, intent(out) :: dest_ptr(:)
    integer :: bmi_status
    
    select case(trim(var_name))
    case default
      bmi_status = BMI_FAILURE
    end select
  end function aquacrop_get_ptr_float

  function aquacrop_get_ptr_int(self, var_name, dest_ptr) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    integer, pointer, intent(out) :: dest_ptr(:)
    integer :: bmi_status
    
    select case(trim(var_name))
    case default
      bmi_status = BMI_FAILURE
    end select
  end function aquacrop_get_ptr_int

  function aquacrop_get_at_indices_double(self, var_name, dest, indices) &
       result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    double precision, intent(inout) :: dest(:)
    integer, intent(in) :: indices(:)
    integer :: bmi_status
    
    if (size(indices) == 1 .and. indices(1) == 1) then
      bmi_status = self%get_value_double(var_name, dest)
    else
      bmi_status = BMI_FAILURE
    end if
  end function aquacrop_get_at_indices_double

  function aquacrop_get_at_indices_float(self, var_name, dest, indices) &
       result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    real, intent(inout) :: dest(:)
    integer, intent(in) :: indices(:)
    integer :: bmi_status
    
    if (size(indices) == 1 .and. indices(1) == 1) then
      bmi_status = self%get_value_float(var_name, dest)
    else
      bmi_status = BMI_FAILURE
    end if
  end function aquacrop_get_at_indices_float

  function aquacrop_get_at_indices_int(self, var_name, dest, indices) &
       result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    character(len=*), intent(in) :: var_name
    integer, intent(inout) :: dest(:)
    integer, intent(in) :: indices(:)
    integer :: bmi_status
    
    if (size(indices) == 1 .and. indices(1) == 1) then
      bmi_status = self%get_value_int(var_name, dest)
    else
      bmi_status = BMI_FAILURE
    end if
  end function aquacrop_get_at_indices_int

  function aquacrop_set_at_indices_double(self, var_name, indices, src) &
       result(bmi_status)
    class(bmi_aquacrop), intent(inout) :: self
    character(len=*), intent(in) :: var_name
    integer, intent(in) :: indices(:)
    double precision, intent(in) :: src(:)
    integer :: bmi_status
    
    if (size(indices) == 1 .and. indices(1) == 1) then
      bmi_status = self%set_value_double(var_name, src)
    else
      bmi_status = BMI_FAILURE
    end if
  end function aquacrop_set_at_indices_double

  function aquacrop_set_at_indices_float(self, var_name, indices, src) &
       result(bmi_status)
    class(bmi_aquacrop), intent(inout) :: self
    character(len=*), intent(in) :: var_name
    integer, intent(in) :: indices(:)
    real, intent(in) :: src(:)
    integer :: bmi_status
    
    if (size(indices) == 1 .and. indices(1) == 1) then
      bmi_status = self%set_value_float(var_name, src)
    else
      bmi_status = BMI_FAILURE
    end if
  end function aquacrop_set_at_indices_float

  function aquacrop_set_at_indices_int(self, var_name, indices, src) &
       result(bmi_status)
    class(bmi_aquacrop), intent(inout) :: self
    character(len=*), intent(in) :: var_name
    integer, intent(in) :: indices(:)
    integer, intent(in) :: src(:)
    integer :: bmi_status
    
    if (size(indices) == 1 .and. indices(1) == 1) then
      bmi_status = self%set_value_int(var_name, src)
    else
      bmi_status = BMI_FAILURE
    end if
  end function aquacrop_set_at_indices_int

  ! ===================================================================
  ! Grid Functions (Scalar grid - following official BMI pattern)
  ! ===================================================================

  function aquacrop_grid_rank(self, grid_id, grid_rank) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    integer, intent(out) :: grid_rank
    integer :: bmi_status
    
    grid_rank = 0  ! Scalar
    bmi_status = BMI_SUCCESS
  end function aquacrop_grid_rank

  function aquacrop_grid_size(self, grid_id, grid_size) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    integer, intent(out) :: grid_size
    integer :: bmi_status
    
    grid_size = 1
    bmi_status = BMI_SUCCESS
  end function aquacrop_grid_size

  function aquacrop_grid_type(self, grid_id, grid_type) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    character(len=*), intent(out) :: grid_type
    integer :: bmi_status
    
    grid_type = "scalar"
    bmi_status = BMI_SUCCESS
  end function aquacrop_grid_type

  function aquacrop_grid_shape(self, grid_id, grid_shape) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    integer, intent(out) :: grid_shape(:)
    integer :: bmi_status
    
    bmi_status = BMI_FAILURE
  end function aquacrop_grid_shape

  function aquacrop_grid_spacing(self, grid_id, grid_spacing) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    double precision, intent(out) :: grid_spacing(:)
    integer :: bmi_status
    
    bmi_status = BMI_FAILURE
  end function aquacrop_grid_spacing

  function aquacrop_grid_origin(self, grid_id, grid_origin) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    double precision, intent(out) :: grid_origin(:)
    integer :: bmi_status
    
    bmi_status = BMI_FAILURE
  end function aquacrop_grid_origin

  function aquacrop_grid_x(self, grid_id, grid_x) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    double precision, intent(out) :: grid_x(:)
    integer :: bmi_status
    
    grid_x(1) = 0.0d0
    bmi_status = BMI_SUCCESS
  end function aquacrop_grid_x

  function aquacrop_grid_y(self, grid_id, grid_y) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    double precision, intent(out) :: grid_y(:)
    integer :: bmi_status
    
    grid_y(1) = 0.0d0
    bmi_status = BMI_SUCCESS
  end function aquacrop_grid_y

  function aquacrop_grid_z(self, grid_id, grid_z) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    double precision, intent(out) :: grid_z(:)
    integer :: bmi_status
    
    grid_z(1) = 0.0d0
    bmi_status = BMI_SUCCESS
  end function aquacrop_grid_z

  function aquacrop_grid_node_count(self, grid_id, count) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    integer, intent(out) :: count
    integer :: bmi_status
    
    count = 1
    bmi_status = BMI_SUCCESS
  end function aquacrop_grid_node_count

  function aquacrop_grid_edge_count(self, grid_id, count) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    integer, intent(out) :: count
    integer :: bmi_status
    
    bmi_status = BMI_FAILURE
  end function aquacrop_grid_edge_count

  function aquacrop_grid_face_count(self, grid_id, count) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    integer, intent(out) :: count
    integer :: bmi_status
    
    bmi_status = BMI_FAILURE
  end function aquacrop_grid_face_count

  function aquacrop_grid_edge_nodes(self, grid_id, edge_nodes) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    integer, intent(out) :: edge_nodes(:)
    integer :: bmi_status
    
    bmi_status = BMI_FAILURE
  end function aquacrop_grid_edge_nodes

  function aquacrop_grid_face_edges(self, grid_id, face_edges) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    integer, intent(out) :: face_edges(:)
    integer :: bmi_status
    
    bmi_status = BMI_FAILURE
  end function aquacrop_grid_face_edges

  function aquacrop_grid_face_nodes(self, grid_id, face_nodes) result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    integer, intent(out) :: face_nodes(:)
    integer :: bmi_status
    
    bmi_status = BMI_FAILURE
  end function aquacrop_grid_face_nodes

  function aquacrop_grid_nodes_per_face(self, grid_id, nodes_per_face) &
       result(bmi_status)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(in) :: grid_id
    integer, intent(out) :: nodes_per_face(:)
    integer :: bmi_status
    
    bmi_status = BMI_FAILURE
  end function aquacrop_grid_nodes_per_face

  ! ===================================================================
  ! Internal Helper Procedures
  ! ===================================================================

  subroutine run_aquacrop_simulation(self, stat)
    class(bmi_aquacrop), intent(in) :: self
    integer, intent(out) :: stat
    character(len=512) :: command
    
    ! Build command to run aquacrop executable
    command = "cd " // trim(self%config_dir) // " && aquacrop"
    
    ! Execute command
    call execute_command_line(trim(command), exitstat=stat)
  end subroutine run_aquacrop_simulation

  subroutine read_daily_output(self, stat)
    class(bmi_aquacrop), intent(inout) :: self
    integer, intent(out) :: stat
    character(len=2048) :: output_file
    character(len=4096) :: line
    integer :: iounit, i
    integer :: col, beg, end_pos
    integer, parameter :: WIDTHS(98) = (/ &
       6, 12, 18, 24, 30, 40, 48, 57, 64, 71, 78, 87, 96, 104, 113, 122, 129, 138, 147, 153, 162, 170, &
       178, 187, 195, 202, 209, 216, 223, 230, 238, 246, 253, 262, 271, 280, 289, 295, 303, 313, 321, &
       330, 339, 347, 359, 368, 377, 387, 396, 404, 412, 422, 432, 442, 452, 462, 472, 481, 491, 501, &
       511, 521, 529, 538, 546, 553, 561, 569, 580, 591, 602, 613, 624, 635, 646, 657, 668, 679, 690, &
       701, 712, 723, 734, 745, 756, 767, 778, 789, 800, 811, 822, 833, 842, 852, 862, 872, 882, 892 /)
    
    stat = 0
    output_file = trim(self%config_dir) // "/OUTP/PROday.OUT"
    
    open(newunit=iounit, file=trim(output_file), status='old', action='read', iostat=stat)
    if (stat /= 0) return
    
    ! Skip header lines (4 lines)
    do i = 1, 4
      read(iounit, '(A)', iostat=stat) line
    end do
    
    ! Read daily data
    self%n_daily_records = 0
    do while (stat == 0 .and. self%n_daily_records < MAX_DAYS)
      read(iounit, '(A)', iostat=stat) line
      if (stat /= 0 .or. len_trim(line) == 0) exit
      
      self%n_daily_records = self%n_daily_records + 1
      
      ! Parse line according to WIDTHS
      beg = 1
      do col = 1, MAX_COLS
        if (col <= size(WIDTHS)) then
          end_pos = WIDTHS(col)
        else
          exit
        end if
        
        if (end_pos <= len_trim(line)) then
          read(line(beg:end_pos), *, iostat=stat) self%daily_data(self%n_daily_records, col)
          if (stat /= 0) self%daily_data(self%n_daily_records, col) = -9.0d0
        else
          self%daily_data(self%n_daily_records, col) = -9.0d0
        end if
        
        beg = end_pos + 1
      end do
    end do
    
    close(iounit)
    stat = 0
  end subroutine read_daily_output

  subroutine update_man_file(self)
    class(bmi_aquacrop), intent(in) :: self
    character(len=2048) :: man_file, temp_file
    character(len=256) :: line
    integer :: iounit_in, iounit_out, stat, line_num
    
    man_file = trim(self%config_dir) // "/project.MAN"
    temp_file = trim(self%config_dir) // "/project.MAN.tmp"
    
    open(newunit=iounit_in, file=trim(man_file), status='old', action='read', iostat=stat)
    if (stat /= 0) return
    
    open(newunit=iounit_out, file=trim(temp_file), status='replace', action='write')
    
    line_num = 0
    do while (stat == 0)
      read(iounit_in, '(A)', iostat=stat) line
      if (stat /= 0) exit
      
      line_num = line_num + 1
      
      if (line_num == 5) then
        ! Line 5 is fertility stress
        write(iounit_out, '(F15.0, A)') self%fertility_stress, &
             "              : Degree of soil fertility stress (%) - Effect is crop specific"
      else if (line_num == 2) then
        ! Line 2 is mulch coverage
        write(iounit_out, '(I6, A)') int(self%mulch_coverage), &
             "        : percentage (%) of ground surface covered by mulches IN growing period"
      else if (line_num == 9) then
        ! Line 9 is weed coverage
        write(iounit_out, '(I6, A)') int(self%weed_coverage), &
             "        : relative cover of weeds at canopy closure (%)"
      else
        write(iounit_out, '(A)') trim(line)
      end if
    end do
    
    close(iounit_in)
    close(iounit_out)
    
    ! Replace original with temp
    call execute_command_line("mv " // trim(temp_file) // " " // trim(man_file))
  end subroutine update_man_file

  subroutine update_irr_file(self)
    class(bmi_aquacrop), intent(in) :: self
    character(len=2048) :: irr_file, pro_file, temp_pro_file
    character(len=256) :: line
    integer :: iounit, iounit_pro, iounit_temp, stat, line_num
    
    irr_file = trim(self%config_dir) // "/project.IRR"
    pro_file = trim(self%config_dir) // "/LIST/project.PRO"
    temp_pro_file = trim(self%config_dir) // "/LIST/project.PRO.tmp"
    
    ! Create simple irrigation file
    open(newunit=iounit, file=trim(irr_file), status='replace', action='write')
    write(iounit, '(A)') "Irrigation"
    write(iounit, '(A)') "     7.1       : AquaCrop Version (August 2023)"
    write(iounit, '(I8, A)') 1, "         : Irrigation method (0=Sprinkler, 1=Surface, 2=Drip, 3=Other)"
    write(iounit, '(I8, A)') 100, "        : Percentage of wetted soil surface (%)"
    write(iounit, '(I8, A)') 1, "         : Number of irrigation events"
    write(iounit, '(A)') "  Day      Depth (mm)"
    write(iounit, '(A)') "===================="
    write(iounit, '(I5, F10.1)') self%irrigation_day, self%irrigation_amount
    close(iounit)
    
    ! Update PRO file to reference IRR file
    open(newunit=iounit_pro, file=trim(pro_file), status='old', action='read', iostat=stat)
    if (stat /= 0) return
    
    open(newunit=iounit_temp, file=trim(temp_pro_file), status='replace', action='write')
    
    line_num = 0
    do while (stat == 0)
      read(iounit_pro, '(A)', iostat=stat) line
      if (stat /= 0) exit
      
      line_num = line_num + 1
      
      if (line_num == 22) then
        write(iounit_temp, '(A)') "   project.IRR"
      else if (line_num == 23) then
        write(iounit_temp, '(A)') "   './'"
      else
        write(iounit_temp, '(A)') trim(line)
      end if
    end do
    
    close(iounit_pro)
    close(iounit_temp)
    
    ! Replace original with temp
    call execute_command_line("mv " // trim(temp_pro_file) // " " // trim(pro_file))
  end subroutine update_irr_file

end module aquacropbmi