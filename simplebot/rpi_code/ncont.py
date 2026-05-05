import json
import math

import sys, time, board, busio, RPi.GPIO as GPIO
from adafruit_pca9685 import PCA9685
# from luma.core.interface.serial import i2c
# from luma.core.render import canvas
# from luma.oled.device import ssd1306

# --- Hardware Setup ---
i2c_bus = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c_bus, address=0x40)
pca.frequency = 50 

# serial = i2c(port=1, address=0x3c)
# display = ssd1306(serial)

GPIO.setmode(GPIO.BCM)
# TRIG, ECHO = 24, 25
TRIG, ECHO = 10, 17
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

LEFT, RIGHT = 0, 1

def de_energize():
    pca.channels[LEFT].duty_cycle = 0
    pca.channels[RIGHT].duty_cycle = 0

def move(l_pulse, r_pulse, duration):
    pca.channels[LEFT].duty_cycle = int((l_pulse / 20.0) * 65535)
    pca.channels[RIGHT].duty_cycle = int((r_pulse / 20.0) * 65535)
    time.sleep(duration)
    de_energize()

def get_dist():
    # Ensure TRIG is low
    GPIO.output(TRIG, False)
    time.sleep(0.01)
    
    # Trigger pulse
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    
    pulse_start = time.time()
    timeout = pulse_start + 0.1 # 100ms timeout
    
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout: return -1
        
    pulse_end = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout: return -1
        
    duration = pulse_end - pulse_start
    distance = (duration * 34300) / 2
    return round(distance, 1)

def get_distance():
    num = 0
    total = 0

    while num < 3:
       temp = get_dist()
       # total = total + get_dist()
       # print(f"total = {total}")
       if total < temp:
           total = temp
       num += 1

    # return round(total/num, 1)
    return round(total, 1)

def relu(x):
    return [max(0, i) for i in x]

def linear(input_vec, weights, bias):
    output = []
    # In PyTorch, weights are often [out_features, in_features]
    for row_weights, b in zip(weights, bias):
        # Calculate dot product + bias
        val = sum(i * w for i, w in zip(input_vec, row_weights)) + b
        output.append(val)
    return output

def get_manual_action(raw_sensor_val):
    # Load the weights once (or move this outside the function for speed)
    with open('robot_weights.json', 'r') as f:
        w = json.load(f)

    # Layer 1: Input -> 16 hidden
    # x will be a list of 16 values
    x = linear([float(raw_sensor_val)], w['layer1_w'], w['layer1_b'])
    x = relu(x)

    # Layer 2: 16 hidden -> 16 hidden
    x = linear(x, w['layer2_w'], w['layer2_b'])
    x = relu(x)

    # Output Layer: 16 hidden -> 2 (Direction, Time)
    prediction = linear(x, w['output_w'], w['output_b'])

    pred_dir = prediction[0]
    pred_time = prediction[1]

    # Logic: 0.0-0.5 is Forward, 0.5-1.0 is Turn
    # 1 = forward 2 = turn
    print(f"pred_dir {pred_dir}")
    if pred_dir < 1.5:
        action = 1
    if pred_dir >= 1.5:
        action = 2
    # action = int(pred_dir) # 1 if pred_dir < 0.5 else 2

    return action, max(0, pred_time)

if __name__ == "__main__":
    # Usage
    try:
    	while True:
            val = get_distance()
            if val > 200.0:
               val = 20.0

            cmd, sec = get_manual_action(val)
            print(f"turn info {val} {cmd} {sec}")
            # control run time or allow ai to control run time
            sec = .4
            if cmd > .4 and cmd < 1.4:
                #cmd = 'forward'
                move(3.0, 1.0, sec)
            else:
                move(3.0, 3.0, sec)
                #cmd = 'turn'
            time.sleep(.4)
        # execute_move(cmd, sec)
        
        
    except KeyboardInterrupt:
            de_energize()
            print("\n[!] User stopped script.")
