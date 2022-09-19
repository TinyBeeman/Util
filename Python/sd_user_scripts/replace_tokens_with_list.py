import math
import os
import sys
import traceback
from typing import List

import modules.scripts as scripts
import gradio as gr

from modules.processing import Processed, process_images
from PIL import Image
from modules.shared import opts, cmd_opts, state

class TokenReplacer():
    tokenLists = {}

    def __init__(self, lines: List[str]):
        for l in lines:
            words = [w.strip() for w in l.split(',')]
            token = words.pop(0)
            self.tokenLists[token] = words
    
    def processOneToken(self, token: str, prompt: str) -> List[str]:
        prompts = []
        index = prompt.find(token)
        if (index >= 0):
            for word in self.tokenLists[token]:
                prompts.append(prompt.replace(token, word))
        else:
            # Don't a bunch of duplicate prompts if the token doesn't appear in the string
            prompts.append(prompt)
        return prompts
        
    def createPrompts(self, prompt:str) -> List[str]:
        prompts = [prompt]
        for token in self.tokenLists:
            newPrompts = []
            while (len(prompts) > 0):
                newPrompts.extend(self.processOneToken(token, prompts.pop()))
            prompts.extend(newPrompts)
        return prompts


class Script(scripts.Script):
    def title(self):
        return "Replace prompt tokens with lists"

    def ui(self, is_img2img):
        help_label = gr.HTML(value="<p>Place each list is on a single line which starts with the token to be replaced "
                                 "with each item that follows in a comma-separated list. For example, if your prompt is</p>"
                                 "<pre>medium painting of a pet</pre>"
                                 "<p>you might put the following in the textbox below:</p>"
                                 "<pre>medium, oil, watercolor</pre>"
                                 "<pre>pet, a cat, a dog, three parakeets</pre>"
                                 "<p>This would generate an oil and a watercolor painting of each of the three pets, for six total prompts.</p>",
                                 visible=False)
        prompt_txt = gr.TextArea(label="Prompts", placeholder="*pet*, a cat, a dog, a bear")
        return [help_label, prompt_txt]


def run(self, p, help_label, txt: str):
    lines = [x.strip() for x in txt.splitlines()]
    lines = [x for x in lines if (x.find(',') >= 0)]
    if (len(lines) == 0):
        return

    replacer = TokenReplacer(lines)
    prompts = replacer.createPrompts(p.prompt)

    img_count = len(prompts) * p.n_iter
    batch_count = math.ceil(img_count / p.batch_size)
    loop_count = math.ceil(batch_count / p.n_iter)
    print(f"Will process {img_count} images in {batch_count} batches.")

    p.do_not_save_grid = True

    state.job_count = batch_count

    images = []
    for loop_no in range(loop_count):
        state.job = f"{loop_no + 1} out of {loop_count}"
        p.prompt = prompts[loop_no*p.batch_size:(loop_no+1)*p.batch_size] * p.n_iter
        proc = process_images(p)
        images += proc.images

    return Processed(p, images, p.seed, "")
