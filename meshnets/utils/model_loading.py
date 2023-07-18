"""Methods for loading models"""

import os
import tempfile
from typing import Union

import mlflow
# pylint: disable=unused-import
from torch import tensor  # used to eval tensors

from meshnets.modules.model import MeshGraphNet
from meshnets.modules.lightning_wrapper import MGNLightningWrapper
from meshnets.utils.datasets import FromDiskGeometricDataset


def load_model_mgn(tracking_uri: str, run_id: str, ckpt: Union[int, str],
                   dataset: FromDiskGeometricDataset) -> MGNLightningWrapper:
    """Load a model from an MLFlow run and a given checkpoints.
    
    The checkpoint can be specified as either an index or the name of the
    checkpoint."""

    client = mlflow.tracking.MlflowClient(tracking_uri=tracking_uri)
    run = client.get_run(run_id)

    params = run.data.params
    # pylint: disable=eval-used
    params = {k: eval(v) for k, v in params.items()}

    model = MeshGraphNet(node_features_size=dataset.num_node_features,
                         edge_features_size=dataset.num_edge_features,
                         output_size=dataset.num_label_features,
                         **params)

    with tempfile.TemporaryDirectory() as temp_dir:
        if isinstance(ckpt, int):
            artifacts = client.list_artifacts(run_id, 'checkpoints')
            ckpt_path = client.download_artifacts(run_id,
                                                  path=artifacts[ckpt].path,
                                                  dst_path=temp_dir)
        elif isinstance(ckpt, str):
            ckpt_path = client.download_artifacts(run_id,
                                                  path=os.path.join(
                                                      'checkpoints', ckpt),
                                                  dst_path=temp_dir)

        wrapper = MGNLightningWrapper.load_from_checkpoint(ckpt_path,
                                                           model=model,
                                                           data_stats=params)

    return wrapper
