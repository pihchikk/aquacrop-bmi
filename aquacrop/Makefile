# Compiler options

DEBUG = 0
STATIC = 0

FC = gfortran
FFLAGS = -O2 -fPIC -J. $(shell pkg-config --cflags bmif)
LDFLAGS = -shared $(shell pkg-config --libs bmif)
LDFLAGS_LIB =
BMI_CFLAGS = $(shell pkg-config --cflags bmif)
BMI_LIBS = $(shell pkg-config --libs bmif)

ifeq ($(STATIC), 1)
    ifneq ($(DEBUG), 0)
        $(error DEBUG=0 is required for STATIC=1 build)
    endif
endif

ifeq ($(findstring gfortran, $(FC)), gfortran)
    ifeq ($(STATIC), 1)
        # For statically compiled (release) executables
        FCFLAGS += -O2 -mtune=generic -funroll-loops
        LDFLAGS_EXE += -static
        LDFLAGS_LIB += -static
    else
        FCFLAGS += -fPIC -fall-intrinsics
        LDFLAGS_LIB += -shared

        ifeq ($(DEBUG), 1)
            # For debugging and development
            PCFLAGS += -gl
            FCFLAGS += -g -Wall -Wextra -Wimplicit-interface -fmax-errors=1 \
                       -fcheck=all -fbacktrace -std=f2008
        else
            # For production
            FCFLAGS += -O2 -march=native -funroll-loops
        endif
    endif
else ifeq ($(FC), ifort)
    ifneq ($(STATIC), 0)
        $(error STATIC=0 is required for FC=ifort)
    endif

    LDFLAGS_LIB += -shared
    FCFLAGS += -fPIC

    ifeq ($(DEBUG), 1)
        # For debugging and development
        FCFLAGS += -g -fpe0 -warn -traceback -debug extended -stand f08 \
                   -check all -check noarg_temp_created
    else
        # For production
        FCFLAGS += -O2 -fp-model strict -xHost
    endif
endif


# Main targets

EXECUTABLE = aquacrop
STATIC_LIBRARY = libaquacrop.a
SHARED_LIBRARY = libaquacrop.so
BMI_LIBRARY = libaquacropbmi.so

ifeq ($(STATIC), 1)
    LIBRARY = $(STATIC_LIBRARY)
else
    LIBRARY = $(SHARED_LIBRARY)
endif

bin: $(EXECUTABLE)
lib: $(LIBRARY)
bmi: $(BMI_LIBRARY)
all: bin lib bmi
.DEFAULT_GOAL = all


# Fortran-related targets

# Core AquaCrop objects (without BMI)
OBJ = climprocessing.o \
    defaultcropsoil.o \
    global.o  \
    inforesults.o \
    initialsettings.o \
    kinds.o \
    project_input.o \
    rootunit.o \
    run.o \
    simul.o \
    startunit.o \
    tempprocessing.o \
    utils.o

# BMI-specific objects
# Note: bmif_2_0 module comes from our local implementation
BMI_OBJ = bmif.o bmi_aquacrop.o

$(STATIC_LIBRARY): $(OBJ) \
    $(OBJ_INTERFACE)
	$(AR) cr $(STATIC_LIBRARY) $(OBJ) $(OBJ_INTERFACE)

$(SHARED_LIBRARY): $(OBJ) \
    $(OBJ_INTERFACE)
	$(FC) $(LDFLAGS_LIB) $(FCFLAGS) $(wildcard *.f90) startunit.F90 -o $(LIBRARY)

# BMI shared library - includes both AquaCrop and BMI wrapper
$(BMI_LIBRARY): $(OBJ) $(BMI_OBJ)
	$(FC) $(LDFLAGS_LIB) $(FCFLAGS) -o $(BMI_LIBRARY) $(OBJ) $(BMI_OBJ) $(BMI_LIBS)

fortranclean:
	$(RM) $(wildcard *.mod) $(wildcard *.o) $(STATIC_LIBRARY) $(SHARED_LIBRARY) $(BMI_LIBRARY)


aquacrop.o: aquacrop.F90 \
    startunit.o
	$(FC) $(FCFLAGS) -c $< -o $@

climprocessing.o: climprocessing.f90 \
    global.o \
    kinds.o
	$(FC) $(FCFLAGS) -c $< -o $@

defaultcropsoil.o: defaultcropsoil.f90 \
    global.o \
    kinds.o
	$(FC) $(FCFLAGS) -c $< -o $@

global.o: global.f90 \
    kinds.o \
    project_input.o \
    utils.o
	$(FC) $(FCFLAGS) -c $< -o $@

inforesults.o: inforesults.f90 \
    global.o \
    kinds.o \
    utils.o
	$(FC) $(FCFLAGS) -c $< -o $@

initialsettings.o: initialsettings.f90 \
    global.o \
    defaultcropsoil.o \
    kinds.o
	$(FC) $(FCFLAGS) -c $< -o $@

kinds.o: kinds.f90
	$(FC) $(FCFLAGS) -c $< -o $@

project_input.o: project_input.f90 \
    kinds.o \
    utils.o
	$(FC) $(FCFLAGS) -c $< -o $@

rootunit.o: rootunit.f90 \
    global.o \
    kinds.o \
    utils.o
	$(FC) $(FCFLAGS) -c $< -o $@

run.o: run.f90 \
    global.o \
    inforesults.o \
    kinds.o \
    rootunit.o \
    simul.o \
    tempprocessing.o \
    climprocessing.o \
    utils.o
	$(FC) $(FCFLAGS) -c $< -o $@

simul.o: simul.f90 \
    global.o \
    tempprocessing.o \
    kinds.o
	$(FC) $(FCFLAGS) -c $< -o $@

startunit.o: startunit.F90 \
    global.o \
    initialsettings.o \
    kinds.o \
    run.o \
    utils.o
	$(FC) $(FCFLAGS) -c $< -o $@

tempprocessing.o: tempprocessing.f90 \
    global.o \
    kinds.o \
    project_input.o \
    utils.o
	$(FC) $(FCFLAGS) -c $< -o $@

utils.o: utils.f90 \
    kinds.o
	$(FC) $(FCFLAGS) -c $< -o $@

# BMI-specific compilation rules

# BMI base module comes from installed bmi-fortran package
# No need to compile bmif_2_0.f90 - it's provided by the system
bmif.o: bmif.f90 bmi_aquacrop.o
	$(FC) $(FCFLAGS) $(BMI_CFLAGS) -c $< -o $@

# BMI AquaCrop wrapper 
bmi_aquacrop.o: bmi_aquacrop.f90 \
    global.o \
    run.o \
    kinds.o
	$(FC) $(FCFLAGS) $(BMI_CFLAGS) -c $< -o $@

# Installation
PREFIX ?= /usr/local
INSTALL_LIB = $(PREFIX)/lib
INSTALL_INC = $(PREFIX)/include
INSTALL_PC = $(PREFIX)/lib/pkgconfig

install: $(BMI_LIBRARY)
	mkdir -p $(INSTALL_LIB) $(INSTALL_INC) $(INSTALL_PC)
	install -m 644 $(BMI_LIBRARY) $(INSTALL_LIB)/
	install -m 644 *.mod $(INSTALL_INC)/
	echo 'prefix=$(PREFIX)' > $(INSTALL_PC)/aquacropbmi.pc
	echo 'exec_prefix=$${prefix}' >> $(INSTALL_PC)/aquacropbmi.pc
	echo 'libdir=$${exec_prefix}/lib' >> $(INSTALL_PC)/aquacropbmi.pc
	echo 'includedir=$${prefix}/include' >> $(INSTALL_PC)/aquacropbmi.pc
	echo '' >> $(INSTALL_PC)/aquacropbmi.pc
	echo 'Name: aquacropbmi' >> $(INSTALL_PC)/aquacropbmi.pc
	echo 'Description: AquaCrop BMI Library' >> $(INSTALL_PC)/aquacropbmi.pc
	echo 'Version: 7.0' >> $(INSTALL_PC)/aquacropbmi.pc
	echo 'Requires: bmif' >> $(INSTALL_PC)/aquacropbmi.pc
	echo 'Libs: -L$${libdir} -laquacropbmi' >> $(INSTALL_PC)/aquacropbmi.pc
	echo 'Cflags: -I$${includedir}' >> $(INSTALL_PC)/aquacropbmi.pc

uninstall:
	rm -f $(INSTALL_LIB)/$(BMI_LIBRARY)
	rm -f $(INSTALL_INC)/*.mod
	rm -f $(INSTALL_PC)/aquacropbmi.pc


# Interface Fortran code: always adding the parent module and the kinds and
# utils modules as dependencies for convenience, even if not actually used.

# Finally, the actual 'executable' and 'clean' targets

# Fortran-based executable
$(EXECUTABLE): aquacrop.o
	$(FC) $(LDFLAGS_EXE) aquacrop.o $(OBJ) -o $(EXECUTABLE)

# BMI test executable
test_bmi_complete: test_bmi_complete.f90 $(BMI_LIBRARY)
	$(FC) $(FCFLAGS) $(BMI_CFLAGS) -o $@ $< -L. -laquacropbmi -Wl,-rpath,. $(BMI_LIBS)

clean: fortranclean
	$(RM) $(EXECUTABLE) test_bmi_complete