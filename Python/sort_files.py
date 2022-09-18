from os import listdir, mkdir, rename, getcwd
from os.path import isfile, join, splitext, join, exists, isdir
import argparse
import sys
import regex as re

# Example Pattern:
# (?:[^-]+-){2}(?P<token>[^-,]+)


def help():
	print()

def main():
	parser = argparse.ArgumentParser(prog=sys.argv[0], description="This command moves all files that match a certain format into their respective folder")
	parser.add_argument('--path', action="store", dest="path", type=str, required=False, default="")
	parser.add_argument('--pattern', action="store", dest="pattern", type=str, required=True, help="The pattern must return a named capture named \"token\". Ex: (?:[^-]+-){2}(?P<token>[^-,]+)")
	parser.add_argument('--test', action="store_true", dest="test", default=False, required=False)
	parser.add_argument('--h,-h,--?,-?', action="store_true", dest="help", default=False, required=False)
	parser.add_argument('--v,', action="store_true", dest="verbose", default=False, required=False)
	args = parser.parse_args()

	if (args.help):
		parser.print_help()
		sys.exit(0)

	path = args.path
	if (len(path) == 0):
		path = sys.path = getcwd()
	elif (not isdir(path)):
		print(path + " is not a valid folder.")
		sys.exit(2)
	pattern = args.pattern
	verbose = args.verbose
	test = args.test

	nameParser = re.compile(pattern)
	
	onlypngs = [ f for f in listdir(path) if (isfile(join(path, f)) and splitext(f)[1].casefold() == ".png") ]

	jobs = []
	for p in onlypngs:
		match = nameParser.search(p)
		if not match:
			if (verbose):
				print("Failed to find token in " + p)
			continue
		token = match.group('token')
		if (len(token) > 0):
			jobs.append((p, token))

	for ft in jobs:
		oldFile = join(path, ft[0])
		newPath = join(path, ft[1])
		newFile = join(newPath, ft[0])
		if (not exists(newPath)):
			if (verbose or test):
				print(f"mkdir({newPath})")
			if not test:
				mkdir(newPath)
		if (verbose or test):
			print(f"rename({oldFile}, {newFile}")
		if not test:
			rename(oldFile, newFile)


if __name__ == "__main__":
    main()