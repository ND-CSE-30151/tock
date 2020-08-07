import xml.sax.saxutils

class Tree:
    def __init__(self, label, children=None):
        self.label = label
        self.children = children or []

    def svg(self):
        node_width = 32
        node_height = 16
        sister_distance = 64
        level_distance = 32
        raise_label = 3

        def height(node):
            if len(node.children) == 0:
                return 0
            else:
                return 1+max(height(child) for child in node.children)
        h = height(self)
                
        ret = []
        ret.append(f'<svg height="{h*level_distance+node_height}">\n'
                   '  <style>\n'
                   '    .nonterminal {\n'
                   f'      font: {node_height}px serif;\n'
                   '      text-anchor: middle;\n'
                   '    }\n'
                   '    .terminal {\n'
                   f'      font: {node_height}px monospace;\n'
                   '      text-anchor: middle;\n'
                   '    }\n'
                   '  </style>\n')
        def draw(node, x, y):
            cls = 'nonterminal' if len(node.children) > 0 else 'terminal'
            label = xml.sax.saxutils.escape(node.label)
            if len(node.children) > 0:
                cxs = []
                for child in node.children:
                    cx, x = draw(child, x, y+level_distance)
                    cxs.append(cx)
                nx = (cxs[0] + cxs[-1])/2
                for cx in cxs:
                    ret.append(f'<line x1="{nx}" y1="{y}" x2="{cx}" y2="{y+level_distance-node_height}" style="stroke:rgb(0,0,0);stroke-width:2"/>\n')
            else:
                nx = x
                x += sister_distance
            ret.append(f'<text x="{nx}" y="{y-raise_label}" class="{cls}">{label}</text>\n')
            return nx, x
        draw(self, node_width/2, node_height)
        ret.append('</svg>\n')
        
        return ''.join(ret)

    def _repr_svg_(self):
        return self.svg()
