import sys, time, board, busio, RPi.GPIO as GPIO
from adafruit_pca9685 import PCA9685

# --- Hardware Setup ---
i2c_bus = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c_bus, address=0x40)
pca.frequency = 50 

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

def get_distance():
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

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "dist":
        d = get_distance()
        # We print ONLY the number so the LLM can read it easily
        print(d)

    elif cmd == "stop":
        de_energize()
        print("STOPPED")

    elif cmd == "forward":
        sec = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
        # move(2.0, 1.0, sec)
        move(3.0, 1.0, sec)
        print(f"DONE: Moved forward {sec}s")

    elif cmd == "left":
        sec = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
        move(1.0, 1.0, sec)
        print(f"DONE: Turned left {sec}s")

    elif cmd == "right":
        sec = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
        move(3.0, 3.0, sec)
        print(f"DONE: Turned right {sec}s")

