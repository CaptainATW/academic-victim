import asyncio
import pyperclip
import tkinter as tk
from tkinter import scrolledtext
import os
from ai import stream_gpt4_response  # Import from ai.py
from PIL import ImageGrab  # For taking screenshots
from pynput import mouse, keyboard  # For capturing mouse and keyboard events
import platform
from PIL import Image, ImageTk

class PopupWindow:
    def __init__(self, master, loop):
        self.master = master
        self.loop = loop  # Store the main event loop

        # Set the window title
        master.title("academic victim")

        # Set the background of the master canvas to #1e1f22 (dark black)
        master.config(bg="#1e1f22")

        # Set the window icon based on the platform
        if platform.system() == "Darwin":  # macOS
            icon_path = "icon.png"
            if os.path.exists(icon_path):
                icon_image = Image.open(icon_path)
                icon_photo = ImageTk.PhotoImage(icon_image)
                master.iconphoto(True, icon_photo)
        elif platform.system() == "Windows":  # Windows
            icon_path = "icon.ico"
            if os.path.exists(icon_path):
                master.iconbitmap(icon_path)

        master.overrideredirect(True)  # Remove window decorations
        master.attributes("-alpha", 0.9)  # Set transparency
        master.attributes("-topmost", True)  # Always on top
        master.geometry("500x220+100+100")  # Adjusted height to accommodate the smaller top bar

        # Create text_area first with Arial font, white text, and read-only state
        # Remove the border and highlight by setting bd=0 and highlightthickness=0
        self.text_area = scrolledtext.ScrolledText(
            master, 
            wrap=tk.WORD, 
            width=40, 
            height=10, 
            font=("Arial", 12), 
            fg="white", 
            bg="#1e1f22", 
            bd=0,  # No border
            highlightthickness=0  # No highlight border
        )
        self.text_area.pack(expand=True, fill='both')

        # Make the text box read-only initially
        self.text_area.config(state=tk.DISABLED)

        # Function to check if the API key exists
        def check_api_key_exists():
            if platform.system() == "Darwin":  # macOS
                config_file = os.path.expanduser("~/.academic_victim")
            elif platform.system() == "Windows":
                config_file = os.path.join(os.environ["USERPROFILE"], ".academic_victim")
            else:
                config_file = ".academic_victim"  # Fallback to current directory for other OS
            
            return os.path.exists(config_file)

        # Check if the API key file exists
        self.api_key_set = check_api_key_exists()

        # If API key is not set, display a message
        if not self.api_key_set:
            self.display_api_key_message()
        else:
            # Display default message when API key is loaded
            self.display_default_message()

        # Top bar frame (hidden by default) with #343740 (gray) background
        self.top_bar = tk.Frame(master, height=30, bg="#343740")
        self.top_bar.pack(fill=tk.X)
        self.top_bar.pack_forget()  # Hide the top bar initially

        # Button styling (#343740 background, white text, no padding, and gray when focused)
        button_style = {
            "height": 1,
            "relief": tk.FLAT,  # No border
            "bg": "#4752c4",  # Gray background
            "fg": "white",  # White text
            "highlightcolor": "#4752c4",
            "highlightthickness": 0,  # Remove highlight border (important for macOS)
            "font": ("Arial", 11, "bold")
        }

        # Add the "academic victim" label with white text and #343740 background
        self.label = tk.Label(self.top_bar, text="academic victim", fg="white", bg="#343740", font=("Arial", 11, "bold"))
        if platform.system() == "Darwin":
            self.label.pack(side=tk.LEFT, padx=5, pady=(0, 5))  # Added vertical padding for centering
        else:
            self.label.pack(side=tk.LEFT, padx=(7,7), pady=(5, 5))  # Added vertical padding for centering

        # Close button (square) with white text and #343740 background
        self.close_button = tk.Button(self.top_bar, text="X", command=self.close_window, **button_style)
        if platform.system() == "Darwin":
            self.close_button.pack(side=tk.RIGHT, padx=(0,5), pady=(0, 5))  # Added vertical padding for centering
        else:
            self.close_button.pack(side=tk.RIGHT, padx=(3), pady=(5, 5)) 

        # Copy button (square) with white text and #343740 background
        self.copy_button = tk.Button(self.top_bar, text="C", command=self.copy_last_response, **button_style)
        if platform.system() == "Darwin":
            self.copy_button.pack(side=tk.RIGHT, padx=(0,5), pady=(0, 5))  # Added vertical padding for centering
        else:
            self.copy_button.pack(side=tk.RIGHT, padx=(3), pady=(5, 5)) 

        # Model button (adjust width based on text length) with white text and #343740 background
        self.model_options = ["gpt-4o", "chatgpt-4o-latest", "gpt-4o-mini"]
        self.current_model_index = 2  # Default to gpt-4o-mini
        model_text = f"Model: {self.model_options[self.current_model_index]}"
        self.model_button = tk.Button(self.top_bar, text=model_text, command=self.cycle_model, **button_style)
        self.model_button.config(width=len(model_text))  # Set width based on text length
        if platform.system() == "Darwin":
            self.model_button.pack(side=tk.RIGHT, padx=(0,5), pady=(0, 5))  # No padding
        else:
            self.model_button.pack(side=tk.RIGHT, padx=(3), pady=(5, 5)) 

        # Track the start of the assistant's response
        self.response_start_index = None

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

        # Initialize positions for screenshots
        self.pos1 = None
        self.pos2 = None

        # Set up keyboard listener for screenshot commands
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.keyboard_listener.start()

        # Detect if running on macOS or Windows
        self.is_macos = platform.system() == "Darwin"
        self.is_windows = platform.system() == "Windows"
        self.ctrl_pressed = False  # Track if Control key is pressed
        self.shift_pressed = False  # Track if Shift key is pressed

    def update_text(self, text):
        """Update the text area with new text."""
        # Temporarily enable the text area to insert text
        self.text_area.config(state=tk.NORMAL)

        if "Processing new clipboard content..." in text:
            # Mark the start of the assistant's response
            self.response_start_index = self.text_area.index(tk.END)
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)
        self.last_response += text  # Append to last response

        # Disable the text area again to make it read-only
        self.text_area.config(state=tk.DISABLED)

    def close_window(self):
        self.master.destroy()  # Close the window
        os._exit(0)  # Exit the program

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

    def on_key_press(self, key):
        """Handle keyboard shortcuts for marking positions and taking screenshots."""
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            if key == keyboard.Key.alt_l:
                self.shift_pressed = True
            if self.ctrl_pressed and self.shift_pressed:
                if self.is_windows:
                    # Use key codes for Windows
                    if str(key) == '<49>':
                        self.pos1 = self.get_mouse_position()
                        print(f"POS1 set at {self.pos1}")
                    elif str(key) == '<50>':
                        self.pos2 = self.get_mouse_position()
                        print(f"POS2 set at {self.pos2}")
                    elif str(key) == '<51>':
                        if self.pos1 and self.pos2:
                            print(f"Taking screenshot between {self.pos1} and {self.pos2}")
                            self.take_screenshot()
                        else:
                            print("Error: POS1 and POS2 must be set before taking a screenshot.")
                else:
                    # Use key.char for macOS
                    if key.char == '1':
                        self.pos1 = self.get_mouse_position()
                        print(f"POS1 set at {self.pos1}")
                    elif key.char == '2':
                        self.pos2 = self.get_mouse_position()
                        print(f"POS2 set at {self.pos2}")
                    elif key.char == '3':
                        if self.pos1 and self.pos2:
                            print(f"Taking screenshot between {self.pos1} and {self.pos2}")
                            self.take_screenshot()
                        else:
                            print("Error: POS1 and POS2 must be set before taking a screenshot.")
        except AttributeError:
            pass

    def on_key_release(self, key):
        """Handle key release events."""
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False
        if key == keyboard.Key.shift:
            self.shift_pressed = False
    def get_mouse_position(self):
        """Get the current mouse position."""
        with mouse.Controller() as controller:
            position = controller.position
            return position

    def take_screenshot(self):
        """Take a screenshot between POS1 and POS2 and send it to the AI."""
        # Convert floating-point coordinates to integers
        x1, y1 = map(int, self.pos1)
        x2, y2 = map(int, self.pos2)
        
        # Define the bounding box for the screenshot
        bbox = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        
        # Take the screenshot
        screenshot = ImageGrab.grab(bbox)
        
        # Convert the image to RGB mode (JPEG does not support RGBA)
        screenshot = screenshot.convert("RGB")
        
        # Create the images/ directory if it doesn't exist

        #if not os.path.exists("images"):
        #    os.makedirs("images")
        
        # Generate the filename with the current timestamp
        #timestamp = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
        #screenshot_path = f"images/screenshot_{timestamp}.jpg"
        
        # Save the screenshot as a JPEG
        #screenshot.save(screenshot_path)

        # Use the stored event loop to schedule the coroutine
        asyncio.run_coroutine_threadsafe(self.send_screenshot_to_ai(screenshot), self.loop)

    async def send_screenshot_to_ai(self, screenshot):
        """Send the screenshot to the AI and display the response."""
        self.update_text("Processing screenshot...\n")
        async for response_chunk in stream_gpt4_response(prompt=None, image=screenshot, model=self.model_options[self.current_model_index]):
            self.update_text(response_chunk)
            self.master.update()
        self.update_text("\n\n")

    def display_api_key_message(self):
        """Display a message prompting the user to provide an OpenAI API key."""
        self.text_area.insert(tk.END, "Thanks for installing academic victim.\n")
        self.text_area.insert(tk.END, "You need an OpenAI API key to use this.\n")
        self.text_area.insert(tk.END, "Please copy your API key (it should start with 'sk-').\n")
        self.text_area.see(tk.END)

    async def check_for_api_key(self):
        """Check the clipboard for a valid OpenAI API key and update the .env file if found."""
        last_clipboard = pyperclip.paste()  # Initialize with current clipboard content
        while not self.api_key_set:
            current_clipboard = pyperclip.paste()
            if current_clipboard != last_clipboard and current_clipboard.startswith("sk-") and len(current_clipboard) > 30:
                # Valid API key found
                self.api_key = current_clipboard
                self.api_key_set = True
                self.update_env_file(self.api_key)
                self.text_area.insert(tk.END, "API key detected and saved.\n")
                self.text_area.insert(tk.END, "Please restart the program to use the new API key.\n")
                self.text_area.insert(tk.END, "The program will close in 3 seconds.\n")
                self.text_area.see(tk.END)
                await asyncio.sleep(3)  # Wait for 3 seconds
                self.close_window()  # Close the window
            last_clipboard = current_clipboard
            await asyncio.sleep(1)  # Check every second

    def update_env_file(self, api_key):
        """Write the API key to the hidden .academic_victim file."""
        
        # Determine the appropriate file path based on the operating system
        if platform.system() == "Darwin":  # macOS
            config_file = os.path.expanduser("~/.academic_victim")
        elif platform.system() == "Windows":
            config_file = os.path.join(os.environ["USERPROFILE"], ".academic_victim")
        else:
            config_file = ".academic_victim"  # Fallback to current directory for other OS

        # Ensure the directory exists
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        with open(config_file, "a") as env_file:
            env_file.write(f"\nOPENAI_API_KEY={api_key}\n")
        print(f"API key saved to {config_file}: {api_key}...")  # Debugging: Print the first few characters of the API key

    def display_default_message(self):
        """Display a default message when the window is opened with a loaded API key."""
        # Temporarily enable the text area to insert text
        self.text_area.config(state=tk.NORMAL)

        # Insert the default message with bold, light gray color, and font size 6
        self.text_area.insert(tk.END, "Copy any text to start, or use the following shortcuts:\n", ("bold", "small", "gray"))
        self.text_area.insert(tk.END, "Ctrl+Alt+1 for Position 1\n", ("bold", "small", "gray"))
        self.text_area.insert(tk.END, "Ctrl+Alt+2 for Position 2\n", ("bold", "small", "gray"))
        self.text_area.insert(tk.END, "Ctrl+Alt+3 to take a screenshot between 2 positions and send\n", ("bold", "small", "gray"))
        self.text_area.see(tk.END)

        # Configure the tag for bold, light gray, and small font size
        self.text_area.tag_configure("bold", font=("Arial", 6, "bold"))
        self.text_area.tag_configure("small", font=("Arial", 6))
        self.text_area.tag_configure("gray", foreground="light gray")

        # Disable the text area again to make it read-only
        self.text_area.config(state=tk.DISABLED)

async def check_clipboard(popup):
    last_clipboard = pyperclip.paste()  # Initialize with current clipboard content
    while True:
        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard != last_clipboard and current_clipboard != popup.ignore_clipboard:
                print(f"New clipboard content detected: {current_clipboard[:50]}...")  # Debug print
                print(f"Ignored content: {popup.ignore_clipboard[:50]}...")  # Debug print
                popup.update_text("Processing new clipboard content...\n")
                async for response_chunk in stream_gpt4_response(prompt=current_clipboard, image=None, model=popup.model_options[popup.current_model_index]):
                    popup.update_text(response_chunk)
                    await asyncio.sleep(0.01)  # Allow GUI to update
                popup.update_text("\n\n")
                last_clipboard = current_clipboard
            popup.ignore_clipboard = ""  # Reset ignore_clipboard after each check
        except Exception as e:
            print(f"Error in check_clipboard: {e}")
        await asyncio.sleep(0.5)  # Check every half second for more responsiveness

async def main():
    root = tk.Tk()
    loop = asyncio.get_event_loop()  # Get the main event loop
    popup = PopupWindow(root, loop)  # Pass the event loop to PopupWindow

    if not popup.api_key_set:
        # Start the task to check for the API key if it's not set
        api_key_task = asyncio.create_task(popup.check_for_api_key())
    else:
        # Start the clipboard task if the API key is already set
        clipboard_task = asyncio.create_task(check_clipboard(popup))

    try:
        while True:
            root.update()
            await asyncio.sleep(0.01)  # Reduced sleep time for smoother updates
    except tk.TclError:
        print("Window closed")
    finally:
        if not popup.api_key_set:
            api_key_task.cancel()
        else:
            clipboard_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
