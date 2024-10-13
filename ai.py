import base64
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI client
api_key = os.getenv("OPENAI_API_KEY").strip()  # Strip any extra spaces or newlines
if not api_key:
    print("Error: OPENAI_API_KEY not found in environment variables.")  # Debugging: Check if API key is loaded
else:
    print(f"API Key loaded: {api_key}...")  # Debugging: Print the first few characters of the API key

client = AsyncOpenAI(api_key=api_key)

async def stream_gpt4_response(prompt=None, image_path=None, model="gpt-4o-mini"):  # Changed model to gpt-4o-mini
    try:
        if image_path:
            # Encode the image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Send the image to the AI
            stream = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What’s in this image?"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                stream=True
            )
        else:
            # Handle text prompt
            stream = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"Error: {e}"
