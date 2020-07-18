import sys, subprocess
import re

def run_dot(dot):
    from IPython.display import SVG
    dot = dot.encode('utf8')
    process = subprocess.Popen(['dot', '-Tsvg'], 
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
    out, err = process.communicate(dot)
    if err:
        raise Exception(err)
    out = out.decode('utf8')
    out = re.sub(r'<title>.*?</title>', '', out)
    return SVG(out)
