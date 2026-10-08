"""Standard set self-attention and a capacity-matched pointwise ablation."""
import numpy as np
import torch
from torch import nn
from clock_regret_attention.core import summary


def features(record):
    h=record['h']; f=record['f']; q=record['q']; a=record['a']; b=record['b']
    ca,cb,ta,tb,eligible=summary(h,f,a,b,q)
    total=sum(q); count=len(h)
    context=[a/b,float(ca/cb),ta/(count*a),tb/(count*b),len(eligible)/count,
             np.log1p(float(cb-ca))/10]
    tokens=[[hi/a,hi/b,np.log1p(float(qi))/10,float(qi/total),int(fi),int(i in eligible)]
            for i,(hi,fi,qi) in enumerate(zip(h,f,q))]
    return np.asarray([row+context for row in tokens],dtype=np.float32)


class AttentionRanker(nn.Module):
    def __init__(self):
        super().__init__()
        self.project=nn.Linear(12,32)
        self.encoder=nn.TransformerEncoderLayer(d_model=32,nhead=2,dim_feedforward=64,
                                                dropout=0.0,batch_first=True,activation='relu')
        self.score=nn.Linear(32,1)

    def forward(self,x): return self.score(self.encoder(self.project(x))).squeeze(-1)


class MLPRanker(nn.Module):
    def __init__(self):
        super().__init__()
        self.net=nn.Sequential(nn.Linear(12,88),nn.ReLU(),nn.Linear(88,88),nn.ReLU(),nn.Linear(88,1))

    def forward(self,x): return self.net(x).squeeze(-1)
