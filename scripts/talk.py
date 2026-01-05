# save as talk.py
from openai import OpenAI

client = OpenAI()

STYLE = "talk like dis: casual, typo-y, short, friendly. keep it readable."

while True:
    try:
        prompt = input("> ").strip()
        if not prompt:
            continue
        if prompt in {"exit", "quit"}:
            break

        stream = client.responses.create(
            model="gpt-5",
            instructions=STYLE,
            input=prompt,
            stream=True,
        )

        for event in stream:
            # most events are metadata; text deltas come as output chunks
            if getattr(event, "type", "") == "response.output_text.delta":
                print(event.delta, end="", flush=True)
        print()
    except (EOFError, KeyboardInterrupt):
        break