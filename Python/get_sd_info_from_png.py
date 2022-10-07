import re
import argparse
from PIL import Image, PngImagePlugin
from os import getcwd, listdir, mkdir, rename
from os.path import isfile, join, splitext, join, exists, isdir
import sys
import html

re_param_code = r"\s*([\w ]+):\s*([^,]+)(?:,|$)"
re_param = re.compile(re_param_code)
re_params = re.compile(r"^(?:" + re_param_code + "){3,}$")
re_imagesize = re.compile(r"^(\d+)x(\d+)$")


# parses generation parameters string, the one you see in text field under the picture in UI:
# girl with an artist's beret, determined, blue eyes, desert scene, computer monitors, heavy makeup, by Alphonse Mucha and Charlie Bowater, ((eyeshadow)), (coquettish), detailed, intricate
# Negative prompt: ugly, fat, obese, chubby, (((deformed))), [blurry], bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), messy drawing
# Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 965400086, Size: 512x512, Model hash: 45dee52b
#    returns a dict with field values
def parse_generation_parameters(x: str):

    res = {}

    prompt = ""
    negative_prompt = ""

    done_with_prompt = False

    *lines, lastline = x.strip().split("\n")
    if not re_params.match(lastline):
        lines.append(lastline)
        lastline = ''

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("Negative prompt:"):
            done_with_prompt = True
            line = line[16:].strip()

        if done_with_prompt:
            negative_prompt += ("" if negative_prompt == "" else "\n") + line
        else:
            prompt += ("" if prompt == "" else "\n") + line

    if len(prompt) > 0:
        res["Prompt"] = prompt

    if len(negative_prompt) > 0:
        res["Negative prompt"] = negative_prompt

    for k, v in re_param.findall(lastline):
        m = re_imagesize.match(v)
        if m is not None:
            res[k+"-1"] = m.group(1)
            res[k+"-2"] = m.group(2)
        else:
            res[k] = v

    return res

class SDRenderInfo:
	def __init__ (self):
		self.m_prompt = ""
		self.m_neg_prompt = ""
		self.m_steps = 0
		self.m_sampler = ""
		self.m_cfg = 0.0
		self.m_seed = 0
		self.m_width = 0
		self.m_height = 0

	def init_from_params(self, params):
		self.m_prompt = params["Prompt"]
		self.m_neg_prompt = params["Negative prompt"]
		self.m_steps = params["Steps"]
		self.m_sampler = params["Sampler"]
		self.m_cfg = params["CFG scale"]
		self.m_seed = params["Seed"]
		self.m_width = params["Size-1"]
		self.m_height = params["Size-2"]

	def init_from_image(self, image):
		param_str = image.text["parameters"]
		param_dict = parse_generation_parameters(param_str)
		self.init_from_params(param_dict)

	def describe(self):
		output = "Prompt: " + self.m_prompt + "\n"
		output += "Negative prompt: " + self.m_neg_prompt + "\n"
		output += "Steps: " + self.m_steps + "\n"
		output += "Sampler: " + self.m_sampler + "\n"
		output += "CFG scale: " + self.m_cfg + "\n"
		output += "Seed: " + self.m_seed + "\n"
		output += "Width: " + self.m_width + "\n"
		output += "Height: " + self.m_height + "\n"
		return output

	def get_prompt(self):
		return self.m_prompt
	def get_neg_prompt(self):
		return self.m_neg_prompt
	def get_steps(self):
		return self.m_steps
	def get_sampler(self):
		return self.m_sampler
	def get_cfg(self):
		return self.m_cfg
	def get_seed(self):
		return self.m_seed
	def get_width(self):
		return self.m_width
	def get_height(self):
		return self.m_height

def main():
	parser = argparse.ArgumentParser(prog=sys.argv[0], description="Get PNG Info Test")
	parser.add_argument('--image', action="store", dest="image", type=str, required=False, default="")
	parser.add_argument('--h,-h,--?,-?', action="store_true", dest="help", default=False, required=False)
	args = parser.parse_args()

	image_file = args.image
	
	if (not isfile(image_file)):
		print(image_file + " is not a valid file.")
		sys.exit(2)

	image = Image.open(image_file)
	ri = SDRenderInfo()
	ri.init_from_image(image)
	print (ri.describe())


if __name__ == "__main__":
	main()