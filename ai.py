import base64
import os
import json
from openai import AsyncOpenAI
from PIL import Image
import platform
from io import BytesIO

formatted_text = ""
INCLUDE_CONTEXT = False
ENABLE_CHAT_HISTORY = False  # Changed from True to False
CHAT_HISTORY_FILE = "chat_history.json"
ENABLE_CLIPBOARD = True  # New global variable

def load_chat_history():
    """Load chat history from JSON file"""
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading chat history: {e}")
    
    # Return default history if file doesn't exist or has error
    return {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Your job is to answer difficult coding questions. Output all answers in python, unless said otherwise."
                    }
                ]
            }
        ]
    }

def save_chat_history(messages):
    """Save chat history to JSON file"""
    try:
        with open(CHAT_HISTORY_FILE, 'w') as f:
            json.dump({"messages": messages}, f, indent=2)
    except Exception as e:
        print(f"Error saving chat history: {e}")

def append_to_history(role, content):
    """Append a new message to chat history if enabled"""
    if not ENABLE_CHAT_HISTORY:
        return
        
    history = load_chat_history()
    history["messages"].append({
        "role": role,
        "content": [
            {
                "type": "text",
                "text": content
            }
        ]
    })
    save_chat_history(history["messages"])

def load_api_key():
    config_file = os.path.expanduser("~/.academic_victim") if platform.system() == "Darwin" else \
                 os.path.join(os.environ["USERPROFILE"], ".academic_victim") if platform.system() == "Windows" else \
                 ".academic_victim"
    
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            for line in f:
                if line.startswith("OPENAI_API_KEY="):
                    api_key = line.split("=")[1].strip()
                    return api_key if api_key.startswith("sk-") else None
    return None

def clear_formatted_text():
    global formatted_text
    formatted_text = ""

def process_image(image):
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def toggle_context():
    global INCLUDE_CONTEXT
    INCLUDE_CONTEXT = not INCLUDE_CONTEXT
    return INCLUDE_CONTEXT

def reset_chat_history():
    """Reset chat history and return number of messages deleted"""
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, 'r') as f:
                old_history = json.load(f)
                num_messages = len(old_history.get("messages", [])) - 1  # Subtract 1 to exclude system message
        else:
            num_messages = 0

        # Create new history with just the system message
        new_history = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Your job is to answer difficult coding questions. Output all answers in python, unless said otherwise."
                        }
                    ]
                }
            ]
        }
        
        # Save new history
        with open(CHAT_HISTORY_FILE, 'w') as f:
            json.dump(new_history, f, indent=2)
            
        return num_messages
    except Exception as e:
        print(f"Error resetting chat history: {e}")
        return 0

def toggle_chat_history():
    """Toggle whether messages are saved to chat history"""
    global ENABLE_CHAT_HISTORY
    ENABLE_CHAT_HISTORY = not ENABLE_CHAT_HISTORY
    return ENABLE_CHAT_HISTORY

api_key = load_api_key()
client = AsyncOpenAI(api_key=api_key.strip()) if api_key else None

async def image_ocr(image):
    global formatted_text
    if not client:
        return
        
    try:
        base64_string = process_image(image)
        stream = await client.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=[
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "Your job is to act as a image to text OCR. You are provided an image that displays instructions, code, etc. Output ONLY what is in the image, nothing else. You can format it, if it is code blocks you can use markdown."}]
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
            response_format={"type": "text"}
        )
        
        response_text = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response_text += chunk.choices[0].delta.content
                yield chunk.choices[0].delta.content
        
        formatted_text += response_text + "\n\n"
        
    except Exception as e:
        yield f"Error in OCR processing: {e}"

async def orion_response(prompt=None, image=None, model="o1-mini"):
    """Specialized method for Orion models following their specific guidelines"""
    if not client:
        yield "Error: No API key found. Please provide a valid OpenAI API key."
        return

    try:
        history = load_chat_history()
        messages = history["messages"]

        # Add context if enabled and exists
        if INCLUDE_CONTEXT and formatted_text:
            messages.append({
                "role": "user",
                "content": [{"type": "text", "text": f"Here is the full text of the problem:\n{formatted_text}"}]
            })

        if image:
            base64_string = process_image(image)
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this image and provide a clear, accurate answer."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_string}"}}
                ]
            })
        else:
            # If context is enabled, include it with the prompt
            if INCLUDE_CONTEXT and formatted_text:
                full_prompt = f"Here is the full text of the coding question:\n{formatted_text}\n\nUser question:\n{prompt}"
            else:
                full_prompt = prompt
                
            messages.append({
                "role": "user",
                "content": [{"type": "text", "text": full_prompt}]
            })

        # Non-streaming call for Orion models
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "text"}
        )

        response_content = response.choices[0].message.content
        
        # Save both the user's prompt and the assistant's response
        if prompt:
            append_to_history("user", full_prompt if INCLUDE_CONTEXT and formatted_text else prompt)
        append_to_history("assistant", response_content)
        
        yield response_content

    except Exception as e:
        yield f"Error: {e}"

async def stream_gpt4_response(prompt=None, image=None, model="gpt-4o-mini"):
    """Original method for non-Orion models"""
    if not client:
        yield "Error: No API key found. Please provide a valid OpenAI API key."
        return

    try:
        history = load_chat_history()
        messages = history["messages"]

        # Add context if enabled and exists
        if INCLUDE_CONTEXT and formatted_text:
            messages.append({
                "role": "user",
                "content": [{"type": "text", "text": f"Here is the entire coding problem: \n{formatted_text}"}]
            })

        if image:
            base64_string = process_image(image)
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": "Here an image of the question. Read and understand the image, then solve the question."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_string}"}}
                ]
            })
        else:
            # If context is enabled, include it with the prompt
            if INCLUDE_CONTEXT and formatted_text:
                full_prompt = f"Here is full text of the coding question:\n{formatted_text}\n\nUser question:\n{prompt}"
            else:
                full_prompt = prompt
                
            messages.append({
                "role": "user",
                "content": [{"type": "text", "text": full_prompt}]
            })

        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=0.1,
            max_tokens=16383,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={"type": "text"}
        )

        full_response = ""
        if prompt:
            append_to_history("user", full_prompt if INCLUDE_CONTEXT and formatted_text else prompt)

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                yield content

        # Save the complete response after streaming
        append_to_history("assistant", full_response)

    except Exception as e:
        yield f"Error: {e}"
