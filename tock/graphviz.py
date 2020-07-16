import sys, subprocess

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
    return SVG(out.decode('utf8'))
