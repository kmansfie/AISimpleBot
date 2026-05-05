import torch
import torch.nn as nn
import json

# 1. Define the architecture so PyTorch can load the weights
class RobotNet(nn.Module):
    def __init__(self):
        super(RobotNet, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(1, 16), # Layer 0
            nn.ReLU(),        # Layer 1
            nn.Linear(16, 16),# Layer 2
            nn.ReLU(),        # Layer 3
            nn.Linear(16, 2)  # Layer 4
        )

    def forward(self, x):
        return self.network(x)

# 2. Load the trained weights
model = RobotNet()
model.load_state_dict(torch.load('robot_brain.pth'))
model.eval()

# 3. Extract the weights into a standard Python dictionary
# We convert tensors to lists so JSON can handle them
weights_dict = {
    "layer1_w": model.network[0].weight.tolist(),
    "layer1_b": model.network[0].bias.tolist(),
    "layer2_w": model.network[2].weight.tolist(),
    "layer2_b": model.network[2].bias.tolist(),
    "output_w": model.network[4].weight.tolist(),
    "output_b": model.network[4].bias.tolist()
}

# 4. Save to JSON
with open('robot_weights.json', 'w') as f:
    json.dump(weights_dict, f, indent=4)

print("Successfully converted robot_brain.pth to robot_weights.json")

