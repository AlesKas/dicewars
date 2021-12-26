import torch.nn as nn
import numpy as np
import torch
import time
import os
import sys
from NN_scripts.model import DCNN

class DCNNTrainer:

    def __init__(self, in_channels, out_classes,
                model_name, load=False, learning_rate=0.01,
                start_epoch=0, end_epoch=1000):
        
        self.name = model_name
        self.device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = DCNN(in_channels, out_classes)
        self.optimizer = torch.optim.Adam(self.model.parameters(), learning_rate)
        self.criterion = nn.CrossEntropyLoss().to(self.device)
        self.start_epoch = start_epoch
        self.end_epoch = end_epoch
        self.best_loss = 10000
        self.epochs_no_improvement = 0

        if load:
            checkpoint = torch.load(f"pretrained_weights/{model_name}.pt")
            state_dict = checkpoint['state_dict']
            unParalled_state_dict = {}
            for key in state_dict.keys():
                unParalled_state_dict[key.replace("module.", "")] = state_dict[key]
            self.model.load_state_dict(unParalled_state_dict, strict=False)
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        self.model = nn.DataParallel(self.model, 
                                     device_ids = [i for i in range(torch.cuda.device_count())])
        self.model.to(self.device)
        self.scheduler = torch.optim.lr_scheduler.StepLR(self.optimizer, 
                                                         step_size=int(1000* 0.8),
                                                         gamma=0.5)


    def fit(self, train_data, valid_data):
        for epoch in range(self.start_epoch, self.end_epoch):
            epoch_time = time.time()
            train_losses = self.train(train_data)
            valid_losses = self.valid(valid_data)
            self.valid_loss = np.mean(np.array(valid_losses))
            train_loss = np.mean(np.array(train_losses))
            self.check_for_improvement(train_loss, epoch, epoch_time)
            self.scheduler.step()

        
    def train(self, train_data):
        self.model.train()
        losses = []
        for idx, patch in enumerate(train_data):
            x, y = patch['x'].to(self.device), patch['y'].to(self.device)
            pred = self.model(x)
            loss = self.criterion(pred, y)
            self.optimizer.zero_grad()
            losses.append(loss.item())
            loss.backward()
            self.optimizer.step()
            if (idx + 1) % 5 == 0:
                print(f"Iteration: {idx}, losses: {np.mean(np.array(losses))}")
                sys.stdout.flush()

        return losses


    def valid(self, valid_data):
        
        losses = []
        with torch.no_grad():
            self.model.eval()
            for _, patch in enumerate(valid_data):
                x, y = patch['x'].to(self.device), patch['y'].to(self.device)
                pred = self.model(x)
                loss = self.criterion(pred, y)
                losses.append(loss.item())
  
        return losses


    def check_for_improvement(self, train_loss, epoch, epoch_time):
        text = """\nEpoch {}
        Training loss is {:.4f}, Validation loss is {:.4f},
        Time: {:.2f}s""".format(epoch+1,
                                train_loss,
                                self.valid_loss,
                                time.time()- epoch_time)

        if self.valid_loss < self.best_loss:
            text += "\nValidation loss decreases from {:.4f} to {:.4f}".format(self.best_loss,
                                                                               self.valid_loss)
            torch.save({'epoch': epoch+1,
		                'state_dict' : self.model.state_dict(),
		                'optimizer_state_dict': self.optimizer.state_dict(),
		                },os.path.join("pretrained_weights", f"{self.name}.pt"))
            self.best_loss = self.valid_loss
        else:
            self.epochs_no_improvement += 1
            text += """\nValidation loss does not decrease from {:.4f} epochs without improvement {}""".format(self.best_loss,
                                                                                                               self.epochs_no_improvement)
        print(text)
        sys.stdout.flush()
