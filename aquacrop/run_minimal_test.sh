#!/bin/bash
cd /mnt/d/KNP/aquacrop-bmi/aquacrop

cat > test_minimal.f90 << 'FORTRAN_CODE'
program test_minimal
    use bmif
    use, intrinsic :: iso_c_binding
    implicit none
    
    type(bmi_aquacrop) :: model
    integer :: status
    real(c_double) :: val(1)
    character(len=1024) :: config_file
    
    config_file = "bmi_test_data/LIST/project.PRO"
    
    ! Initialize
    status = model%initialize(config_file)
    print '(A,I0)', "Initialize status: ", status
    
    ! Try to get fertility_stress
    print *, ""
    print *, "Attempting: get_value_double('crop__fertility_stress', val)"
    status = model%get_value_double("crop__fertility_stress", val)
    print '(A,I0)', "Status code: ", status
    print '(A,I0)', "BMI_SUCCESS = ", BMI_SUCCESS  
    print '(A,I0)', "BMI_FAILURE = ", BMI_FAILURE
    
    if (status == BMI_SUCCESS) then
        print '(A,F10.2)', "✅ Got value: ", val(1)
    else
        print *, "❌ get_value_double FAILED"
    end if
    
    ! Try canopy cover for comparison
    print *, ""
    print *, "For comparison, trying: get_value_double('crop__canopy_cover', val)"
    status = model%get_value_double("crop__canopy_cover", val)
    print '(A,I0)', "Status code: ", status
    
    if (status == BMI_SUCCESS) then
        print '(A,F10.2)', "✅ Got value: ", val(1)
    else
        print *, "❌ FAILED"
    end if
    
    status = model%finalize()
    
end program test_minimal
FORTRAN_CODE

echo "Compiling minimal test..."
gfortran -I/usr/local/include test_minimal.f90 -L. -laquacropbmi -o test_minimal

if [ $? -eq 0 ]; then
    echo "✅ Compiled"
    echo ""
    echo "Running test..."
    echo "========================================================================"
    ./test_minimal
    echo "========================================================================"
else
    echo "❌ Compilation failed"
fi
