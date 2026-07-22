"""Extracts plain text from a LangChain message's `.content` field.

`.content` is typed as `str | list[str | dict]` in LangChain core, and in
practice its shape depends on the provider: OpenAI's integration always
returns a plain string, but Gemini's returns a list of content blocks
(`{"type": "text", "text": "..."}`, plus provider-internal blocks like a
"thought signature" with empty text) — including in `AIMessageChunk`s while
streaming. This normalizes either shape to the plain string every caller in
this codebase actually wants, so a future provider swap doesn't ripple
through every place `.content` is read.
"""


def extract_text(content: str | list) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)
