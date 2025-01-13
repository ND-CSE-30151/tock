/*
 This code is a heavily modified version of Finite State Machine
 Designer (http://madebyevan.com/fsm/), made available under the
 MIT License (see below).
  
 Copyright (c) 2010 Evan Wallace

 Permission is hereby granted, free of charge, to any person
 obtaining a copy of this software and associated documentation
 files (the "Software"), to deal in the Software without
 restriction, including without limitation the rights to use,
 copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the
 Software is furnished to do so, subject to the following
 conditions:

 The above copyright notice and this permission notice shall be
 included in all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 OTHER DEALINGS IN THE SOFTWARE.
*/

/* 
   Bugs:
   
   - In Jupyter, if the canvas is too wide, a horizontal scrollbar
     appears, which makes the output too high, so a vertical scrollbar
     appears too.

*/

/* Geometry */

function boxContainsPoint(x1, y1, x2, y2, x, y) {
    return (x >= x1-hitTargetPadding && x <= x2+hitTargetPadding &&
            y >= y1-hitTargetPadding && y <= y2+hitTargetPadding);
}

// Transform c such that a is at origin and b is on positive x-axis
function transformToLine(ax, ay, bx, by, cx, cy) {
    var dx = bx - ax;
    var dy = by - ay;
    var length = Math.hypot(dx, dy);
    return {'bx': length,
            'cx': (dx * (cx - ax) + dy * (cy - ay)) / length,
            'cy': (dx * (cy - ay) - dy * (cx - ax)) / length};
}

function principalAngle(theta) {
    theta = theta % (2*Math.PI);
    if (theta < -Math.PI) theta += 2*Math.PI;
    if (theta > Math.PI) theta -= 2*Math.PI;
    return theta;
}

function snapAngle(angle, r) {
    // snap to 90 degrees
    var snap = Math.round(angle / (Math.PI / 2)) * (Math.PI / 2);
    if (Math.abs(angle - snap) * r <= snapToPadding) angle = snap;
    return principalAngle(angle);
}

function det(a, b, c, d, e, f, g, h, i) {
    return a*e*i + b*f*g + c*d*h - a*f*h - b*d*i - c*e*g;
}

function circleFromThreePoints(x1, y1, x2, y2, x3, y3) {
    /*
      Solve for x, y, and z = r²-x²-y² using Cramer's Rule:
        (x1-x)² + (y1-y)² = r²
        (x2-x)² + (y2-y)² = r² 
        (x3-x)² + (y3-y)² = r²
     */
    var a = det(x1, y1, 1, x2, y2, 1, x3, y3, 1);
    var bx = -det(x1*x1 + y1*y1, y1, 1, x2*x2 + y2*y2, y2, 1, x3*x3 + y3*y3, y3, 1);
    var by = det(x1*x1 + y1*y1, x1, 1, x2*x2 + y2*y2, x2, 1, x3*x3 + y3*y3, x3, 1);
    var c = -det(x1*x1 + y1*y1, x1, y1, x2*x2 + y2*y2, x2, y2, x3*x3 + y3*y3, x3, y3);
    var circle = {
        'x': -bx / (2*a),
        'y': -by / (2*a),
        'radius': Math.sqrt(bx*bx + by*by - 4*a*c) / (2*Math.abs(a))
    };
    return circle;
}

function intersectCircleLine(ax, ay, ar, la, lb, lc) {
    /* Intersection of
       - The circle centered at (ax, ay) with radius ar
       - The line la * x + lb * y = lc
    */

    // Recenter at (ax, ay)
    lc -= la*ax + lb*ay;

    // Normalize so (la, lb) is a unit vector and lc is distance to origin
    h = Math.hypot(la, lb);
    la /= h; lb /= h; lc /= h;

    if (Math.abs(lc) > ar)
        return [];
    else if (Math.abs(lc) === ar)
        return [{'x': ax + la*lc, 'y': ay + lb*lc}];
    else {
        d = Math.sqrt(ar**2-lc**2);
        return [{'x': ax + la*lc - lb*d, 'y': ay + lb*lc + la*d},
                {'x': ax + la*lc + lb*d, 'y': ay + lb*lc - la*d}];
    }
}

function intersectCircles(x1, y1, r1, x2, y2, r2) {
    var d = Math.hypot(x2-x1, y2-y1);
    var xu = (x2-x1)/d; // unit vector from (x1,y1) to (x2,y2)
    var yu = (y2-y1)/d;
    if (d > r1+r2 || d < Math.abs(r1-r2))
        return [];
    var d1 = (d**2 + r1**2 - r2**2)/(2*d); // from (x1,y1) to midpoint
    if (d == r1+r2)
        return [{'x': x1+d1*xu, 'y': y1+d1*yu}];
    var a = Math.sqrt(r1**2-d1**2); // from midpoint to intersections
    return [{'x': x1+d1*xu - a*yu, 'y': y1+d1*yu + a*xu},
            {'x': x1+d1*xu + a*yu, 'y': y1+d1*yu - a*xu}];
}

/* Model */

function Node(x, y) {
    this.x = x; // center of node
    this.y = y;
    this.mouseOffsetX = 0; // when node is being moved, center relative to mouse
    this.mouseOffsetY = 0;
    this.isAcceptState = false;
    this.text = new Text();
    this.width = Math.max(2*nodeMargin, nodeHeight);
}

Node.prototype.setMouseStart = function(x, y) {
    this.mouseOffsetX = this.x - x;
    this.mouseOffsetY = this.y - y;
};

Node.prototype.setAnchorPoint = function(x, y) {
    this.x = x + this.mouseOffsetX;
    this.y = y + this.mouseOffsetY;

    // Snap to horizontal/vertical alignment with other nodes
    for(var i = 0; i < nodes.length; i++) {
        if(nodes[i] == this) continue;

        if(Math.abs(this.x - nodes[i].x) < snapToPadding)
            this.x = nodes[i].x;
        if(Math.abs(this.y - nodes[i].y) < snapToPadding)
            this.y = nodes[i].y;
    }
};

Node.prototype.draw = function(ctx) {
    // draw the text
    var text = this.text;
    text.draw(ctx, this.x, this.y, nodeFontSize, null, selectedObject == this);
    this.width = Math.max(this.text.width + 2*nodeMargin, nodeHeight);

    // draw the border
    var border = new Path2D();
    border.roundRect(this.x-this.width/2,this.y-nodeHeight/2,
                     this.width, nodeHeight, nodeCornerRadius);
    ctx.stroke(border);
    
    // draw a double border for an accept state
    if (this.isAcceptState) {
        border = new Path2D();
        border.roundRect(this.x-this.width/2-acceptDistance,this.y-nodeHeight/2-acceptDistance,
                         this.width+2*acceptDistance, nodeHeight+2*acceptDistance,
                         nodeCornerRadius+acceptDistance);
        ctx.stroke(border);
    }
    
    this.containsPoint = function (x, y) {
        ctx.save();
        ctx.lineWidth = hitTargetPadding*2;
        var part = null;
        if (ctx.isPointInStroke(border, x, y)) part = "circle";
        else if (text.containsPoint(x, y)) part = "text";
        else if (ctx.isPointInPath(border, x, y)) part = "node";
        ctx.restore();
        return part;
    }
};

Node.prototype.closestPointOnCircle = function(x, y) {
    var w = this.width/2 + (this.isAcceptState ? acceptDistance : 0);
    var h = nodeHeight/2 + (this.isAcceptState ? acceptDistance : 0);
    var r = nodeCornerRadius + (this.isAcceptState ? acceptDistance : 0);
    var dx = x-this.x;
    var dy = y-this.y;
    var m = Math.abs(dy/dx);
    if (m >= h/(w-r)) // top or bottom
        return {'x': this.x+h/Math.abs(dy)*dx, 'y': this.y+Math.sign(dy)*h};
    else if (m <= (h-r)/w) // left or right
        return {'x': this.x+Math.sign(dx)*w, 'y': this.y+w/Math.abs(dx)*dy};
    else { // corner
        var ps = intersectCircleLine(w-r, h-r, r, Math.abs(dy), -Math.abs(dx), 0);
        for (p of ps)
            if (p.x >= 0 && p.y >= 0)
                return {'x': this.x+Math.sign(dx)*p.x, 'y': this.y+Math.sign(dy)*p.y};
    }
    return {'x': null, 'y': null};
};

Node.prototype.intersectArc = function(ax, ay, ar, astart, aend, ccw) {
    /* Find first intersection of arc with border. Assume that starting point is inside the node.
       ax, ay, ar: center and radius of circle
       astart, aend: angles (radians)
       ccw: counterclockwise */

    var w = this.width/2 + (this.isAcceptState ? acceptDistance : 0);
    var h = nodeHeight/2 + (this.isAcceptState ? acceptDistance : 0);
    var r = nodeCornerRadius + (this.isAcceptState ? acceptDistance : 0);

    // Intersect circle with border of node
    
    // Sides
    var ps = [];
    ps.push(...intersectCircleLine(ax, ay, ar, 0, 1, this.y-h));
    ps.push(...intersectCircleLine(ax, ay, ar, 0, 1, this.y+h));
    ps.push(...intersectCircleLine(ax, ay, ar, 1, 0, this.x-w));
    ps.push(...intersectCircleLine(ax, ay, ar, 1, 0, this.x+w));

    // Corners
    for (p of intersectCircles(ax, ay, ar, this.x+w-r, this.y+h-r, r))
        if (p.x >= this.x+w-r && p.y >= this.y+h-r) ps.push(p);
    for (p of intersectCircles(ax, ay, ar, this.x+w-r, this.y-h+r, r))
        if (p.x >= this.x+w-r && p.y <= this.y-h+r) ps.push(p);
    for (p of intersectCircles(ax, ay, ar, this.x-w+r, this.y+h-r, r))
        if (p.x <= this.x-w+r && p.y >= this.y+h-r) ps.push(p);
    for (p of intersectCircles(ax, ay, ar, this.x-w+r, this.y-h+r, r))
        if (p.x <= this.x-w+r && p.y <= this.y-h+r) ps.push(p);

    var dir = ccw ? -1 : +1;
    astart = principalAngle(dir*astart);
    aend = principalAngle(dir*aend);
    if (aend < astart) aend += 2*Math.PI;

    var firstAngle = null;
    var firstPoint = null;
    for (var p of ps) {
        var angle = principalAngle(dir * Math.atan2(p.y-ay, p.x-ax));
        if (angle < astart) angle += 2*Math.PI;
        if (astart <= angle && angle <= aend) {
            if (firstAngle === null || angle < firstAngle) {
                firstAngle = angle;
                firstPoint = p;
            }
        }
    }
    return firstPoint;
}

function PointNode(x, y) {
    this.x = x;
    this.y = y;
}

PointNode.prototype.setAnchorPoint = function(x, y) {
    this.x = x;
    this.y = y;
}

PointNode.prototype.draw = function(ctx) {
}

PointNode.prototype.closestPointOnCircle = function(x, y) {
    return { 'x': this.x, 'y': this.y };
}

PointNode.prototype.intersectArc = function(ax, ay, ar, astart, aend, ccw) {
    return { 'x': this.x, 'y': this.y };
}

function StartLink(start, node) {
    this.node = node;
    this.anchorAngle = 0;
    this.anchorRadius = 0;
    if (start)
        this.setAnchorPoint(start.x, start.y);
}

StartLink.prototype.setAnchorPoint = function(x, y) {
    var dx = x - this.node.x;
    var dy = y - this.node.y;
    var p = this.node.closestPointOnCircle(x, y);
    this.anchorRadius = Math.hypot(p.x-this.node.x, p.y-this.node.y)+startLength;
    this.anchorAngle = snapAngle(Math.atan2(dy, dx), this.anchorRadius);
};

StartLink.prototype.draw = function(ctx) {
    var startX = this.node.x + this.anchorRadius * Math.cos(this.anchorAngle);
    var startY = this.node.y + this.anchorRadius * Math.sin(this.anchorAngle);
    var end = this.node.closestPointOnCircle(startX, startY);

    // draw the line
    var edge = new Path2D();
    edge.moveTo(startX, startY);
    edge.lineTo(end.x, end.y);
    ctx.stroke(edge);

    this.containsPoint = function(x, y) {
        ctx.save();
        ctx.lineWidth = hitTargetPadding*2;
        var part = null;
        if (ctx.isPointInStroke(edge, x, y)) part = "edge";
        ctx.restore();
        return part;
    }

    // draw the head of the arrow
    drawArrow(ctx, end.x, end.y, this.anchorAngle+Math.PI, selectedObject == this);
};

StartLink.prototype.parallels = function(other) { return false; }

function Link(a, b) {
    this.nodeA = a; // source node
    this.nodeB = b; // target node
    this.text = new Text();
    this.perpendicularPart = 0; // pixels from line between nodeA and nodeB; positive is clockwise (like TikZ "bend left") and negative is ccw (like "bend right")
    this.lineAngleAdjust = 0; // when link is straight line, 0 means label is on right side and π means left side
    this.mouseOffsetX = 0;
    this.mouseOffsetY = 0;
}

Link.prototype.setMouseStart = function(x, y) {
    if (this.text.containsPoint(x, y)) {
        var anchor = this.getAnchorPoint();
        this.mouseOffsetX = anchor.x - x;
        this.mouseOffsetY = anchor.y - y;
    } else {
        this.mouseOffsetX = 0;
        this.mouseOffsetY = 0;
    }
}

Link.prototype.getAnchorPoint = function() {
    var dx = this.nodeB.x - this.nodeA.x;
    var dy = this.nodeB.y - this.nodeA.y;
    var scale = Math.hypot(dx, dy);
    return {
        'x': this.nodeA.x + dx / 2 + dy * this.perpendicularPart / scale,
        'y': this.nodeA.y + dy / 2 - dx * this.perpendicularPart / scale
    };
};

Link.prototype.setAnchorPoint = function(x, y) {
    x += this.mouseOffsetX;
    y += this.mouseOffsetY;
    var circle = circleFromThreePoints(this.nodeA.x, this.nodeA.y, this.nodeB.x, this.nodeB.y, x, y);
    const big = 1e6;
    if (circle.radius >= big) {
        var t = transformToLine(this.nodeA.x, this.nodeA.y, this.nodeB.x, this.nodeB.y, x, y);
        if (t.cx >= 0 && t.cx <= t.bx) {
            // (x,y) is between the endpoints
            this.lineAngleAdjust = (t.cy < 0) * Math.PI;
            this.perpendicularPart = 0;
        } else {
            // (x,y) is outside the endpoints
            this.perpendicularPart = t.cy < 0 ? big : -big;
        }
    } else {
        var t = transformToLine(this.nodeA.x, this.nodeA.y, this.nodeB.x, this.nodeB.y, x, y);
        var r = circle.radius * -Math.sign(t.cy);
        var midX = (this.nodeA.x + this.nodeB.x)/2 - circle.x;
        var midY = (this.nodeA.y + this.nodeB.y)/2 - circle.y;
        var c = Math.hypot(midX, midY); // distance from center to midpoint
        t = transformToLine(this.nodeA.x, this.nodeA.y, this.nodeB.x, this.nodeB.y, circle.x, circle.y);
        c *= -Math.sign(t.cy);
        this.perpendicularPart = r + c;
        // snap to a straight line
        if(Math.abs(this.perpendicularPart) < snapToPadding) {
            this.lineAngleAdjust = (this.perpendicularPart > 0) * Math.PI;
            this.perpendicularPart = 0;
        }
    }
};

Link.prototype.draw = function (ctx) {
    var anchor = this.getAnchorPoint(); // where the text goes
    var edge = new Path2D();
    var start, end; // endpoints
    var textAngle; // what direction relative to anchor the text goes
    var arrowAngle; // what direction the arrow points

    // Trivial edge: just don't draw anything?
    if (Math.hypot(this.nodeB.x-this.nodeA.x, this.nodeB.y-this.nodeA.y) < 1) {
        this.containsPoint = ((x, y) => null);
        return;
    }

    // Straight edge
    else if (this.perpendicularPart == 0) {
        start = this.nodeA.closestPointOnCircle(anchor.x, anchor.y);
        end = this.nodeB.closestPointOnCircle(anchor.x, anchor.y);
        var angle = Math.atan2(this.nodeB.y - this.nodeA.y, this.nodeB.x - this.nodeA.x);
        edge.moveTo(start.x, start.y);
        edge.lineTo(end.x ,end.y);
        textAngle = principalAngle(angle + Math.PI/2 + this.lineAngleAdjust);
        arrowAngle = angle;
    }
    
    // Curved edge
    else {
        // Compute arc from center of nodeA through anchor to center of nodeB
        var circle = circleFromThreePoints(this.nodeA.x, this.nodeA.y, this.nodeB.x, this.nodeB.y, anchor.x, anchor.y);
        var startAngle = Math.atan2(this.nodeA.y-circle.y, this.nodeA.x-circle.x);
        var endAngle = Math.atan2(this.nodeB.y-circle.y, this.nodeB.x-circle.x);
        var isReversed = (this.perpendicularPart < 0);
    
        // Clip arc to borders of nodes
        start = this.nodeA.intersectArc(circle.x, circle.y, circle.radius, startAngle, endAngle, isReversed);
        console.assert(start !== null);
        startAngle = Math.atan2(start.y-circle.y, start.x-circle.x);
        end = this.nodeB.intersectArc(circle.x, circle.y, circle.radius, endAngle, startAngle, !isReversed);
        console.assert(end !== null);
        endAngle = Math.atan2(end.y-circle.y, end.x-circle.x);
        if (endAngle < startAngle) endAngle += 2*Math.PI;
    
        edge.arc(circle.x, circle.y, circle.radius, startAngle, endAngle, isReversed);
        
        textAngle = (startAngle+endAngle)/2 + (isReversed ? Math.PI : 0);
        arrowAngle = endAngle + (isReversed ? -1:+1) * (Math.PI/2-arrowAngleAdjust);
    }

    // draw the edge
    ctx.stroke(edge);
    
    // draw the head of the arrow
    drawArrow(ctx, end.x, end.y, arrowAngle, selectedObject == this);
    
    // draw the text
    var text = this.text;
    text.draw(ctx, anchor.x, anchor.y, linkFontSize, textAngle, selectedObject == this);

    this.containsPoint = function(x, y) {
        ctx.save();
        ctx.lineWidth = hitTargetPadding*2;
        var part = null;
        if (ctx.isPointInStroke(edge, x, y)) {
            if (Math.hypot(x-start.x, y-start.y) <= hitTargetPadding)
                part = 'source';
            else if (Math.hypot(x-end.x, y-end.y) <= hitTargetPadding+2*arrowSize)
                part = 'target';
            else
                part = "edge";
        }
        else if (text.containsPoint(x, y)) part = "text";
        ctx.restore();
        return part;
    };
};

Link.prototype.parallels = function(other) {
    return (other instanceof Link &&
            this.nodeA === other.nodeA && this.nodeB === other.nodeB &&
            Math.abs(this.perpendicularPart - other.perpendicularPart) < 1);
}

function SelfLink(node, mouse) {
    this.node = node; // source/target node
    this.anchorAngle = 0; // angle of midpoint (radius is fixed)
    this.mouseOffsetAngle = 0; // when link is being moved, angle of anchor relative to angle of mouse
    this.text = new Text();

    if(mouse) {
        this.setAnchorPoint(mouse.x, mouse.y);
    }
}

SelfLink.prototype.setMouseStart = function(x, y) {
    this.mouseOffsetAngle = this.anchorAngle - Math.atan2(y - this.node.y, x - this.node.x);
};

SelfLink.prototype.setAnchorPoint = function(x, y) {
    this.anchorAngle = Math.atan2(y - this.node.y, x - this.node.x) + this.mouseOffsetAngle;
    this.anchorAngle = snapAngle(this.anchorAngle, Math.hypot(x-this.node.x, y-this.node.y));
};

SelfLink.prototype.draw = function(ctx) {
    const h = 2.5; // controls height of loop
    const w = 1; // controls width of loop
    var end = this.node.closestPointOnCircle(
        this.node.x + Math.cos(this.anchorAngle), 
        this.node.y + Math.sin(this.anchorAngle));
    var start = this.node.intersectArc(end.x, end.y, selfLinkRadius, this.anchorAngle-0.99*Math.PI, this.anchorAngle+0.99*Math.PI);
    var side = {'x': end.x-start.x, 'y': end.y-start.y};
    var normal = {'x': end.y-start.y, 'y': start.x-end.x};
    var control1 = {'x': start.x + h*normal.x - w*side.x,
                    'y': start.y + h*normal.y - w*side.y};
    var control2 = {'x': end.x + h*normal.x + w*side.x,
                    'y': end.y + h*normal.y + w*side.y};
    
    // draw arc
    var edge = new Path2D();
    edge.moveTo(start.x, start.y);
    edge.bezierCurveTo(control1.x, control1.y,
                       control2.x, control2.y,
                       end.x, end.y);
    ctx.stroke(edge);

    // draw the text at midpoint of path
    var text = this.text;
    var textX = (start.x + control1.x*3 + control2.x*3 + end.x)/8;
    var textY = (start.y + control1.y*3 + control2.y*3 + end.y)/8;
    var textAngle = Math.atan2(end.y-start.y,
                               end.x-start.x) - Math.PI/2;
    text.draw(ctx, textX, textY, linkFontSize, textAngle, selectedObject == this);
    
    // draw the head of the arrow
    var arrowAngle = Math.atan2(control2.y-end.y,
                                control2.x-end.x) + Math.PI - arrowAngleAdjust;
    drawArrow(ctx, end.x, end.y, arrowAngle, selectedObject == this);
    
    this.containsPoint = function(x, y) {
        ctx.save();
        ctx.lineWidth = hitTargetPadding*2;
        var part = null;
        if (ctx.isPointInStroke(edge, x, y)) {
            if (Math.hypot(x-start.x, y-start.y) <= hitTargetPadding)
                part = 'source';
            else if (Math.hypot(x-end.x, y-end.y) <= hitTargetPadding+2*arrowSize)
                part = 'target';
            else
                part = 'edge';
        } else if (text.containsPoint(x, y))
            part = 'text';
        ctx.restore();
        return part;
    };
};

SelfLink.prototype.parallels = function(other) {
    return (other instanceof SelfLink &&
            this.node === other.node &&
            Math.abs(this.anchorAngle - other.anchorAngle) < 0.01);
}

function Text(s) {
    if (s === undefined) s = '';
    this.lines = [s]; // array of strings
    this.x = this.y = null; // top center
    this.width = this.height = null;
    this.caretLine = 0;
    this.caretChar = 0;
    this.lineWidths = [];
    this.lineHeight = null;
}

Text.prototype.draw = function(ctx, x, y, fontSize, angleOrNull, isSelected) {
    ctx.save();
    ctx.font = fontSize+'px monospace';
    this.lineHeight = fontSize*1.2;
    var width = 0;
    var height = 0;
    this.lineWidths = [];
    var caret;
    for (var i=0; i<this.lines.length; i++) {
        var line = this.lines[i];
        var dims = ctx.measureText(line);
        width = Math.max(width, dims.width);
        this.lineWidths.push(dims.width);
        if (i === this.caretLine) {
            var cdims = ctx.measureText(line.slice(0, this.caretChar));
            caret = [-dims.width/2+cdims.width, height];
        }
        height += this.lineHeight;
    }

    // center the text
    y -= height/2;

    // position the text intelligently if given an angle
    if(angleOrNull != null) {
        var cos = Math.cos(angleOrNull);
        var sin = Math.sin(angleOrNull);
        var cornerPointX = (width/2 + fontSize/4) * (cos > 0 ? 1 : -1);
        var cornerPointY = (height/2 + fontSize/4) * (sin > 0 ? 1 : -1);
        var slide = sin * Math.pow(Math.abs(sin), 10) * cornerPointX - cos * Math.pow(Math.abs(cos), 10) * cornerPointY;
        x += cornerPointX - sin * slide;
        y += cornerPointY + cos * slide;
    }
    // Now (x,y) is where the top center of the box should appear

    // draw text and caret (round the coordinates so the caret falls on a pixel)
    x = Math.round(x);
    y = Math.round(y);
    ctx.textBaseline = "top";
    for (var i=0; i<this.lines.length; i++)
        ctx.fillText(this.lines[i], x-this.lineWidths[i]/2, y+i*this.lineHeight);
    if (isSelected && caretVisible && canvasHasFocus() && document.hasFocus()) {
        ctx.lineWidth = lineWidth;
        ctx.beginPath();
        ctx.moveTo(x+caret[0], y+caret[1]);
        ctx.lineTo(x+caret[0], y+caret[1]+this.lineHeight);
        ctx.stroke();
    }
    ctx.restore();

    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
}

Text.prototype.insert = function(c) {
    var l = this.caretLine;
    var toEnd = this.lines[l].length - this.caretChar;
    this.lines[l] = this.lines[l].slice(0, this.caretChar) + c + this.lines[l].slice(this.caretChar);
    this.lines[l] = convertShortcuts(this.lines[l]);
    this.caretChar = this.lines[l].length - toEnd;
};

Text.prototype.str = function() {
    console.assert(this.lines.length === 1);
    return this.lines[0];
};

Text.prototype.empty = function() {
    var n = 0;
    for (var line of this.lines)
        n += line.trim().length;
    return n === 0;
};

Text.prototype.handleKey = function(key) {
    switch (key) {
    case 8: // backspace
        if (this.caretChar > 0) {
            this.lines[this.caretLine] = this.lines[this.caretLine].slice(0, this.caretChar-1) + this.lines[this.caretLine].slice(this.caretChar);
            this.caretChar--;
        } else if (this.caretLine > 0) {
            this.lines.splice(this.caretLine-1, 2, this.lines[this.caretLine-1] + this.lines[this.caretLine]);
            this.caretLine--;
            this.caretChar = this.lines[this.caretLine].length;
        }
        break;
    case 13: // return
        this.lines.splice(this.caretLine, 1,
                          this.lines[this.caretLine].slice(0, this.caretChar),
                          this.lines[this.caretLine].slice(this.caretChar));
        this.caretLine++;
        this.caretChar = 0;
        break;
    case 37: // left
        if (this.caretChar > 0)
            this.caretChar--;
        else if (this.caretLine > 0) {
            this.caretLine--;
            this.caretChar = this.lines[this.caretLine].length;
        }
        break;
    case 39: // right
        if (this.caretChar < this.lines[this.caretLine].length)
            this.caretChar++;
        else if (this.caretLine < this.lines.length-1) {
            this.caretLine++;
            this.caretChar = 0;
        }
        break;
    case 38: // up
        if (this.caretLine > 0) {
            this.caretLine--;
            this.caretChar = Math.min(this.caretChar, this.lines[this.caretLine].length);
        }
        break;
    case 40: // down
        if (this.caretLine < this.lines.length-1) {
            this.caretLine++;
            this.caretChar = Math.min(this.caretChar, this.lines[this.caretLine].length);
        }
        break;
    }
};

Text.prototype.moveCaret = function(x, y) {
    // Find line
    var l = Math.floor((y-this.y)/this.lineHeight);
    l = Math.max(0, Math.min(this.lines.length, l));
    this.caretLine = l;
    // Estimate char
    var c = Math.round((x - (this.x-this.lineWidths[l]/2)) / this.lineWidths[l] * this.lines[l].length);
    c = Math.max(0, Math.min(this.lines[l].length, c));
    this.caretChar = c;
    resetCaret();
    draw();
};

Text.prototype.containsPoint = function(x, y) {
    return boxContainsPoint(this.x-this.width/2, this.y,
                            this.x+this.width/2, this.y+this.height,
                            x, y);
}

/* Drawing */

function drawArrow(ctx, x, y, angle, isSelected) {
    var dx = Math.cos(angle) * arrowSize;
    var dy = Math.sin(angle) * arrowSize;
    var w = isSelected ? 1.5 : 1;
    ctx.beginPath();
    ctx.moveTo(x - 3*dx + w*dy, y - 3*dy - w*dx);
    ctx.lineTo(x, y);
    ctx.lineTo(x - 3*dx - w*dy, y - 3*dy + w*dx);
    ctx.lineTo(x - 2*dx, y - 2*dy);
    ctx.fill();
}

function canvasHasFocus() {
    return document.activeElement == canvas;
}

function canvasFocus() {
    if (selectedObject != null && 'text' in selectedObject) {
        // on mobile, if there is text, make the soft keyboard appear
        canvas.contentEditable = true;
        canvas.focus();
    } else {
        canvas.contentEditable = false;
    }
}

var mappings = {'&': 'ε', '|-': '⊢', '-|': '⊣', '_': '␣', '->': '→'};
function convertShortcuts(s) {
    for (var a in mappings)
        s = s.replaceAll(a, mappings[a]);
    return s;
}

// The insertion point for text labels
var caretTimer;
var caretVisible = true;

function resetCaret() {
    clearInterval(caretTimer);
    caretTimer = setInterval(function () { caretVisible = !caretVisible; draw(); }, 500);
    caretVisible = true;
}

var canvas;
var canvas_dpr;
var canvasWidth = 600;
var canvasHeight = 600;
var nodeHeight = 25;
var nodeCornerRadius = 8;
var nodeMargin = 6;
var acceptDistance = 6;
var startLength = 40;
var selfLinkRadius = 15;
var arrowSize = 3.5;
var arrowAngleAdjust = 0.08;
var lineWidth = 1.5;
var nodeFontSize = 10 / 72 * 96; // 10pt
var linkFontSize = 9 / 72 * 96; // 9pt
var selectColor = '#00823e';

var snapToPadding = 6;
var hitTargetPadding = 6;

var nodes = [];
var links = [];

var selectedObject = null; // the Link or Node currently selected
var movingObject = false; // whether selectedObject is currently being moved
var currentLink = null; // the Link currently being drawn
var currentLinkSource, currentLinkTarget;
var currentLinkPart; // which part of currentLink is being moved
var originalLink; // the Link being reattached
var trash;

function deleteObject() {
    var trash = [];
    for(var i = 0; i < nodes.length; i++) {
        if(nodes[i] == selectedObject) {
            trash.push(nodes[i]);
            nodes.splice(i--, 1);
        }
    }
    for (var i=0; i<links.length; i++) {
        if(links[i] == selectedObject || links[i].node == selectedObject || links[i].nodeA == selectedObject || links[i].nodeB == selectedObject) {
            trash.push(links[i]);
            links.splice(i--, 1);
        }
    }
    return trash;
}

function draw() {
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.translate(0.5, 0.5);

    for(var i = 0; i < nodes.length; i++) {
        if (nodes[i] == selectedObject) {
            ctx.lineWidth = 2*lineWidth;
            ctx.fillStyle = ctx.strokeStyle = selectColor;
        } else {
            ctx.lineWidth = lineWidth;
            ctx.fillStyle = ctx.strokeStyle = 'black';
        }
        nodes[i].draw(ctx);
    }
    for(var i = 0; i < links.length; i++) {
        if (links[i] == selectedObject) {
            ctx.lineWidth = 2*lineWidth;
            ctx.fillStyle = ctx.strokeStyle = selectColor;
        } else {
            ctx.lineWidth = lineWidth;
            ctx.fillStyle = ctx.strokeStyle = 'black';
        }
        links[i].draw(ctx);
    }
    if(currentLink != null) {
        ctx.lineWidth = lineWidth;
        ctx.fillStyle = ctx.strokeStyle = 'black';
        currentLink.draw(ctx);
    }

    ctx.restore();
}

function selectObject(x, y) {
    for(var i = 0; i < links.length; i++) {
        var part = links[i].containsPoint(x, y);
        if (part !== null) {
            return {'object': links[i], 'part': part};
        }
    }
    for(var i = 0; i < nodes.length; i++) {
        var part = nodes[i].containsPoint(x, y);
        if (part !== null) {
            return {'object': nodes[i], 'part': part};
        }
    }
    return {'object': null};
}

var message_bar;
function message(s) {
    s = s.toString().replace(/(Error:\s*)*/, ''); // Colab generates two of these
    message_bar.innerHTML = s;
}

var help_div;

function main(ei) {
    var container = document.createElement("div");
    container.setAttribute("class", "editor");
    container.setAttribute("id", "editor"+ei);
    container.style.maxWidth = canvasWidth + "px";
    container.style.position = "relative";
    container.style.left = 0;
    container.style.top = 0;
    element.append(container);

    canvas = document.createElement("canvas");
    canvas.style.border = "1px solid gray";
    canvas.style.outline = "0px"; // no focus ring
    canvas.style.background = "white";
    canvas.style.boxSizing = "border-box";
    canvas.style.width = "100%";
    canvas.style.maxWidth = canvasWidth + "px";
    canvas.style.aspectRatio = canvasWidth + " / " + canvasHeight;
    canvas.style.cursor = "default"; // don't change cursor to 'text' on desktop
    canvas.setAttribute("tabindex", -1); // make canvas focusable
    canvas_dpr = window.devicePixelRatio || 1;
    canvas.width = canvasWidth * canvas_dpr;
    canvas.height = canvasHeight * canvas_dpr;
    container.append(canvas);

    nodeHeight *= canvas_dpr;
    nodeCornerRadius *= canvas_dpr;
    nodeMargin *= canvas_dpr;
    startLength *= canvas_dpr;
    acceptDistance *= canvas_dpr;
    selfLinkRadius *= canvas_dpr;
    arrowSize *= canvas_dpr;
    lineWidth *= canvas_dpr;
    nodeFontSize *= canvas_dpr;
    linkFontSize *= canvas_dpr;
    snapToPadding *= canvas_dpr; hitTargetPadding *= canvas_dpr;

    var controls = document.createElement("div");
    container.append(controls);

    function make_button(label, callback) {
        var button = document.createElement("button");
        button.style.margin = "5px";
        button.textContent = label;
        button.onclick = callback;
        controls.append(button);
    };
    make_button('Load', () => { load(ei); });
    make_button('Save', () => { save(ei); });
    make_button('Help', () => { help_div.style.display = "block"; });

    message_bar = document.createElement("span");
    message_bar.style.margin = "5px";
    controls.append(message_bar);

    help_div = document.createElement("div");
    help_div.innerHTML = "<table>" +
        "<p>Based on FSM Designer by Evan Wallace.</p>" +
        "<tr><td>New state</td><td>double-click canvas</td></tr>" +
        "<tr><td>Start state</td><td>drag from canvas to state</td></tr>" +
        "<tr><td>Accept state</td><td>double-click state</td></tr>" +
        "<tr><td>Rename state</td><td>click on center of state</td></tr>" +
        "<tr><td>Delete state</td><td>drag state outside canvas</td></tr>" +
        "<tr><td>New transition</td><td>drag from boundary of state to another state</td></tr>" +
        "<tr><td>Rename transition</td><td>click on transition</td></tr>" +
        "<tr><td>Delete transition</td><td>drag transition outside canvas</td></tr>" +
        "</table>";
    help_div.style.display = "none";
    help_div.style.position = "absolute";
    help_div.style.left = 0;
    help_div.style.top = 0;
    help_div.style.boxSizing = "border-box";
    help_div.style.width = "100%";
    help_div.style.height = "100%";
    help_div.style.padding = "0px 16px";
    help_div.style.background = "#ffffffc0";
    help_div.style.color = "black";
    help_div.addEventListener("click", () => { help_div.style.display = "none"; });
    container.append(help_div);
    
    load(ei); // bug: if there is an error later in the notebook, this doesn't work

    canvas.ontouchstart = function(e) {
        onmousedown(crossBrowserRelativeMousePos(e));
        canvasFocus();
    };
    canvas.onmousedown = function (e) {
        if (e.button === 0 && !control)
            onmousedown(crossBrowserRelativeMousePos(e));
        canvasFocus();
    };

    canvas.ondblclick = function(e) {
        var mouse = crossBrowserRelativeMousePos(e);
        selectedObject = selectObject(mouse.x, mouse.y).object;

        if(selectedObject == null) {
            // create new Node
            selectedObject = new Node(mouse.x, mouse.y);
            if(typeof Jupyter !== 'undefined') Jupyter.keyboard_manager.disable();
            nodes.push(selectedObject);
            canvasFocus();
            resetCaret();
            draw();
        } else if(selectedObject instanceof Node) {
            // toggle accept state
            selectedObject.isAcceptState = !selectedObject.isAcceptState;
            draw();
        }
        e.preventDefault();
    };

    canvas.onmousemove = function (e) {
        onmousemove(crossBrowserRelativeMousePos(e));
    };
    canvas.addEventListener('touchmove', function(e) {
        onmousemove(crossBrowserRelativeMousePos(e));
        e.preventDefault(); // don't scroll
    }, { passive: false });

    document.onmouseup = document.ontouchend = function(e) {
        movingObject = false;
        if(currentLink != null) {
            if (currentLink instanceof StartLink ||
                currentLink instanceof SelfLink ||
                currentLink instanceof Link && currentLink.nodeA instanceof Node && currentLink.nodeB instanceof Node) {
                selectedObject = currentLink;
                if (currentLink instanceof StartLink) {
                    for(var i=0; i<links.length; i++) {
                        if (links[i] instanceof StartLink)
                            links.splice(i--, 1);
                    }
                }
                links.push(currentLink);
                canvasFocus();
                resetCaret();
            }
            currentLink = null;
            draw();
        }
    };
    
    canvas.onmouseleave = function(e) {
        if (movingObject) {
            trash = deleteObject(selectedObject);
            draw();
        }
    }

    canvas.onmouseenter = function(e) {
        if (movingObject) {
            for (var i=0; i<trash.length; i++) {
                if (trash[i] instanceof Node)
                    nodes.push(trash[i]);
                else
                    links.push(trash[i]);
            }
            draw();
            resetCaret();
        }
    }
}

/* Events */

var control = false; // whether the Ctrl key is down

function onmousedown(mouse) {
    var moused = selectObject(mouse.x, mouse.y);
    selectedObject = null;
    
    if (moused.object != null) {
        if (moused.object instanceof Node && moused.part === 'circle') {
            // begin creating Link/SelfLink
            movingObject = false;
            originalLink = null;
            currentLink = new SelfLink(moused.object, mouse);
            currentLinkSource = currentLinkTarget = moused.object;
            currentLinkPart = 'target';
        } else if (moused.part === 'source' || moused.part === 'target') {
            // detach Link
            movingObject = false;
            originalLink = currentLink = moused.object;
            for (var i=0; i<links.length; i++)
                if (links[i] === currentLink)
                    links.splice(i--, 1);
            if (currentLink instanceof Link) {
                currentLinkSource = currentLink.nodeA;
                currentLinkTarget = currentLink.nodeB;
            } else if (currentLink instanceof SelfLink) {
                currentLinkSource = currentLinkTarget = currentLink.node;
            }
            currentLinkPart = moused.part;
        } else {
            // move Node or Link/StartLink/SelfLink
            selectedObject = moused.object;
            movingObject = true;
            if (moused.object.setMouseStart)
                moused.object.setMouseStart(mouse.x, mouse.y);
            if (moused.part === 'text')
                moused.object.text.moveCaret(mouse.x, mouse.y);
        }
        draw();
    } else {
        // begin creating StartLink
        movingObject = false;
        originalLink = null;
        currentLink = new Link(new PointNode(mouse.x, mouse.y), new PointNode(mouse.x, mouse.y));
        currentLinkSource = currentLink.nodeA;
        currentLinkTarget = currentLink.nodeB;
        currentLinkPart = 'target';
        // don't draw() right away, because there might be a double-click
    }
    resetCaret();
};

function onmousemove(mouse) {
    var moused = selectObject(mouse.x, mouse.y);
    
    if (currentLink != null) {
        if (!(moused.object instanceof Node))
            moused.object = new PointNode(mouse.x, mouse.y);
        if (currentLinkPart === 'source')
            currentLinkSource = moused.object;
        else if (currentLinkPart === 'target')
            currentLinkTarget = moused.object;
        if (!originalLink && currentLinkSource instanceof PointNode && currentLinkTarget instanceof Node)
            currentLink = new StartLink(currentLinkSource, currentLinkTarget);
        else if (currentLinkSource instanceof Node && currentLinkTarget === currentLinkSource)
            currentLink = new SelfLink(currentLinkSource, mouse);
        else 
            currentLink = new Link(currentLinkSource, currentLinkTarget);
        if (originalLink) {
            currentLink.text = originalLink.text;
            if (originalLink instanceof Link && currentLink instanceof Link)
                currentLink.perpendicularPart = originalLink.perpendicularPart;
            if (originalLink instanceof SelfLink && currentLink instanceof Link)
                currentLink.perpendicularPart = selfLinkRadius*2;
        }
        draw();
    }

    if (movingObject) {
        selectedObject.setAnchorPoint(mouse.x, mouse.y);
        draw();
    }
};

document.onkeydown = function(e) {
    var key = crossBrowserKey(e);
    if (key == 17) {
        control = true;
    } else if (canvasHasFocus() &&
        selectedObject != null && 'text' in selectedObject) {
        if (key == 32) {
            // on tablets, this can't be handled by onkeypress
            selectedObject.text.insert(String.fromCharCode(key));
            e.preventDefault();
        } else if (key < 48) {
            selectedObject.text.handleKey(key);
            e.preventDefault();
        }
        resetCaret();
        draw();
    }
}

document.onkeyup = function(e) {
    var key = crossBrowserKey(e);
    if (key == 17) {
        control = false;
    }
};

document.onkeypress = function(e) {
    var key = crossBrowserKey(e);
    if (canvasHasFocus() &&
        key >= 0x20 && key <= 0x7E &&
        !e.metaKey && !e.altKey && !e.ctrlKey &&
        selectedObject != null && 'text' in selectedObject) {
        selectedObject.text.insert(String.fromCharCode(key));
        resetCaret();
        draw();
        e.preventDefault();
    }
};

function crossBrowserKey(e) {
    e = e || window.event;
    return e.which || e.keyCode;
}

function crossBrowserElementPos(e) {
    e = e || window.event;
    // Add up offsets
    var obj = e.target || e.srcElement;
    var x = 0, y = 0;
    while(obj.offsetParent) {
        x += obj.offsetLeft;
        y += obj.offsetTop;
        obj = obj.offsetParent;
    }
    // Add up scroll positions
    obj = e.target || e.srcElement;
    while (obj.offsetParent) {
        x -= obj.scrollLeft;
        y -= obj.scrollTop;
        obj = obj.parentElement;
    }
    return { 'x': x * canvas_dpr, 'y': y * canvas_dpr };
}

function crossBrowserMousePos(e) {
    e = e || window.event;
    var x = e.pageX || e.clientX + document.body.scrollLeft + document.documentElement.scrollLeft;
    var y = e.pageY || e.clientY + document.body.scrollTop + document.documentElement.scrollTop;
    return { 'x': x * canvas_dpr, 'y': y * canvas_dpr };
}

function crossBrowserRelativeMousePos(e) {
    var element = crossBrowserElementPos(e);
    var mouse = crossBrowserMousePos(e);
    return {
        'x': (mouse.x - element.x) * canvasWidth / canvas.offsetWidth,
        'y': (mouse.y - element.y) * canvasHeight / canvas.offsetHeight
    };
}

function getNodeId(node) {
    for(var i = 0; i < nodes.length; i++)
        if(nodes[i] == node)
            return i;
}

/* Loading and saving */

function to_json() {
    var g = {'nodes': {}, 'edges': {}};
    var start;
    for (var i = 0; i < links.length; i++) {
        if (links[i] instanceof StartLink)
            start = getNodeId(links[i].node);
    }
    for (var i = 0; i < nodes.length; i++) {
        g.nodes[nodes[i].text.str()] = {
            'start': i == start,
            'accept': nodes[i].isAcceptState
        };
    }
    if (Object.keys(g.nodes).length != nodes.length) {
        message("Every state must have a unique name.");
        return null;
    }
    for (var i = 0; i < links.length; i++) {
        if (links[i] instanceof Link) {
            var u = links[i].nodeA.text.str();
            var v = links[i].nodeB.text.str();
            if (!(u in g.edges)) g.edges[u] = {};
            if (!(v in g.edges[u])) g.edges[u][v] = [];
            for (var line of links[i].text.lines) {
                line = line.trim(); if (line.length === 0) continue;
                g.edges[u][v].push({ 'label': line });
            }
        } else if (links[i] instanceof SelfLink) {
            var v = links[i].node.text;
            if (!(v in g.edges)) g.edges[v] = {};
            if (!(v in g.edges[v])) g.edges[v][v] = [];
            for (var line of links[i].text.lines) {
                line = line.trim(); if (line.length === 0) continue;
                g.edges[v][v].push({ 'label': line });
            }
        }
    }
    return g;
}

function save(ei) {
    for (var vi=0; vi<nodes.length; vi++)
        if (nodes[vi].text.empty()) {
            message('Every state must have a nonempty name.');
            return;
        }
    for (var li=0; li<links.length; li++)
        if ((links[li] instanceof Link || links[li] instanceof SelfLink) && links[li].text.empty()) {
            message('Every transition must have a nonempty label.');
            return;
        }
    
    var g = to_json();
    if (g === null) return;
    if (typeof Jupyter !== 'undefined') {
        function handle (r) {
            if (r.content.status == "ok") {
                message('Save successful');
            } else if (r.content.status == "error") {
                message(r.content.evalue);
                console.log(r);
            }
        }
        var cmd = 'import tock, json; tock.graphs.editor_save(' + ei + ', json.loads("""' + JSON.stringify(g) + '"""))';
        Jupyter.notebook.kernel.execute(cmd, {"shell": {"reply": handle}});
    } else if (typeof google !== 'undefined') {
        var result = google.colab.kernel.invokeFunction('notebook.editor_save', [ei, g])
            .then(() => message('Save successful'), message);
    } else {
        message('Save requires Colab or Jupyter NbClassic.');
        console.log(g);
    }
}

function from_json(g) {
    // Clear the current graph
    nodes = [];
    links = [];
    selectedObject = null;

    // Transform from graphviz coordinates to ours
    var eps = Math.min(canvas.width, canvas.height)*0.03; // canvas margin
    
    // I thought the scale factor should be 96/72 but it needs to be more
    var scale = Math.min(1.5*canvas_dpr,
                         canvas.width/(g.xmax-g.xmin+2*eps),
                         canvas.height/(g.ymax-g.ymin+2*eps));
    var shift = {'x': canvas.width/2 - (g.xmax+g.xmin)*scale/2,
                 'y': canvas.height/2 + (g.ymax+g.ymin)*scale/2};
    
    function tx(x) { return x*scale+shift.x; }
    function ty(y) { return -y*scale+shift.y; }

    var node_index = {}
    for (var v in g.nodes) {
        var newnode;
        if ('x' in g.nodes[v] && 'y' in g.nodes[v])
            newnode = new Node(tx(g.nodes[v].x), ty(g.nodes[v].y));
        else
            newnode = new Node(0, 0); // will move later
        var label = v;
        if (g.nodes[v].start)
            links.push(new StartLink({'x': tx(g.nodes[v].startx),
                                      'y': ty(g.nodes[v].starty)},
                                     newnode));
        if (g.nodes[v].accept)
            newnode.isAcceptState = true;
        newnode.text = new Text(label);
        nodes.push(newnode);
        node_index[v] = newnode;
    }

    for (var u in g.edges) {
        var unode = node_index[u];
        for (var v in g.edges[u]) {
            var vnode = node_index[v];
            for (var i=0; i<g.edges[u][v].length; i++) {
                var newlink;
                if (u == v)
                    newlink = new SelfLink(unode);
                else
                    newlink = new Link(unode, vnode);
                newlink.setAnchorPoint(tx(g.edges[u][v][i].anchorx),
                                       ty(g.edges[u][v][i].anchory));
                newlink.text = new Text(g.edges[u][v][i].label);
                // Coalesce parallel links
                if (links.length > 0 && links[links.length-1].parallels(newlink))
                    links[links.length-1].text.lines.push(...newlink.text.lines);
                else
                    links.push(newlink);
            }
        }
    }
}

function load(ei) {
    if (typeof Jupyter !== 'undefined') {
        function handle (r) {
            if (r.msg_type == "stream") {
                message('Load successful');
                from_json(JSON.parse(r.content.text));
                draw();
            } else if (r.msg_type == "error") {
                message(r.content.evalue);
                console.log(r);
            }
        }
        var cmd = 'import tock; import json; print(json.dumps(tock.graphs.editor_load(' + ei + ')))';
        Jupyter.notebook.kernel.execute(cmd, {"iopub": {"output": handle}});
    } else if (typeof google !== 'undefined') {
        function success (r) {
            message('Load successful');
            from_json(r.data['application/json']);
            draw();
        }
        var result = google.colab.kernel.invokeFunction('notebook.editor_load', [ei]).then(success, message);
    } else {
        message('Load requires Colab or Jupyter NbClassic.');
    }
}
