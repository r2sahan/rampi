# crontab runs this file every 3 minutes

import helper
from time import sleep
from drivers import Turta_APDS9960, Turta_BME680, Turta_MotionSensor

# Initialize
apds9960 = Turta_APDS9960.APDS9960Sensor()
bme680 = Turta_BME680.BME680Sensor()
motionSensor = Turta_MotionSensor.MotionSensor()
wait_time = 3


@helper.safe_log
def run_sensors():
    measure_time = 30
    temperatures = []
    humidities = []
    pressures = []
    gas_resistances = []
    motions = []
    ambient_lights = []
    proximities = []
    cpu_temperatures = []
    while measure_time > 0:
        temperatures.append(bme680.read_temperature())
        humidities.append(bme680.read_humidity())
        pressures.append(bme680.read_pressure())
        gas_resistances.append(bme680.read_gas_resistance())
        motions.append(motionSensor.read_motion_state())
        ambient_lights.append(apds9960.read_ambient_light())
        proximities.append(apds9960.read_proximity())
        cpu_temperatures.append(helper.get_cpu_temperature())
        measure_time = measure_time - 1
        sleep(wait_time)

    temperature = helper.get_avg(temperatures, 1)  # C
    humidity = helper.get_avg(humidities, 1)  # RH
    pressure = helper.get_avg(pressures)  # Pa
    gas_resistance = helper.get_avg(gas_resistances)  # Ohms
    motion = helper.get_sum(motions)
    ambient_light = helper.get_avg(ambient_lights)
    proximity = helper.get_avg(proximities)
    cpu_temperature = helper.get_avg(cpu_temperatures, 1)

    data = [temperature, humidity, pressure, motion, gas_resistance,
            ambient_light, proximity, cpu_temperature]

    helper.log(data)
    helper.send(data)
    helper.capture(motions)


run_sensors()
