from mlx_lm import load, generate

MODEL = "Edge0/Edge0-35B-A3B-preview"

print("Loading model...")
model, tokenizer = load(MODEL)

print("Model loaded!")
print("Type 'exit' to quit.\n")

messages = []

while True:
    try:
        user = input("You: ").strip()

        if user.lower() in ("exit", "quit"):
            break

        if not user:
            continue

        messages.append({
            "role": "user",
            "content": user
        })

        prompt = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False
        )

        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=512,
            verbose=True
        )

        print("\nAI:", response)
        print()

        messages.append({
            "role": "assistant",
            "content": response
        })

    except KeyboardInterrupt:
        print("\nExiting...")
        break

    except Exception as e:
        print(f"\nError: {e}\n")
