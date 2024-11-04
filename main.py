import asyncio
import pyperclip
import tkinter as tk
from tkinter import scrolledtext, Tk
import os
from ai import stream_gpt4_response, image_ocr, clear_formatted_text, toggle_context, orion_response, reset_chat_history, toggle_chat_history, ENABLE_CHAT_HISTORY
from PIL import ImageGrab, Image, ImageTk
from pynput import mouse, keyboard
import platform
from queue import Queue, Empty

# Import macOS specific modules if needed
if platform.system() == "Darwin":
    from tkmacosx import Button

class PopupWindow:
    def __init__(self, master, loop):
        self.master = master
        self.loop = loop
        self.key_event_queue = Queue()
        self.setup_window()
        self.setup_text_area()
        self.setup_top_bar()
        self.initialize_state()
        self.bind_events()
        self.check_api_key()
        self.check_mouse_position()
        self.process_key_events()

    def setup_window(self):
        self.master.title("academic victim")
        self.master.config(bg="#1e1f22")
        self.setup_icon()
        self.master.overrideredirect(True)
        self.master.attributes("-alpha", 0.9, "-topmost", True)
        self.master.geometry("400x800+100+100")

    def setup_icon(self):
        if platform.system() == "Darwin":
            if os.path.exists("icon.png"):
                icon_image = Image.open("icon.png")
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.master.iconphoto(True, icon_photo)
        elif platform.system() == "Windows" and os.path.exists("icon.ico"):
            self.master.iconbitmap("icon.ico")

    def setup_text_area(self):
        self.text_area = scrolledtext.ScrolledText(
            self.master,
            wrap=tk.WORD,
            width=40,
            height=10,
            font=("Arial", 14),
            fg="white",
            bg="#1e1f22",
            bd=0,
            highlightthickness=0
        )
        self.text_area.pack(expand=True, fill='both')
        self.text_area.config(state=tk.DISABLED)
        self.text_area.vbar.pack_forget()

    def setup_top_bar(self):
        self.top_bar = tk.Frame(self.master, height=30, bg="#343740")
        self.setup_top_bar_elements()
        self.top_bar.pack_forget()
        self.top_bar.lift()

    def setup_top_bar_elements(self):
        self.label = tk.Label(self.top_bar, text="academic victim", fg="white", bg="#343740", font=("Arial", 11, "bold"))
        self.label.pack(side=tk.LEFT, padx=5, pady=(0, 2))

        button_config = {
            "fg": "white",
            "activebackground": "#3b45a8",
            "activeforeground": "white",
            "height": 25,
            "relief": tk.FLAT,
            "highlightcolor": "#4752c4",
            "highlightthickness": 0,
            "font": ("Arial", 11, "bold"),
            "takefocus": 0
        }

        toggle_button_config = button_config.copy()
        toggle_button_config["width"] = 30

        if platform.system() == "Darwin":
            button_config["borderless"] = False
            toggle_button_config["borderless"] = False
            Button_class = Button
            if "bg" in button_config: del button_config["bg"]
            if "bg" in toggle_button_config: del toggle_button_config["bg"]
        else:
            Button_class = tk.Button
            button_config["height"] = 1
            toggle_button_config["height"] = 1
            button_config["bg"] = "#4752c4"

        # Create all buttons
        if platform.system() == "Darwin":
            self.context_button = Button_class(self.top_bar, text="CTX", command=self.toggle_context_button, 
                                             background="#ff4444", **toggle_button_config)
            self.history_button = Button_class(self.top_bar, text="HST", command=self.toggle_history_button,
                                             background="#44ff44", **toggle_button_config)
            self.wipe_history_button = Button_class(self.top_bar, text="WH", command=self.wipe_history_button,
                                                  background="#4752c4", **toggle_button_config)
            self.wipe_context_button = Button_class(self.top_bar, text="WC", command=self.wipe_context_button,
                                                  background="#4752c4", **toggle_button_config)
            self.close_button = Button_class(self.top_bar, text="X", command=self.close_window, 
                                           width=30, background="#4752c4", **button_config)
            self.copy_button = Button_class(self.top_bar, text="C", command=self.copy_last_response, 
                                          width=30, background="#4752c4", **button_config)
        else:
            self.context_button = Button_class(self.top_bar, text="CTX", command=self.toggle_context_button, 
                                             bg="#ff4444", **toggle_button_config)
            self.history_button = Button_class(self.top_bar, text="HST", command=self.toggle_history_button,
                                             bg="#44ff44", **toggle_button_config)
            self.wipe_history_button = Button_class(self.top_bar, text="WH", command=self.wipe_history_button,
                                                  bg="#4752c4", **toggle_button_config)
            self.wipe_context_button = Button_class(self.top_bar, text="WC", command=self.wipe_context_button,
                                                  bg="#4752c4", **toggle_button_config)
            self.close_button = Button_class(self.top_bar, text="X", command=self.close_window, 
                                           width=30, **button_config)
            self.copy_button = Button_class(self.top_bar, text="C", command=self.copy_last_response, 
                                          width=30, **button_config)
        
        self.model_options = [
            "o1-preview", 
            "o1-mini",
            "gpt-4o-mini",
            "chatgpt-4o-latest",
            "gpt-4o"
        ]
        self.current_model_index = 1
        model_text = f"Model: {self.model_options[self.current_model_index]}"
        
        if platform.system() == "Darwin":
            self.model_button = Button_class(self.top_bar, text=model_text, command=self.cycle_model, 
                                           width=len(model_text)*7, background="#4752c4", **button_config)
        else:
            self.model_button = Button_class(self.top_bar, text=model_text, command=self.cycle_model, 
                                           width=len(model_text), **button_config)

        # Pack buttons in reverse order
        for button in [self.close_button, self.copy_button, self.context_button, 
                      self.history_button, self.wipe_history_button, self.wipe_context_button, 
                      self.model_button]:
            button.pack(side=tk.RIGHT, padx=(0,1), pady=(0, 2))

    def initialize_state(self):
        self.offset_x = self.offset_y = 0
        self.is_dragging = False
        self.last_response = ""
        self.ignore_clipboard = ""
        self.pos1 = self.pos2 = None
        self.ctrl_pressed = self.shift_pressed = False
        self.response_start_index = None
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.keyboard_listener.start()

    def bind_events(self):
        self.master.bind("<B1-Motion>", self.do_move)
        self.master.bind("<ButtonRelease-1>", self.stop_move)

    def check_api_key(self):
        def check_api_key_exists():
            config_file = os.path.expanduser("~/.academic_victim") if platform.system() == "Darwin" else \
                         os.path.join(os.environ["USERPROFILE"], ".academic_victim") if platform.system() == "Windows" else \
                         ".academic_victim"
            return os.path.exists(config_file)

        self.api_key_set = check_api_key_exists()
        if not self.api_key_set:
            self.display_api_key_message()
        else:
            self.display_default_message()

    def update_text(self, text, tag=None):
        """Update the text area with new text, optionally with a tag."""
        self.text_area.config(state=tk.NORMAL)
        if "Processing new clipboard content..." in text:
            self.response_start_index = self.text_area.index(tk.END)
        
        # If chat history is disabled, use yellow text unless a specific tag is provided
        if not ENABLE_CHAT_HISTORY and tag is None:
            self.text_area.tag_configure("history_disabled", foreground="#FFD700")
            self.text_area.insert(tk.END, text, "history_disabled")
        else:
            if tag:
                self.text_area.insert(tk.END, text, tag)
            else:
                self.text_area.insert(tk.END, text)
                
        self.text_area.see(tk.END)
        self.last_response += text
        self.text_area.config(state=tk.DISABLED)

    def close_window(self):
        self.master.destroy()
        os._exit(0)

    def copy_last_response(self):
        if self.response_start_index:
            assistant_response = self.text_area.get(self.response_start_index, tk.END).strip()
            pyperclip.copy(assistant_response)
            self.ignore_clipboard = assistant_response
            print("copied", assistant_response)
            print("ignore clipboard", self.ignore_clipboard)

    def cycle_model(self):
        self.current_model_index = (self.current_model_index + 1) % len(self.model_options)
        model_text = f"Model: {self.model_options[self.current_model_index]}"
        self.model_button.config(text=model_text)
        if platform.system() == "Darwin":
            self.model_button.config(width=len(model_text)*7)
        else:
            self.model_button.config(width=len(model_text))

    def do_move(self, event):
        if not self.is_dragging:
            self.offset_x = self.master.winfo_x() - event.x_root
            self.offset_y = self.master.winfo_y() - event.y_root
            self.is_dragging = True

        x = event.x_root + self.offset_x
        y = event.y_root + self.offset_y

        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = max(0, min(x, screen_width - self.master.winfo_width()))
        y = max(0, min(y, screen_height - self.master.winfo_height()))

        self.master.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        self.is_dragging = False

    def check_mouse_position(self):
        x, y = self.master.winfo_pointerx(), self.master.winfo_pointery()
        window_x, window_y = self.master.winfo_rootx(), self.master.winfo_rooty()
        window_width, window_height = self.master.winfo_width(), self.master.winfo_height()

        if window_x <= x <= window_x + window_width and window_y <= y <= window_y + window_height:
            self.show_top_bar()
        else:
            self.hide_top_bar()

        self.master.after(100, self.check_mouse_position)

    def show_top_bar(self):
        self.top_bar.pack(side=tk.TOP, fill=tk.X)
        self.top_bar.lift()

    def hide_top_bar(self):
        self.top_bar.pack_forget()

    def on_key_press(self, key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                self.shift_pressed = True
                
            if self.ctrl_pressed and self.shift_pressed:
                try:
                    if hasattr(key, 'char') and key.char in ['1', '2', '3', '4', '5', '7', '8', '9']:
                        key_num = key.char
                    elif hasattr(key, 'vk') and (49 <= key.vk <= 53 or key.vk in [55, 56, 57]):
                        key_num = str(key.vk - 48)
                    else:
                        return
                    
                    self.key_event_queue.put(key_num)
                    
                except AttributeError as e:
                    print(f"Key processing error: {e}")
                
        except Exception as e:
            print(f"Error in key press handler: {e}")

    def on_key_release(self, key):

        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False
        elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.shift_pressed = False
    def get_mouse_position(self):
        with mouse.Controller() as controller:
            position = controller.position
            return position

    def take_screenshot(self, for_ocr=False):
        if not (self.pos1 and self.pos2):
            return
            
        try:
            x1, y1 = map(int, self.pos1)
            x2, y2 = map(int, self.pos2)
            bbox = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            screenshot = ImageGrab.grab(bbox).convert("RGB")
            
            if for_ocr:
                # Configure OCR tag and show processing message
                self.text_area.tag_configure("ocr", foreground="#00ff00")
                self.display_message("Processing OCR...\n")
                
                async def process_ocr():
                    try:
                        async for chunk in image_ocr(screenshot):
                            self.master.after(0, lambda c=chunk: self.update_text(c, "ocr"))
                        self.master.after(0, lambda: self.update_text("\n\n"))
                    except Exception as e:
                        print(f"Error in OCR processing: {e}")
                        self.master.after(0, lambda: self.display_message(f"Error: {str(e)}\n\n"))
                
                asyncio.run_coroutine_threadsafe(process_ocr(), self.loop)
            else:
                async def process_screenshot():
                    try:
                        async for chunk in stream_gpt4_response(prompt=None, image=screenshot, 
                                                              model=self.model_options[self.current_model_index]):
                            self.master.after(0, lambda c=chunk: self.update_text(c))
                        self.master.after(0, lambda: self.update_text("\n\n"))
                    except Exception as e:
                        print(f"Error in screenshot processing: {e}")
                        self.master.after(0, lambda: self.display_message(f"Error: {str(e)}\n\n"))
                
                asyncio.run_coroutine_threadsafe(process_screenshot(), self.loop)
            
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            self.master.after(0, lambda: self.display_message(f"Error taking screenshot: {str(e)}\n\n"))

    def take_ocr_screenshot(self):
        self.take_screenshot(for_ocr=True)

    def display_api_key_message(self):
        print("Displaying API key message...")
        self.display_message(
            "Thanks for installing academic victim.\n"
            "You need an OpenAI API key to use this.\n"
            "Please copy your API key (it should start with 'sk-').\n",
            clear=True
        )
        print("API key message displayed")

    async def check_for_api_key(self):
        last_clipboard = pyperclip.paste()
        while not self.api_key_set:
            current_clipboard = pyperclip.paste()
            if current_clipboard != last_clipboard and current_clipboard.startswith("sk-") and len(current_clipboard) > 30:
                self.api_key = current_clipboard
                self.api_key_set = True
                self.update_env_file(self.api_key)
                self.display_message(
                    "API key detected and saved.\n"
                    "Please restart the program to use the new API key.\n"
                    "The program will close in 3 seconds.\n",
                    clear=True
                )
                await asyncio.sleep(3)
                self.close_window()
            last_clipboard = current_clipboard
            await asyncio.sleep(1)

    def update_env_file(self, api_key):
        config_file = os.path.expanduser("~/.academic_victim") if platform.system() == "Darwin" else \
                     os.path.join(os.environ["USERPROFILE"], ".academic_victim") if platform.system() == "Windows" else \
                     ".academic_victim"
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "a") as env_file:
            env_file.write(f"\nOPENAI_API_KEY={api_key}\n")
        print(f"API key saved to {config_file}: {api_key[:10]}...")

    def display_default_message(self):
        messages = [
            ("Copy any text to start, or use the following shortcuts:\n", ("bold", "small", "gray")),
            ("Ctrl+Alt+1 for Position 1\n", ("bold", "small", "gray")),
            ("Ctrl+Alt+2 for Position 2\n", ("bold", "small", "gray")),
            ("Ctrl+Alt+3 to take a screenshot between 2 positions and send\n", ("bold", "small", "gray")),
            ("Ctrl+Alt+4 to take an OCR screenshot between 2 positions and send\n", ("bold", "small", "gray")),
            ("Ctrl+Alt+5 to toggle context inclusion\n", ("bold", "small", "gray")),
            ("Ctrl+Alt+7 to toggle chat history\n", ("bold", "small", "gray")),
            ("Ctrl+Alt+8 to reset chat history\n", ("bold", "small", "gray")),
            ("Ctrl+Alt+9 to clear OCR history\n", ("bold", "small", "gray"))
        ]
        
        for message, tags in messages:
            self.display_message(message, tags)

    def display_message(self, message, tags=None, clear=False):
        """Centralized method for displaying messages in the text area.
        
        Args:
            message (str): The message to display
            tags (tuple): Optional tuple of tags to apply ("bold", "small", "gray", "ocr")
            clear (bool): Whether to clear the text area before displaying
        """
        self.text_area.config(state=tk.NORMAL)
        
        if clear:
            self.text_area.delete(1.0, tk.END)
        
        if tags:
            self.text_area.insert(tk.END, message, tags)
        else:
            self.text_area.insert(tk.END, message)
        
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def toggle_context_button(self):
        context_enabled = toggle_context()
        if platform.system() == "Darwin":
            self.context_button.configure(background="#44ff44" if context_enabled else "#ff4444")
        else:
            self.context_button.configure(bg="#44ff44" if context_enabled else "#ff4444")
        self.display_message(f"Context {'enabled' if context_enabled else 'disabled'}.\n\n")

    def toggle_history_button(self):
        history_enabled = toggle_chat_history()
        if platform.system() == "Darwin":
            self.history_button.configure(background="#44ff44" if history_enabled else "#ff4444")
        else:
            self.history_button.configure(bg="#44ff44" if history_enabled else "#ff4444")
        if history_enabled:
            self.text_area.tag_configure("history_disabled", foreground="white")
            self.display_message("Chat history enabled - Messages will be saved to history.\n\n")
        else:
            self.text_area.tag_configure("history_disabled", foreground="#FFD700")
            self.display_message("Chat history disabled - Messages will not be saved to history.\n\n", ("history_disabled",))

    def process_key_events(self):
        """Process any pending keyboard events in the queue"""
        try:
            while True:
                key_num = self.key_event_queue.get_nowait()
                if key_num == '1':
                    self.pos1 = self.get_mouse_position()
                    print(f"POS1 set at {self.pos1}")
                elif key_num == '2':
                    self.pos2 = self.get_mouse_position()
                    print(f"POS2 set at {self.pos2}")
                elif key_num == '3':
                    if self.pos1 and self.pos2:
                        print(f"Taking screenshot between {self.pos1} and {self.pos2}")
                        self.take_screenshot()
                    else:
                        self.display_message("Error: POS1 and POS2 must be set before taking a screenshot.\n\n")
                elif key_num == '4':
                    if self.pos1 and self.pos2:
                        print(f"Taking OCR screenshot between {self.pos1} and {self.pos2}")
                        self.take_ocr_screenshot()
                    else:
                        self.display_message("Error: POS1 and POS2 must be set before taking a screenshot.\n\n")
                elif key_num == '5':
                    self.toggle_context_button()
                elif key_num == '7':
                    self.toggle_history_button()
                elif key_num == '8':
                    num_deleted = reset_chat_history()
                    self.display_message(f"Chat history reset! {num_deleted} messages were deleted.\n\n")
                elif key_num == '9':
                    clear_formatted_text()
                    self.display_message("OCR history cleared.\n\n")
        except Empty:
            pass
        
        # Schedule the next check
        self.master.after(100, self.process_key_events)

    def wipe_history_button(self):
        num_deleted = reset_chat_history()
        self.display_message(f"Chat history reset! {num_deleted} messages were deleted.\n\n")
        # Flash the button
        if platform.system() == "Darwin":
            self.wipe_history_button.configure(background="#ff4444")
            self.master.after(200, lambda: self.wipe_history_button.configure(background="#4752c4"))
        else:
            self.wipe_history_button.configure(bg="#ff4444")
            self.master.after(200, lambda: self.wipe_history_button.configure(bg="#4752c4"))

    def wipe_context_button(self):
        clear_formatted_text()
        self.display_message("OCR history cleared.\n\n")
        # Flash the button
        if platform.system() == "Darwin":
            self.wipe_context_button.configure(background="#ff4444")
            self.master.after(200, lambda: self.wipe_context_button.configure(background="#4752c4"))
        else:
            self.wipe_context_button.configure(bg="#ff4444")
            self.master.after(200, lambda: self.wipe_context_button.configure(bg="#4752c4"))

async def check_clipboard(popup):
    last_clipboard = pyperclip.paste()
    while True:
        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard != last_clipboard and current_clipboard != popup.ignore_clipboard:
                print(f"New clipboard content detected: {current_clipboard[:50]}...")
                print(f"Ignored content: {popup.ignore_clipboard[:50]}...")
                popup.display_message("Processing new clipboard content...\n")
                
                # Choose the appropriate method based on the model
                current_model = popup.model_options[popup.current_model_index]
                if current_model.startswith("o1-"):
                    # Use orion_response for o1 models
                    async for response_chunk in orion_response(prompt=current_clipboard, model=current_model):
                        popup.update_text(response_chunk)
                else:
                    # Use stream_gpt4_response for other models
                    async for response_chunk in stream_gpt4_response(prompt=current_clipboard, model=current_model):
                        popup.update_text(response_chunk)
                        await asyncio.sleep(0.01)
                        
                popup.update_text("\n\n")
                last_clipboard = current_clipboard
            popup.ignore_clipboard = ""
        except Exception as e:
            print(f"Error in check_clipboard: {e}")
        await asyncio.sleep(0.5)

async def main():
    root = Tk()
    loop = asyncio.get_event_loop()
    popup = PopupWindow(root, loop)
    print("PopupWindow initialized")

    if not popup.api_key_set:
        print("No API key found, starting check_for_api_key task")
        api_key_task = asyncio.create_task(popup.check_for_api_key())
    else:
        print("API key found, starting clipboard task")
        clipboard_task = asyncio.create_task(check_clipboard(popup))

    try:
        print("Entering main loop")
        while True:
            root.update()
            await asyncio.sleep(0.01)
    except tk.TclError as e:
        print(f"Window closed with error: {e}")
    finally:
        if not popup.api_key_set:
            print("Canceling API key task")
            api_key_task.cancel()
        else:
            print("Canceling clipboard task")
            clipboard_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
