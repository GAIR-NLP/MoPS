import random
import re
import uuid
from pathlib import Path
from typing import List

import numpy as np
import tyro
from ndicts import NestedDict
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity as cos_sim
from tqdm import tqdm

from mops.constants import client, logger, openai_model
from mops.prompts import (
    BACKGROUND_PROMPT,
    ENDING_PROMPT,
    EVENT_PROMPT,
    PROTAGONIST_ANTAGONIST_PROMPT,
    PROTAGONIST_DEUTERAGONIST_PROMPT,
    PROTAGONIST_PROMPT,
    TWIST_PROMPT,
)
from mops.utils import embedding, open_json, save_json


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


def filter_serial_numbers(texts: List[str]):
    # filter serial number 1. 2. 3. ...
    pattern = r"\d+\."
    result = []
    for text in texts:
        replaced_text = re.sub(pattern, "", text)
        result.append(replaced_text.strip())
    return result


def pair_deduplicate(texts_a: List[str], texts_b: List[str], threshold: float = 0.85):
    """Remove duplicate texts from `texts_a` based on
    their embedding similarity to texts in `texts_b`."""

    if len(texts_b) == 0:
        return texts_a

    # Remove fixed formats from the string
    # for accurately calculating embedding similarity
    pure_texts_a = [
        text.lower()
        .replace("deuteragonist:", "")
        .replace("protagonist:", "")
        .replace("antagonist:", "")
        .replace("the ending of the narrative is to explore", "")
        for text in texts_a
    ]
    pure_texts_b = [
        text.lower()
        .replace("deuteragonist:", "")
        .replace("protagonist:", "")
        .replace("antagonist:", "")
        .replace("the ending of the narrative is to explore", "")
        for text in texts_b
    ]
    embedding_array_a = embedding(pure_texts_a)
    embedding_array_b = embedding(pure_texts_b)
    sim_matrix = cos_sim(embedding_array_a, embedding_array_b)
    to_keep_a = np.ones(len(texts_a), dtype=bool)
    for i in range(sim_matrix.shape[0]):
        if sim_matrix[i].max() > threshold:
            to_keep_a[i] = False
    keeped_texts_a = []
    for idx, is_keep in enumerate(to_keep_a):
        if is_keep:
            keeped_texts_a.append(texts_a[idx])
    return keeped_texts_a


def generate_background(client: OpenAI, theme: str) -> List[str]:
    backgrounds = []

    for component in ["time and place", "time", "place"]:
        prompt = BACKGROUND_PROMPT.format(theme=theme, component=component)
        response = get_response(client, prompt)
        backgrounds += response.split("\n")

    # remove empty str
    backgrounds = [res for res in backgrounds if res]
    backgrounds = filter_serial_numbers(backgrounds)
    # shuffle the list
    random.shuffle(backgrounds)
    return backgrounds


def collect_background(
    theme_path: Path,
    background_path: Path,
    client: OpenAI,
    max_backgrounds_per_theme: int,
):
    theme_dict = open_json(theme_path)
    background_dict = open_json(background_path, create_if_not_exists=True)
    logger.info(f"Load themes from: {theme_path}")
    logger.info(f"Collect backgrounds in: {background_path}")

    # nested version of modular dictionaries
    nd_theme_dict = NestedDict(theme_dict)
    nd_background_dict = NestedDict(background_dict)

    all_themes = list(nd_theme_dict.keys())
    for theme_key_path in tqdm(all_themes, "Collecting backgrounds for each theme"):
        theme_key_exists = theme_key_path in nd_background_dict.keys()
        if not theme_key_exists:
            nd_background_dict[theme_key_path] = {}
        num_background = len(nd_background_dict[theme_key_path])

        (theme,) = theme_key_path
        while num_background < max_backgrounds_per_theme:
            # generate 30 backgrounds at once(time: 10, place: 10, time & place: 10)
            background_list = generate_background(client, theme=theme)
            cur_background_list = list(nd_background_dict[theme_key_path].keys())
            background_list = pair_deduplicate(
                background_list,
                cur_background_list,
                threshold=0.85,
            )

            background_list = background_list[
                : max_backgrounds_per_theme - num_background
            ]
            for background in background_list:
                background_key_path = (theme, background)
                nd_background_dict[background_key_path] = str(uuid.uuid4())
            num_background += len(background_list)

        save_json(nd_background_dict.to_dict(), background_path)


def generate_persona(client: OpenAI, theme: str, background: str) -> List[str]:
    personas = []

    protagonist_prompt = PROTAGONIST_PROMPT.format(theme=theme, background=background)
    protagonist_response = get_response(client, protagonist_prompt)
    personas += protagonist_response.split("\n")

    protagonist_antagonist_prompt = PROTAGONIST_ANTAGONIST_PROMPT.format(
        theme=theme, background=background
    )
    protagonist_antagonist_response = get_response(
        client, protagonist_antagonist_prompt
    )
    personas += protagonist_antagonist_response.split("\n")

    protagonist_deuteragonist_prompt = PROTAGONIST_DEUTERAGONIST_PROMPT.format(
        theme=theme, background=background
    )
    protagonist_deuteragonist_response = get_response(
        client, protagonist_deuteragonist_prompt
    )
    personas += protagonist_deuteragonist_response.split("\n")

    # remove empty str
    personas = [res for res in personas if res]
    personas = filter_serial_numbers(personas)
    # shuffle the list
    random.shuffle(personas)

    return personas


def collect_persona(
    background_path: Path,
    persona_path: Path,
    client: OpenAI,
    max_personas_per_background: int,
):
    background_dict = open_json(background_path)
    persona_dict = open_json(persona_path, create_if_not_exists=True)
    logger.info(f"Load backgrounds from: {background_path}")
    logger.info(f"Collect personas in: {persona_path}")

    # nested version of modular dictionaries
    nd_background_dict = NestedDict(background_dict)
    nd_persona_dict = NestedDict(persona_dict)

    all_backgrounds = list(nd_background_dict.keys())
    for background_key_path in tqdm(
        all_backgrounds, "Collecting personas for each background"
    ):
        background_key_exists = background_key_path in nd_persona_dict.keys()
        if not background_key_exists:
            nd_persona_dict[background_key_path] = {}
        num_persona = len(nd_persona_dict[background_key_path])

        (theme, background) = background_key_path
        while num_persona < max_personas_per_background:
            # generate 9 personas at once
            # (Protagonist: 3, Protagonist + Antagonist: 3, Protagonist + Deuteragonist: 3)
            persona_list = generate_persona(client, theme=theme, background=background)

            cur_persona_list = list(nd_persona_dict[background_key_path].keys())
            persona_list = pair_deduplicate(
                persona_list,
                cur_persona_list,
                threshold=0.85,
            )

            persona_list = persona_list[: max_personas_per_background - num_persona]
            for persona in persona_list:
                persona_key_path = (theme, background, persona)
                nd_persona_dict[persona_key_path] = str(uuid.uuid4())
            num_persona += len(persona_list)

        save_json(nd_persona_dict.to_dict(), persona_path)


def generate_event(
    client: OpenAI, theme: str, background: str, persona: str
) -> List[str]:
    events = []

    prompt = EVENT_PROMPT.format(
        theme=theme,
        background=background,
        persona=persona,
    )
    response = get_response(client, prompt)
    events += response.split("\n")

    # remove empty str
    events = [res for res in events if res]
    events = filter_serial_numbers(events)
    # shuffle the list
    random.shuffle(events)
    return events


def collect_event(
    persona_path: Path,
    event_path: Path,
    client: OpenAI,
    max_events_per_persona: int,
):
    persona_dict = open_json(persona_path)
    event_dict = open_json(event_path, create_if_not_exists=True)
    logger.info(f"Load personas from: {persona_path}")
    logger.info(f"Collect events in: {event_path}")

    # nested version of modular dictionaries
    nd_persona_dict = NestedDict(persona_dict)
    nd_event_dict = NestedDict(event_dict)

    all_personas = list(nd_persona_dict.keys())
    for persona_key_path in tqdm(all_personas, "Collecting events for each persona"):
        persona_key_exists = persona_key_path in nd_event_dict.keys()
        if not persona_key_exists:
            nd_event_dict[persona_key_path] = {}
        num_persona = len(nd_event_dict[persona_key_path])

        (theme, background, persona) = persona_key_path
        while num_persona < max_events_per_persona:
            # generate 2 events at once
            event_list = generate_event(
                client, theme=theme, background=persona, persona=persona
            )
            cur_event_list = list(nd_event_dict[persona_key_path].keys())
            event_list = pair_deduplicate(
                event_list,
                cur_event_list,
                threshold=0.85,
            )

            event_list = event_list[: max_events_per_persona - num_persona]
            for event in event_list:
                event_key_path = (theme, background, persona, event)
                nd_event_dict[event_key_path] = str(uuid.uuid4())
            num_persona += len(event_list)

        save_json(nd_event_dict.to_dict(), event_path)


def generate_ending(
    client: OpenAI, theme: str, background: str, persona: str, event: str
) -> List[str]:
    endings = []

    prompt = ENDING_PROMPT.format(
        theme=theme,
        background=background,
        persona=persona,
        event=event,
    )
    response = get_response(client, prompt)
    endings += response.split("\n")

    # remove empty str
    endings = [res for res in endings if res]
    endings = filter_serial_numbers(endings)
    # shuffle the list
    random.shuffle(endings)
    return endings


def collect_ending(
    event_path: Path, ending_path: Path, client: OpenAI, max_endings_per_event: int
):
    event_dict = open_json(event_path)
    ending_dict = open_json(ending_path, create_if_not_exists=True)
    logger.info(f"Load events from: {event_path}")
    logger.info(f"Collect endings in: {ending_path}")

    # nested version of modular dictionaries
    nd_event_dict = NestedDict(event_dict)
    nd_ending_dict = NestedDict(ending_dict)

    all_events = list(nd_event_dict.keys())
    for event_key_path in tqdm(all_events, "Collecting endings for each event"):
        event_key_exists = event_key_path in nd_ending_dict.keys()
        if not event_key_exists:
            nd_ending_dict[event_key_path] = {}
        num_ending = len(nd_ending_dict[event_key_path])

        (theme, background, persona, event) = event_key_path
        while num_ending < max_endings_per_event:
            # generate 1 ending at once
            ending_list = generate_ending(
                client, theme=theme, background=background, persona=persona, event=event
            )
            cur_ending_list = list(nd_ending_dict[event_key_path].keys())
            ending_list = pair_deduplicate(
                ending_list,
                cur_ending_list,
                threshold=0.85,
            )

            ending_list = ending_list[: max_endings_per_event - num_ending]
            for ending in ending_list:
                ending_key_path = (theme, background, persona, event, ending)
                nd_ending_dict[ending_key_path] = str(uuid.uuid4())
            num_ending += len(ending_list)

        save_json(nd_ending_dict.to_dict(), ending_path)


def generate_twist(
    client: OpenAI,
    theme: str,
    background: str,
    persona: str,
    event: str,
    ending: str,
):
    twists = []
    prompt = TWIST_PROMPT.format(
        theme=theme,
        background=background,
        persona=persona,
        event=event,
        ending=ending,
    )

    response = get_response(client, prompt)
    twists += response.split("\n")

    twists = [twist for twist in twists if twist]
    twists = filter_serial_numbers(twists)
    random.shuffle(twists)
    return twists


def collect_twist(
    ending_path: Path,
    twist_path: Path,
    client: OpenAI,
    max_twists_per_ending: int,
):
    ending_dict = open_json(ending_path)
    twist_dict = open_json(twist_path, create_if_not_exists=True)
    logger.info(f"Load endings from: {ending_path}")
    logger.info(f"Collect twists in: {twist_path}")

    # nested version of modular dictionaries
    nd_ending_dict = NestedDict(ending_dict)
    nd_twist_dict = NestedDict(twist_dict)

    all_endings = list(nd_ending_dict.keys())
    for ending_key_path in tqdm(all_endings, "Collecting twists for each ending"):
        ending_key_exists = ending_key_path in nd_twist_dict.keys()
        if not ending_key_exists:
            nd_twist_dict[ending_key_path] = {}
        num_twist = len(nd_twist_dict[ending_key_path])

        (theme, background, persona, event, ending) = ending_key_path
        while num_twist < max_twists_per_ending:
            # generate 30 twists at once(time: 10, place: 10, time & place: 10)
            twist_list = generate_twist(
                client,
                theme=theme,
                background=background,
                persona=persona,
                event=event,
                ending=ending,
            )
            cur_twist_list = list(nd_twist_dict[ending_key_path].keys())
            twist_list = pair_deduplicate(
                twist_list,
                cur_twist_list,
                threshold=0.85,
            )

            twist_list = twist_list[: max_twists_per_ending - num_twist]
            for twist in twist_list:
                twist_key_path = (theme, background, persona, event, ending, twist)
                nd_twist_dict[twist_key_path] = str(uuid.uuid4())
            num_twist += len(twist_list)

        save_json(nd_twist_dict.to_dict(), twist_path)


def main(
    module_dir: Path,
    step: str,
    max_backgrounds_per_theme: int = 30,
    max_personas_per_background: int = 9,
    max_events_per_persona: int = 2,
    max_endings_per_event: int = 1,
    max_twists_per_ending: int = 1,
):
    match step:
        case "background":
            collect_background(
                module_dir / "theme.json",
                module_dir / "background.json",
                client,
                max_backgrounds_per_theme,
            )
        case "persona":
            collect_persona(
                module_dir / "background.json",
                module_dir / "persona.json",
                client,
                max_personas_per_background,
            )
        case "event":
            collect_event(
                module_dir / "persona.json",
                module_dir / "event.json",
                client,
                max_events_per_persona,
            )
        case "ending":
            collect_ending(
                module_dir / "event.json",
                module_dir / "ending.json",
                client,
                max_endings_per_event,
            )
        case "twist":
            collect_twist(
                module_dir / "ending.json",
                module_dir / "twist.json",
                client,
                max_twists_per_ending,
            )


if __name__ == "__main__":
    tyro.cli(main)
