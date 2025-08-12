import os

MAX_PATH_LENGTH = 260  # Windows max path length
MAX_FILENAME_LENGTH = 258  # max filename length to avoid issues

def clean_filename(filename: str) -> str:
    # Remove underscores and hyphens
    cleaned = filename.replace('_', '').replace('-', '')
    # If filename is too long, cut it
    if len(cleaned) > MAX_FILENAME_LENGTH:
        # Preserve the file extension
        if '.' in cleaned:
            base, ext = cleaned.rsplit('.', 1)
            base = base[:MAX_FILENAME_LENGTH - len(ext) - 1]
            cleaned = f"{base}.{ext}"
        else:
            cleaned = cleaned[:MAX_FILENAME_LENGTH]
    return cleaned

def shorten_long_paths(root_dir: str):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if len(full_path) > MAX_PATH_LENGTH:
                new_filename = clean_filename(filename)
                if new_filename != filename:
                    new_full_path = os.path.join(dirpath, new_filename)
                    # Check if new file name already exists to avoid overwriting
                    if not os.path.exists(new_full_path):
                        print(f"Renaming:\n{full_path}\n->\n{new_full_path}\n")
                        os.rename(full_path, new_full_path)
                    else:
                        print(f"Skipped renaming {full_path} because {new_full_path} exists.")
                else:
                    print(f"Filename clean-up did not shorten: {filename}")

if __name__ == "__main__":
    root_folder = r''  # change this to your project root folder if needed
    shorten_long_paths(root_folder)
