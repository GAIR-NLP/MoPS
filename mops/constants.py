import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from mops.logger import get_logger

load_dotenv(override=True)

data_dir = Path(__file__).parent.parent / "data"

figure_dir = Path(__file__).parent.parent / "figures"

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE"),
)

openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-1106")

logger = get_logger(Path(__file__).parent.parent / "log.log")

