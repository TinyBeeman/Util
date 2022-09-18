# generate_gallery: Simple script to generate an HTML from subfolders full of images.

import argparse
from os import getcwd, listdir, mkdir, rename
from os.path import isfile, join, splitext, join, exists, isdir
import sys


supported_exts = [ ".png", ".gif", ".jpg", ".jpeg"]

def ext_supported(ext: str) -> bool:
  return ext.casefold() in supported_exts

def main():
  parser = argparse.ArgumentParser(prog=sys.argv[0], description="This command generates an HTML file that lists all PNGs or JPGs one level deep")
  parser.add_argument('--path', action="store", dest="path", type=str, required=False, default="")
  parser.add_argument('--h,-h,--?,-?', action="store_true", dest="help", default=False, required=False)
  args = parser.parse_args()

  path = args.path
  if (len(path) == 0):
    path = sys.path = getcwd()
  elif (not isdir(path)):
    print(path + " is not a valid folder.")
    sys.exit(2)
  
  subfolders = [ f for f in listdir(path) if isdir(join(path, f))]
  subfolders.sort()

  test = True

  jobs = []
  for sf in subfolders:
    fullsub = join(path, sf)
    files = [ f for f in listdir(fullsub) if (isfile(join(fullsub, f)) and ext_supported(splitext(f)[1])) ]
    jobs.append((sf, files))

  html_header = """<html>
  <head>
  <style>

    * { box-sizing: border-box; }
  body { background: #eee; }

  H3.token {
    text-align: center;
  }

  .gallery {
    display: grid;
    grid-gap: 10px;
    grid-template-columns: repeat(auto-fit, 186px);

    max-width: 1000px;
    margin: 0 auto;
  }

  .gallery img {
    padding: 10px;
    max-height: 300;
    max-width: 300;
    border: 1px solid #ddd;
    background: #fff;
    object-fit: contain;
    position: relative;
  }

  @media only screen and (max-width: 600px) {
    .gallery {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  .gallery img:focus {
    z-index: 9;
    transform: scale(2);
    transition: transform ease 0.5s;
  }
  </style>
  </head>
  <body>
  """


  html_footer = "</body></html>\n"
  html_body = ""

  for tlist in jobs:
    token = tlist[0]
    files = tlist[1]
    html_body += f"\n<H3 class=\"token\"><span>{token}</span></H3></div>\n<div class=\"gallery\">"

    for i in files:
      html_body += f"<img src=\"{token}/{i}\" tabindex=\"0\" />"

    html_body += "</div>"

  html_file = open(join(path, "gallery.html"), "w")
  html_file.write(html_header + html_body + html_footer)
  html_file.close()


if __name__ == "__main__":
    main()


