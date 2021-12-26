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


class DCNN(nn.Module):

    def __init__(self, in_channels, out_classes):
        super().__init__()
        self.conv1 = ConvBlock(in_channels, in_channels, kernel_size=3)
        self.conv2 = ConvBlock(in_channels, in_channels, kernel_size=3)
        self.fc = nn.Linear(64, out_classes, bias=True)

    def forward(self, x):
        out = self.conv1(x)
        out = self.conv2(out)
        out = out.view(out.size(0), -1)
        out = self.fc(out)
        return out




if __name__ == "__main__":
    if __name__ == "__main__":
        model = DCNN(1, 4)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = nn.DataParallel(model, device_ids = [i for i in range(torch.cuda.device_count())])
        model.to(device)
        model.train()
        pytorch_total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(pytorch_total_params)
        x = torch.rand((1,1,35,34))
        out = model(x)