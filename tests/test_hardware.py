from codecarbon.external import hardware

def test_output():
    temp = hardware.CPU.get_cpu_temperature()
    assert type(temp) == float
    temp_in_expected_range = False
    for x in range(15000):
        x_to_float = float(x/100)
        if round(temp, 2) == x_to_float :
            temp_in_expected_range = True
    assert temp_in_expected_range == True
