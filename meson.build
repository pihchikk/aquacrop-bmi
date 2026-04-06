project(
    'aquacrop_bmi_babel',
    'c',
    'fortran',
    'cython',
    version: '0.2.9',
)

py = import('python').find_installation(pure: false)
compiler = meson.get_compiler('fortran')

numpy_inc = run_command(
    py,
    ['-c', 'import numpy; print(numpy.get_include())'],
    check: true
).stdout().strip()

incs = include_directories(['aquacrop_bmi_babel/lib', numpy_inc])

# Get BMI dependency from system
bmif_dep = dependency('bmif', method: 'pkg-config')

# Compile Fortran BMI library from sources
fortran_sources = files(
    'aquacrop_fortran/kinds.f90',
    'aquacrop_fortran/utils.f90',
    'aquacrop_fortran/project_input.f90',
    'aquacrop_fortran/global.f90',
    'aquacrop_fortran/climprocessing.f90',
    'aquacrop_fortran/defaultcropsoil.f90',
    'aquacrop_fortran/inforesults.f90',
    'aquacrop_fortran/initialsettings.f90',
    'aquacrop_fortran/rootunit.f90',
    'aquacrop_fortran/simul.f90',
    'aquacrop_fortran/tempprocessing.f90',
    'aquacrop_fortran/startunit.F90',
    'aquacrop_fortran/run.f90',
    'aquacrop_fortran/bmif.f90',
    'aquacrop_fortran/bmi_aquacrop.f90',
)

fortran_lib = shared_library(
    'aquacropbmi',
    fortran_sources,
    dependencies: [bmif_dep],
    install: true,
    fortran_args: ['-g'],
)

# Python package files
install_pkg_srcs = [
    'aquacrop_bmi_babel/__init__.py',
    'aquacrop_bmi_babel/_bmi.py', 
    'aquacrop_bmi_babel/bmi.py',
    'aquacrop_bmi_babel/_version.py',
    'aquacrop_bmi_babel/bmi_aquacrop.py',
    'aquacrop_bmi_babel/aquacrop_runner.py',
    'aquacrop_bmi_babel/calibrate_bmi.py',
    'aquacrop_bmi_babel/models.py',
    'aquacrop_bmi_babel/project.py',
    'aquacrop_bmi_babel/util.py',
    'aquacrop_bmi_babel/settings.py',
    'aquacrop_bmi_babel/soil_texture.py',
    'aquacrop_bmi_babel/validation.py',
    'aquacrop_bmi_babel/main.py',
]
py.install_sources(install_pkg_srcs, subdir: 'aquacrop_bmi_babel')

# Data modules (crop/soil data)
install_subdir(
    'aquacrop_bmi_babel/data_modules',
    install_dir: py.get_install_dir() / 'aquacrop_bmi_babel',
)

# Examples (optional)
install_subdir(
    'aquacrop_bmi_babel/examples',
    install_dir: py.get_install_dir() / 'aquacrop_bmi_babel',
)

# Library subpackage
install_lib_srcs = [
    'aquacrop_bmi_babel/lib/__init__.py',
    'aquacrop_bmi_babel/lib/aquacrop.pyx',
]
py.install_sources(install_lib_srcs, subdir: 'aquacrop_bmi_babel/lib')

# Cython extension (uses compiled Fortran library)
py.extension_module(
    'aquacrop',
    [
        'aquacrop_bmi_babel/lib/bmi_interoperability.f90',
        'aquacrop_bmi_babel/lib/aquacrop.pyx',
    ],
    dependencies: [bmif_dep],  # ✓ только bmif_dep
    link_with: [fortran_lib],  # ✓ fortran_lib через link_with!
    include_directories: incs,
    fortran_args: ['-g'],  
    install: true,
    subdir: 'aquacrop_bmi_babel/lib',
)

# BMI metadata (for model_metadata)
install_subdir(
    'meta/AquaCrop',
    install_dir: py.get_install_dir() / 'aquacrop_bmi_babel/data',
)

run_command('cp', '-r', 'aquacrop_bmi_babel/data', 'build')
