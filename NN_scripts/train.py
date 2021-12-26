import argparse
from NN_scripts.model import DCNN

from torch.utils.data import DataLoader

from NN_scripts.dataset import get_datasets
from NN_scripts.trainer import DCNNTrainer


parser = argparse.ArgumentParser()
parser.add_argument('--model', '-m', type=str)
parser.add_argument('--load_weights', '-l', action='store_true')
args = parser.parse_args()


train, valid = get_datasets('../data')

train_loader = DataLoader(train, batch_size=8, num_workers=4, shuffle=True)
valid_loader = DataLoader(valid, batch_size=8, num_workers=4)

trainer = DCNNTrainer(start_epoch=0,
                      end_epoch=1000,
                      learning_rate=0.0002,
                      model_name=args.model,
                      load=args.load_weights,
                      in_channels=1,
                      out_classes=4)

trainer.fit(train_loader, valid_loader)