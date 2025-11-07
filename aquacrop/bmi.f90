! Wrapper module для совместимости с babelizer
module bmif
    ! Импортируем константы из BMI-Fortran
    use bmif_2_0, only: BMI_SUCCESS, BMI_FAILURE, BMI_MAX_COMPONENT_NAME, &
                        BMI_MAX_VAR_NAME, BMI_MAX_TYPE_NAME, BMI_MAX_UNITS_NAME
    
    ! Импортируем ваш тип КАК "bmi" (алиас!)
    use aquacropbmi, only: bmi => bmi_aquacrop
    
    implicit none
    public
end module bmif