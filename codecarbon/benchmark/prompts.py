"""
Prompt assembly for the LLM energy benchmark.

Builds prompts for a target input-length bucket from a fixed, versioned prompt
set (spec §4.1). Two properties matter:

* **Determinism** — the same request index always produces the same prompt, so
  a run can be reproduced exactly.
* **Prefix uniqueness** — every prompt differs from every other in its first
  tokens. Engines with automatic prefix caching (vLLM enables it by default in
  recent versions) would otherwise skip the input-processing work for repeated
  prefixes, and the benchmark would measure the cache rather than the model.

Lengths are approximate: without the model's own tokenizer the harness cannot
hit an exact token count, so it targets a word budget and records the
*measured* input token count reported by the engine, as §4.1 requires.
"""

import json
import os
from typing import List

# English prose runs roughly 1.3 tokens per word across common BPE tokenizers.
# Only used to aim at a bucket; the recorded value always comes from the engine.
_TOKENS_PER_WORD = 1.3

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "data", "benchmark"
)


def load_prompt_set(version: str = "v1") -> List[str]:
    """Load the versioned instruction prompts."""
    path = os.path.join(_DATA_DIR, f"prompts_{version}.jsonl")
    with open(path, encoding="utf-8") as fd:
        return [json.loads(line)["text"] for line in fd if line.strip()]


def load_context(version: str = "v1") -> List[str]:
    """Load the versioned filler passage, split into sentences."""
    path = os.path.join(_DATA_DIR, f"context_{version}.txt")
    with open(path, encoding="utf-8") as fd:
        return [line.strip() for line in fd if line.strip()]


def build_prompt(
    index: int,
    instructions: List[str],
    context: List[str],
    target_tokens: int,
) -> str:
    """
    Build the prompt for request ``index`` at the given input-length bucket.

    The leading marker guarantees a unique prefix per request; rotating the
    context by ``index`` keeps the body varied as well.
    """
    instruction = instructions[index % len(instructions)]
    marker = f"[request {index:06d}]"

    budget_words = int(target_tokens / _TOKENS_PER_WORD)
    used = len(marker.split()) + len(instruction.split())

    filler: List[str] = []
    position = index % max(len(context), 1)
    while used < budget_words and context:
        sentence = context[position % len(context)]
        filler.append(sentence)
        used += len(sentence.split())
        position += 1
        # Guard against a context shorter than the budget looping forever
        # without adding words.
        if not sentence:
            break

    if filler:
        return f"{marker} {' '.join(filler)}\n\n{instruction}"
    return f"{marker} {instruction}"


def build_prompts(
    n_requests: int,
    target_tokens: int,
    version: str = "v1",
    start_index: int = 0,
) -> List[str]:
    """Build ``n_requests`` prompts targeting an input-length bucket."""
    instructions = load_prompt_set(version)
    context = load_context(version)
    return [
        build_prompt(i, instructions, context, target_tokens)
        for i in range(start_index, start_index + n_requests)
    ]
