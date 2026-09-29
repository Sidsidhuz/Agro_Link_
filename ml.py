"""Optional CPU inference for the original 150x150, four-class PyTorch CNN."""
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).resolve().parent
MODEL_DIR = BASE / "models"
LABELS = {
    "Corn": ["Corn___Common_Rust", "Corn___Gray_Leaf_Spot", "Corn___Healthy", "Corn___Northern_Leaf_Blight"],
    "Banana": ["cordana", "Banana_Healthy", "pestalotiopsis", "sigatoka"],
    "Grapes": ["Black_Root", "Grapes_Esca", "Leaf_Blight", "Grapes_Healthy"],
}


def weight_path(crop):
    return MODEL_DIR / f"{crop}_disease.pth"


@lru_cache(maxsize=3)
def load_model(crop, modified_time):
    import torch
    from torch import nn

    class CNN_Model(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(3, 32, 3, padding=1)
            self.pool = nn.MaxPool2d(2, 2)
            self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
            self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
            self.flatten = nn.Flatten()
            self.fc1 = nn.Linear(128 * 18 * 18, 256)
            self.dropout = nn.Dropout(0.5)
            self.fc2 = nn.Linear(256, len(LABELS[crop]))

        def forward(self, x):
            x = self.pool(torch.relu(self.conv1(x)))
            x = self.pool(torch.relu(self.conv2(x)))
            x = self.pool(torch.relu(self.conv3(x)))
            x = self.flatten(x)
            x = torch.relu(self.fc1(x))
            x = self.dropout(x)
            return self.fc2(x)

    model = CNN_Model()
    model.load_state_dict(torch.load(weight_path(crop), map_location="cpu", weights_only=True))
    model.eval()
    return model


def predict(crop, image_path):
    import torch
    from torchvision import transforms
    from PIL import Image

    model_path = weight_path(crop)
    model = load_model(crop, model_path.stat().st_mtime_ns)
    preprocess = transforms.Compose([
        transforms.Resize((150, 150)), transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5]),
    ])
    with Image.open(image_path) as image, torch.inference_mode():
        tensor = preprocess(image.convert("RGB")).unsqueeze(0)
        probabilities = torch.softmax(model(tensor), dim=1)[0]
        index = int(torch.argmax(probabilities))
    return {"prediction": LABELS[crop][index], "confidence": round(float(probabilities[index]), 4)}
