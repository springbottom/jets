import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from ._adjacency import _Adjacency


def compute_dij(p, alpha, R):
    p1 = p.unsqueeze(1) + 1e-10
    p2 = p.unsqueeze(2) + 1e-10

    delta_eta = p1[:,:,:,1] - p2[:,:,:,1]

    delta_phi = p1[:,:,:,2] - p2[:,:,:,2]
    delta_phi = torch.remainder(delta_phi + math.pi, 2*math.pi) - math.pi

    delta_r = (delta_phi**2 + delta_eta**2)**0.5

    dij = torch.min(p1[:,:,:,0]**(2.*alpha), p2[:,:,:,0]**(2.*alpha)) * delta_r / R

    return dij

class _PhysicsAdjacency(_Adjacency):
    '''
    Computes the physics-based adjacency matrix.
    '''
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

    @property
    def alpha(self):
        pass

    @property
    def R(self):
        pass

    def raw_matrix(self, p, mask=None, **kwargs):
        dij = compute_dij(p, self.alpha, self.R)
        return -dij


class FixedPhysicsAdjacency(_PhysicsAdjacency):
    '''
    Computes a fixed version of the dij
    '''
    def __init__(self, alpha=None, R=None,index='',**kwargs):
        name='phy'+index
        super().__init__(name=name, **kwargs)
        self.register_buffer('_alpha',torch.tensor(alpha).float())
        self.register_buffer('_R',torch.tensor(R).float())

    @property
    def alpha(self):
        return self._alpha

    @property
    def R(self):
        return self._R


class TrainablePhysicsAdjacency(_PhysicsAdjacency):
    def __init__(self, alpha_init=0, R_init=0,index='',**kwargs):
        name='tphy'+index
        super().__init__(name=name, **kwargs)
        base_alpha_init = 0
        base_R_init = 0

        self._base_alpha = nn.Parameter(torch.Tensor([base_alpha_init]))
        self._base_R = nn.Parameter(torch.Tensor([base_R_init]))


    @property
    def alpha(self):
        alpha = F.tanh(self._base_alpha)
        #import ipdb; ipdb.set_trace()
        #alpha_monitor(alpha=alpha.data[0])
        return alpha

    @property
    def R(self):
        R = torch.exp(self._base_R)
        #R_monitor(R=R.data[0])
        return R

class LearnedFunctionOfPhysics(_PhysicsAdjacency):
    '''
    Using the dij computed from physics, learns a monotone function of the dij.
    '''
    def __init__(self, alpha=None, R=None,index='',**kwargs):
        name='lphy'+index
        super().__init__(name=name, **kwargs)
        self.register_buffer('_alpha',torch.tensor(alpha).float())
        self.register_buffer('_R',torch.tensor(R).float())

        fc1 = nn.Linear(1, 100)
        self.weight1 = fc1.weight
        self.bias1 = fc1.bias

        fc2 = nn.Linear(100, 1)
        self.weight2 = fc2.weight
        self.bias2 = fc2.bias
        #self.relu = nn.ReLU()
        #self.fc2 = nn.Linear(100,1)

    @property
    def alpha(self):
        return self._alpha

    @property
    def R(self):
        return self._R

    def block(self, x):
        x = F.linear(x, self.weight1.pow(2), self.bias1)
        x = F.sigmoid(x)
        x = F.linear(x, self.weight2.pow(2), self.bias2)
        return x

    def raw_matrix(self, p, **kwargs):
        neg_dij = super().raw_matrix(p, **kwargs)
        return self.block(neg_dij.view(*neg_dij.shape, 1)).squeeze(-1)

PHYSICS_ADJACENCIES = dict(
    tphy=TrainablePhysicsAdjacency,
    phy=FixedPhysicsAdjacency,
    lphy=LearnedFunctionOfPhysics
)
