import torch
import torch.nn as nn


class ConvBlock(nn.Module):

    def __init__(self, in_channels, out_channels, stride=1, padding=1, kernel_size=3):
        super().__init__()
        self.conv = nn.Sequential(nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size,
                                            stride=stride, padding=padding),
                                  nn.ReLU(inplace=True),
                                  nn.MaxPool2d(2))

    def forward(self, x):
        return self.conv(x)

class DenseBlock(nn.Module):

    def __init__(self, in_channels, out_channels, dropout_chance) -> None:
        super().__init__()
        self.layer = nn.Sequential(nn.Linear(in_channels, out_channels, bias=True),
                                   nn.ReLU(),
                                   nn.Dropout(dropout_chance))

    def forward(self, x):
        return self.layer(x)


class DCNN(nn.Module):

    def __init__(self, in_channels, out_classes):
        super().__init__()
        #self.conv1 = ConvBlock(in_channels, in_channels, kernel_size=3)
        #self.conv2 = ConvBlock(in_channels, in_channels, kernel_size=3)
        self.fc1 = DenseBlock(in_channels, 64, dropout_chance=0.25)
        self.fc2 = DenseBlock(64, 32, dropout_chance=0.0)
        self.last = nn.Linear(32, out_classes, bias=True)

    def forward(self, x):
        #out = self.conv1(x)
        #out = self.conv2(out)
        #out = out.view(out.size(0), -1)
        out = self.fc1(x)
        out = self.fc2(out)
        out = self.last(out)
        return out




if __name__ == "__main__":
    if __name__ == "__main__":
        model = DCNN(633, 4)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = nn.DataParallel(model, device_ids = [i for i in range(torch.cuda.device_count())])
        model.to(device)
        model.train()
        pytorch_total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(pytorch_total_params)
        x = torch.rand((1,1,633))
        out = model(x)