import pandas as pd
import torch
import torch.nn as nn
import torch.nn.init as init
from torch.utils.data import Dataset

class MyNetwork(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(MyNetwork, self).__init__()

        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, output_dim)
        init.xavier_uniform_(self.fc1.weight)
        init.xavier_uniform_(self.fc2.weight)

    def forward(self, x):
        x = torch.tanh(self.fc1(x))
        x = torch.sigmoid(self.fc2(x))

        return x
    
class MyDataset(Dataset):
    def __init__(self, csv_filename):
        self.data = pd.read_csv(csv_filename)
        self.data_columns = self.data.columns[:-1].tolist()
        self.label_columns = self.data.columns[-1:].tolist()

    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        sample = self.data.iloc[idx]
        features = sample[self.data_columns].values
        labels = sample[self.label_columns].values
        return torch.Tensor(features), torch.Tensor(labels)