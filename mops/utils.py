import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer
from sklearn.manifold import TSNE

from mops.constants import logger


def embedding(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> NDArray:
    model = SentenceTransformer(model_name)
    embedding = model.encode(texts)
    assert isinstance(embedding, np.ndarray)
    return embedding


def dim_reduction(
    embeddings: NDArray, perplexity: int = 50, random_state: int = 42
) -> NDArray:
    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=random_state)
    vis_dims = tsne.fit_transform(embeddings)
    assert vis_dims.shape == (embeddings.shape[0], 2)
    return vis_dims


def open_json(file: Path, mode: str = "r", create_if_not_exists: bool = False):
    if not file.exists() and create_if_not_exists:
        file.write_text(json.dumps({}))
        logger.warning(f"Create json file at: {file}")

    with open(file, mode) as fp:
        data = json.load(fp)
    return data


def open_jsonl(file: Path, mode: str = "r", create_if_not_exists: bool = True):
    if not file.exists() and create_if_not_exists:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()  # Creates an empty file
        logger.info(f"Create jsonl file at: {file}")

    with open(file, mode, encoding="utf-8") as fp:
        data = [json.loads(line) for line in fp.readlines()]
        return data


def save_json(json_dict: Dict, file: Path, mode: str = "w"):
    with open(file, mode, encoding="utf-8") as fp:
        json.dump(json_dict, fp, ensure_ascii=False, indent=4)


def save_jsonl(
    json_lines: List[Dict],
    file: Path,
    mode: str = "w",
    ensure_ascii=True,
):
    with open(file, mode, encoding="utf-8") as fp:
        for json_line in json_lines:
            fp.write(json.dumps(json_line, ensure_ascii=ensure_ascii) + "\n")


def save_fig(fig: Figure, fig_path: Path, **kwargs):
    if not fig_path.exists():
        fig_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Save figure to: {fig_path}")
    fig.savefig(fig_path, **kwargs)
