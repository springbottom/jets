import torch.nn.functional as F
import torch
from torch.autograd import Variable
import numpy as np

from src.data_ops.wrapping import wrap
from src.admin.utils import see_tensors_in_memory

def loss(y_pred, y, y_mask, bm):
    l = nll
    return l(y_pred, y, y_mask, bm)

def kl(y_pred, y, y_mask):
    n = y_pred.shape[1]
    dists = wrap(torch.Tensor(distances(n)) ** (1/2.5)).view(-1, n, n)

    logprobs = stable_log(y_pred)

    lossfn = torch.nn.KLDivLoss(reduce=False)

    l = lossfn(logprobs, y)
    l = l * dists
    l = reweight_loss(l, y)
    l = l.masked_select(y_mask.byte())
    l = l.mean()
    return l

def nll(y_pred, y, y_mask, batch_mask):
    n = y_pred.shape[1]
    n_ = batch_mask.sum(1,keepdim=True)[:,:,0]

    #x = F.sigmoid(distances(n) - n / 2)
    dists = wrap(torch.Tensor(distances(n))).view(-1, n, n) * batch_mask
    x = torch.exp(-(n_.unsqueeze(1) - dists - 1)*0.01)
    #import ipdb; ipdb.set_trace()

    dists = (x)
    lossfn = torch.nn.NLLLoss(reduce=False)
    logprobs = stable_log(torch.stack([1-y_pred, y_pred], 1))

    l = (lossfn(logprobs, y.long()))
    l = l * dists
    l = reweight_loss(l, y)
    l = l.masked_select(y_mask.byte())
    l = l.mean()
    return l

def cho_loss(y_pred, y, y_mask):
    n = y_pred.shape[1]
    dists = wrap(torch.Tensor(distances(n)) ** (1./2.5))

    y_pred = y_pred.view(-1, n ** 2)
    y = y.view(-1, n ** 2)

    l = my_bce_loss(y_pred, y, reduce=False)

    l = reweight_loss(l, y)
    l = l * dists
    l = l.masked_select(y_mask.view(-1, n**2).byte())
    l = l.mean()
    return l

def vanilla_bce_loss(y_pred, y, y_mask):
    n = y_pred.shape[1]
    l = my_bce_loss(y_pred, y, reduce=False).view(-1, n**2)
    l = l.masked_select(y_mask.view(-1, n**2).byte())
    l = l.mean()
    return l


def distance_loss(y_pred, y, y_mask):
    return ((y_pred - y).pow(2) * y_mask).mean()

def reweight_loss(l, y):
    n_pos = y.sum(1, keepdim=True)
    n_neg = (1 - y).sum(1, keepdim=True)

    l_pos = y * l
    l_neg = (1 - y) * l

    l = (l_pos * n_neg + l_neg * n_pos) / (n_pos + n_neg)
    return l

def reweight(tensor, idx, weight):
    tensor[:,idx] =  tensor[:,idx] * weight
    return tensor

def distances(n):
    indices = np.arange(n ** 2)
    rows = indices // n
    columns = indices % n
    b_dists = abs(rows - columns)
    return b_dists

def stable_log(x):
    minvar = Variable(torch.Tensor([1e-20]))
    if torch.cuda.is_available():
        minvar = minvar.cuda()
    x = torch.log(torch.max(x, minvar))

    return x


def my_bce_loss(input, target, weight=None, reduce=True):
    input = stable_log(input)

    if not (target.size() == input.size()):
        raise ValueError("Target size ({}) must be the same as input size ({})".format(target.size(), input.size()))

    max_val = (-input).clamp(min=0)
    loss = input - input * target + max_val + ((-max_val).exp() + (-input - max_val).exp()).log()
    if weight is not None:
        loss = loss * weight
    if reduce:
        loss = loss.mean()
    return loss
