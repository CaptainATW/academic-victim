import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not found in environment variables.")  # Debugging: Check if API key is loaded
else:
    print(f"API Key loaded: {api_key[:5]}...")  # Debugging: Print the first few characters of the API key

client = AsyncOpenAI(api_key=api_key)

async def stream_gpt4_response(prompt, model="gpt-4o-mini"):
    try:
        stream = await client.chat.completions.create(
            model=model,  # Use the model passed from the popup
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"Error: {e}"