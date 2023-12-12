from PIL import Image
from pix2tex.cli import LatexOCR

img = Image.open(r'img_teste\trash\screenshot.png')
model = LatexOCR()
print(f"${model(img)}$")