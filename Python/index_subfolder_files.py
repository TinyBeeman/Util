import os
import sys
import argparse


def str_empty(s):
	return (s == "" or s.isspace())

def extract_wildcard_value(filename, prefix, postfix):
    # Extract the wildcard value from the filename
    return filename.split(prefix)[1].split(postfix)[0].replace("_", " ")

def main(root_directory, prefix, postfix, filepath):
    # Initialize a dictionary to store folder names and corresponding wildcard values
    category_dict = {}
    wildcard_dict = {}

    # Iterate through all subfolders and files
    for folder, _, files in os.walk(root_directory):
        for filename in files:
            if prefix in filename and postfix in filename and filename.endswith(".png"):
                wildcard_value = extract_wildcard_value(filename, prefix, postfix)

                # Add the wildcard value to the corresponding folder
                folder_name = os.path.basename(folder)
                if folder_name not in category_dict:
                    category_dict[folder_name] = set()
                category_dict[folder_name].add(wildcard_value)

                # Add the folder name to the wildcard value
                if wildcard_value not in wildcard_dict:
                    wildcard_dict[wildcard_value] = set()
                wildcard_dict[wildcard_value].add(folder_name)

    
    category_dict = {k: category_dict[k] for k in sorted(category_dict)}
    wildcard_dict = {k: wildcard_dict[k] for k in sorted(wildcard_dict)}

    output = ""
    for folder, wvs in category_dict.items():
        output += f"{folder}\n"
        for wv in sorted(wvs):
            output += (f"\t{wv}\n")
    output += "\n"
    for wv, cats in wildcard_dict.items():
        output += f"{wv}\n"
        for cat in sorted(cats):
            output += (f"\t{cat}\n")

    if (str_empty(filepath)):
        print(output)
    else:
        # Write the folder names and artist names to category_dict.txt
        with open(filepath, "w") as outfile:
            outfile.write(output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract artist names from filenames and save to category_dict.txt")
    parser.add_argument("--root", required=False, help="Root directory containing subfolders and files", default=os.getcwd())
    parser.add_argument("--prefix", required=False, help="The string to appear before the wildcard", default="((artwork_by_")
    parser.add_argument("--postfix", required=False, help="The string to appear before the wildcard", default="))")
    parser.add_argument("--file", required=False, help="The filepath to output to. If not set, outputs to stdout", default="")
    args = parser.parse_args()

    main(args.root, args.prefix, args.postfix, args.file)
