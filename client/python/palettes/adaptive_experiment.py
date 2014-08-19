from PIL import Image, ImageDraw
import glob
from colormath.color_objects import *
from colormath.color_conversions import convert_color
from os.path import dirname
 
def get_colors(infile, outfile, numcolors=256, swatchsize=10, resize=150):
 
    image = Image.open(infile)
    image = image.resize((resize, resize))
    result = image.convert('P', palette=Image.ADAPTIVE, colors=numcolors)
    result.putalpha(0)
    colors = result.getcolors(resize*resize)

    hslcolors = map(lambda x: convert_color(sRGBColor(x[1][0], x[1][1], x[1][2], is_upscaled=True), HSLColor), colors)
    hslcolors = sorted(hslcolors, key=lambda c: c.hsl_s)
    hslcolors = sorted(hslcolors, key=lambda c: c.hsl_h)
    hslcolors = map(lambda c: HSLColor(c.hsl_h, 0.5 + 0.5 * c.hsl_s, 0.55 + 0.15 * c.hsl_l), hslcolors)
    hslcolors = map(lambda x: convert_color(x, sRGBColor).get_upscaled_value_tuple(), hslcolors)
 
    # Save colors to file
 
    pal = Image.new('RGB', (swatchsize*numcolors, swatchsize * 20))
    draw = ImageDraw.Draw(pal)
 
    posx = 0
    for col in hslcolors:
        draw.rectangle([posx, 0, posx+swatchsize, swatchsize * 20], fill=col)
        posx = posx + swatchsize
 
    del draw
    pal.save(outfile, "PNG")

    print "palettes.append(%s)" % str(hslcolors)

print "palettes = []"
pwd = dirname(__file__)
for ii, filename in enumerate(glob.glob(pwd + '/images/*.*')):
    get_colors(filename, pwd + "/images/palettes/%d_colors.png" % ii)