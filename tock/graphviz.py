import sys, subprocess
import six

impl = None

def guess_impl():
    """Try to guess best way to run GraphViz."""
    from IPython.display import display, Javascript
    try:
        run_dot_dot("digraph { foo -> bar; }")
        return "dot"
    except:
        pass

    try:
        display(Javascript('require.config({'
                           # increase timeout (it's a large script)
                           '  waitSeconds: 10,'
                           # location of script
                           '  paths: {viz: "//github.com/mdaines/viz.js/releases/download/v1.2.1/viz"},'
                           # tells require.js what symbols to take
                           '  shim: {run_dot: {exports: "Viz"}}});'
                           # clear any old module in case there was an error
                           'require.undef("run_dot")'))
        return "js"
    except:
        pass

    raise RuntimeError("couldn't figure out how to run GraphViz")

def run_dot(dot):
    """Converts a graph in DOT format into an IPython displayable object."""
    global impl
    if impl is None:
        impl = guess_impl()
    if impl == "dot":
        return run_dot_dot(dot)
    elif impl == "js":
        return run_dot_js(dot)
    else:
        raise ValueError("unknown implementation {}".format(impl))

def run_dot_dot(dot):
    from IPython.display import SVG
    if isinstance(dot, six.text_type):
        dot = dot.encode('utf8')
    process = subprocess.Popen(['dot', '-Tsvg'], 
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
    out, err = process.communicate(dot)
    if err:
        raise Exception(err)
    return SVG(out.decode('utf8'))

def run_dot_js(dot):
    from IPython.display import Javascript
    dot = dot.replace("\\", r"\\")
    dot = dot.replace("\"", r"\"")
    dot = dot.replace("\n", r"\n")
    return Javascript('require(["viz"], function (Viz) {'
                      # wrap the SVG inside a div
                      '  var div = $("<div>");'
                      '  element.append(div);'
                      # generate the SVG
                      '  div.append(Viz("%s"));'
                      # set the div's size to match the SVG
                      '  var svg = div.find("svg");'
                      '  div.css("width", svg.attr("width"));'
                      '  div.css("height", svg.attr("height"));'
                      '})' % dot)
