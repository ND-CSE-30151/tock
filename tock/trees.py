import xml.sax.saxutils

class Tree:
    def __init__(self, label, children=None):
        self.label = label
        self.children = children or []

    def svg(self):
        node_width = 9 # per character, approximate
        node_height = 14
        node_depth = 4
        sister_distance = 14
        level_distance = 14

        pos = {}
        def layout(node, x1, y1):
            """Layout the tree rooted at node, with upper-left corner at x1, y1.
            
            Returns: the lower-right corner.
            """
            if len(node.children) > 1:
                x2, y2 = x1, y1
                cy1 = y1 + node_height+node_depth+level_distance
                for ci, child in enumerate(node.children):
                    if ci > 0:
                        x2 += sister_distance
                    x2, cy2 = layout(child, x2, cy1)
                    y2 = max(y2, cy2)
                nx = (pos[node.children[0]][0] + pos[node.children[-1]][0])/2
            elif len(node.children) == 1:
                child = node.children[0]
                cx1 = x1
                cy1 = y1 + node_height+node_depth+level_distance
                if len(node.label) > len(child.label):
                    cx1 += (len(node.label) - len(child.label)) * node_width / 2
                x2, y2 = layout(child, cx1, cy1)
                nx = pos[child][0]
            else:
                nx = x1 + node_width*len(node.label)/2
                x2 = x1 + node_width*len(node.label)
                y2 = y1 + node_height+node_depth
            pos[node] = (nx, y1+node_height)
            return x2, y2
        x2, y2 = layout(self, 0, 0)
                
        ret = []
        ret.append(f'<svg width="{x2}" height="{y2}">\n'
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
        
        for node in pos:
            cls = 'nonterminal' if len(node.children) > 0 else 'terminal'
            label = xml.sax.saxutils.escape(node.label)
            nx, ny = pos[node]
            ret.append(f'<text x="{nx}" y="{ny}" class="{cls}">{label}</text>\n')
            if len(node.children) > 0:
                for child in node.children:
                    cx, cy = pos[child]
                    ret.append(f'<line x1="{nx}" y1="{ny+node_depth}" x2="{cx}" y2="{cy-node_height}" style="stroke:rgb(0,0,0);stroke-width:1"/>\n')
        ret.append('</svg>\n')

        return ''.join(ret)

    def _repr_svg_(self):
        return self.svg()
