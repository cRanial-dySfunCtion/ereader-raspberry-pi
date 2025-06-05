import tkinter as tk
from PIL import Image, ImageTk
import zipfile
import io
import os
import re
import threading
from config import *

# === SET YOUR LIBRARY FOLDER PATH HERE ===

supported_formats = (".jpg", ".jpeg", ".png", ".bmp", ".gif")
cbz_extension = ".cbz"
FULLSCREEN_DELAY = 5000  # milliseconds (5 seconds)

def get_first_image(cbz_path):
    try:
        with zipfile.ZipFile(cbz_path, 'r') as zf:
            images = [f for f in zf.namelist() if f.lower().endswith(supported_formats)]
            images.sort()
            if not images:
                return None
            img_data = zf.read(images[0])
            image = Image.open(io.BytesIO(img_data))
            return image
    except Exception:
        return None

def show_book_selection_screen():
    books = [f for f in os.listdir(library_folder)
             if os.path.isdir(os.path.join(library_folder, f)) and not f.startswith('.')]
    books.sort(key=natural_sort_key)
    if not books:
        raise FileNotFoundError("No books (folders) found in the library folder.")

    root = tk.Tk()
    root.title("Select Book")
    root.after(FULLSCREEN_DELAY, lambda: set_fullscreen(root))

    def quit_app(event=None):
        root.destroy()

    thumb_size = (200, 300)
    columns = 4

    # --- Scrollable Canvas Setup ---
    canvas = tk.Canvas(root, bg="black")
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg="black")

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    thumb_images = []

    for idx, book in enumerate(books):
        book_path = os.path.join(library_folder, book)
        # Find first CBZ in book folder
        cbz_files = [os.path.join(book_path, f) for f in os.listdir(book_path) if f.lower().endswith(cbz_extension)]
        cbz_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
        if cbz_files:
            img = get_first_image(cbz_files[0])
        else:
            img = None
        if img is not None:
            img.thumbnail(thumb_size, Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
        else:
            tk_img = ImageTk.PhotoImage(Image.new("RGB", thumb_size, "gray"))
        thumb_images.append(tk_img)

        btn = tk.Button(scroll_frame, image=tk_img, command=lambda i=idx: open_chapter_selection(books[i], root))
        btn.grid(row=idx // columns * 2, column=idx % columns, padx=20, pady=10)
        lbl = tk.Label(scroll_frame, text=book, fg="white", bg="black", font=("Arial", 14))
        lbl.grid(row=idx // columns * 2 + 1, column=idx % columns, padx=20, pady=(0, 20))

    # Enable mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    root.bind("<Escape>", quit_app)
    root.mainloop()

def open_chapter_selection(book, book_selection_root):
    book_selection_root.destroy()
    show_chapter_selection_screen(book)

def natural_sort_key(s):
    # Split by digits and dots, treat as float if possible
    parts = re.split(r'(\d+(?:\.\d+)?)', s)
    key = []
    for part in parts:
        try:
            # Try to convert to float (handles both integers and decimals)
            key.append(float(part))
        except ValueError:
            key.append(part.lower())
    return key

def show_chapter_selection_screen(book):
    book_path = os.path.join(library_folder, book)
    cbz_files = [os.path.join(book_path, f) for f in os.listdir(book_path) if f.lower().endswith(cbz_extension)]
    cbz_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
    if not cbz_files:
        raise FileNotFoundError(f"No CBZ files found in the book '{book}'.")

    root = tk.Tk()
    root.title(f"Select Chapter - {book}")
    root.attributes("-fullscreen", True)
    root.focus_force()
    root.attributes("-topmost", True)
    root.attributes("-topmost", False)

    def back_to_books(event=None):
        root.destroy()
        show_book_selection_screen()

    thumb_size = (200, 300)
    columns = 4

    # --- Scrollable Canvas Setup ---
    canvas = tk.Canvas(root, bg="black")
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg="black")

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    thumb_images = []

    for idx, cbz_path in enumerate(cbz_files):
        chapter_name = os.path.splitext(os.path.basename(cbz_path))[0]
        img = get_first_image(cbz_path)
        if img is not None:
            img.thumbnail(thumb_size, Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
        else:
            tk_img = ImageTk.PhotoImage(Image.new("RGB", thumb_size, "gray"))
        thumb_images.append(tk_img)

        btn = tk.Button(scroll_frame, image=tk_img, command=lambda i=idx: open_reader(i, cbz_files, root))
        btn.grid(row=idx // columns * 2, column=idx % columns, padx=20, pady=10)
        lbl = tk.Label(scroll_frame, text=chapter_name, fg="white", bg="black", font=("Arial", 14))
        lbl.grid(row=idx // columns * 2 + 1, column=idx % columns, padx=20, pady=(0, 20))

    # Enable mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    root.bind("<Escape>", back_to_books)
    root.mainloop()

def open_reader(selected_cbz_index, cbz_files, chapter_selection_root):
    chapter_selection_root.destroy()
    start_reader(selected_cbz_index, cbz_files)

def start_reader(start_cbz_index, cbz_files):
    global root, current_cbz_index, cbz_file, image_files, current_index, current_rotation

    current_cbz_index = start_cbz_index
    current_index = 0
    current_rotation = 0

    def load_cbz_images(cbz_path):
        with zipfile.ZipFile(cbz_path, 'r') as zf:
            images = [f for f in zf.namelist() if f.lower().endswith(supported_formats)]
            images.sort()
            if not images:
                raise FileNotFoundError(f"No supported images in {cbz_path}")
            return images

    cbz_file = cbz_files[current_cbz_index]
    image_files = load_cbz_images(cbz_file)

    root = tk.Tk()
    root.title("CBZ Image Viewer")
    root.after(FULLSCREEN_DELAY, lambda: set_fullscreen(root))

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    photo_label = tk.Label(root, bg="black")
    photo_label.pack(expand=True)

    root.update()  # Force window to display before loading the first image

    def resize_and_center(image):
        img_width, img_height = image.size
        ratio = min(screen_width / img_width, screen_height / img_height)
        new_size = (int(img_width * ratio), int(img_height * ratio))
        return image.resize(new_size, Image.LANCZOS)

    def show_image(index):
        global cbz_file, image_files
        with zipfile.ZipFile(cbz_file, 'r') as zf:
            img_data = zf.read(image_files[index])
            image = Image.open(io.BytesIO(img_data))
            rotated_image = image.rotate(current_rotation, expand=True)
            resized_image = resize_and_center(rotated_image)
            tk_image = ImageTk.PhotoImage(resized_image)
            photo_label.config(image=tk_image)
            photo_label.image = tk_image  # Keep reference!

    def next_image(event=None):
        global current_index, current_cbz_index, cbz_file, image_files, current_rotation
        if current_index < len(image_files) - 1:
            current_index += 1
            show_image(current_index)
        else:
            if current_cbz_index < len(cbz_files) - 1:
                current_cbz_index += 1
                cbz_file = cbz_files[current_cbz_index]
                image_files = load_cbz_images(cbz_file)
                current_index = 0
                current_rotation = 0
                show_image(current_index)

    def prev_image(event=None):
        global current_index, current_cbz_index, cbz_file, image_files, current_rotation
        if current_index > 0:
            current_index -= 1
            show_image(current_index)
        else:
            if current_cbz_index > 0:
                current_cbz_index -= 1
                cbz_file = cbz_files[current_cbz_index]
                image_files = load_cbz_images(cbz_file)
                current_index = len(image_files) - 1
                current_rotation = 0
                show_image(current_index)

    def exit_fullscreen(event=None):
        root.destroy()
        # Return to chapter selection for the current folder (full path)
        book_folder = os.path.dirname(cbz_files[0])
        show_chapter_selection_screen(book_folder)

    def rotate_clockwise(event=None):
        global current_rotation
        current_rotation = (current_rotation + 90) % 360
        show_image(current_index)

    def rotate_counterclockwise(event=None):
        global current_rotation
        current_rotation = (current_rotation - 90) % 360
        show_image(current_index)

    root.bind("<Right>", next_image)
    root.bind("<Left>", prev_image)
    root.bind("<Escape>", exit_fullscreen)
    root.bind("w", rotate_clockwise)
    root.bind("q", rotate_counterclockwise)

    show_image(current_index)
    root.mainloop()

def show_folder_selection_screen(current_folder, first=False):
    subfolders = [f for f in os.listdir(current_folder)
                  if os.path.isdir(os.path.join(current_folder, f)) and not f.startswith('.')]
    subfolders.sort(key=natural_sort_key)

    if subfolders:
        root = tk.Tk()
        root.title("Select Folder")
        root.after(FULLSCREEN_DELAY, lambda: set_fullscreen(root))

        thumb_size = (160, 240)  # Slightly smaller for Pi performance
        columns = 4

        # --- Scrollable Canvas Setup ---
        canvas = tk.Canvas(root, bg="black")
        scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="black")

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        thumb_images = []
        btns = []

        # Create all buttons with placeholders first
        for idx, folder in enumerate(subfolders):
            folder_path = os.path.join(current_folder, folder)
            tk_img = ImageTk.PhotoImage(Image.new("RGB", thumb_size, "gray"))
            thumb_images.append(tk_img)
            btn = tk.Button(scroll_frame, image=tk_img, command=lambda p=folder_path: open_next_folder(p, root))
            btn.grid(row=idx // columns * 2, column=idx % columns, padx=20, pady=10)
            lbl = tk.Label(scroll_frame, text=folder, fg="white", bg="black", font=("Arial", 14))
            lbl.grid(row=idx // columns * 2 + 1, column=idx % columns, padx=20, pady=(0, 20))
            btns.append(btn)

        # Background thread to load thumbnails (search all nested subfolders for first CBZ)
        def load_thumbnails():
            for idx, folder in enumerate(subfolders):
                folder_path = os.path.join(current_folder, folder)
                thumb_img = None
                # Walk all subfolders until we find a CBZ
                for rootdir, dirs, files in os.walk(folder_path):
                    cbz_files = [os.path.join(rootdir, f) for f in files if f.lower().endswith(cbz_extension)]
                    cbz_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
                    if cbz_files:
                        thumb_img = get_first_image(cbz_files[0])
                        break
                if thumb_img is not None:
                    thumb_img.thumbnail(thumb_size, Image.LANCZOS)
                    tk_img = ImageTk.PhotoImage(thumb_img)
                    # Update the button image in the main thread
                    def update_btn(idx=idx, tk_img=tk_img):
                        btns[idx].config(image=tk_img)
                        thumb_images[idx] = tk_img  # Keep reference
                    root.after(0, update_btn)
        threading.Thread(target=load_thumbnails, daemon=True).start()

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Bind Esc: close if at main folder, go up if not
        if os.path.abspath(current_folder) != os.path.abspath(library_folder):
            def back_to_parent(event=None):
                root.destroy()
                show_folder_selection_screen(os.path.dirname(current_folder))
            root.bind("<Escape>", back_to_parent)
        else:
            def quit_app(event=None):
                root.destroy()
            root.bind("<Escape>", quit_app)

        root.mainloop()
    else:
        # No subfolders: show CBZ selection screen for this folder
        show_chapter_selection_screen(current_folder)

def open_next_folder(next_folder, current_root):
    current_root.destroy()
    show_folder_selection_screen(next_folder)

def show_chapter_selection_screen(folder):
    cbz_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(cbz_extension)]
    cbz_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))
    if not cbz_files:
        raise FileNotFoundError(f"No CBZ files found in the folder '{folder}'.")

    root = tk.Tk()
    root.title(f"Select Chapter")
    root.after(FULLSCREEN_DELAY, lambda: set_fullscreen(root))

    thumb_size = (200, 300)
    columns = 4

    # --- Scrollable Canvas Setup ---
    canvas = tk.Canvas(root, bg="black")
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg="black")

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    thumb_images = []

    for idx, cbz_path in enumerate(cbz_files):
        chapter_name = os.path.splitext(os.path.basename(cbz_path))[0]
        img = get_first_image(cbz_path)
        if img is not None:
            img.thumbnail(thumb_size, Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
        else:
            tk_img = ImageTk.PhotoImage(Image.new("RGB", thumb_size, "gray"))
        thumb_images.append(tk_img)

        btn = tk.Button(scroll_frame, image=tk_img, command=lambda i=idx: open_reader(i, cbz_files, root))
        btn.grid(row=idx // columns * 2, column=idx % columns, padx=20, pady=10)
        lbl = tk.Label(scroll_frame, text=chapter_name, fg="white", bg="black", font=("Arial", 14))
        lbl.grid(row=idx // columns * 2 + 1, column=idx % columns, padx=20, pady=(0, 20))

    # Enable mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def back_to_folders(event=None):
        root.destroy()
        show_folder_selection_screen(os.path.dirname(folder))

    root.bind("<Escape>", back_to_folders)
    root.mainloop()

def set_fullscreen(win):
    win.attributes("-fullscreen", True)
    win.focus_force()
    win.attributes("-topmost", True)
    win.attributes("-topmost", False)
    # win.overrideredirect(True)  # Keep this commented out!

# At the end of your file, start with the main library folder:
if __name__ == "__main__":
    show_folder_selection_screen(library_folder, first=True)
