import torch
import os
import numpy as np
import copy
import random

from torch.utils.data import Dataset


class Games(Dataset):

    def __init__(self, data_list):
        super().__init__()
        self.data, self.labels = self.__load(data_list)
    

    def __load(self, data_list):
        
        data = []
        labels = []

        for key, item in data_list.items():
            label = torch.zeros(4)
            label[item-1] = 1
            labels.append(label)
            game = torch.from_numpy(np.load(key)).permute((0,2,1))
            data.append(game)
        return torch.concat(data), torch.stack(labels)


    def __getitem__(self, index):

        data = copy.deepcopy(self.data[index])
        label = copy.deepcopy(self.labels[index])

        return {'x': data.float(),
                'y': label.long()}


    def __len__(self):
        return self.data.shape[0]


def get_datasets(dirname, training_split=0.75):

    data = {}

    for subdir in os.listdir(dirname):
        subdir_path = os.path.join(dirname, subdir)
        for item in os.listdir(subdir_path):
            item_path = os.path.join(subdir_path, item)
            data[item_path] = int(subdir)
    
    split_idx = int(len(data)*training_split)
    data = list(data.items())
    random.shuffle(data)
    training_data = dict(data[:split_idx])
    validation_data = dict(data[split_idx:])

    train = Games(training_data)
    valid = Games(validation_data)

    return train, valid