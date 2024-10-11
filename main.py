import asyncio
import pyperclip
import tkinter as tk
from tkinter import scrolledtext
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PopupWindow:
    def __init__(self, master):
        self.master = master
        master.overrideredirect(True)  # Remove window decorations
        master.attributes("-alpha", 0.9)  # Set transparency
        master.attributes("-topmost", True)  # Always on top
        master.geometry("400x300+100+100")  # Set initial size and position

        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=40, height=10)
        self.text_area.pack(expand=True, fill='both')
        
        # Disable text selection
        self.text_area.bind("<Button-1>", lambda event: "break")
        
        # Hide scrollbar
        self.text_area.pack_forget()
        self.text_area.pack(expand=True, fill='both')
        self.text_area.vbar.pack_forget()

        # Make window draggable
        master.bind("<ButtonPress-1>", self.start_move)
        master.bind("<B1-Motion>", self.do_move)

        self.x = 0
        self.y = 0

    def update_text(self, text):
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        new_x = self.master.winfo_x() + deltax
        new_y = self.master.winfo_y() + deltay
        
        # Ensure the window stays within screen boundaries
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = self.master.winfo_width()
        window_height = self.master.winfo_height()
        
        new_x = max(0, min(new_x, screen_width - window_width))
        new_y = max(0, min(new_y, screen_height - window_height))
        
        self.master.geometry(f"+{new_x}+{new_y}")

async def stream_gpt4_response(prompt):
    try:
        stream = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"Error: {e}"

async def check_clipboard(popup):
    last_clipboard = pyperclip.paste()  # Initialize with current clipboard content
    while True:
        current_clipboard = pyperclip.paste()
        if current_clipboard != last_clipboard:
            last_clipboard = current_clipboard
            popup.update_text("Processing new clipboard content...\n")
            async for response_chunk in stream_gpt4_response(current_clipboard):
                popup.update_text(response_chunk)
                popup.master.update()
            popup.update_text("\n\n")
        await asyncio.sleep(1)  # Check every second

async def main():
    root = tk.Tk()
    popup = PopupWindow(root)

    clipboard_task = asyncio.create_task(check_clipboard(popup))

    try:
        while True:
            root.update()
            await asyncio.sleep(0.1)
    except tk.TclError:
        print("Window closed")
    finally:
        clipboard_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
