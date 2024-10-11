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
        master.geometry("500x220+100+100")  # Adjusted height to accommodate the smaller top bar

        # Top bar frame (hidden by default)
        self.top_bar = tk.Frame(master, height=30)
        self.top_bar.pack(fill=tk.X)
        self.top_bar.pack_forget()  # Hide the top bar initially

        # Button styling (black background, white text, no padding, and black when focused)
        button_style = {
            "width": 2,  # Square buttons for "Close" and "Copy"
            "height": 1,
            "relief": tk.FLAT,  # No border
            "bg": "gray",  # Black background
            "fg": "black",  # White text
            #"activebackground": "black",  # Keep background black when focused
            #"activeforeground": "black",  # Keep text white when focused
            "highlightthickness": 0,  # Remove highlight border (important for macOS)
        }

        # Close button (square)
        self.close_button = tk.Button(self.top_bar, text="X", command=self.close_window, **button_style)
        self.close_button.pack(side=tk.LEFT, padx=0, pady=0)  # No padding

        # Copy button (square)
        self.copy_button = tk.Button(self.top_bar, text="C", command=self.copy_last_response, **button_style)
        self.copy_button.pack(side=tk.LEFT, padx=0, pady=0)  # No padding

        # Track the start of the assistant's response
        self.response_start_index = None

        # Model button (adjust width based on text length)
        self.model_options = ["gpt-4o", "chatgpt-4o-latest", "gpt-4o-mini"]
        self.current_model_index = 2  # Default to gpt-4o-mini
        model_text = f"Model: {self.model_options[self.current_model_index]}"
        self.model_button = tk.Button(self.top_bar, text=model_text, command=self.cycle_model, **button_style)
        self.model_button.config(width=len(model_text))  # Set width based on text length
        self.model_button.pack(side=tk.LEFT, padx=0, pady=0)  # No padding

        # Text area for displaying responses
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

        # Periodically check mouse position to show/hide the top bar
        self.check_mouse_position()

        self.offset_x = 0
        self.offset_y = 0
        self.is_dragging = False
        self.last_response = ""  # Store the last response for copying
        self.ignore_clipboard = ""  # Flag to ignore clipboard changes after copying

    def update_text(self, text):
        if "Processing new clipboard content..." in text:
            # Mark the start of the assistant's response
            self.response_start_index = self.text_area.index(tk.END)
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)
        self.last_response += text  # Append to last response

    def close_window(self):
        # Unbind the event handlers before closing the window
        self.master.unbind("<B1-Motion>")
        self.master.unbind("<ButtonRelease-1>")
        self.master.destroy()  # Properly close the window
        os._exit(0)  # Forcefully exit the Python program

    def copy_last_response(self):
        if self.response_start_index:
            # Get the text from the start of the assistant's response to the end
            assistant_response = self.text_area.get(self.response_start_index, tk.END).strip()
            pyperclip.copy(assistant_response)  # Copy only the assistant's response to clipboard
            self.ignore_clipboard = assistant_response  # Set flag to ignore clipboard changes
            print("copied", assistant_response)
            print("ignore clipboard", self.ignore_clipboard)

    def cycle_model(self):
        self.current_model_index = (self.current_model_index + 1) % len(self.model_options)
        model_text = f"Model: {self.model_options[self.current_model_index]}"
        self.model_button.config(text=model_text)
        # Adjust the width of the model button based on the new text length
        self.model_button.config(width=len(model_text))

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

    def check_mouse_position(self):
        """Periodically check the mouse position to show/hide the top bar."""
        x, y = self.master.winfo_pointerx(), self.master.winfo_pointery()
        window_x, window_y = self.master.winfo_rootx(), self.master.winfo_rooty()
        window_width, window_height = self.master.winfo_width(), self.master.winfo_height()

        # Check if the mouse is inside the window
        if window_x <= x <= window_x + window_width and window_y <= y <= window_y + window_height:
            self.show_top_bar()
        else:
            self.hide_top_bar()

        # Check again after 100ms
        self.master.after(100, self.check_mouse_position)

    def show_top_bar(self):
        """Show the top bar and ensure buttons are packed."""
        self.top_bar.pack(fill=tk.X)

    def hide_top_bar(self):
        """Hide the top bar."""
        self.top_bar.pack_forget()

async def check_clipboard(popup):
    last_clipboard = pyperclip.paste()  # Initialize with current clipboard content
    while True:
        current_clipboard = pyperclip.paste()
        if current_clipboard != last_clipboard and current_clipboard != popup.ignore_clipboard:
            print("ignore clipboard here", popup.ignore_clipboard)
            last_clipboard = current_clipboard
            popup.update_text("Processing new clipboard content...\n")
            async for response_chunk in stream_gpt4_response(current_clipboard, popup.model_options[popup.current_model_index]):
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