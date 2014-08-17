import glob
from PIL import Image
import struct
from itertools import islice, imap
from colormath.color_objects import *
from colormath.color_conversions import convert_color

html = open("index.html", "w")


for filename in glob.glob('./images/*'):
    html.write("<div>")
    html.write("<img width=\"150px\" src=\"" + filename + "\">")
    print filename


    im = Image.open(filename)
    colordata = im.getcolors(im.size[0]*im.size[1])
    hslcolordata = map(lambda x: (x[0], convert_color(sRGBColor(*(x[1]), is_upscaled=True), HSLColor)), colordata)
    hslcolordata = reversed(sorted(hslcolordata, key=lambda tup: tup[0]))
    hslcolordata = islice(hslcolordata, 0, 2048)
    hslcolordata = sorted(hslcolordata, key=lambda tup: abs(0.65 - tup[1].hsl_l))
    hslcolordata = islice(hslcolordata, 0, 256)
    hslcolordata = reversed(sorted(hslcolordata, key=lambda tup: tup[1].hsl_s))
    hslcolordata = reversed(sorted(hslcolordata, key=lambda tup: tup[1].hsl_h))
    colors = zip(*hslcolordata)[1]

    for color in colors:
        print color
        rgb = convert_color(color, sRGBColor).get_upscaled_value_tuple()
        hex_value = "#" + struct.pack('BBB',*rgb).encode('hex')

        html.write("""
            <div style="background: {color}; width: 500px; height: 50px; color: white;">
            color
            </div>
        """.format(color=hex_value))
        html.write("</div>")

    