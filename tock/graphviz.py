import sys, subprocess
import re

def run_dot(dot, format="svg"):
    if format not in ["svg", "dot"]:
        raise ValueError(f"invalid format 'format'")
    dot = dot.encode('utf8')
    process = subprocess.Popen(['dot', '-T'+format], 
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
    out, err = process.communicate(dot)
    if err:
        raise Exception(err)
    out = out.decode('utf8')
    if format == "svg":
        from IPython.display import SVG
        out = re.sub(r'<title>.*?</title>', '', out)
        return SVG(out)
    elif format == "dot":
        return out
