# 🤖 Simple Bot

A clean, minimal robot project skeleton.

## 🚀 Getting Started

### 1. Start the Robot

```bash
cd /home/kmansfie/zbot
source zbot/bin/activate
```

### 2. Run the Robot

```bash
python robot_bridge_nostop.py
```

### 3. Send Commands

```bash
dist        # Get distance
forward 2  # Move forward
right 0.5  # Turn right
stop        # Emergency stop
```

## 📁 Project Structure

```
simplebot/
├── README.md              # This file
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
├── LICENSE                # License
├── pc_code/               # PC control scripts
├── rpi_code/              # Raspberry Pi code
├── prompts/               # LLM prompts
└── logs/                  # Exploration logs
```

## 📋 Next Steps

1. **Create your controllers** in `pc_code/`
2. **Create motor bridge** in `rpi_code/`
3. **Add LLM prompts** in `prompts/`
4. **Save logs** in `logs/`

## 🛠️ Hardware

- Ultrasonic sensor (HC-SR04)
- Motor controller (GPIO-based)
- Raspberry Pi

## ⚙️ Configuration

Edit `config.py`:

```python
REMOTE_HOST = "kmansfie@192.168.0.36"
ROBOT_SCRIPT = "source zbot/bin/activate && python3 robot_bridge_nostop.py"
DISTANCE_THRESHOLD = 15  # cm
MAX_FORWARD = 2  # seconds
TURN_DURATION = 0.5  # seconds
OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen3.5:4b"
```

---

*Created for Kim's robot projects*
