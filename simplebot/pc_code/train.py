import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd

# 1. DATA LOADING
def load_robot_data(file_path):
    data = pd.read_csv(file_path, header=None)
    # X: Sensor (Input), y: Direction and Time (Outputs)
    X = torch.tensor(data.iloc[:, 1].values, dtype=torch.float32).unsqueeze(1)
    y = torch.tensor(data.iloc[:, 2:4].values, dtype=torch.float32)
    return X, y

# 2. MODEL DEFINITION
class RobotNet(nn.Module):
    def __init__(self):
        super(RobotNet, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(1, 16),
            nn.ReLU(),
            nn.Linear(16, 16),
            nn.ReLU(),
            nn.Linear(16, 2) # Two outputs: Direction and Time
        )

    def forward(self, x):
        return self.network(x)

# 3. SETUP & TRAINING
X_train, y_train = load_robot_data('robot_movements.csv')
model = RobotNet()
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

print("Starting training...")
for epoch in range(200):
    # Predict
    outputs = model(X_train)
    loss = criterion(outputs, y_train)
    
    # Backprop
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    if (epoch + 1) % 20 == 0:
        print(f'Epoch [{epoch+1}/200], Loss: {loss.item():.6f}')

# 4. TESTING THE BRAIN
# Let's feed it a fake sensor reading to see what it suggests
test_sensor_val = torch.tensor([[0.5]]) # Example sensor value
model.eval() # Set to evaluation mode
with torch.no_grad():
    prediction = model(test_sensor_val)
    direction, time = prediction[0]
    print(f"\nTest Sensor Input: {test_sensor_val.item()}")
    print(f"Predicted Direction: {direction:.4f}, Predicted Time: {time:.4f}")

# 5. SAVE FOR ROBOT DEPLOYMENT
torch.save(model.state_dict(), 'robot_brain.pth')

