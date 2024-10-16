import base64
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI client
api_key = os.getenv("OPENAI_API_KEY")  # Get the API key from the environment

if api_key:
    api_key = api_key.strip()  # Strip any extra spaces or newlines
    print(f"API Key loaded: {api_key[:5]}...")  # Debugging: Print the first few characters of the API key
    client = AsyncOpenAI(api_key=api_key)
else:
    print("Error: OPENAI_API_KEY not found in environment variables.")  # Debugging: Check if API key is loaded
    client = None  # Set client to None if no API key is found

async def stream_gpt4_response(prompt=None, image_path=None, model="gpt-4o-mini"):
    if not client:
        yield "Error: No API key found. Please provide a valid OpenAI API key."
        return

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
                        "role": "system",
                        "content": [
                            {
                            "type": "text",
                            "text": "When provided with a quiz question, determine the answer. If the question appears straightforward or simple, respond quickly. If it seems complex or difficult, take additional time to think through the answer thoroughly.\n\n# Steps\n\n1. **Assess the Question**: Quickly read through the question to understand its complexity.\n2. **Determine Complexity**:\n   - If the question is **easy**, rely on basic knowledge or obvious solutions to answer promptly.\n   - If the question is **hard**, analyze the components, consider various possibilities, and apply logical reasoning.\n3. **Generate Answer**:\n   - Apply relevant knowledge or logic to formulate an answer based on your assessment.\n4. **Reflect**: Briefly review the reasoning and ensure the answer aligns with the complexity of the question.\n\n# Output Format\n\n- Provide a short, concise answer. If complex reasoning is involved, briefly summarize the thought process leading to the answer.\n\n# Examples\n\n**Example 1: Easy Question**\n- **Input**: What is 2 + 2?\n- **Output**: 4\n\n**Example 2: Hard Question**\n- **Input**: Analyze the impact of World War I on the global political landscape.\n- **Output**: The impact of World War I on the global political landscape includes the redrawing of national borders, the establishment of the League of Nations, and significant shifts in political power, particularly leading to the fall of empires like Austro-Hungarian and Ottoman, contributing to the rise of new ideologies and tensions leading to World War II.\n\n# Notes\n\n- Prioritize clarity and accuracy in your answers.\n- Consider the context of the quiz, as it might provide clues to answer complex questions effectively."
                            }
                    ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Here an image of the question. Read and understand the image."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                stream=True,
                temperature=0.1,
                max_tokens=16383,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={
                    "type": "text"
                }
            )
        else:
            # Handle text prompt
            stream = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": [
                        {
                            "type": "text",
                            "text": "When provided with a quiz question, determine the answer. If the question appears straightforward or simple, respond quickly. If it seems complex or difficult, take additional time to think through the answer thoroughly.\n\n# Steps\n\n1. Assess the Question: Quickly read through the question to understand its complexity.\n2. Determine Complexity:\n   - If the question is easy, rely on basic knowledge or obvious solutions to answer promptly.\n   - If the question is hard, analyze the components, consider various possibilities, and apply logical reasoning.\n3. Generate Answer:\n   - Apply relevant knowledge or logic to formulate an answer based on your assessment.\n4. Reflect: Briefly review the reasoning and ensure the answer aligns with the complexity of the question.\n\n# Output Format\n\n- Provide a short, concise answer. If complex reasoning is involved, briefly summarize the thought process leading to the answer.\n\n# Examples\n\nExample 1: Easy Question\n- Input: What is 2 + 2?\n- Output: 4\n\nExample 2: Hard Question\n- Input: Analyze the impact of World War I on the global political landscape.\n- Output: The impact of World War I on the global political landscape includes the redrawing of national borders, the establishment of the League of Nations, and significant shifts in political power, particularly leading to the fall of empires like Austro-Hungarian and Ottoman, contributing to the rise of new ideologies and tensions leading to World War II.\n\n# Notes\n\n- Prioritize clarity and accuracy in your answers.\n- Consider the context of the quiz, as it might provide clues to answer complex questions effectively."
                        }
                        ]
                    },
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                stream=True,
                temperature=0.1,
                max_tokens=16383,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={
                    "type": "text"
                }
            )

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"Error: {e}"
