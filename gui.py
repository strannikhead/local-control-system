import os
import tkinter as tk
from tkinter import filedialog, messagebox
import cvs
import exceptions


class CVSApp:
    def __init__(self, root):
        # Window options
        self.root = root
        self.root.title("Control Version System")
        self.root.geometry("600x400")

        self.current_dir = None
        self.items = []

        self.init_menu()

        # Frame for file list
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        # Scrollbar
        self.scrollbar = tk.Scrollbar(self.frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Canvas to contain the checklist
        self.canvas = tk.Canvas(self.frame, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.canvas.yview)
        # Frame inside the canvas
        self.check_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.check_frame, anchor='nw')
        # Button to show selected files
        self.show_button = tk.Button(self.root, text="Commit", command=self.commit)
        self.show_button.pack(pady=10)
        # Text field
        self.text_field = tk.Entry(self.root, textvariable=tk.StringVar(), )
        self.text_field.pack(pady=10)

    def init_menu(self):
        # File
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Directory", command=self.open_directory)
        file_menu.add_command(label="Exit", command=root.quit)

        # Options
        options_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Initialize", command=self.init)

    def init_window_content(self):
        # Frame for file list
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        # Scrollbar
        self.scrollbar = tk.Scrollbar(self.frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Canvas to contain the checklist
        self.canvas = tk.Canvas(self.frame, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.canvas.yview)
        # Frame inside the canvas
        self.check_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.check_frame, anchor='nw')
        # Button to commit
        self.show_button = tk.Button(self.root, text="Commit", command=self.commit)
        self.show_button.pack(pady=10)
        # Text field
        self.text_field = tk.Entry(self.root, textvariable=tk.StringVar(), )
        self.text_field.pack(pady=10)

    @staticmethod
    def print_test():
        messagebox.showinfo('test', 'This is a test message')

    def init_cvs_directories(self):
        cvs.MAIN_BRANCH = f"{self.current_dir}/.cvs/branches/main"
        cvs.BRANCHES = f"{self.current_dir}/.cvs/branches"
        cvs.BRANCHES_LOG = f"{self.current_dir}/.cvs/branches_log"
        cvs.STAGING_AREA = f"{self.current_dir}/.cvs/staging_area.json"
        cvs.GITIGNORE = f"{self.current_dir}/.cvs/cvsignore.json"
        cvs.CURRENT_DIR = f"{self.current_dir}"

    def init(self):
        if self.current_dir is None:
            messagebox.showinfo('Error', 'Directory not selected')
        self.init_cvs_directories()
        print(self.current_dir)
        try:
            cvs._init()
            self.populate_file_list()
        except exceptions.RepositoryException:
            messagebox.showinfo('Error', 'Repository already initialized')

    def commit(self):
        try:
            cvs._check_repository_existence()
        except exceptions.RepositoryException:
            messagebox.showinfo('Error', 'Repository not initialized')
        else:
            if not self.items:
                messagebox.showinfo('Error', 'No items to commit')
            else:
                cvs._reset()
                cvs._add(self.items)
                cvs._commit(self.text_field.get(), console_info=True)

    def open_directory(self):
        directory = filedialog.askdirectory()
        self.current_dir = directory
        cvs.CURRENT_DIR = directory
        self.init_cvs_directories()
        if directory:
            self.populate_file_list()

    def populate_file_list(self):
        # Clear the previous list
        for widget in self.check_frame.winfo_children():
            widget.destroy()

        self.items.clear()

        # Add files to the checklist
        for filename in os.listdir(self.current_dir):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.check_frame, text=filename, variable=var)
            chk.pack(anchor='w')
            self.items.append((os.path.join(cvs.CURRENT_DIR, filename), var))

        self.check_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def show_selected(self):
        selected_files = [filename for filename, var in self.items if var.get()]
        if not selected_files:
            messagebox.showinfo("No Files", "No Files Selected")
        else:
            print(f"Selected Files:\n {', '.join(selected_files)}")
            print()
            print(self.text_field.get())


if __name__ == "__main__":
    root = tk.Tk()
    app = CVSApp(root)
    root.mainloop()
