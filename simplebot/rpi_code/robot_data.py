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
DIST_HALF_SECOND = 12.0 # real value is 11.

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

repeats = 0
repeatval = 0

def get_distance():
    num = 0
    total = 1000.0
    global repeats
    global repeatval

    while num < 3:
        # total = total + get_dist()
        temp = get_dist()
        if temp < total:
            total = temp
             
        num += 1
        print(f"get_distance {num} {total}")
    # return round(total/num, 1)
    if total < 0:
        total = 10.0

    # get off the wall
    print(f"---------------- Check for repeats {total} {repeatval}")
    if total > repeatval - 3 and total < repeatval + 3:
        print(f"found repeat {repeats} {repeatval}")
        repeats += 1
        if repeats >= 3:
            total = 10.0
    else:
        repeats = 0
        repeatval = total
    

    return round(total, 1)

if __name__ == "__main__":
    f = open("samples.txt", "a")
    sample = 1

    try:
        while True:
            d = get_distance()
            print(f"Distance {d}")
            sec = .4 # attempt a 90 degree turn
            if d < 30:
                move(3.0, 3.0, sec)
                print(f"DONE: Turned right {sec}s")
                f.write(f"{sample}, {d}, 2, {sec}\n")
            sec = .4
            if d>= 30:
                # sec = (d / DIST_HALF_SECOND) * .5
                if sec > 4:
                    sec = 3.9
                #if d > 60:
                #    sec = .5
                #if d > 80:
                #    sec = 2
                print(f"run for {sec}")
                move(3.0, 1.0, sec)
                print(f"DONE: Moved forward {sec}s")
                f.write(f"{sample}, {d}, 1, {sec}\n")
            sample += 1
            print(f"*********** number of samples {sample}")
            time.sleep(.5)
    
    except KeyboardInterrupt:
        de_energize()
        print("\n[!] User stopped script.")
        f.close()
    
