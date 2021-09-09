import torch
import torch.nn as nn
from torchvision import datasets
from torchvision.transforms import ToTensor
from torch.utils.data import DataLoader
from torch import optim

from codecarbon import EmissionsTracker

tracker = EmissionsTracker(project_name="pytorch-mnist-multigpu")
tracker.start()
# https://medium.com/@nutanbhogendrasharma/pytorch-convolutional-neural-network-with-mnist-dataset-4e8a4265e118
# https://pytorch.org/tutorials/beginner/blitz/data_parallel_tutorial.html#create-model-and-dataparallel

# Parameters and DataLoaders
input_size = 5
output_size = 2

batch_size = 30
data_size = 100

train_data = datasets.MNIST(
    root=".",
    train=True,
    transform=ToTensor(),
    download=True,
)
test_data = datasets.MNIST(root=".", train=False, transform=ToTensor())


loaders = {
    "train": DataLoader(train_data, batch_size=60, shuffle=True, num_workers=4),
    "test": DataLoader(test_data, batch_size=60, shuffle=True, num_workers=2),
}


class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.conv1 = nn.Sequential(
            nn.Conv2d(
                in_channels=1,
                out_channels=16,
                kernel_size=5,
                stride=1,
                padding=2,
            ),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(16, 32, 5, 1, 2),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        # fully connected layer, output 10 classes
        self.out = nn.Linear(32 * 7 * 7, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        # flatten the output of conv2 to (batch_size, 32 * 7 * 7)
        x = x.view(x.size(0), -1)
        output = self.out(x)
        return output


cnn = CNN()
loss_func = nn.CrossEntropyLoss()
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
optimizer = optim.Adam(cnn.parameters(), lr=0.01)


if torch.cuda.device_count() > 1:
    print("Let's use", torch.cuda.device_count(), "GPUs!")
    # dim = 0 [30, xxx] -> [10, ...], [10, ...], [10, ...] on 3 GPUs
    cnn = nn.DataParallel(cnn)


cnn.to(device)
bidx = 0

for epoch in range(10):
    cnn.train()
    for i, (image, label) in enumerate(loaders["train"]):
        print(f"\rBatch {bidx} | Epoch {epoch}", end="")
        bidx += 1
        input = image.to(device)

        optimizer.zero_grad()

        output = cnn(input)
        loss = loss_func(output, label.to(device))
        loss.backward()

        optimizer.step()

    cnn.eval()
    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in loaders["test"]:
            data = images.to(device)
            test_output = cnn(images)
            pred_y = torch.max(test_output, 1)[1].data.squeeze().cpu()
            correct += float((pred_y == labels).sum().item())
            total += float(labels.size(0))
        print(f"\nTest Accuracy: {correct / total:.3f}")
    tracker.flush()

tracker.stop()
