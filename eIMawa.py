import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk, scrolledtext, Tk, PhotoImage
from PIL import Image, ImageTk
import sys
import os
import threading
from psd_tools import PSDImage
import base64
import tempfile


if getattr(sys, 'frozen', False):
    # Running in a bundled executable
    application_path = sys._MEIPASS
else:
    # Running in a normal Python environment
    application_path = os.path.dirname(os.path.abspath(__file__))

logo_path = os.path.join(application_path, 'logoTop.png')
icon_path = os.path.join(application_path,'your_icon.ico')



original_image = Image.open(logo_path)

print(f"Application Path: {application_path}")
print(f"Logo Path: {logo_path}")

def process_psd(file_path):
    psd = PSDImage.open(file_path)
    # For simplicity, let's convert the PSD to a PIL Image and save it as a PNG
    # You'll need to decide how you want to handle layers and other PSD specifics
    pil_image = psd.compose()
    new_path = file_path.rsplit('.', 1)[0] + '.png'  # Change extension to .png
    pil_image.save(new_path)
    return new_path  # Return the new path for further processing if needed


# Step 1: Define a stop event for thread control
stop_event = threading.Event()


class RedirectText(object):
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')

    def flush(self):  # Needed for file-like interface
        pass

def select_folder():
    folder_path = filedialog.askdirectory()
    return folder_path

def downgrade_images_in_folder(folder_path, max_size_kb, progress_bar):
    output_folder = os.path.join(folder_path, 'downsized')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Output folder created at: {output_folder}")

    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp','.tiff','.tif','.psd'))]
    if not images:
        print("No images found to process.")
        messagebox.showinfo('Error', 'No images found to process.')
        return

    total_images = len(images)
    print(f"Total images to process: {total_images}")

    for index, filename in enumerate(images, start=1):
        if stop_event.is_set():
            print('Process stopped by user.')
            break
        original_path = os.path.join(folder_path, filename)
        if filename.lower().endswith('.psd'):
            # Special handling for PSD files
            try:
                original_path = process_psd(original_path)
                # Update the filename to the new PNG file
                filename = os.path.basename(original_path)
            except Exception as e:
                print(f"Error processing PSD image {filename}: {e}")
                continue  # Skip to the next file
        try:
            new_path = os.path.join(output_folder, filename.rsplit('.', 1)[0] + '_downgraded.' + filename.rsplit('.', 1)[1])

            with Image.open(original_path) as img:
                img_format = img.format
                if os.path.getsize(original_path) > max_size_kb * 1024:
                    quality = 85
                    img.save(new_path, format=img_format, quality=quality)
                    while os.path.getsize(new_path) > max_size_kb * 1024 and quality > 10:
                        quality -= 5
                        img.save(new_path, format=img_format, quality=quality)
                    print(f"Image saved at: {new_path} with quality: {quality}")
                else:
                    # If the image doesn't need to be downgraded, optionally copy it as is or skip
                    print(f"Image does not exceed max size and was not downgraded: {filename}")


        except Exception as e:
            print(f"Error processing image {filename}: {e}")

        update_progress_bar(progress_bar, index, total_images)

    messagebox.showinfo('Complete', 'Images processed successfully')
    progress_bar['value'] = 0
    stop_event.clear()

def update_progress_bar(progress_bar, current, total):
    progress = int((current / total) * 100)
    progress_bar['value'] = progress
    progress_bar.update_idletasks()

def start_downgrading():
    stop_event.clear()
    folder_path = select_folder()
    if folder_path:
        max_size_kb = simpledialog.askinteger("Input", "Maximum image size in MB:", parent=root, minvalue=1, maxvalue=10000) * 1024  # Correctly convert MB to KB for processing
        if max_size_kb:
            threading.Thread(target=downgrade_images_in_folder, args=(folder_path, max_size_kb, progress)).start()

def stop_processing():
    stop_event.set()

root = tk.Tk()
root.title('EIMAWA Image Downgrader')
# Load the image file with Pillow
root.iconbitmap(default=icon_path)

# Convert the Pillow Image object to a Tkinter PhotoImage object
logo = ImageTk.PhotoImage(original_image)
logo_label = ttk.Label(root,image=logo)
logo_label.pack(pady=20)

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
progress.pack(fill=tk.X)

btn_select_folder = tk.Button(frame, text="Select Folder and Start", command=start_downgrading)
btn_select_folder.pack(fill=tk.X, pady=5)

# Add a scrolled text widget to display logs
log_widget = scrolledtext.ScrolledText(root, state='disabled', height=10)
log_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Redirect stdout and stderr
sys.stdout = RedirectText(log_widget)
sys.stderr = RedirectText(log_widget)

btn_stop = tk.Button(frame, text='Stop Processing', command=stop_processing)
btn_stop.pack(fill=tk.X, pady=5)

root.mainloop()
