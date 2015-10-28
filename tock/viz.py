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

    display(Javascript('require.config({waitSeconds: 10, paths: {viz: "//github.com/mdaines/viz.js/releases/download/v1.2.0/viz"}, shim: {viz: {exports: "Viz"}}}); require.undef("viz")'))

    def viz(dot):
        dot = dot.replace("\\", r"\\")
        dot = dot.replace("\"", r"\"")
        dot = dot.replace("\n", r"\n")
        return Javascript('require(["viz"], function (Viz) {var div = $("<div>"); element.append(div); div.append(Viz("%s", {format: "svg", engine: "dot"})); var svg = div.find("svg"); div.css("width", svg.attr("width")); div.css("height", svg.attr("height")); })' % dot)

