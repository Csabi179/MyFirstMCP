from dotenv import load_dotenv
from groq import Groq


load_dotenv()

client = Groq()

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "system",
            "content": "You are a concise and helpful assistant.",
        },
        {
            "role": "user",
            "content": "Reply with exactly: Groq connection works",
        },
    ],
)

print(response.choices[0].message.content)