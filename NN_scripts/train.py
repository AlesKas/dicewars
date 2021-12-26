from NN_scripts.dataset import get_datasets



train, valid = get_datasets('../data')

print(train[2]['x'].size())