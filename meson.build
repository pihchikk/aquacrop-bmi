project(
    'aquacrop_bmi_babel',
    'fortran',
    'cython',
    version: '0.1',
)

py = import('python').find_installation(pure: false)
compiler = meson.get_compiler('fortran')

# python_inc = py.get_path('data') / 'include'
numpy_inc = run_command(
    py,
    [
        '-c',
        'import numpy; print(numpy.get_include())'
    ],
    check: true
).stdout().strip()
incs = include_directories(
    [
        'aquacrop_bmi_babel/lib',
        # python_inc,
        numpy_inc,
    ]
)

deps = [
]

# Files get copied to <python directory>/site-packages/<subdir>
install_pkg_srcs = [
    'aquacrop_bmi_babel/__init__.py',
    'aquacrop_bmi_babel/_bmi.py',
    'aquacrop_bmi_babel/_version.py',
]
py.install_sources(
    install_pkg_srcs,
    subdir: 'aquacrop_bmi_babel',
)

install_lib_srcs = [
    'aquacrop_bmi_babel/lib/__init__.py',
    'aquacrop_bmi_babel/lib/aquacrop.pyx',
]
py.install_sources(
    install_lib_srcs,
    subdir: 'aquacrop_bmi_babel/lib',
)
py.extension_module(
    'aquacrop',
    [
        'aquacrop_bmi_babel/lib/bmi_interoperability.f90',
        'aquacrop_bmi_babel/lib/aquacrop.pyx',
    ],
    dependencies: [
        dependency('aquacropbmi', method : 'pkg-config'),
    ],
    include_directories: incs,
    install: true,
    subdir: 'aquacrop_bmi_babel/lib',
)

install_subdir(
    'meta/AquaCrop',
    install_dir: py.get_install_dir() / 'aquacrop_bmi_babel/data',
)

# This is a temporary fix for editable installs.
run_command('cp', '-r', 'aquacrop_bmi_babel/data', 'build')