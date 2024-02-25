import pprint
import random

import tiktoken
import tqdm
from openai import OpenAI
from pandas._typing import FilePath

from ord.utils import json_load, json_dump

_API_KEY = "YOUR_API_KEY"
Client = OpenAI(api_key=_API_KEY)
MODEL_NAME = "gpt-3.5-turbo-0125"
MAX_TOKENS = 1000


def print_models():
    ml = Client.models.list()
    pprint.pp([*ml])


def sample_test_set(test_json: FilePath, k=100):
    test_set = json_load(test_json)
    random.seed(42)
    test_set = random.sample(test_set, k)
    return sorted(test_set, key=lambda x: x['reaction_id'])


def get_cot_prompt(procedure_text: str, cot_prefix_file: str = "cot_prefix.txt"):
    with open(cot_prefix_file, "r") as f:
        cot_prefix = f.read()

    prompt = f"""{cot_prefix}
Here is a new reacton_text.
new_reaction_text = ```{procedure_text}```
Please follow the above instructions and the workflow for dealing the two given examples. Extract and return the ORD JSON record."""
    return prompt


def calculate_tokens(prompt: str):
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(prompt))


def get_response(procedure_text: str):
    response = Client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "Act as a professional researcher in organic chemistry."
            },
            {
                "role": "user",
                "content": get_cot_prompt(procedure_text)
            }
        ],
        temperature=0,
        max_tokens=MAX_TOKENS,
        top_p=1
    )
    return response


def cot_experiment(test_json: FilePath, k: int):
    test_set_samples = sample_test_set(test_json, k)
    for data in tqdm.tqdm(test_set_samples):
        reaction_text = data['instruction']
        reaction_id = data['reaction_id']
        gpt_response = get_response(reaction_text)
        json_dump(f"cot_response/{reaction_id}.json", gpt_response.model_dump(), indent=2)


if __name__ == '__main__':
    cot_experiment(
        test_json="/home/qai/workplace/LLM_organic_synthesis/workplace_data/datasets/USPTO-t100k-n2048-COT.json",
        k=100
    )
