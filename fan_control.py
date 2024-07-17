from subprocess import run as srun, PIPE
from time import sleep
from datetime import timedelta as td, datetime as dt
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for fan control steps
STEP1 = 48
STEP2 = 60
STEP3 = 65
STEP4 = 72

SLEEP_TIMER = 1  # Sleep time between checks
TICKS = 3  # Number of cycles before checking again
DELTA_TEMP = 3  # Temperature variation for speed change
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
FAN_CONTROL_FILE = '/sys/class/thermal/cooling_device0/cur_state'

def main():
    t0 = dt.now()
    old_speed = 0

    while True:
        sleep(SLEEP_TIMER)
        t1 = dt.now()
        
        if t1 > t0 + td(minutes=TICKS):
            t0 = t1
            celsius = get_cpu_temp()

            speed = determine_fan_speed(celsius)
            delta_temp_neg = celsius - DELTA_TEMP
            delta_temp_pos = celsius + DELTA_TEMP

            if old_speed != speed and not (delta_temp_neg <= celsius <= delta_temp_pos):
                update_fan_speed(speed, celsius, t0)
                old_speed = speed

def get_cpu_temp():
    temp_out = get_output('vcgencmd measure_temp')
    try:
        return int(temp_out.split('temp=')[1].split('.')[0])
    except (IndexError, ValueError):
        return 40  # Default value in case of error

def determine_fan_speed(temp):
    # Using a dictionary to simulate a switch-case
    switch = {
        temp < STEP1: 0,
        STEP1 <= temp < STEP2: 1,
        STEP2 <= temp < STEP3: 2,
        STEP3 <= temp < STEP4: 3,
        temp >= STEP4: 4
    }
    return switch[True]

def update_fan_speed(speed, temp, timestamp):
    logging.info(f'Updating fan speed to {speed} at {timestamp.strftime(DATETIME_FORMAT)} (Temp: {temp}ºC)')
    _command = f'echo {speed} | sudo tee -a {FAN_CONTROL_FILE} > /dev/null'
    call_shell(_command)
    check_val = get_output(f'cat {FAN_CONTROL_FILE}')
    logging.info(f'Confirmed FAN speed set to: {check_val.strip()}')

def call_shell(cmd, shell=True):
    return srun(cmd, stdout=PIPE, shell=shell)

def get_output(cmd, shell=True):
    stdout = call_shell(cmd, shell=shell).stdout
    try:
        return stdout.decode('utf-8')
    except UnicodeDecodeError:
        return ""

# Run the script
if __name__ == "__main__":
    main()
