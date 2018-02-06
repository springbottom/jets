import torch
import torch.nn as nn
import torch.nn.functional as F

from .jet_transforms import construct_transform
from .readout import construct_readout
from .embedding import construct_embedding
from .reduction import construct_reduction
from data_ops.batching import batch_leaves, batch_trees

class JetClassifier(nn.Module):
    '''
    Top-level architecture for binary classification of jets.
    A classifier comprises multiple possible parts:
    - Particle embedding - converts n particles to n embedded states
    - Dimensionality reduction - converts n_1 states to n_2 states
    - Transform - converts a number of states to a single jet embedding
    - Predictor - classifies according to the jet embedding

    Inputs: jets, a list of N jet data dictionaries
    Outputs: N-length binary tensor
    '''
    def __init__(self, **kwargs):
        super().__init__()
        self.predictor = construct_readout(
                            'clf',
                            kwargs.get('hidden', None)
                        )
        self.transform = construct_transform(
                            kwargs.get('jet_transform', None),
                            **kwargs)

    def forward(self, jets):
        raise NotImplementedError


class TreeJetClassifier(JetClassifier):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def forward(self, jets):
        jets = batch_trees(jets)
        h, _ = self.transform(jets)
        outputs = self.predictor(h)
        return outputs

class LeafJetClassifier(JetClassifier):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def forward(self, jets):
        jets, mask = batch_leaves(jets)
        h, _ = self.transform(jets=jets, mask=mask)
        outputs = self.predictor(h)
        return outputs
