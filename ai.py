import base64
import os
from openai import AsyncOpenAI
from PIL import Image
import platform
from io import BytesIO
# Load API key from the hidden .academic_victim file
def load_api_key():
    if platform.system() == "Darwin":  # macOS
        config_file = os.path.expanduser("~/.academic_victim")
    elif platform.system() == "Windows":
        config_file = os.path.join(os.environ["USERPROFILE"], ".academic_victim")
    else:
        config_file = ".academic_victim"  # Fallback to current directory for other OS
    
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            for line in f:
                if line.startswith("OPENAI_API_KEY="):
                    api_key = line.split("=")[1].strip()
                    if api_key and api_key.startswith("sk-"):
                        return api_key
    return None

api_key = load_api_key()

if api_key:
    api_key = api_key.strip()  # Strip any extra spaces or newlines
    print(f"API Key loaded: {api_key[:5]}...")  # Debugging: Print the first few characters of the API key
    client = AsyncOpenAI(api_key=api_key)
else:
    print("Error: OPENAI_API_KEY not found in environment variables.")  # Debugging: Check if API key is loaded
    client = None  # Set client to None if no API key is found

# Add at the top with other global variables
formatted_text = ""

async def image_ocr(image):
    """OCR function that processes images and saves the text to a global variable."""
    global formatted_text
    
    if not client:
        return
        
    try:
        # Create a BytesIO buffer to hold the image data
        buffer = BytesIO()
        
        # Save the image to the buffer
        image.save(buffer, format="JPEG")
        
        # Get the byte data from the buffer
        image_bytes = buffer.getvalue()
        
        # Encode the byte data to base64
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        
        # Send the image to the AI with OCR-specific prompt
        stream = await client.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "Your job is to act as a image to text OCR. You are provided an image that displays instructions, code, etc. Output ONLY what is in the image, nothing else. You can format it, if it is code blocks you can use markdown."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Convert this image to text."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_string}"}}
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
        
        # Collect the response and append to formatted_text
        response_text = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response_text += chunk.choices[0].delta.content
        
        formatted_text += response_text + "\n\n"
        
    except Exception as e:
        print(f"Error in OCR processing: {e}")

async def stream_gpt4_response(prompt=None, image=None, model="gpt-4o-mini"):
    if not client:
        yield "Error: No API key found. Please provide a valid OpenAI API key."
        return

    try:
        if image:
            # Create a BytesIO buffer to hold the image data
            buffer = BytesIO()

            # Save the image to the buffer in a specific format (e.g., PNG)
            image.save(buffer, format="JPEG")

            # Get the byte data from the buffer
            image_bytes = buffer.getvalue()

            # Encode the byte data to base64
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            
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
                            {"type": "text", "text": "Here an image of the question. Read and understand the image, then solve the question."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_string}"}}
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
