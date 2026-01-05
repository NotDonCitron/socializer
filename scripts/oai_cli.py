import sys
import argparse
import os
from openai import OpenAI

# Initialize client. OpenAI() looks for OPENAI_API_KEY env var by default.
client = OpenAI()

STYLE = "talk like dis: casual, a lil typo-y, short sentences, friendly, use emojis sometimes. no big formal tone."

history = []

def get_response(prompt):
    messages = [{"role": "system", "content": STYLE}]
    for u, a in history:
        messages.append({"role": "user", "content": u})
        messages.append({"role": "assistant", "content": a})
    
    messages.append({"role": "user", "content": prompt})

    model = os.environ.get("OPENAI_MODEL", "gpt-4o")

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
        
        full_response = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                print(content, end="", flush=True)
        
        print()  # newline after streaming
        return full_response
    except Exception as e:
        print(f"\nError calling OpenAI: {e}")
        return f"Error: {e}"

def main():
    parser = argparse.ArgumentParser(description="OpenAI Chat CLI")
    parser.add_argument('--json', action='store_true', help="Output in JSON format")
    parser.add_argument('prompt', nargs='?', help="Single prompt for non-interactive mode")
    args = parser.parse_args()

    prompt = None
    if args.prompt:
        prompt = args.prompt
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
        if not prompt:
            return

    if prompt:
        # Non-interactive mode
        response = get_response(prompt)
        if args.json:
            import json
            print(json.dumps({"input": prompt, "output": response}))
        else:
            # Response is already printed by streaming in get_response
            pass
        return

    # Interactive mode
    print("OpenAI Chat CLI. Type 'exit' to quit, '/style <new_style>' to change style, '/history' to show history.")
    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                break
            if user_input.startswith("/style "):
                global STYLE
                STYLE = user_input[7:].strip()
                print(f"Style changed to: {STYLE}")
                continue
            if user_input == "/history":
                for i, (user_msg, ai_msg) in enumerate(history):
                    print(f"{i+1}. You: {user_msg}")
                    print(f"   AI: {ai_msg}")
                continue

            response = get_response(user_input)
            history.append((user_input, response))
        except (EOFError, KeyboardInterrupt):
            break

if __name__ == "__main__":
    main()
