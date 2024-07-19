import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from tkinter.ttk import Progressbar
from pygments import lex
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name
from pygments.token import Token
import os
import subprocess
import threading
import time

class SwankyNCode(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # Hide the main window initially

        self.show_loading_screen()
        self.after(6000, self.show_initial_screen)

    def show_loading_screen(self):
        self.loading_screen = tk.Toplevel(self)
        self.loading_screen.overrideredirect(True)
        self.loading_screen.geometry("400x300+500+200")
        self.loading_screen.configure(bg="black")

        tk.Label(self.loading_screen, text="SwankyNCode", font=("Helvetica", 24), fg="white", bg="black").pack(pady=20)
        
        self.progress = Progressbar(self.loading_screen, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.pack(pady=20)
        
        self.progress_label = tk.Label(self.loading_screen, text="0%", font=("Helvetica", 12), fg="white", bg="black")
        self.progress_label.pack(pady=10)

        self.file_loading_label = tk.Label(self.loading_screen, text="Loading dependencies...", font=("Helvetica", 12), fg="white", bg="black")
        self.file_loading_label.pack(pady=10)

        self.loading_files = ["core.py", "gui.py", "syntax_highlighter.py", "file_manager.py", "terminal.py"]
        self.current_loading_file_index = 0

        self.update_loading_screen()

    def update_loading_screen(self):
        if self.current_loading_file_index < len(self.loading_files):
            file = self.loading_files[self.current_loading_file_index]
            self.file_loading_label.config(text=f"Loading {file}...")
            self.current_loading_file_index += 1
            self.progress['value'] = (self.current_loading_file_index / len(self.loading_files)) * 100
            self.progress_label.config(text=f"{int(self.progress['value'])}%")
            self.loading_screen.after(1000, self.update_loading_screen)
        else:
            self.loading_screen.after(1000, self.show_main_window)

    def show_initial_screen(self):
        self.initial_screen = tk.Toplevel(self)
        self.initial_screen.geometry("400x300+500+200")
        self.initial_screen.configure(bg=self.bg_color)

        tk.Label(self.initial_screen, text="SwankyNCode", font=("Helvetica", 24), fg=self.text_color, bg=self.bg_color).pack(pady=20)

        btn_edit_file = tk.Button(self.initial_screen, text="Edit Existing File", command=self.open_file, font=("Helvetica", 14), bg=self.highlight_color, fg=self.text_color)
        btn_edit_file.pack(pady=10)

        btn_new_file = tk.Button(self.initial_screen, text="Create and Edit New File", command=self.create_new_file, font=("Helvetica", 14), bg=self.highlight_color, fg=self.text_color)
        btn_new_file.pack(pady=10)

        btn_open_folder = tk.Button(self.initial_screen, text="Open and Edit Folder", command=self.open_folder, font=("Helvetica", 14), bg=self.highlight_color, fg=self.text_color)
        btn_open_folder.pack(pady=10)

    def show_main_window(self):
        self.loading_screen.destroy()
        self.deiconify()
        self.configure_theme()
        
        self.create_menu()
        self.create_layout()
        self.create_editor()
        self.create_terminal()
        self.create_file_manager()

    def configure_theme(self):
        self.current_theme = "dark"
        self.bg_color = "#282C34"
        self.text_color = "#ABB2BF"
        self.highlight_color = "#3E4451"
        self.configure(bg=self.bg_color)

    def create_menu(self):
        menu_bar = tk.Menu(self)
        
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open File", command=self.open_file)
        file_menu.add_command(label="Save File", command=self.save_file)
        file_menu.add_command(label="Open Folder", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        theme_menu = tk.Menu(menu_bar, tearoff=0)
        theme_menu.add_command(label="Dark Theme", command=lambda: self.change_theme("dark"))
        theme_menu.add_command(label="Light Theme", command=lambda: self.change_theme("light"))
        menu_bar.add_cascade(label="Theme", menu=theme_menu)
        
        self.config(menu=menu_bar)

    def create_layout(self):
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=self.bg_color)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.file_frame = tk.Frame(self.paned_window, bg=self.bg_color)
        self.editor_frame = tk.Frame(self.paned_window, bg=self.bg_color)

        self.paned_window.add(self.file_frame, width=200)
        self.paned_window.add(self.editor_frame, width=800)

    def create_editor(self):
        self.editor = scrolledtext.ScrolledText(self.editor_frame, wrap=tk.WORD, undo=True, bg=self.bg_color, fg=self.text_color, insertbackground=self.text_color)
        self.editor.pack(fill=tk.BOTH, expand=True)
        self.editor.bind('<KeyRelease>', self.on_key_release)
        self.editor.bind("<Key>", self.on_key_press)

    def create_terminal(self):
        self.terminal_frame = tk.Frame(self, height=150, bg=self.bg_color)
        self.terminal_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.terminal_output = scrolledtext.ScrolledText(self.terminal_frame, wrap=tk.WORD, height=10, bg=self.bg_color, fg=self.text_color, insertbackground=self.text_color)
        self.terminal_output.pack(fill=tk.BOTH, expand=True)
        
        self.terminal_input = tk.Entry(self.terminal_frame, bg=self.bg_color, fg=self.text_color, insertbackground=self.text_color)
        self.terminal_input.pack(fill=tk.X)
        self.terminal_input.bind("<Return>", self.execute_command)
        self.update_terminal_prompt()

    def create_file_manager(self):
        self.tree = ttk.Treeview(self.file_frame)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.on_file_open)

    def open_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.load_file(file_path)

    def create_new_file(self):
        self.editor.delete(1.0, tk.END)
        self.initial_screen.destroy()
        self.deiconify()

    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("All Files", "*.*"), ("Text Files", "*.txt"), ("Python Files", "*.py")])
        if file_path:
            with open(file_path, 'w') as file:
                content = self.editor.get(1.0, tk.END)
                file.write(content)

    def open_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.load_folder(folder_path)

    def load_folder(self, folder_path):
        self.tree.delete(*self.tree.get_children())
        self.insert_folder_items('', folder_path)
        self.initial_screen.destroy()
        self.deiconify()

    def insert_folder_items(self, parent, folder_path):
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                node = self.tree.insert(parent, 'end', text=item, open=False)
                self.insert_folder_items(node, item_path)
            else:
                self.tree.insert(parent, 'end', text=item, open=False, values=[item_path])

    def load_file(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        self.editor.delete(1.0, tk.END)
        self.editor.insert(tk.END, content)
        self.initial_screen.destroy()
        self.deiconify()

    def on_file_open(self, event):
        item = self.tree.selection()[0]
        file_path = self.tree.item(item, "values")
        if file_path:
            self.load_file(file_path[0])

    def change_theme(self, theme):
        self.current_theme = theme
        self.configure_theme()
        self.editor.configure(bg=self.bg_color, fg=self.text_color, insertbackground=self.text_color)
        self.terminal_output.configure(bg=self.bg_color, fg=self.text_color, insertbackground=self.text_color)
        self.terminal_input.configure(bg=self.bg_color, fg=self.text_color, insertbackground=self.text_color)

    def on_key_release(self, event=None):
        code = self.editor.get(1.0, tk.END)
        self.highlight_syntax(code)

    def on_key_press(self, event=None):
        if event.char in ('(', '[', '{'):
            self.editor.insert(tk.INSERT, {'(': ')', '[': ']', '{': '}'}[event.char])
            self.editor.mark_set(tk.INSERT, f"{self.editor.index(tk.INSERT)}-1c")
        self.highlight_syntax(self.editor.get(1.0, tk.END))

    def highlight_syntax(self, code):
        lexer = get_lexer_by_name("python", stripall=True)
        tokens = lex(code, lexer)
        style = get_style_by_name("monokai" if self.current_theme == "dark" else "default")
        
        keywords = {
            "red": ["func", "function", "fn"],
            "blue": ["var", "const", "float", "int32", "int64", "int128", "float32", "float64", "float128", "string", "str"],
            "gray": ["//", "#"],
            "green": ["\""],
        }
        
        self.editor.mark_set("range_start", "1.0")
        for token, content in tokens:
            start_index = self.editor.index("range_start")
            end_index = f"{start_index}+{len(content)}c"
            
            if token in Token.Comment:
                self.editor.tag_add("comment", start_index, end_index)
            elif token in Token.Literal.String:
                self.editor.tag_add("string", start_index, end_index)
            else:
                self.editor.mark_set("range_start", end_index)
                continue
            
            for color, words in keywords.items():
                if any(content.startswith(word) for word in words):
                    self.editor.tag_add(color, start_index, end_index)
                    break
            
            self.editor.mark_set("range_start", end_index)
        
        self.editor.tag_configure("comment", foreground="gray")
        self.editor.tag_configure("string", foreground="darkgreen")
        self.editor.tag_configure("red", foreground="red")
        self.editor.tag_configure("blue", foreground="blue")
        self.editor.tag_configure("gray", foreground="gray")

    def execute_command(self, event=None):
        command = self.terminal_input.get()
        self.terminal_input.delete(0, tk.END)
        if command.strip():
            if command.startswith('cd '):
                try:
                    os.chdir(command.strip()[3:])
                    self.update_terminal_prompt()
                except FileNotFoundError:
                    self.terminal_output.insert(tk.END, f"Directory not found: {command.strip()[3:]}\n")
            else:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                self.terminal_output.insert(tk.END, result.stdout + result.stderr)
                self.terminal_output.yview(tk.END)

    def update_terminal_prompt(self):
        current_dir = os.getcwd()
        self.terminal_input.config(prompt=f"{current_dir} $ ")

if __name__ == "__main__":
    app = SwankyNCode()
    app.mainloop()