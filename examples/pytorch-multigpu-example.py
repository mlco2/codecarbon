import numpy as np
import torch
from torch import nn
from torch import optim
from torch.utils.data import DataLoader
from torch.utils.data.sampler import SubsetRandomSampler
from torchvision import datasets
from torchvision.transforms import ToTensor

from codecarbon import EmissionsTracker

tracker = EmissionsTracker(project_name="pytorch-mnist-multigpu")
tracker.start()
# https://medium.com/@nutanbhogendrasharma/pytorch-convolutional-neural-network-with-mnist-dataset-4e8a4265e118
# https://pytorch.org/tutorials/beginner/blitz/data_parallel_tutorial.html#create-model-and-dataparallel
# https://gist.github.com/MattKleinsmith/5226a94bad5dd12ed0b871aed98cb123

# Parameters and DataLoaders

batch_size = 30
valid_ratio = 0.15

train_data = datasets.MNIST(
    root=".",
    train=True,
    transform=ToTensor(),
    download=True,
)
test_data = datasets.MNIST(root=".", train=False, transform=ToTensor())

n_valid = int(len(train_data) * valid_ratio)
indices = np.random.permutation(len(train_data))
valid_idx = indices[:n_valid]
train_idx = indices[n_valid:]
train_sampler = SubsetRandomSampler(train_idx)
valid_sampler = SubsetRandomSampler(valid_idx)

loaders = {
    "train": DataLoader(
        train_data,
        batch_size=batch_size,
        sampler=train_sampler,
        num_workers=4,
        pin_memory=True,
    ),
    "val": DataLoader(
        train_data,
        batch_size=batch_size,
        sampler=valid_sampler,
        num_workers=4,
        pin_memory=True,
    ),
    "test": DataLoader(
        test_data, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True
    ),
}


class CNN(nn.Module):
    def __init__(self):
        super().__init__()
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
optimizer = optim.Adam(cnn.parameters(), lr=0.001)


if torch.cuda.device_count() > 1:
    print("Let's use", torch.cuda.device_count(), "GPUs!")
    # dim = 0 [30, xxx] -> [10, ...], [10, ...], [10, ...] on 3 GPUs
    cnn = nn.DataParallel(cnn)


cnn.to(device)
bidx = 0

for epoch in range(10):
    cnn.train()
    # train for 1 epoch
    for _, (image, label) in enumerate(loaders["train"]):
        print(f"\rBatch {bidx} | Epoch {epoch}", end="")
        bidx += 1
        input = image.to(device)

        optimizer.zero_grad()

        output = cnn(input)
        loss = loss_func(output, label.to(device))
        loss.backward()

        optimizer.step()

    cnn.eval()

    # Measure validation accuracy at each epoch
    with torch.no_grad():
        correct = 0
        total = 0
        for images, labels in loaders["val"]:
            data = images.to(device)
            test_output = cnn(images)
            pred_y = torch.max(test_output, 1)[1].data.squeeze().cpu()
            correct += float((pred_y == labels).sum().item())
            total += float(labels.size(0))
        print(f"\nValidation Accuracy: {correct / total:.3f}")

# Measure final test accuracy
with torch.no_grad():
    correct = 0
    total = 0
    for images, labels in loaders["test"]:
        data = images.to(device)
        test_output = cnn(images)
        pred_y = torch.max(test_output, 1)[1].data.squeeze().cpu()
        correct += float((pred_y == labels).sum().item())
        total += float(labels.size(0))
    print(f"\nFinal test Accuracy: {correct / total:.3f}")
    tracker.flush()

tracker.stop()
