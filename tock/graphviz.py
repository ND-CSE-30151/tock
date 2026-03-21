import sys, subprocess
import re

def _run_dot_text(dot, format):
    if format not in ["svg", "dot"]:
        raise ValueError(f"invalid format 'format'")
    dot = dot.encode('utf8')
    try:
        process = subprocess.Popen(['dot', '-T'+format], 
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
    except FileNotFoundError as e:
        raise FileNotFoundError("Graphviz's `dot` executable is required. Install Graphviz from https://graphviz.org/download/.") from e
    out, err = process.communicate(dot)
    if err:
        raise Exception(err)
    return out.decode('utf8')

def dot_to_svg_text(dot):
    out = _run_dot_text(dot, "svg")
    return re.sub(r'<title>.*?</title>', '', out)

def run_dot(dot, format="svg"):
    out = _run_dot_text(dot, format)
    if format == "svg":
        from IPython.display import SVG
        return SVG(re.sub(r'<title>.*?</title>', '', out))
    elif format == "dot":
        return out
