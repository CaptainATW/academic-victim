import asyncio
import pyperclip
import tkinter as tk
from tkinter import scrolledtext
import os
from dotenv import load_dotenv
from ai import stream_gpt4_response  # Import from openai.py

# Load environment variables
load_dotenv()

class PopupWindow:
    def __init__(self, master):
        self.master = master
        master.overrideredirect(True)  # Remove window decorations
        master.attributes("-alpha", 0.9)  # Set transparency
        master.attributes("-topmost", True)  # Always on top
        master.geometry("500x200+100+100")  # Set initial size and position

        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=40, height=10)
        self.text_area.pack(expand=True, fill='both')
        
        # Disable text selection
        self.text_area.bind("<Button-1>", lambda event: "break")
        
        # Hide scrollbar
        self.text_area.pack_forget()
        self.text_area.pack(expand=True, fill='both')
        self.text_area.vbar.pack_forget()

        # Make window draggable
        master.bind("<B1-Motion>", self.do_move)
        master.bind("<ButtonRelease-1>", self.stop_move)

        self.offset_x = 0
        self.offset_y = 0
        self.is_dragging = False

    def update_text(self, text):
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)

    def do_move(self, event):
        if not self.is_dragging:
            self.offset_x = self.master.winfo_x() - event.x_root
            self.offset_y = self.master.winfo_y() - event.y_root
            self.is_dragging = True

        x = event.x_root + self.offset_x
        y = event.y_root + self.offset_y
        
        # Ensure the window stays within screen boundaries
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = max(0, min(x, screen_width - self.master.winfo_width()))
        y = max(0, min(y, screen_height - self.master.winfo_height()))
        
        self.master.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        self.is_dragging = False

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
            await asyncio.sleep(0.01)  # Reduced sleep time for smoother updates
    except tk.TclError:
        print("Window closed")
    finally:
        clipboard_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
