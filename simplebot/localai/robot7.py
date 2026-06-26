import time
import board
import busio
from adafruit_pca9685 import PCA9685
import RPi.GPIO as GPIO
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

# --- Hardware Setup ---
try:
    i2c_bus = busio.I2C(board.SCL, board.SDA)
    pca = PCA9685(i2c_bus, address=0x40)
    pca.frequency = 50 

    serial = i2c(port=1, address=0x3c)
    display = ssd1306(serial)

    GPIO.setmode(GPIO.BCM)
    TRIG, ECHO = 24, 25
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)

    LEFT, RIGHT = 0, 1
except Exception as e:
    print(f"Hardware Error: {e}")
    exit()

def move(l_pulse, r_pulse):
    """Sends the pulse. 1.5 is the magic number for STOP."""
    pca.channels[LEFT].duty_cycle = int((l_pulse / 20.0) * 65535)
    pca.channels[RIGHT].duty_cycle = int((r_pulse / 20.0) * 65535)

def get_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    
    pulse_start, pulse_end = time.time(), time.time()
    timeout = time.time() + 0.1
    
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout: return None
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout: return None
        
    return round(((pulse_end - pulse_start) * 34300) / 2, 1)

# --- Main Execution ---
try:
    print("Z-Bot active. Ctrl+C to Kill.")
    while True:
        dist = get_distance()
        
        if dist and dist < 25:
            move(1.5, 1.5) # Force Stop
            action, obs = "STOPPED", "BLOCKED"
        else:
            move(2.0, 1.0) # Forward
            action, obs = "FORWARD", "CLEAR"

        with canvas(display) as draw:
            draw.text((0, 0),  f"ACT: {action}", fill="white")
            draw.text((0, 16), "MSG: ACTIVE", fill="white")
            draw.text((0, 32), f"OBJ: {obs}", fill="white")
            draw.text((0, 48), f"DST: {dist if dist else '---'} cm", fill="white")
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n[!] User stopped script.")

finally:
    # THIS SECTION RUNS NO MATTER WHAT
    print("[!] Cleaning up hardware...")
    
    # 1. Active Stop: Send the Neutral pulse
    try:
        move(1.5, 1.5)
        time.sleep(0.2) # Give the chip a millisecond to process
    except:
        pass

    # 2. De-energize: Turn off PWM entirely
    try:
        pca.channels[LEFT].duty_cycle = 0
        pca.channels[RIGHT].duty_cycle = 0
        pca.deinit()
    except:
        pass

    # 3. Release GPIO
    GPIO.cleanup()
    
    with canvas(display) as draw:
        draw.text((20, 25), "HALTED", fill="white")
    
    print("[x] Robot safely stopped.")

