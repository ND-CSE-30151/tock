### First try to use external dot

try:
    import subprocess
    from IPython.display import SVG

    def viz(dot):
        process = subprocess.Popen(['dot', '-Tsvg'], 
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
        out, err = process.communicate(dot)
        if err:
            raise Exception(err)
        return SVG(out.decode('utf8'))

    viz("digraph { foo -> bar; }")

### But if it doesn't work, download viz.js

except:

    from IPython.display import display, Javascript

    display(Javascript('require.config({'
                       # increase timeout (it's a large script)
                       '  waitSeconds: 10,'
                       # location of script
                       '  paths: {viz: "//github.com/mdaines/viz.js/releases/download/v1.2.0/viz"},'
                       # tells require.js what symbols to take
                       '  shim: {viz: {exports: "Viz"}}});'
                       # clear any old module in case there was an error
                       'require.undef("viz")'))

    def viz(dot):
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

