# 🤖 Simple Bot

This is a project for a very simple robot and provides obstacle avoidance functionality.  This funnctionality is provided by a neural network. This neural network is trained on a PC with a GPU.  I will try and present some clear instructions as to how to get this project running to allow you to try the robot and see how it works.

The robot is a robot that uses continuously rotating servo motors.  These are inexpensive and easy to work with.  Along with two of these servo motors there is also an ultrasonic range finder.  This sensor has it's challenges.  I used a lid from a large jar of cashews.  Did some cutting on the lid hot glued a cell phone charging bank (great power source) to the lid.  On top of the power bank I hot glued a Raspberry Pi 3.  I had it laying around and thought I would put it to work.  I hooked it up and included a pca9865 pwm module to drive the servo motors.  I believe this is all that is involved.  I'll include a schematic for your information.

With the two servo motors you can spin the robot on itself.  It can turn on a dime.  It is very manuverable.

Issues with the ultrasonic range finder.  When you try and take a reading with the a wall at a good angle to the sensor it returns a very large number and the robot thinks it is clear ahead.  It tries to climb the wall.  Most of the time it recovers from this error state and continues.  I added some code in the control program to try and detect when it tries to climb a wall.  I put a check in the code when it got the same distance reading three times in a row it just does a 90 degree turn.  It works sometimes.

The first thing to do is clone this repository.

There are a few directories in the repository.  You have the pc_code directory where all the pc software is stored.  In the rpi_code is the raspberry pi code is where the raspberry pi code is stored.

The code in rpi_code contains a program called "robot_bridge_nostop.py".  This code contains routines to drive the motors, reads distance from the ultrasonic range finder, and runs an inference engine to control the robot using weights that came from training on samples collected by running the robot.  The training was done on a large PC with a GPU.  The sample file contained 1000 samples and thus wasn't very large.  It was enough to show a proof of concept and controlled the robot as well as the human developed robot control program that was used to collect the samples. 

The procedure I used to implement this project was the following:

#1 - The first thing you need is some data to train with.  I have found that the best way to collect data is to create a small control program that moves the robot.  This would include motor movement and range finding.  I then use the range findings to either turn if we are closer than say 30cm from an object or to move forward if we have more room.  Once the control program is moving the robot without hitting object I use that to collect data.  I record the range value then record the movement command to the motors.  That is either a turn or a move forward command.  I let the robot run for about an hour doing this.  We have collected our data.

#2 - I take the data and put it into a program that splits the inputs and outputs.  The input being the single range value and the outputs are the motor control values.  With this I can plug these values into a traning program that will give me a set of weights as a result.

#3 - The weights are then put into a program that has an inference engine that can take a range input and translate it into motor movement.  This inference engine runs on the robot.  Currently the weights are in a json format as there aren't a lot of weights.  The Neural network has one input neuron, 16 hidden layer neurons, and 2 output neurons.  This also helps with the size of the weights.  The weights are easily contained in a single file in json format.  

NOTE: At this point I have used these weights to run the robot that the data was collected from (RP3, Cell phone power bank, 2 continuously turning servo motors, and 1 ultrasonic range finder).  This same set of weights was able to run on a robot with a raspberry pi pico 2 w, cell phone power bank, 2 continuously turning servo motors, and 1 utlrasonic range finder.  There were no changes necessary to the weights.  I found that interesting that it would work.  It showed me the quality of the weights generated.

One issue with the raspberry pi pico 2 w robot.  It would shutdown after about a minute of running as the raspberry pi pico 2 w didn't draw enough current to keep the cell phone power bank awake.  I'm looking into another battery solution.

Next steps - The ultrasonic range finder has problems when it doesn't have a perpindicular surface in front of it to get a good range value.  If the object is at an angle to the range finder the distance can be much larger that it actually is.  This causes the robot to move forward and run into the object.  With Walls it tries to climb the walls.  I was thinking of turning the robot slightly to the right and take a range value then move to robot to the left and take a reading there.  Finally returning to the middle and deciding which direction to go.  I was thinking that if I took the lowest value and do the appropriate thing with that value that would be very conservative and give me some good results.


#***********************************

Getting started

# Clone the repository.
git clone https://github.com/kmansfie/AISimpleBot.git

# in pc_code do the following

#create the virtual environment named 'pc_code'
python3 -m venv pc_code

# Activate the environment
source pc_code/bin/activate

# install torch
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu130

# install pandas
pip3 install pandas

# then run the training.
python3 train.py

# you should see this
Starting training...
Epoch [20/200], Loss: 0.433995
Epoch [40/200], Loss: 0.142026
Epoch [60/200], Loss: 0.067175
Epoch [80/200], Loss: 0.041402
Epoch [100/200], Loss: 0.043106
Epoch [120/200], Loss: 0.038078
Epoch [140/200], Loss: 0.036695
Epoch [160/200], Loss: 0.035347
Epoch [180/200], Loss: 0.034148
Epoch [200/200], Loss: 0.034301

Test Sensor Input: 0.5
Predicted Direction: 1.7215, Predicted Time: 0.5486

# you should now have a file called robot_brain.pth
# now you have to convert this to json format.
python3 wtojson.py
Successfully converted robot_brain.pth to robot_weights.json

# now you should have a file called robot_weights.json that
# you copy to your robot and then run the inference engine
# on the robot.
scp robot_weigths.json user@robot:.

python3 -u ncont.py


   



#***********************************

More details on the 

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
