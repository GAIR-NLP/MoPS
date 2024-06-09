import json
import re
from pathlib import Path
from typing import List, Literal, Optional, Tuple

import tyro
from ndicts import NestedDict
from openai import OpenAI
from tqdm import tqdm

from mops.constants import client, logger, openai_model
from mops.prompts import SYNYHESIZE_PROMPT, VERIFY_PROMPT
from mops.utils import open_json, open_jsonl

Mask = Literal["theme", "background", "persona", "event", "ending", "twist"]
KeyPath = Tuple[str, str, str, str, str, str]


def get_response(
    client: OpenAI,
    content: str,
    model: str = openai_model,
    temperature: float = 0.6,
):
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": content}],
        temperature=temperature,
    )
    response = completion.choices[0].message.content
    assert isinstance(response, str)
    return response


def apply_mask(key_path: KeyPath, masks: Optional[List[Mask]] = None) -> KeyPath:
    if not masks:
        return key_path

    mask_indices = {
        "theme": 0,
        "background": 1,
        "persona": 2,
        "event": 3,
        "ending": 4,
        "twist": 5,
    }
    for mask in masks:
        if mask not in mask_indices:
            raise ValueError(f"Invalid mask type: {mask}")

    key_path_list = list(key_path)

    for mask in masks:
        index = mask_indices[mask]
        key_path_list[index] = ""

    return tuple(key_path_list)  # type: ignore[reportReturnType]


def synthesize(
    modular_path: Path,
    premise_path: Path,
    client: OpenAI,
    masks: Optional[List[Mask]] = None,
):
    modular_dict = open_json(modular_path)
    nd_modular_dict = NestedDict(modular_dict)

    premises = open_jsonl(premise_path)

    logger.info(f"Load modular from: {modular_path}")
    logger.info(f"Synthesize premises in: {premise_path}")
    logger.info(f"Masks: {masks}")

    ids = [premise["id"] for premise in premises]

    for key_path in tqdm(nd_modular_dict, desc="Synthesizing"):
        # if key_path id is already synthesized, just skip it.
        if (id := nd_modular_dict[key_path]) in ids:
            continue

        key_path = apply_mask(key_path, masks)
        theme, background, persona, event, ending, twist = key_path

        prompt = SYNYHESIZE_PROMPT.format(
            theme=theme,
            background=background,
            persona=persona,
            event=event,
            ending=ending,
            twist=twist,
        )

        premise = get_response(client, prompt, temperature=0.0)
        premise_dict = dict(
            id=id,
            premise=premise,
            theme=theme,
            background=background,
            persona=persona,
            event=event,
            ending=ending,
            twist=twist,
        )
        with open(premise_path, "a") as f:
            f.write(json.dumps(premise_dict) + "\n")


def verify(premise_path: Path, verified_premise_path: Path, client: OpenAI):
    premises = open_jsonl(premise_path)
    verified_premises = open_jsonl(verified_premise_path)

    logger.info(f"Load premises from: {premise_path}")
    logger.info(f"Verify premises in: {verified_premise_path}")

    ids = [verified_premise["id"] for verified_premise in verified_premises]

    def extract_ans(text: str):
        pattern = r"\[\[(Yes|No)\]\]"
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
        else:
            return "No"

    for premise_dict in tqdm(premises, desc="Verifying premises"):
        if premise_dict["id"] in ids:
            continue

        prompt = VERIFY_PROMPT.format(premise=premise_dict["premise"])
        response = get_response(client, prompt)
        ans = extract_ans(response)

        if ans == "Yes":
            logger.warning(
                f"Detect Error in id: {premise_dict['id']}, premise: {premise_dict['premise']}"
            )
            continue

        with open(verified_premise_path, "a") as f:
            f.write(json.dumps(premise_dict) + "\n")


def main(
    module_dir: Path,
    premise_dir: Path,
    enable_verify: bool = False,
    masks: Optional[List[Mask]] = None,
):
    synthesize(
        module_dir / "twist.json",
        premise_dir / "premise.jsonl",
        client,
        masks,
    )
    if enable_verify:
        verify(
            premise_dir / "premise.jsonl",
            premise_dir / "verified_premise.jsonl",
            client,
        )


if __name__ == "__main__":
    tyro.cli(main)
