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
        self.root.geometry("400x400")
        self.root.resizable(False, False)

        # self.current_dir = None
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
        # Text field
        self.text_field = tk.Text(self.root, width=42, height=2, border=5)
        self.text_field.pack(side=tk.LEFT, fill=tk.X)
        # Commit button
        self.show_button = tk.Button(self.root, text="Commit", command=self.commit)
        self.show_button.pack(pady=10, side=tk.LEFT)

    def init_menu(self):
        # File
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Directory", command=self.open_directory)
        file_menu.add_command(label="Exit", command=self.root.quit)
        # Options
        options_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Initialize", command=self.init)
        # Branches
        self.branches_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Branches", menu=self.branches_menu)
        # Cherry Picks
        self.cherry_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Cherry picks", menu=self.cherry_menu)

    @staticmethod
    def print_test():
        messagebox.showinfo('test', 'This is a test message')

    @staticmethod
    def init_cvs_directories(directory):
        cvs.MAIN_BRANCH = f"{directory}/.cvs/branches/main"
        cvs.BRANCHES = f"{directory}/.cvs/branches"
        cvs.BRANCHES_LOG = f"{directory}/.cvs/branches_log"
        cvs.STAGING_AREA = f"{directory}/.cvs/staging_area.json"
        cvs.GITIGNORE = f"{directory}/.cvs/cvsignore.json"
        cvs.CURRENT_DIR = f"{directory}"

    def init(self):
        if cvs.CURRENT_DIR == '.' or not cvs.CURRENT_DIR:
            messagebox.showinfo('Error', 'Directory not selected')
        print(cvs.CURRENT_DIR)
        try:
            cvs._init()
            self.populate_file_list()
            messagebox.showinfo('Success', 'Cvs initialized')
        except exceptions.RepositoryException:
            messagebox.showinfo('Error', 'Repository already initialized')

    def commit(self):
        try:
            cvs._check_repository_existence()
        except exceptions.RepositoryException:
            messagebox.showinfo('Error', 'Repository not selected')
        else:
            items = self.get_items()
            if not items:
                messagebox.showinfo('Error', 'No items to commit')
            else:
                try:
                    cvs._add(items, console_info=True)
                except:
                    pass
                cvs._commit(self.text_field.get("1.0", "end"), console_info=True)
                messagebox.showinfo('Success', 'Commit successful')

    def open_directory(self):
        directory = filedialog.askdirectory()
        self.init_cvs_directories(directory)
        if directory:
            self.populate_file_list()
            self.init_menu()

        branches = cvs._get_branches()
        print(branches)
        for branch in branches:
            self.branches_menu.add_command(label=branch, command=lambda b=branch: self.checkout(b, console_info=True))

        try:
            cvs._check_repository_existence()
            staging_area = cvs._update_staging_area()
            current_branch = staging_area["current_branch"]
            self.init_cherry_pick(current_branch)
        except:
            pass

    def checkout(self, branch, console_info=False):
        cvs._checkout(branch, console_info)
        self.populate_file_list()
        self.init_cherry_pick(branch)

    def init_cherry_pick(self, branch):
        commits = cvs._get_commits(branch)
        for commit in commits:
            self.cherry_menu.add_command(label=' - '.join(commit), command=lambda c=commit[0]: self.cherry_pick(c))

    def cherry_pick(self, commit_id):
        cvs._cherry_pick(commit_id, console_info=True)
        self.populate_file_list()

    def populate_file_list(self):
        # Clear the previous list
        for widget in self.check_frame.winfo_children():
            widget.destroy()

        self.items.clear()

        # Add files to the checklist
        for filename in os.listdir(cvs.CURRENT_DIR):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.check_frame, text=filename, variable=var)
            chk.pack(anchor='w')
            self.items.append((os.path.join(cvs.CURRENT_DIR, filename), var))

        self.check_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def get_items(self):
        return [filename for filename, var in self.items if var.get()]

    def show_selected(self):
        selected_files = [filename for filename, var in self.items if var.get()]
        if not selected_files:
            messagebox.showinfo("No Files", "No Files Selected")
        else:
            print(f"Selected Files:\n {', '.join(selected_files)}")
            print()
            print(self.text_field.get('1.0', 'end'))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = CVSApp(root)
    root.mainloop()
