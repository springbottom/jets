import logging
import time
from src.data_ops.wrapping import unwrap

from .loss import loss


def _validation(model, data_loader):
    t_valid = time.time()
    model.eval()

    valid_loss = 0.
    yy, yy_pred = [], []
    mask = []
    for i, batch in enumerate(data_loader):
        (x, y, y_mask, batch_mask) = batch
        y_pred = model(x, mask=batch_mask)

        vl = loss(y_pred, y, y_mask)

        valid_loss = valid_loss + float(unwrap(vl))

        #y_pred = y_pred * y_mask
        yy.append(unwrap(y))
        yy_pred.append(unwrap(y_pred))
        mask.append(unwrap(batch_mask))

        del y; del y_pred; del y_mask; del x; del batch_mask; del batch

    valid_loss /= len(data_loader)

    logdict = dict(
        yy=yy,
        yy_pred=yy_pred,
        mask=mask,
        valid_loss=valid_loss,
        model=model,
    )
    model.train()

    t1=time.time()
    logging.info("Validation took {:.1f} seconds".format(time.time() - t_valid))
    return logdict
