import logging
import numpy as np
from ..datasets import WeightedJetDataset
from ..datasets import JetDataset

def crop(jets, pileup=False):
    #logging.warning("Cropping...")
    if pileup:
        pt_min, pt_max, m_min, m_max = 300, 365, 150, 220
    else:
        pt_min, pt_max, m_min, m_max = 250, 300, 50, 110


    good_jets = []
    bad_jets = []
    #good_indices = []
    for i, j in enumerate(jets):
        if pt_min < j.pt < pt_max and m_min < j.mass < m_max:
            good_jets.append(j)
            #good_indices.append(i)
        else:
            bad_jets.append(j)

    # Weights for flatness in pt
    w = np.zeros(len(good_jets))

    jets_0 = [jet for jet in good_jets if jet.y == 0]
    pdf, edges = np.histogram([j.pt for j in jets_0], density=True, range=[pt_min, pt_max], bins=50)
    pts = [j.pt for j in jets_0]
    indices = np.searchsorted(edges, pts) - 1
    inv_w = 1. / pdf[indices]
    inv_w /= inv_w.sum()
    for i, (iw, jet) in enumerate(zip(inv_w, good_jets)):
        if jet.y == 0:
            w[i] = iw

    jets_1 = [jet for jet in good_jets if jet.y == 1]
    pdf, edges = np.histogram([j.pt for j in jets_1], density=True, range=[pt_min, pt_max], bins=50)
    pts = [j.pt for j in jets_1]
    indices = np.searchsorted(edges, pts) - 1
    inv_w = 1. / pdf[indices]
    inv_w /= inv_w.sum()
    for i, (iw, jet) in enumerate(zip(inv_w, good_jets)):
        if jet.y == 1:
            w[i] = iw


    return good_jets, bad_jets, w

def crop_dataset(dataset, pileup):
    good_jets, bad_jets, w = crop(dataset.jets, pileup)
    cropped_dataset = JetDataset(bad_jets)
    new_dataset = WeightedJetDataset(good_jets, w)
    return new_dataset, cropped_dataset