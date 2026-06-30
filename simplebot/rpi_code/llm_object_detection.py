#!/usr/bin/env python3
import requests 
import sys, time, board, busio, RPi.GPIO as GPIO
from adafruit_pca9685 import PCA9685
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
import os 
import json
import re

print("Start robot to llm com")
url = "http://100.120.121.96:11434/api/generate"

# Combine instructions into a single block that starts EXACTLY the same way every loop
# SYSTEM_INSTRUCTIONS = """You are an autonomous robot navigation agent exploring a room.
# 
# 
# CRITICAL NAVIGATION RULES:
# 1. If the Ultrasonic reading is LESS than 30.0 cm, you are facing a wall. You MUST choose "left" or "right" to turn away. Do NOT choose "forward" or "stop".
# 2. If the Ultrasonic reading is GREATER than 30.0 cm, the path is clear. You should choose "forward".
# 3. Move exactly 0.5 seconds per action.
# 4. Keep your 'notes' field under 10 words.
# 
# Respond strictly with valid JSON matching this schema:
# {
#     "action": "forward|left|right|backward",
#     "duration": 0.5,
#     "notes": "short observation string"
# }"""
# --- Updated Instructions for Object Following Mode ---
SYSTEM_INSTRUCTIONS = """You are an autonomous tracking robot. Your goal is to FOLLOW the target object detected in the telemetry data.

TARGET TRACKING RULES:
1. Look at the Radar Scan Array indexes: 0=Far Left, 1=Left, 2=Center, 3=Right, 4=Far Right.
2. Find the index with the LOWEST distance value (the target).
3. If the lowest value is at index 0 or 1, the target is to your left. Choose "left" to center it.
4. If the lowest value is at index 3 or 4, the target is to your right. Choose "right" to center it.
5. If the lowest value is at index 2 (Center):
   - If the distance is GREATER than 22.0 cm, choose "forward" to get closer.
   - If the distance is LESS than 12.0 cm, choose "backward" to back up.
   - If the distance is between 12.0 cm and 22.0 cm, choose "stop" to maintain distance.
6. If all values in the array are greater than 70.0 cm, the target is too far away. Choose "forward" to prowl straight ahead and hunt for it.

Respond strictly with valid JSON matching this schema:
{
    "action": "forward|left|right|backward|stop",
    "duration": 0.4,
    "notes": "tracking target target_index"
}"""

# --- Hardware Setup ---
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

def de_energize():
    pca.channels[LEFT].duty_cycle = 0
    pca.channels[RIGHT].duty_cycle = 0

def move(l_pulse, r_pulse, duration):
    pca.channels[LEFT].duty_cycle = int((l_pulse / 20.0) * 65535)
    pca.channels[RIGHT].duty_cycle = int((r_pulse / 20.0) * 65535)
    time.sleep(duration)
    de_energize()

def get_dist():
    GPIO.output(TRIG, False)
    time.sleep(0.01)
    
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    
    pulse_start = time.time()
    timeout = pulse_start + 0.1 
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout: return -1
        time.sleep(0.00001)
        
    pulse_end = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout: return -1
        time.sleep(0.00001)
        
    duration = pulse_end - pulse_start
    distance = (duration * 34300) / 2
    return round(distance, 1)

def get_distance():
    num = 0
    total = 0
    while num < 3:
       total = total + get_dist()
       num += 1
    return round(total/num, 1)

def scan_environment():
    print("[*] Initiating Full-Body Radar Scan...", flush=True)
    # 1. Turn hard left to establish a starting boundary (~ -45 degrees)
    move(1.0, 1.0, 0.3) 
    time.sleep(0.2)     # Let the chassis settle down to prevent shaky readings
    
    scan_data = []
    
    # 2. Rotate right in tiny increments (5 small steps across a ~90-degree arc)
    for step in range(5):
        distance = get_distance()
        scan_data.append(distance)
        
        # Click the robot slightly to the right
        move(2.0, 2.0, 0.08) 
        time.sleep(0.1) 
        
    # 3. Return the robot back to center (Turn left back to original forward heading)
    move(1.0, 1.0, 0.25)
    print(f"[*] Scan Complete. Results (Left to Right): {scan_data}", flush=True)
    return scan_data

TIMEOUT_SECONDS = 4.0


if __name__ == "__main__":
    try:
        print("llm_object_detection ver 0.1", flush=True)
        sec = 0.0
        prev_d = 500.0
        last_action = "forward"

        with requests.Session() as session:
            while True:
                # d = get_distance()

                # # Try to detect specular reflection wall glitching and compensate for it
                # if last_action == "forward":
                #     print(f"d = {d} prev_d = {prev_d}")
                #     if d > prev_d:
                #         print("correct hugging wall")
                #         d = 15.0
                #     else:
                #         prev_d = d
                # if last_action == "left" or last_action == "right":
                #     prev_d = 500.0

                # # --- Adaptive Multi-Angle Telemetry Assembly ---
                # if d <= 30.0:
                #     # Near an obstacle! Trigger full-body scan to map spatial openings
                #     scan_results = scan_environment()
                #     
                #     dynamic_telemetry = f"""Input telemetry data:
# - Center Ultrasonic reading: {d} cm (OBSTACLE DETECTED)
# - Multi-Angle Radar Scan Array (Far Left to Far Right): {scan_results} cm

# CRITICAL DIRECTIONAL INSTRUCTION:
# Analyze the Radar Scan Array. Choose the direction ("left" or "right") that points toward the largest clear distance values in the array to steer away from the obstacle."""
                # else:
                #     # Path is completely open, standard forward driving
                #     dynamic_telemetry = f"Input telemetry data:\nUltrasonic reading: {d} cm\nPath is completely clear ahead."

                # # Append the dynamic part to the bottom of the static text
                # full_prompt = f"{SYSTEM_INSTRUCTIONS}\n\n{dynamic_telemetry}"
                # 
                # payload = {
                #     "model": "qwen-big-context:latest",
                #     "prompt": full_prompt,
                #     "stream": False,
                #     "format": "json",
                #     "options": {
                #         "temperature": 0.1,
                #         "num_predict": 400
                #     }
                # }

                # In tracking mode, we run the scan sweep to locate the object
                scan_results = scan_environment()

                # Find the smallest distance and where it is in the array
                min_distance = min(scan_results)
                target_index = scan_results.index(min_distance)

                print(f"[*] Tracking Telemetry -> Closest Object: {min_distance} cm at index {target_index}", flush=True)

                # Assemble the target tracking prompt payload
                dynamic_telemetry = f"""Input telemetry data:
- Multi-Angle Radar Scan Array (Index 0 to 4): {scan_results} cm
- Closest Detected Target Distance: {min_distance} cm
- Target Array Index: {target_index}"""

                full_prompt = f"{SYSTEM_INSTRUCTIONS}\n\n{dynamic_telemetry}"

                payload = {
                    "model": "qwen-big-context:latest",
                    "prompt": full_prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 200 # Lowered slightly for faster RTT
                    }
                }

                t0 = time.time()
                response = session.post(url, json=payload, timeout=TIMEOUT_SECONDS)
                t1 = time.time()
                llm_total = t1 - t0
                print(f"LLM Network RTT: {llm_total:.4f} seconds")

                action = "forward"
                value = 0.5

                if response.status_code == 200:                                               
                    response_data = response.json()                                           
                    response_json_str = response_data.get("response", "{}")

                    # If 'response' is empty, fall back to the data inside the 'thinking' key
                    if not response_json_str.strip():
                        response_json_str = response_data.get("thinking", "{}")

                    try:
                        cmd = json.loads(response_json_str)
                        action = cmd.get("action", "forward")
                        value = float(cmd.get("duration", 0.5))
                    except Exception as parse_error:
                        print(f"JSON recovery fallback triggered: {parse_error}")
                        action = 'stop'
                        # If json.loads fails, try regex extraction
                        action_match = re.search(r'"action"\s*:\s*"([^"]+)"', response_json_str)
                        if action_match:
                            action = action_match.group(1)   
                        else:
                            action = "stop"                  
                        
                else:                                                                         
                    print(f"Error: {response.status_code} - {response.text}")                                   

                last_action = action
                print(f"Action = {action}")
                
                # --- Action Execution States ---
                if action == "stop":
                    de_energize()
                    print("STOPPED", flush=True)
            
                elif action == "forward":
                    sec = value if value > 0.0 else 0.5
                    # fail safe to avoid hitting walls
                    # if d > 30.0:
                    move(2.0, 1.0, sec*2.0)
            
                elif action == "backward":
                    sec = value if value > 0.0 else 0.5
                    move(1.0, 2.0, sec)
            
                elif action == "left":
                    sec = value if value > 0.0 else 0.5
                    move(1.0, 1.0, sec)
            
                elif action == "right":
                    sec = value if value > 0.0 else 0.5
                    move(2.0, 2.0, sec)
            
                # Update visual display readouts
                final_dist = get_distance()
                with canvas(display) as draw:
                    draw.text((0, 0),  f"ACT: {action}", fill="white")
                    draw.text((0, 16), f"SEC: {sec:.2f}", fill="white")
                    draw.text((0, 32), f"DST: {final_dist}", fill="white")
                    draw.text((0, 48), f"RTT: {llm_total:.2f}s", fill="white")
                    
    except KeyboardInterrupt:
        print("\n[!] Disconnecting robot cleanly. Powering down servos...", flush=True)
        de_energize()
        GPIO.cleanup()

    except Exception as general_crash:
        print(f"\n[!] Unexpected Script Crash: {general_crash}",flush=True)

    finally:
        print("\n[*] Cleaning hardware registers. Powering down servos...", flush=True)
        de_energize()
        GPIO.cleanup()

