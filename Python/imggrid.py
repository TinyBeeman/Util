import os
import PIL
from PIL import Image
import argparse
import re

def allow_file(fname, prefix) -> bool:
    ext_allowed = fname.lower().endswith(('.png', '.jpg', '.jpeg'))
    name_allowed = not fname.lower().startswith(prefix)
    return ( ext_allowed and name_allowed )

                                                                                                                                   

def extract_artist_name(filename):
    # Match the artist name after "_by)_" or "_by_"
    pattern = r"_by\)_|_by_"
    match = re.search(pattern, filename)
    
    if match:
        # Extract the artist name (excluding "_by)_" or "_by_")
        artist_name = filename[match.end():].split(")")[0]
        return artist_name
    else:
        print("Failed to find artist name in " + filename)
        return None

def str_cmp(a, b):
    a = a.lower()
    b = b.lower()
    if (a > b):
        return 1
    elif (a == b):
        return 0
    return -1


def compare_by_artist(a, b):
    artist_a = extract_artist_name(a)
    artist_b = extract_artist_name(b)

    if (artist_a is None or artist_b is None or artist_a == artist_b):
        return str_cmp(a[25:], b[21:])
    else:
        return str_cmp(artist_a, artist_b)

def sort_filenames(image_files, cmp):
    from functools import cmp_to_key
    return sorted(image_files, key=cmp_to_key(cmp))

def create_image_grid(image_folder: str, output_folder: str, cols:int, rows: int, max_per_grid: int, prefix: str, scale: float):
    # Get a list of all image files in the specified folder
    folder_list = os.listdir(image_folder)
    image_files = [f for f in folder_list if (allow_file(f, prefix)) ]

    # Can create custom sort methods via this line and a custom cmp function..    
    # image_files = sort_filenames(image_files, cmp=compare_by_artist)
    
    if max_per_grid <= 0 or max_per_grid > (cols * rows):
        max_per_grid = cols * rows
        pad = 0
    else:
        pad = (cols * rows) - max_per_grid
        
    filecount = len(image_files)

    c_grids = filecount // max_per_grid
    if ((filecount % max_per_grid) != 0):
        c_grids += 1

    # Iterate through the image files, combining every four images into a grid
    for i in range(0, c_grids):
        first_file_index = i * max_per_grid
        print(f"Processing {i} of {c_grids} grids")
        # Create a new blank image for the grid

        imgs = []
        max_w = 1
        max_h = 1
        for r in range(0, rows):
            for c in range(0, cols):
                i_offset = r * cols + c
                if (i_offset < max_per_grid) and ((first_file_index + i_offset) < len(image_files)):
                    img = Image.open(os.path.join(image_folder, image_files[first_file_index + i_offset]))
                    imgs.append(img)
                    max_w = max(max_w, img.width)
                    max_h = max(max_h, img.height)

        grid_w = max_w * cols
        grid_h = max_h * rows
        grid = Image.new('RGB', (grid_w, grid_h))

        for r in range(0, rows):
            for c in range(0, cols):
                i_grid = r * cols + c
                if (i_grid < len(imgs)):
                    x = (i_grid % cols) * max_w
                    y = (i_grid // rows) * max_h
                    print (f"pasting to {x},{y} ({image_files[first_file_index + i_grid]})")
                    grid.paste(imgs[i_grid], (x, y))

        if (scale != 1.0):
            grid = grid.resize((int(grid_w * scale), int(grid_h * scale)), Image.BICUBIC)
        
        grid_filename = f"{prefix}{image_files[first_file_index]}"
        grid.save(os.path.join(output_folder, grid_filename))
        print(f"Saved {grid_filename}")
        for img in imgs:
            img.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract artist names from filenames and save to category_dict.txt")
    parser.add_argument("--input", required=False, type=str, help="Firectory containing images", default=os.getcwd())
    parser.add_argument("--output", required=False, type=str, help="Directory to store output files", default=os.getcwd())
    parser.add_argument("--prefix", required=False, type=str, help="Prefix to prepend to output filenames", default="grid_")
    parser.add_argument("--cols", type=int, required=False, help="How many columns wide is the grid", default="2")
    parser.add_argument("--rows", type=int, required=False, help="How many rows tall is the grid", default="2")
    parser.add_argument("--max", type=int, required=False, help="If specified, will limit the grids to the specified images and pad the rest with blanks.", default="0")
    parser.add_argument("--scale", type=float, required=False, help="Scale the grid by this multiplier", default=1.0)
    args = parser.parse_args()

    create_image_grid(args.input, args.output, args.cols, args.rows, args.max, args.prefix, args.scale)
