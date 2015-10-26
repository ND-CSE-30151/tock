class Store:
    def _repr_html_(self, graphviz=False):
        # Graphviz has its own limited version of HTML which forces
        # us to use tables for everything

        if graphviz:
            TABLE = '<table border="0">'
            TR = '<tr>'
            TD = '<td>'
            TD_head = '<td bgcolor="#c0e0ff">'
        else:
            TABLE = '<table style="border: none; display: inline-block;">'
            TR = '<tr style="border: none;">'
            TD = '<td style="border: none;">'
            TD_head = '<td style="border: none; background: #c0e0ff;">'

        result = [TABLE+TR]
        if self.position == -1:
            result.append(TD_head + '&nbsp;</td>')
        for i, x in enumerate(self.values):
            if i == self.position and not self.single:
                result.append(TD_head + '%s</td>' % x)
            else:
                result.append(TD + '%s</td>' % x)
        if self.position == len(self.values):
            result.append(TD_head + '&nbsp;</td>')
        result.append('</tr></table>')
        return "".join(result)


    def _repr_ansi_(self):

        def head_color(s):
            return "\033[48;5;189m" + s + "\033[0m"
        def cell_color(s):
            return "\033[48;5;188m" + s + "\033[0m"

        values = self.values
        position = self.position

        s1 = []
        s2 = []
        s3 = []
        if self.position == -1:
            s1.append(head_color("   "))
            s2.append(head_color("   "))
            s3.append(head_color("   "))
        for i, x in enumerate(values):
            if i == position and not self.single:
                color = head_color
            else:
                color = cell_color
            sx = "  %s  " % x
            s1.append(color(" " * len(sx)) + " ")
            s2.append(color(sx) + " ")
            s3.append(color(" " * len(sx)) + " ")
        if self.position == len(self.values):
            s1.append(head_color("   "))
            s2.append(head_color("   "))
            s3.append(head_color("   "))
        s1.append("\n")
        s2.append("\n")
        s3.append("\n")
        return "".join(s1+s2+s3)

