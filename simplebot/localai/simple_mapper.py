#!/usr/bin/env python3
"""
Simple Room Mapper for Z-Bot
Uses robot_bridge commands to explore and map the room
"""
import subprocess
import time
import os

class ZBotMapper:
    def __init__(self, home_dir="/home/kmansfie/aibot"):
        self.home_dir = home_dir
        self.map = {}  # Simple coordinate map
        self.start_pos = (0, 0)
        self.current_pos = (0, 0)
        self.map_file = os.path.join(home_dir, "maps", "simple_map.txt")
        
    def get_distance(self):
        """Get ultrasonic distance reading"""
        try:
            result = subprocess.run(
                ["python3", os.path.join(self.home_dir, "robot_bridge.py"), "dist"],
                capture_output=True, text=True, timeout=5
            )
            dist = float(result.stdout.strip())
            return dist if dist > 0 else -1
        except:
            return -1
    
    def move_forward(self, seconds=1.0):
        """Move robot forward"""
        subprocess.run(
            ["python3", os.path.join(self.home_dir, "robot_bridge.py"), "forward", str(seconds)],
            timeout=30
        )
    
    def move_left(self, seconds=0.5):
        """Turn left"""
        subprocess.run(
            ["python3", os.path.join(self.home_dir, "robot_bridge.py"), "left", str(seconds)],
            timeout=30
        )
    
    def move_right(self, seconds=0.5):
        """Turn right"""
        subprocess.run(
            ["python3", os.path.join(self.home_dir, "robot_bridge.py"), "right", str(seconds)],
            timeout=30
        )
    
    def stop(self):
        """Stop robot"""
        subprocess.run(
            ["python3", os.path.join(self.home_dir, "robot_bridge.py"), "stop"],
            timeout=30
        )
    
    def explore(self, steps=50, turn_interval=10):
        """Simple exploration pattern"""
        print(f"Starting exploration with {steps} steps...")
        print(f"Turning every {turn_interval} steps")
        print("-" * 40)
        
        for step in range(steps):
            # Move forward
            self.move_forward(1.0)
            print(f"Step {step+1:3d}: Moving forward...")
            time.sleep(0.5)
            
            # Random turn every N steps
            if step % turn_interval == 0 and step > 0:
                turn = "right" if step % (turn_interval * 2) == 0 else "left"
                self.move_right(0.5) if turn == "right" else self.move_left(0.5)
                print(f"Step {step+1:3d}: Turned {turn}")
                time.sleep(0.3)
            
            # Check distance
            dist = self.get_distance()
            print(f"  Distance: {dist:.1f} cm")
            
            # Stop if wall detected
            if dist < 30 and dist > 0:
                self.stop()
                print(f"  [!] Wall detected at {dist:.1f}cm, stopping!")
                time.sleep(1)
        
        print("-" * 40)
        print("Exploration complete!")
        print(f"Current position: ({self.current_pos[0]}, {self.current_pos[1]})")
    
    def manual_explore(self):
        """Manual exploration - follow your commands"""
        print("Manual exploration mode")
        print("Commands:")
        print("  forward [seconds]")
        print("  left [seconds]")
        print("  right [seconds]")
        print("  dist")
        print("  stop")
        print("-" * 40)
    
    def run_manual(self):
        """Run manual exploration loop"""
        while True:
            try:
                cmd = input("> ").strip().lower().split()
                
                if not cmd[0] or cmd[0] == "quit" or cmd[0] == "exit":
                    break
                
                action = cmd[0]
                
                if action in ["forward", "left", "right"]:
                    sec = float(cmd[1]) if len(cmd) > 1 else 1.0
                    func = getattr(self, f"move_{action}", None)
                    if func:
                        func(sec)
                        print(f"✓ Moved {action} for {sec}s")
                elif action == "dist":
                    dist = self.get_distance()
                    print(f"Distance: {dist:.1f} cm")
                elif action == "stop":
                    self.stop()
                    print("✓ Stopped")
                elif action == "clear":
                    print("Map cleared")
                
                time.sleep(0.5)
            except Exception as e:
                print(f"Error: {e}")
        
        # Save map
        self.save_map()
    
    def save_map(self):
        """Save map to file"""
        os.makedirs(os.path.dirname(self.map_file), exist_ok=True)
        with open(self.map_file, 'w') as f:
            f.write("Z-Bot Simple Map\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Start position: {self.start_pos}\n")
            f.write(f"Last position: {self.current_pos}\n\n")
            f.write("Path followed:\n")
            for i, pos in enumerate(self.path):
                f.write(f"  {i+1}. {pos}\n")
        print(f"Map saved to {self.map_file}")
    
    def run(self, mode="manual"):
        """Run mapper in mode: 'exploration' or 'manual'"""
        if mode == "exploration":
            self.explore(steps=50, turn_interval=10)
        else:
            self.run_manual()


if __name__ == "__main__":
    print("Z-Bot Simple Mapper")
    print("=" * 40)
    mapper = ZBotMapper()
    
    # Default to manual mode for safe exploration
    print("\nChoose mode:")
    print("  1. Exploration (automatic)")
    print("  2. Manual (I control movements)")
    print()
    
    choice = input("Choose (1 or 2): ").strip()
    
    if choice == "1":
        mapper.run(mode="exploration")
    elif choice == "2":
        mapper.run(mode="manual")
    else:
        print("Invalid choice, using manual mode")
        mapper.run(mode="manual")