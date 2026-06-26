import json
import math
import sys, time, board, busio, RPi.GPIO as GPIO
from adafruit_pca9685 import PCA9685

# --- Hardware Setup ---
# Initialize the I2C bus (SDA/SCL pins) for communication with the PCA9685
i2c_bus = busio.I2C(board.SCL, board.SDA)
# Create the PCA9685 object at address 0x40 (standard default)
pca = PCA9685(i2c_bus, address=0x40)
pca.frequency = 50 # Set frequency to 50Hz (standard for servos/motor controllers)

# GPIO Setup for the HC-SR04 Ultrasonic Sensor
GPIO.setmode(GPIO.BCM)
TRIG, ECHO = 10, 17 # Trigger pin and Echo pin
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# PCA9685 Channel indices for the motors
LEFT, RIGHT = 0, 1

def de_energize():
    """Sets motor duty cycles to 0 to stop movement and save power."""
    try:
        # We wrap these in a try block because I2C writes can fail
        # if a wire is loose or there is electrical noise.
        pca.channels[LEFT].duty_cycle = 0
        pca.channels[RIGHT].duty_cycle = 0
    except OSError:
        # Instead of crashing the script, we just print the error
        # and allow the loop to try again on the next cycle.
        print("[!] I2C Write Failed during de-energize")

def move(l_pulse, r_pulse, duration):
    """
    Controls motors based on pulse widths (ms).
    """
    try:
        pca.channels[LEFT].duty_cycle = int((l_pulse / 20.0) * 65535)
        pca.channels[RIGHT].duty_cycle = int((r_pulse / 20.0) * 65535)
        time.sleep(duration)
        de_energize()
    except OSError:
        print("[!] I2C Write Failed during move")

# def de_energize():
#     """Sets motor duty cycles to 0 to stop movement and save power."""
#     pca.channels[LEFT].duty_cycle = 0
#     pca.channels[RIGHT].duty_cycle = 0

# def move(l_pulse, r_pulse, duration):
#     """
#     Controls motors based on pulse widths (ms).
#     Duty cycle calculation: (Target Pulse / 20ms period) * 16-bit max value (65535)
#     """
#     pca.channels[LEFT].duty_cycle = int((l_pulse / 20.0) * 65535)
#     pca.channels[RIGHT].duty_cycle = int((r_pulse / 20.0) * 65535)
#     time.sleep(duration) # Keep moving for the specified time
#     de_energize()        # Stop after duration

def get_dist():
    """Calculates physical distance using the HC-SR04 ultrasonic sensor."""
    # Ensure TRIG is low to start clean
    GPIO.output(TRIG, False)
    time.sleep(0.01)
    
    # Send a 10-microsecond pulse to trigger the sensor
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    
    pulse_start = time.time()
    timeout = pulse_start + 0.1 # 100ms safety timeout to prevent hanging
    
    # Wait for ECHO pin to go HIGH (start of return pulse)
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout: return -1
        
    # Wait for ECHO pin to go LOW (end of return pulse)
    pulse_end = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout: return -1
        
    # Distance = (time taken * speed of sound) / 2 (for the round trip)
    duration = pulse_end - pulse_start
    distance = (duration * 34300) / 2
    return round(distance, 1)

def get_distance():
    """Averages/Filters 3 sensor readings to reduce noise and 'ghost' readings."""
    num = 0
    max_val = 0
    while num < 3:
       temp = get_dist()
       # This logic currently keeps the largest value of the 3 samples
       if max_val < temp:
           max_val = temp
       num += 1
    return round(max_val, 1)

def relu(x):
    """Rectified Linear Unit: The activation function. If x < 0, it becomes 0."""
    return [max(0, i) for i in x]

def linear(input_vec, weights, bias):
    """
    The 'Linear' or 'Dense' layer of the neural network.
    Calculates: (Input * Weights) + Bias
    """
    output = []
    # Each row in weights corresponds to one 'neuron' in the next layer
    for row_weights, b in zip(weights, bias):
        # Calculate dot product: sum of (input_i * weight_i)
        val = sum(i * w for i, w in zip(input_vec, row_weights)) + b
        output.append(val)
    return output

def get_manual_action(raw_sensor_val):
    """Feeds the sensor data through the neural network to decide an action."""
    # Load trained weights from JSON file
    with open('robot_weights.json', 'r') as f:
        w = json.load(f)

    # Layer 1: Takes 1 input (distance) and outputs 16 hidden values
    x = linear([float(raw_sensor_val)], w['layer1_w'], w['layer1_b'])
    x = relu(x)

    # Layer 2: Takes 16 hidden values and outputs 16 hidden values
    x = linear(x, w['layer2_w'], w['layer2_b'])
    x = relu(x)

    # Output Layer: Takes 16 hidden values and outputs 2 results (Direction, Time)
    prediction = linear(x, w['output_w'], w['output_b'])

    pred_dir = prediction[0]
    pred_time = prediction[1]

    # Threshold logic: Decides if it should move forward (1) or turn (2)
    # The NN is trained to output a value that falls into these buckets
    if pred_dir < 1.5:
        action = 1
    else:
        action = 2

    return action, max(0, pred_time)

if __name__ == "__main__":
    try:
        while True:
            # 1. Get filtered distance from sensor
            val = get_distance()
            
            # Clamp value if sensor goes out of range
            if val > 200.0:
               val = 20.0

            # 2. Ask the Neural Network what to do based on that distance
            cmd, sec = get_manual_action(val)
            print(f"Reading: {val} | Action: {cmd} | Time: {sec}")
            
            # Currently overrides NN time with a fixed .4s for safety
            sec = .4
            
            # 3. Execute movement
            if 0.4 < cmd < 1.4:
                # Move forward (asymmetric pulse widths for motor calibration)
                move(3.0, 1.0, sec)
            else:
                # Turn (equal pulse widths for a pivot)
                move(3.0, 3.0, sec)
            
            # Brief pause before next 'thought' cycle
            time.sleep(.4)
        
    except KeyboardInterrupt:
        de_energize() # Always stop the motors on Ctrl+C
        print("\n[!] User stopped script.")

