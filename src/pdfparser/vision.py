from __future__ import annotations

from typing import Any, Dict
import os

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

PROMPT = (
    "You are a document structure refinement assistant. Given a JSON with pages, blocks (headings/paragraphs), and images, improve heading levels, merge/split paragraphs if necessary, and add alt text for images. Return valid JSON in the same schema."
)


def refine_with_vision(doc: Dict[str, Any], model: str = "gpt-4o-mini", verbose: bool = False) -> Dict[str, Any]:
    if OpenAI is None:
        raise RuntimeError("openai package not installed. Install with `pip install pdfparser[vision]`. ")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=api_key)

    # For simplicity, we only send JSON text. Images already extracted paths could be summarized if needed.
    import json
    payload = json.dumps(doc)[:150000]  # guard size

    if verbose:
        print(f"Sending {len(payload)} bytes to vision model {model}")

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": payload},
        ],
        temperature=0.2,
    )
    txt = resp.choices[0].message.content or ""

    # Attempt to parse JSON from the response; if it fails, return original doc
    try:
        import json
        # Some models wrap JSON in code fences
        if "```" in txt:
            txt = txt.split("```", 2)[1]
            if txt.strip().startswith("json"):
                txt = "\n".join(txt.splitlines()[1:])
        refined = json.loads(txt)
        return refined
    except Exception:
        if verbose:
            print("Failed to parse vision output; returning original doc")
        return doc
