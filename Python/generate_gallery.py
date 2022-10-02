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
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.1/jquery.min.js"></script>
  <style>

    * { box-sizing: border-box; }
  body { background: #eee; }

  .center {
    text-align: center;
  }

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
    transform: scale(3);
    transition: transform ease 0.5s;
  }
  </style>
  </head>
  <body>

  """


  html_footer = """
  <script id="rendered-js" >

	var g_data = null;
	
	function filter(search_txt) {
		var search_txt_lower = search_txt.toLowerCase().trim();
		var gallery_root = $("#gallery_root");
		gallery_root.empty();
      	for (var token in g_data) {
			if (search_txt.length > 0 && !token.toLowerCase().includes(search_txt_lower))
				continue;
			var newDiv = $( '<div class="header"><H3 class="token"><span>' + token  + '</span></H3></div>' );
			var newGallery = $( '<div class="gallery"></div>' );
			rgImages = g_data[token];
			for (var k in rgImages)
			{
				imgPath = rgImages[k];
				newGallery.append($( `<img class="gallery_img" loading="lazy" src="${token}/${imgPath}" tabindex="0" />` ));
			}
			gallery_root.append(newDiv);
			gallery_root.append(newGallery);
      }
	}

    document.addEventListener("DOMContentLoaded", function() {
      var json = $("#img-data").attr("value");
      g_data = JSON.parse(json);
	  filter("");

	  $("#filter_btn").click(function() {
		filter($("#search_box").val());
	  });

	  $("#clear_btn").click(function() {
		filter("");
	  });
    }
  	);
  </script>
  </body>
  </html>
  """
  html_body = """<div id="root">
                  <div class="search_controls center">
                    <input id="search_box" type="text"/><button id="clear_btn">X</button><button id="filter_btn">Filter</button>
                  </div>
                  <div id="gallery_root">
                  </div>"""

  json_tag_start = """<data class="json-data" id="img-data" value='""" + "\n{"
  json_tag_body = ""
  json_tag_end = "\n}'/>"

  first_job = True;
  for tlist in jobs:
    token = tlist[0]
    files = tlist[1]

    if (first_job):
      json_tag_body += "\n\t\"" + token + "\": ["
      first_job = False
    else:
      json_tag_body += ",\n\t\"" + token + "\": ["

    # html_body += f"\n<H3 class=\"token\"><span>{token}</span></H3></div>\n<div class=\"gallery\">"
    first_file = True
    for iFile in files:
      if (first_file):
        json_tag_body += "\n\t\t\"" + iFile + "\""
        first_file = False
      else:
        json_tag_body += ",\n\t\t\"" + iFile + "\""

    json_tag_body += "\n\t]"

    #html_body += f"<img class=\"lazy\" data-src=\"{token}/{i}\" tabindex=\"0\" />"

  html_body += json_tag_start + json_tag_body + json_tag_end;

  html_body += "</div>" # end of root div

  html_file = open(join(path, "gallery.html"), "w")
  html_file.write(html_header + html_body + html_footer)
  html_file.close()


if __name__ == "__main__":
    main()


