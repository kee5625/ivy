import os

from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)
completion = client.chat.completions.create(
    model="qwen/qwen3-32b",
    messages=[
        {
            "role":"user",
            "content":"Explain wsosgoih"
        }
    ]
)

print(completion.choices[0].messages.content)