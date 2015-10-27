### external dot

import subprocess

def viz_sh(dot):
    process = subprocess.Popen(['dot', '-Tsvg'], 
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
    out, err = process.communicate(dot)
    if err:
        raise Exception(err)
    return SVG(out.decode('utf8'))

### viz.js

try:
    from IPython.display import display, Javascript, SVG
except ImportError:
    pass

# Due to a bug in require.js, this doesn't work with IPython 3.1
display(Javascript('require.config({baseUrl: "/files", shim: {viz: {exports: "Viz"}}})'))

def viz_js(dot):
    dot = dot.replace("\\", r"\\")
    dot = dot.replace("\"", r"\"")
    dot = dot.replace("\n", r"\n")
    return Javascript('require(["viz"], function (Viz) {var div = $("<div>"); element.append(div); div.append(Viz("%s", {format: "svg", engine: "dot"})); var svg = div.find("svg"); div.css("width", svg.attr("width")); div.css("height", svg.attr("height")); })' % dot)

viz = viz_js
#viz = viz_sh
