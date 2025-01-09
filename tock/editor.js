/*
 Finite State Machine Designer (http://madebyevan.com/fsm/)
 License: MIT License (see below)

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
     
   - If two nodes have the same position and are connected by a curved
     edge, the edge disappears.
*/

/* Geometry */

function boxContainsPoint(box, x, y) {
    return (x >= box[0]-hitTargetPadding && x <= box[2]+hitTargetPadding &&
            y >= box[1]-hitTargetPadding && y <= box[3]+hitTargetPadding);
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
    h = Math.sqrt(la**2 + lb**2);
    la /= h; lb /= h; lc /= h;

    if (Math.abs(lc) > ar)
        return [];
    else if (Math.abs(lc) === ar)
        return [{'x': ax + la*lc, 'y': ay + lb*lc}];
    else {
        d = Math.sqrt(ar**2-lc*lc);
        return [{'x': ax + la*lc - lb*d, 'y': ay + lb*lc + la*d},
                {'x': ax + la*lc + lb*d, 'y': ay + lb*lc - la*d}];
    }
}

function intersectCircles(x1, y1, r1, x2, y2, r2) {
    var d = Math.sqrt((x2-x1)**2 + (y2-y1)**2);
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
    drawText(ctx, this.text, this.x, this.y, nodeFontSize, null, selectedObject == this);
    this.width = Math.max(this.text.box[2]-this.text.box[0] + 2*nodeMargin, nodeHeight);

    // draw the border
    ctx.beginPath();
    ctx.roundRect(this.x-this.width/2,this.y-nodeHeight/2,
                  this.width, nodeHeight, nodeCornerRadius);
    ctx.stroke();
    
    // draw a double border for an accept state
    if (this.isAcceptState) {
        ctx.beginPath();
        ctx.roundRect(this.x-this.width/2-acceptDistance,this.y-nodeHeight/2-acceptDistance,
                      this.width+2*acceptDistance, nodeHeight+2*acceptDistance, nodeCornerRadius+acceptDistance);
        ctx.stroke();
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

Node.prototype.containsPoint = function(x, y) {
    var w = this.width/2 + (this.isAcceptState ? acceptDistance : 0);
    var h = nodeHeight/2 + (this.isAcceptState ? acceptDistance : 0);
    var r = nodeCornerRadius + (this.isAcceptState ? acceptDistance : 0);
    var dx = Math.abs(x-this.x);
    var dy = Math.abs(y-this.y);
    if (boxContainsPoint([this.x-w,this.y-h,this.x+w,this.y+h], x, y)) {
        // calculate distance to border
        var distance;
        if (dx <= w-r) // top or bottom
            distance = Math.abs(dy - h);
        else if (dy <= h-r) // left or right
            distance = Math.abs(dx - w);
        else {
            distance = Math.abs(Math.sqrt((dx-w+r)**2 + (dy-h+r)**2) - r);
        }
        if (distance <= hitTargetPadding)
            return 'circle';
        else if (boxContainsPoint(this.text.box, x, y))
            return 'text';
        else
            return 'node';
    }
    return null;
};

Node.prototype.intersectArc = function(ax, ay, ar, astart, aend, ccw) {
    /* Find first intersection of arc with border. Assume that starting poitn is inside the node.
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
    this.x = x; // center of node
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
    this.anchorRadius = Math.sqrt((p.x-this.node.x)**2 + (p.y-this.node.y)**2)+startLength;
    this.anchorAngle = snapAngle(Math.atan2(dy, dx), this.anchorRadius);
};

StartLink.prototype.getEndPoints = function() {
    var startX = this.node.x + this.anchorRadius * Math.cos(this.anchorAngle);
    var startY = this.node.y + this.anchorRadius * Math.sin(this.anchorAngle);
    var end = this.node.closestPointOnCircle(startX, startY);
    return {
        'startX': startX,
        'startY': startY,
        'endX': end.x,
        'endY': end.y,
    };
};

StartLink.prototype.draw = function(ctx) {
    var stuff = this.getEndPoints();

    // draw the line
    ctx.beginPath();
    ctx.moveTo(stuff.startX, stuff.startY);
    ctx.lineTo(stuff.endX, stuff.endY);
    ctx.stroke();

    // draw the head of the arrow
    drawArrow(ctx, stuff.endX, stuff.endY, this.anchorAngle+Math.PI, selectedObject == this);
};

StartLink.prototype.containsPoint = function(x, y) {
    var stuff = this.getEndPoints();
    var t = transformToLine(stuff.startX, stuff.startY, stuff.endX, stuff.endY, x, y);
    if (t.cx >= 0 && t.cx <= t.bx && Math.abs(t.cy) <= hitTargetPadding)
        return 'edge';
    else
        return null;
};

StartLink.prototype.parallels = function(other) { return false; }

function Link(a, b) {
    this.nodeA = a; // source node
    this.nodeB = b; // target node
    this.text = new Text();
    this.lineAngleAdjust = 0; // value to add to textAngle when link is straight line
    this.perpendicularPart = 0; // pixels from line between nodeA and nodeB; positive is clockwise
    this.mouseOffsetX = 0;
    this.mouseOffsetY = 0;
}

Link.prototype.setMouseStart = function(x, y) {
    if (boxContainsPoint(this.text.box, x, y)) {
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
    var scale = Math.sqrt(dx * dx + dy * dy);
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
        if (t.cx >= 0 && t.cx <= t.bx)
            this.perpendicularPart = 0;
        else
            this.perpendicularPart = t.cy < 0 ? big : -big;
        this.lineAngleAdjust = (t.cy < 0) * Math.PI;
    } else {
        var t = transformToLine(this.nodeA.x, this.nodeA.y, this.nodeB.x, this.nodeB.y, x, y);
        var r = circle.radius * -Math.sign(t.cy);
        var midX = (this.nodeA.x + this.nodeB.x)/2 - circle.x;
        var midY = (this.nodeA.y + this.nodeB.y)/2 - circle.y;
        var c = Math.sqrt(midX*midX + midY*midY); // distance from center to midpoint
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

Link.prototype.getEndPointsAndCircle = function() {
    if (this.perpendicularPart == 0) {
        var midX = (this.nodeA.x + this.nodeB.x) / 2;
        var midY = (this.nodeA.y + this.nodeB.y) / 2;
        var start = this.nodeA.closestPointOnCircle(midX, midY);
        var end = this.nodeB.closestPointOnCircle(midX, midY);
        return {
            'hasCircle': false,
            'startX': start.x,
            'startY': start.y,
            'endX': end.x,
            'endY': end.y,
        };
    }
    var anchor = this.getAnchorPoint();

    // Compute arc from center of nodeA through anchor to center of nodeB
    var circle = circleFromThreePoints(this.nodeA.x, this.nodeA.y, this.nodeB.x, this.nodeB.y, anchor.x, anchor.y);

    var isReversed = (this.perpendicularPart < 0);
    var dir = isReversed ? -1 : +1;
    var startAngle = Math.atan2(this.nodeA.y-circle.y, this.nodeA.x-circle.x);
    var endAngle = Math.atan2(this.nodeB.y-circle.y, this.nodeB.x-circle.x);
    var p = this.nodeA.intersectArc(circle.x, circle.y, circle.radius, startAngle, endAngle, isReversed);
    if (p !== null) startAngle = Math.atan2(p.y-circle.y, p.x-circle.x);
    var p = this.nodeB.intersectArc(circle.x, circle.y, circle.radius, endAngle, startAngle, !isReversed);
    if (p !== null) endAngle = Math.atan2(p.y-circle.y, p.x-circle.x);

    var startX = circle.x + circle.radius * Math.cos(startAngle);
    var startY = circle.y + circle.radius * Math.sin(startAngle);
    var endX = circle.x + circle.radius * Math.cos(endAngle);
    var endY = circle.y + circle.radius * Math.sin(endAngle);
    
    return {
        'hasCircle': true,
        'startX': startX,
        'startY': startY,
        'endX': endX,
        'endY': endY,
        'startAngle': startAngle,
        'endAngle': endAngle,
        'circleX': circle.x, // center of arc
        'circleY': circle.y,
        'circleRadius': circle.radius,
        'isReversed': isReversed, // true = counterclockwise, false = clockwise
    };
};

Link.prototype.draw = function(ctx) {
    var stuff = this.getEndPointsAndCircle();
    // draw arc
    ctx.beginPath();
    if (stuff.hasCircle) {
        ctx.arc(stuff.circleX, stuff.circleY, stuff.circleRadius, stuff.startAngle, stuff.endAngle, stuff.isReversed);
    } else {
        ctx.moveTo(stuff.startX, stuff.startY);
        ctx.lineTo(stuff.endX, stuff.endY);
    }
    ctx.stroke();
    // draw the head of the arrow
    if(stuff.hasCircle) {
        drawArrow(ctx, stuff.endX, stuff.endY, stuff.endAngle + (stuff.isReversed?-1:1) * (Math.PI / 2), selectedObject == this);
    } else {
        drawArrow(ctx, stuff.endX, stuff.endY, Math.atan2(stuff.endY - stuff.startY, stuff.endX - stuff.startX), selectedObject == this);
    }
    // draw the text
    if (stuff.hasCircle) {
        var startAngle = stuff.startAngle;
        var endAngle = stuff.endAngle;
        if(endAngle < startAngle) {
            endAngle += Math.PI * 2;
        }
        var textAngle = (startAngle + endAngle) / 2 + stuff.isReversed * Math.PI;
        var textX = stuff.circleX + stuff.circleRadius * Math.cos(textAngle);
        var textY = stuff.circleY + stuff.circleRadius * Math.sin(textAngle);
        drawText(ctx, this.text, textX, textY, linkFontSize, textAngle, selectedObject == this);
    } else {
        var textX = (stuff.startX + stuff.endX) / 2;
        var textY = (stuff.startY + stuff.endY) / 2;
        var textAngle = Math.atan2(stuff.endX - stuff.startX, stuff.startY - stuff.endY);
        drawText(ctx, this.text, textX, textY, linkFontSize, textAngle + this.lineAngleAdjust, selectedObject == this);
    }
};

Link.prototype.containsPoint = function(x, y) {
    if (boxContainsPoint(this.text.box, x, y))
        return 'text';
    var stuff = this.getEndPointsAndCircle();
    if(stuff.hasCircle) {
        var dx = x - stuff.circleX;
        var dy = y - stuff.circleY;
        var distance = Math.sqrt(dx*dx + dy*dy) - stuff.circleRadius;
        if(Math.abs(distance) <= hitTargetPadding) {
            var angle = Math.atan2(dy, dx);
            var startAngle = stuff.startAngle;
            var endAngle = stuff.endAngle;
            if (stuff.isReversed) {
                angle *= -1;
                startAngle *= -1;
                endAngle *= -1;
            }
            if(endAngle < startAngle) {
                endAngle += Math.PI * 2;
            }
            if(angle < startAngle) {
                angle += Math.PI * 2;
            } else if(angle > endAngle) {
                angle -= Math.PI * 2;
            }
            if (angle >= startAngle && angle <= endAngle) {
                if (angle <= startAngle + hitTargetPadding / stuff.circleRadius)
                    return 'source';
                else if (angle >= endAngle - (hitTargetPadding+2*arrowSize) / stuff.circleRadius)
                    return 'target';
                else
                    return 'edge';
            } else
                return null;
        }
    } else {
        var t = transformToLine(stuff.startX, stuff.startY, stuff.endX, stuff.endY, x, y);
        if (t.cx >= 0 && t.cx <= t.bx && Math.abs(t.cy) <= hitTargetPadding) {
            if (t.cx <= hitTargetPadding)
                return 'source';
            else if (t.cx >= t.bx-(hitTargetPadding+2*arrowSize))
                return 'target';
            else
                return 'edge';
        } else
            return null;
    }
    return null;
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
    this.anchorAngle = snapAngle(this.anchorAngle, Math.sqrt((x-this.node.x)**2+(y-this.node.y)**2));
};

SelfLink.prototype.getEndPoints = function() {
    const r = 15; // half the distance between endpoints. Should be less than nodeHeight.
    const h = 2.5; // controls height of loop
    const w = 1; // controls width of loop
    var center = this.node.closestPointOnCircle(
        this.node.x + Math.cos(this.anchorAngle), 
        this.node.y + Math.sin(this.anchorAngle));
    // the start and end are a little to the left and right of center
    var start = this.node.intersectArc(center.x, center.y, r, this.anchorAngle-0.99*Math.PI, this.anchorAngle+0.99*Math.PI);
    var end = this.node.intersectArc(center.x, center.y, r, this.anchorAngle+0.99*Math.PI, this.anchorAngle-0.99*Math.PI, true);
    var side = {'x': end.x-start.x, 'y': end.y-start.y};
    var normal = {'x': end.y-start.y, 'y': start.x-end.x};
    var control1 = {
        'x': start.x + h*normal.x - w*side.x,
        'y': start.y + h*normal.y - w*side.y
    };
    var control2 = {
        'x': end.x + h*normal.x + w*side.x,
        'y': end.y + h*normal.y + w*side.y
    };
    return {
        'start': start,
        'control1': control1,
        'control2': control2,
        'end': end
    };
}

SelfLink.prototype.draw = function(ctx) {
    var stuff = this.getEndPoints();
    // draw arc
    var path = new Path2D();
    path.moveTo(stuff.start.x, stuff.start.y);
    path.bezierCurveTo(stuff.control1.x, stuff.control1.y, 
                       stuff.control2.x, stuff.control2.y, 
                       stuff.end.x, stuff.end.y);
    ctx.stroke(path);

    this.isPointInStroke = function(x, y) {
        ctx.save();
        ctx.lineWidth = hitTargetPadding*2;
        var ans = ctx.isPointInStroke(path, x, y);
        ctx.restore();
        return ans;
    }
    
    // draw the text at midpoint of path
    var textX = stuff.start.x/8 + stuff.control1.x*3/8 + stuff.control2.x*3/8 + stuff.end.x/8;
    var textY = stuff.start.y/8 + stuff.control1.y*3/8 + stuff.control2.y*3/8 + stuff.end.y/8;
    var textAngle = Math.atan2(stuff.end.y-stuff.start.y,
                               stuff.end.x-stuff.start.x) - Math.PI/2;
    var arrowAngle = Math.atan2(stuff.control2.y-stuff.end.y,
                                stuff.control2.x-stuff.end.x) + Math.PI;
    drawText(ctx, this.text, textX, textY, linkFontSize, textAngle, selectedObject == this);
    // draw the head of the arrow
    drawArrow(ctx, stuff.end.x, stuff.end.y, arrowAngle, selectedObject == this);
};

SelfLink.prototype.containsPoint = function(x, y) {
    if (boxContainsPoint(this.text.box, x, y))
        return 'text';
    else if (this.isPointInStroke(x, y)) {
        var stuff = this.getEndPoints();
        if (Math.sqrt((x-stuff.start.x)**2 + (y-stuff.start.y)**2) <= hitTargetPadding)
            return 'source';
        else if (Math.sqrt((x-stuff.end.x)**2 + (y-stuff.end.y)**2) <= hitTargetPadding+2*arrowSize)
            return 'target';
        else
            return 'circle';
    } else
        return null;
};

SelfLink.prototype.parallels = function(other) {
    return (other instanceof SelfLink &&
            this.node === other.node &&
            Math.abs(this.anchorAngle - other.anchorAngle) < 0.01);
}

function Text(s) {
    if (s === undefined) s = '';
    this.lines = [s]; // array of strings
    this.box = null;
    this.caretLine = 0;
    this.caretChar = 0;
    this.offsets = [];
}

Text.prototype.backspace = function() {
    if (this.caretChar > 0) {
        this.lines[this.caretLine] = this.lines[this.caretLine].slice(0, this.caretChar-1) + this.lines[this.caretLine].slice(this.caretChar);
        this.caretChar--;
    } else if (this.caretLine > 0) {
        this.lines.splice(this.caretLine-1, 2, this.lines[this.caretLine-1] + this.lines[this.caretLine]);
        this.caretLine--;
        this.caretChar = this.lines[this.caretLine].length;
    }
};

Text.prototype.newline = function() {
    this.lines.splice(this.caretLine, 1,
                      this.lines[this.caretLine].slice(0, this.caretChar),
                      this.lines[this.caretLine].slice(this.caretChar));
    this.caretLine++;
    this.caretChar = 0;
};

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
    // Top center of box
    var bx = (this.box[0] + this.box[2])/2;
    var by = this.box[1];
    // Find line
    var i;
    for (i=0; i<this.offsets.length; i++)
        if (by+this.offsets[i][1] > y) break;
    if (i>0) i--;
    this.caretLine = i;
    // Estimate char
    this.caretChar = Math.round((x - (bx+this.offsets[i][0])) / (-this.offsets[i][0]*2) * this.lines[i].length);
    resetCaret();
    draw();
};

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

var mappings = {'&': 'ε', '|-': '⊢', '-|': '⊣', '_': '␣', '->': '→'};
function convertShortcuts(s) {
    for (var a in mappings)
        s = s.replaceAll(a, mappings[a]);
    return s;
}

function drawText(ctx, text, x, y, fontSize, angleOrNull, isSelected, maxWidth) {
    ctx.save();
    ctx.font = fontSize+'px monospace';
    const lineHeight = fontSize*1.2;
    var width = 0;
    var height = 0;
    text.offsets = []; // relative to top center of box
    var caret;
    for (var i=0; i<text.lines.length; i++) {
        var line = text.lines[i];
        var dims = ctx.measureText(line);
        width = Math.max(width, dims.width);
        text.offsets.push([-dims.width/2, height]);
        if (i === text.caretLine) {
            var cdims = ctx.measureText(line.slice(0, text.caretChar));
            caret = [-dims.width/2+cdims.width, height];
        }
        height += lineHeight;
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
    for (var i=0; i<text.lines.length; i++)
        ctx.fillText(text.lines[i], x+text.offsets[i][0], y+text.offsets[i][1]);
    if (isSelected && caretVisible && canvasHasFocus() && document.hasFocus()) {
        ctx.lineWidth = lineWidth;
        ctx.beginPath();
        ctx.moveTo(x+caret[0], y+caret[1]);
        ctx.lineTo(x+caret[0], y+caret[1]+lineHeight);
        ctx.stroke();
    }
    ctx.restore();

    text.box = [x-width/2, y, x+width/2, y+height];
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
var selfLinkRadius = 10;
var arrowSize = 3.5;
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
    canvas.setAttribute("contenteditable", true); // make keyboard appear on tablets
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
        button.setAttribute("style", "margin: 5px;");
        button.textContent = label;
        button.onclick = callback;
        controls.append(button);
    }
    make_button('Load', () => { load(ei); });
    make_button('Save', () => { save(ei); });
    make_button('Help', () => { help_div.style.display = "block"; });

    message_bar = document.createElement("span");
    message_bar.setAttribute("style", "margin: 5px;");
    controls.append(message_bar);

    help_div = document.createElement("div");
    help_div.innerHTML = "<table>" +
        "<p>This is the visual editor for <code>tock.Machine</code>, based on FSM Designer by Evan Wallace.</p>" +
        "<tr><td>New state</td><td>double-click canvas</td></tr>" +
        "<tr><td>Start state</td><td>drag from canvas to state</td></tr>" +
        "<tr><td>Accept state</td><td>double-click state</td></tr>" +
        "<tr><td>Rename state</td><td>click on center of state</td></tr>" +
        "<tr><td>Delete state</td><td>drag state outside canvas</td></tr>" +
        "<tr><td>New transition</td><td>drag from boundary of state to another state</td></tr>" +
        "<tr><td>Rename transition</td><td>click on transition</td></tr>" +
        "<tr><td>Delete transition</td><td>drag transition outside canvas</td></tr>" +
        "</table>" +
        "<p>Click anywhere on this help message to dismiss it.</p>";
    help_div.style.display = "none";
    help_div.style.position = "absolute";
    help_div.style.left = 0;
    help_div.style.top = 0;
    help_div.style.boxSizing = "border-box";
    help_div.style.width = "100%";
    help_div.style.height = "100%";
    help_div.style.padding = "16px 32px";
    help_div.style.background = "#ffffffc0";
    help_div.style.color = "black";
    help_div.addEventListener("click", () => { help_div.style.display = "none"; });
    container.append(help_div);
    
    load(ei); // bug: if there is an error later in the notebook, this doesn't work

    canvas.ontouchstart = function(e) {
        onmousedown(crossBrowserRelativeMousePos(e));
    };
    canvas.onmousedown = function (e) {
        if (e.button !== 0 || control) return true;
        onmousedown(crossBrowserRelativeMousePos(e));
    };
        
    canvas.ondblclick = function(e) {
        var mouse = crossBrowserRelativeMousePos(e);
        selectedObject = selectObject(mouse.x, mouse.y).object;

        if(selectedObject == null) {
            // create new Node
            selectedObject = new Node(mouse.x, mouse.y);
            if(typeof Jupyter !== 'undefined') Jupyter.keyboard_manager.disable();
            nodes.push(selectedObject);
            resetCaret();
            draw();
        } else if(selectedObject instanceof Node) {
            // toggle accept state
            selectedObject.isAcceptState = !selectedObject.isAcceptState;
            draw();
        }
        return false;
    };

    canvas.onmousemove = function (e) {
        onmousemove(crossBrowserRelativeMousePos(e));
    };
    canvas.addEventListener('touchmove', function(e) {
        onmousemove(crossBrowserRelativeMousePos(e));
        e.preventDefault();
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

var shift = false; // whether the Shift key is down
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
        resetCaret();
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

    // In Colab the canvas is inside an iframe, which seems to cause trouble
    // with this first case.
    if(0 && canvasHasFocus()) {
        // disable drag-and-drop only if the canvas is already focused
        return false;
    } else {
        // otherwise, let the browser switch the focus away from wherever it was
        resetCaret();
        return true;
    }
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
                currentLink.perpendicularPart = selfLinkRadius;
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

    if (key == 16) {
        shift = true;
    } else if (key == 17) {
        control = true;
    } else if (!canvasHasFocus()) {
        // don't read keystrokes when other things have focus
        return true;
    } else if (key >= 37 && key <= 40 && selectedObject != null && 'text' in selectedObject) { // arrows
        selectedObject.text.handleKey(key);
        resetCaret();
        draw();
        return false;
    } else if (key == 32) { // on tablets, space pages down
        if (selectedObject != null && 'text' in selectedObject) {
            selectedObject.text.insert(String.fromCharCode(key));
            resetCaret();
            draw();
        }
        return false;
    } else if (key == 13 && (selectedObject instanceof Link || selectedObject instanceof SelfLink)) {
        selectedObject.text.newline();
        resetCaret();
        draw();
        return false;
    } else if (key == 8) {
        if (selectedObject != null && 'text' in selectedObject) {
            selectedObject.text.backspace();
            resetCaret();
            draw();
        }
        return false;
    }};

document.onkeyup = function(e) {
    var key = crossBrowserKey(e);

    if (key == 16) {
        shift = false;
    } else if (key == 17) {
        control = false;
    }
};

document.onkeypress = function(e) {
    // don't read keystrokes when other things have focus
    var key = crossBrowserKey(e);
    if (!canvasHasFocus()) {
        // don't read keystrokes when other things have focus
        return true;
    } else if (key >= 0x20 && key <= 0x7E && !e.metaKey && !e.altKey && !e.ctrlKey && selectedObject != null && 'text' in selectedObject) {
        selectedObject.text.insert(String.fromCharCode(key));
        resetCaret();
        draw();
        return false;
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
