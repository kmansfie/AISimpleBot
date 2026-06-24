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
       total = total + get_dist()
       num += 1
    return round(total/num, 1)


if __name__ == "__main__":
    try:
        print("robot_llm_com ver 0.2", flush=True)
        sec = 0.0

        # --- FIX 1: Open a open-ended Session to reuse the TCP handshake ---
        with requests.Session() as session:
            while True:
                d = get_distance()
                print(f"Current distance sensor reading: {d} cm", flush=True)

                msg = f"""You are an autonomous robot navigation agent exploring a room.
                Current Sensor Data:
                - Ultrasonic reading: {d} cm
                
                CRITICAL NAVIGATION RULES:
                1. If the Ultrasonic reading is LESS than 30.0 cm, you are facing a wall. You MUST choose "left" or "right" to turn away. Do NOT choose "forward" or "stop".
                2. If the Ultrasonic reading is GREATER than 30.0 cm, the path is clear. You should choose "forward".
                3. Move exactly 0.5 seconds per action.
                4. "Keep your 'notes' field under 10 words."
                
                Respond strictly with valid JSON matching this schema:
                {{
                    "action": "forward|left|right|backward",
                    "duration": 0.5,
                    "notes": "short observation about the wall distance"
                }}
                """
                
                # msg = f"""You are an autonomous robot navigation agent.
                # Current Sensor Data:
                # - Ultrasonic reading: {d} cm

                # Remember if the distance is less than 30.0 cm you MUST turn.
                # Caution: only move 0.5 seconds in any direction.

                # Respond strictly with valid JSON matching this schema:
                # {{
                #     "action": "forward|left|right|backward,
                #     "duration": 0.5,
                #     "notes": "short observation statement"
                # }}
                # """

                payload = {
                    "model": "qwen-big-context:latest",
                    "prompt": msg,
                    "stream": False,
                    "format": "json", # --- FIX 2: Forces immediate JSON structured generation ---
                    "think": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 150  # Short limit clips reasoning overhead
                    }
                }
     
                t0 = time.time()
                # Using session.post instead of requests.post keeps the connection alive
                response = session.post(url, json=payload)
                t1 = time.time()
                llm_total = t1 - t0
                print(f"LLM Network RTT: {llm_total:.4f} seconds")

                action = "forward"
                value = 0.5

                if response.status_code == 200:                                               
                    response_data = response.json()                                           
                    response_json_str = response_data.get("response", "{}")
                    print(f"Raw Output: {response_json_str.strip()}")
                                                                                              
                    try:
                        cmd = json.loads(response_json_str)
                        action = cmd.get("action", "forward")
                        value = float(cmd.get("duration", 0.5))
                        print(f"***************** Validated Action Execution: {action} for {value}s")
                    except Exception as parse_error:
                        print(f"JSON recovery fallback triggered: {parse_error}")
                        action = 'stop'
                        # If json.loads fails, try regex extraction
                        action_match = re.search(r'"action"\s*:\s*"([^"]+)"', raw_output)
                        if action_match:
                            action = action_match.group(1)   # This would successfully extract "left"
                        else:
                            action = "stop"                  # Ultimate safe fallback
                        
                else:                                                                         
                    print(f"Error: {response.status_code} - {response.text}")                                   

                # --- Action Execution States ---
                if action == "stop":
                    de_energize()
                    print("STOPPED", flush=True)
            
                elif action == "forward":
                    sec = value if value > 0.0 else 0.5
                    if d > 30.0:
                        move(2.0, 1.0, sec)
                    print(f"-------------- DONE: Moved forward {sec}s", flush=True)
            
                elif action == "backward":
                    sec = value if value > 0.0 else 0.5
                    move(1.0, 2.0, sec)
                    print(f"-------------- DONE: Moved backward {sec}s", flush=True)
            
                elif action == "left":
                    sec = value if value > 0.0 else 0.5
                    move(1.0, 1.0, sec)
                    print(f"-------------- DONE: Turned left {sec}s", flush=True)
            
                elif action == "right":
                    sec = value if value > 0.0 else 0.5
                    move(2.0, 2.0, sec)
                    print(f"-------------- DONE: Turned right {sec}s", flush=True)
            
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

