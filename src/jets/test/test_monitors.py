from src.monitors import *
from src.admin.MonitorCollection import MonitorCollection

def train_monitor_collection(logging_frequency):
    roc_auc = ROCAUC(visualizing=True, ndp=5)
    inv_fpr = InvFPR(visualizing=True)
    best_inv_fpr = Best(inv_fpr)
    roc_auc_at_best_inv_fpr = LogOnImprovement(roc_auc, best_inv_fpr)

    metric_monitors = [
        inv_fpr,
        best_inv_fpr,
        roc_auc,
        roc_auc_at_best_inv_fpr,
        Regurgitate('valid_loss', ndp=3,visualizing=True),
        Regurgitate('train_loss', ndp=3,visualizing=True)

    ]
    time_monitors = [
        Regurgitate('epoch', visualizing=False, printing=False),
        Regurgitate('iteration', visualizing=False, printing=False),
        Hours(),
    ]
    optim_monitors = [
        Collect('lr', fn='last', ndp=8,visualizing=True),
    ]
    #grad_monitors = [
    #    GradNorm(visualizing=True),
    #    ParamNorm( visualizing=True),
    #    UpdateRatio( visualizing=True)
    #]

    monitors = metric_monitors + optim_monitors + time_monitors #+ grad_monitors
    #monitors += viz_monitors

    mc = MonitorCollection(*monitors)
    mc.track_monitor = best_inv_fpr
    return mc

def test_monitor_collection():
    roc_auc = ROCAUC(visualizing=True)
    inv_fpr = InvFPR(visualizing=True)
    best_inv_fpr = Best(inv_fpr)

    monitors = [
        inv_fpr,
        best_inv_fpr,
        roc_auc,
        Regurgitate('valid_loss', visualizing=True),
        Regurgitate('model', visualizing=False, numerical=False)
        ]
    mc = MonitorCollection(*monitors)

    return mc
