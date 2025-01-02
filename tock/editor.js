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
   - In Jupyter, if the canvas is too wide, a horizontal scrollbar appears,
   which makes the output too high, so a vertical scrollbar appears too.
*/

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

function snapAngle(angle, r) {
    // snap to 90 degrees
    var snap = Math.round(angle / (Math.PI / 2)) * (Math.PI / 2);
    if(Math.abs(angle - snap) * r <= snapToPadding) angle = snap;
    // keep in the range -pi to pi
    if(angle < -Math.PI) angle += 2 * Math.PI;
    if(angle > Math.PI) angle -= 2 * Math.PI;
    return angle;
}

function Node(x, y) {
    this.x = x; // center of node
    this.y = y;
    this.radius = nodeRadius;
    this.mouseOffsetX = 0; // when node is being moved, center relative to mouse
    this.mouseOffsetY = 0;
    this.isAcceptState = false;
    this.text = '';
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

Node.prototype.draw = function(c) {
    // draw the circle
    c.beginPath();
    c.arc(this.x, this.y, this.radius, 0, 2 * Math.PI, false);
    c.stroke();

    // draw the text
    this.textBox = drawText(c, this.text, this.x, this.y, null, selectedObject == this, this.radius*2*acceptRatio);

    // draw a double circle for an accept state
    if(this.isAcceptState) {
        c.beginPath();
        c.arc(this.x, this.y, this.radius * acceptRatio, 0, 2 * Math.PI, false);
        c.stroke();
    }
};

Node.prototype.closestPointOnCircle = function(x, y) {
    var dx = x - this.x;
    var dy = y - this.y;
    var scale = Math.sqrt(dx * dx + dy * dy);
    return {
        'x': this.x + dx * this.radius / scale,
        'y': this.y + dy * this.radius / scale,
    };
};

Node.prototype.containsPoint = function(x, y) {
    if (boxContainsPoint(this.textBox, x, y))
        return 'label';
    else {
        var distance = Math.hypot(x - this.x, y - this.y);
        if (distance >= this.radius - hitTargetPadding && distance <= this.radius + hitTargetPadding)
            return 'circle';
        else if (distance <= this.radius)
            return 'node';
        else
            return null;
    }
};

function PointNode(x, y) {
    this.x = x; // center of node
    this.y = y;
    this.radius = 0;
}

PointNode.prototype.setAnchorPoint = function(x, y) {
    this.x = x;
    this.y = y;
}

PointNode.prototype.draw = function(c) {
}

PointNode.prototype.closestPointOnCircle = function(x, y) {
    return { 'x': this.x, 'y': this.y }
}

function StartLink(start, node) {
    this.node = node;
    this.anchorAngle = 0;
    this.anchorRadius = node.radius * startRatio;
    if(start)
        this.setAnchorPoint(start.x, start.y);
}

StartLink.prototype.setAnchorPoint = function(x, y) {
    var dx = x - this.node.x;
    var dy = y - this.node.y;
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

StartLink.prototype.draw = function(c) {
    var stuff = this.getEndPoints();

    // draw the line
    c.beginPath();
    c.moveTo(stuff.startX, stuff.startY);
    c.lineTo(stuff.endX, stuff.endY);
    c.stroke();

    // draw the head of the arrow
    drawArrow(c, stuff.endX, stuff.endY, this.anchorAngle+Math.PI);
};

StartLink.prototype.containsPoint = function(x, y) {
    var stuff = this.getEndPoints();
    var t = transformToLine(stuff.startX, stuff.startY, stuff.endX, stuff.endY, x, y);
    if (t.cx >= 0 && t.cx <= t.bx && Math.abs(t.cy) <= hitTargetPadding)
        return 'edge';
    else
        return null;
};

function Link(a, b) {
    this.nodeA = a; // source node
    this.nodeB = b; // target node
    this.text = '';
    this.lineAngleAdjust = 0; // value to add to textAngle when link is straight line
    this.perpendicularPart = 0; // pixels from line between nodeA and nodeB; positive is clockwise
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
    if(this.perpendicularPart == 0) {
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
    var circle = circleFromThreePoints(this.nodeA.x, this.nodeA.y, this.nodeB.x, this.nodeB.y, anchor.x, anchor.y);
    var isReversed = (this.perpendicularPart < 0);
    var reverseScale = isReversed ? -1 : 1;
    var startAngle = Math.atan2(this.nodeA.y - circle.y, this.nodeA.x - circle.x) + reverseScale * this.nodeA.radius / circle.radius;
    var endAngle = Math.atan2(this.nodeB.y - circle.y, this.nodeB.x - circle.x) - reverseScale * this.nodeB.radius / circle.radius;
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

Link.prototype.draw = function(c) {
    var stuff = this.getEndPointsAndCircle();
    // draw arc
    c.beginPath();
    if(stuff.hasCircle) {
        c.arc(stuff.circleX, stuff.circleY, stuff.circleRadius, stuff.startAngle, stuff.endAngle, stuff.isReversed);
    } else {
        c.moveTo(stuff.startX, stuff.startY);
        c.lineTo(stuff.endX, stuff.endY);
    }
    c.stroke();
    // draw the head of the arrow
    if(stuff.hasCircle) {
        drawArrow(c, stuff.endX, stuff.endY, stuff.endAngle + (stuff.isReversed?-1:1) * (Math.PI / 2));
    } else {
        drawArrow(c, stuff.endX, stuff.endY, Math.atan2(stuff.endY - stuff.startY, stuff.endX - stuff.startX));
    }
    // draw the text
    if(stuff.hasCircle) {
        var startAngle = stuff.startAngle;
        var endAngle = stuff.endAngle;
        if(endAngle < startAngle) {
            endAngle += Math.PI * 2;
        }
        var textAngle = (startAngle + endAngle) / 2 + stuff.isReversed * Math.PI;
        var textX = stuff.circleX + stuff.circleRadius * Math.cos(textAngle);
        var textY = stuff.circleY + stuff.circleRadius * Math.sin(textAngle);
        this.textBox = drawText(c, this.text, textX, textY, textAngle, selectedObject == this);
    } else {
        var textX = (stuff.startX + stuff.endX) / 2;
        var textY = (stuff.startY + stuff.endY) / 2;
        var textAngle = Math.atan2(stuff.endX - stuff.startX, stuff.startY - stuff.endY);
        this.textBox = drawText(c, this.text, textX, textY, textAngle + this.lineAngleAdjust, selectedObject == this);
    }
};

Link.prototype.containsPoint = function(x, y) {
    if (boxContainsPoint(this.textBox, x, y))
        return 'label';
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

function SelfLink(node, mouse) {
    this.node = node; // source/target node
    this.anchorAngle = 0; // angle of midpoint (radius is fixed)
    this.mouseOffsetAngle = 0; // when link is being moved, angle of anchor relative to angle of mouse
    this.text = '';

    if(mouse) {
        this.setAnchorPoint(mouse.x, mouse.y);
    }
}

SelfLink.prototype.setMouseStart = function(x, y) {
    this.mouseOffsetAngle = this.anchorAngle - Math.atan2(y - this.node.y, x - this.node.x);
};

SelfLink.prototype.setAnchorPoint = function(x, y) {
    this.anchorAngle = Math.atan2(y - this.node.y, x - this.node.x) + this.mouseOffsetAngle;
    this.anchorAngle = snapAngle(this.anchorAngle, (1.5+0.75)*this.node.radius);
};

SelfLink.prototype.getEndPointsAndCircle = function() {
    var circleX = this.node.x + 1.5 * this.node.radius * Math.cos(this.anchorAngle);
    var circleY = this.node.y + 1.5 * this.node.radius * Math.sin(this.anchorAngle);
    var circleRadius = 0.75 * this.node.radius;
    var startAngle = this.anchorAngle - Math.PI * 0.8;
    var endAngle = this.anchorAngle + Math.PI * 0.8;
    var startX = circleX + circleRadius * Math.cos(startAngle);
    var startY = circleY + circleRadius * Math.sin(startAngle);
    var endX = circleX + circleRadius * Math.cos(endAngle);
    var endY = circleY + circleRadius * Math.sin(endAngle);
    return {
        'hasCircle': true,
        'startX': startX,
        'startY': startY,
        'endX': endX,
        'endY': endY,
        'startAngle': startAngle,
        'endAngle': endAngle,
        'circleX': circleX,
        'circleY': circleY,
        'circleRadius': circleRadius
    };
};

SelfLink.prototype.draw = function(c) {
    var stuff = this.getEndPointsAndCircle();
    // draw arc
    c.beginPath();
    c.arc(stuff.circleX, stuff.circleY, stuff.circleRadius, stuff.startAngle, stuff.endAngle, false);
    c.stroke();
    // draw the text on the loop farthest from the node
    var textX = stuff.circleX + stuff.circleRadius * Math.cos(this.anchorAngle);
    var textY = stuff.circleY + stuff.circleRadius * Math.sin(this.anchorAngle);
    this.textBox = drawText(c, this.text, textX, textY, this.anchorAngle, selectedObject == this);
    // draw the head of the arrow
    drawArrow(c, stuff.endX, stuff.endY, stuff.endAngle + Math.PI * 0.4);
};

SelfLink.prototype.containsPoint = function(x, y) {
    if (boxContainsPoint(this.textBox, x, y))
        return 'label';
    var stuff = this.getEndPointsAndCircle();
    var dx = x - stuff.circleX;
    var dy = y - stuff.circleY;
    var distance = Math.sqrt(dx*dx + dy*dy) - stuff.circleRadius;
    if (Math.abs(distance) <= hitTargetPadding) {
        var angle = Math.atan2(dy, dx);
        var startAngle = stuff.startAngle;
        var endAngle = stuff.endAngle;
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
    } else
        return null;
};

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
    return {
        'x': -bx / (2*a),
        'y': -by / (2*a),
        'radius': Math.sqrt(bx*bx + by*by - 4*a*c) / (2*Math.abs(a))
    };
}

var mappings = {'&': 'ε', '|-': '⊢', '-|': '⊣', '_': '␣', '->': '→'}
function convertShortcuts(text) {
    for (var s in mappings)
        text = text.replaceAll(s, mappings[s]);
    return text;
}

function drawArrow(c, x, y, angle) {
    var dx = Math.cos(angle) * arrowSize;
    var dy = Math.sin(angle) * arrowSize;
    c.beginPath();
    c.moveTo(x, y);
    c.lineTo(x - 2 * dx + dy, y - 2 * dy - dx);
    c.lineTo(x - 2 * dx - dy, y - 2 * dy + dx);
    c.fill();
}

function canvasHasFocus() {
    return document.activeElement == canvas;
}

function drawText(c, originalText, x, y, angleOrNull, isSelected, maxWidth) {
    var text = convertShortcuts(originalText);
    c.save();

    var tmpFontSize = fontSize;
    c.font = ''+tmpFontSize+'px monospace';
    var width = c.measureText(text).width;

    // resize to fit in maxWidth
    if (maxWidth !== undefined && width > maxWidth) {
        tmpFontSize *= maxWidth/width;
        c.font = ''+tmpFontSize+'px monospace';
        width = c.measureText(text).width;
    }

    // center the text
    x -= width / 2;

    // position the text intelligently if given an angle
    if(angleOrNull != null) {
        var cos = Math.cos(angleOrNull);
        var sin = Math.sin(angleOrNull);
        var cornerPointX = (width / 2 + fontSize/4) * (cos > 0 ? 1 : -1);
        var cornerPointY = (fontSize/2 + 5) * (sin > 0 ? 1 : -1);
        var slide = sin * Math.pow(Math.abs(sin), 40) * cornerPointX - cos * Math.pow(Math.abs(cos), 10) * cornerPointY;
        x += cornerPointX - sin * slide;
        y += cornerPointY + cos * slide;
    }

    // draw text and caret (round the coordinates so the caret falls on a pixel)
    x = Math.round(x);
    y = Math.round(y);
    c.textBaseline = "middle";
    c.fillText(text, x, y);
    if(isSelected && caretVisible && canvasHasFocus() && document.hasFocus()) {
        x += width;
        c.lineWidth = lineWidth;
        c.beginPath();
        c.moveTo(x, y - fontSize/2);
        c.lineTo(x, y + fontSize/2);
        c.stroke();
    }
    c.restore();

    return [x, y-tmpFontSize/2, x+width, y+tmpFontSize/2];
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
var nodeRadius = 30;
var arrowSize = 4;
var lineWidth = 1;
var fontSize = 16;
var selectColor = '#00823e';
var startRatio = 2; // relative to nodeRadius
var acceptRatio = 0.8; // relative to nodeRadius

var snapToPadding = 6; // pixels
var hitTargetPadding = 6; // pixels

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
    var c = canvas.getContext('2d');
    c.clearRect(0, 0, canvas.width, canvas.height);
    c.save();
    c.translate(0.5, 0.5);

    for(var i = 0; i < nodes.length; i++) {
        if (nodes[i] == selectedObject) {
            c.lineWidth = 3*lineWidth;
            c.fillStyle = c.strokeStyle = selectColor;
        } else {
            c.lineWidth = lineWidth;
            c.fillStyle = c.strokeStyle = 'black';
        }
        nodes[i].draw(c);
    }
    for(var i = 0; i < links.length; i++) {
        if (links[i] == selectedObject) {
            c.lineWidth = 3*lineWidth;
            c.fillStyle = c.strokeStyle = selectColor;
        } else {
            c.lineWidth = lineWidth;
            c.fillStyle = c.strokeStyle = 'black';
        }
        links[i].draw(c);
    }
    if(currentLink != null) {
        c.lineWidth = lineWidth;
        c.fillStyle = c.strokeStyle = 'black';
        currentLink.draw(c);
    }

    c.restore();
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
    container.style.width="650px";
    container.style.position = "relative";
    container.style.left = 0;
    container.style.top = 0;
    element.append(container);

    canvas = document.createElement("canvas");
    canvas.setAttribute("style", "outline: 1px solid gray; margin: 1px; width: 600px; height: 600px;");
    canvas.setAttribute("tabindex", -1); // make canvas focusable
    canvas_dpr = window.devicePixelRatio || 1;
    canvas.width = 600 * canvas_dpr;
    canvas.height = 600 * canvas_dpr;
    container.append(canvas);
    
    nodeRadius *= canvas_dpr; arrowSize *= canvas_dpr;
    lineWidth *= canvas_dpr; fontSize *= canvas_dpr;
    snapToPadding *= canvas_dpr; hitTargetPadding *= canvas_dpr;

    load(ei); // bug: if there is an error later in the notebook, this doesn't work
    //draw();

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
    help_div.style.width = "100%";
    help_div.style.height = "100%";
    help_div.style.background = "#ffffffc0";
    help_div.style.padding = "10px";
    help_div.addEventListener("click", () => { help_div.style.display = "none"; });
    container.append(help_div);
    
    canvas.onmousedown = function(e) {
        if (e.button !== 0 || control) return true;
        var mouse = crossBrowserRelativeMousePos(e);
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
                if(moused.object.setMouseStart)
                    moused.object.setMouseStart(mouse.x, mouse.y);
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
    };

    canvas.onmousemove = function(e) {
        var mouse = crossBrowserRelativeMousePos(e);
        var moused = selectObject(mouse.x, mouse.y);
        
        if(currentLink != null) {
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
                    currentLink.perpendicularPart = 2*originalLink.node.radius;
            }
            draw();
        }

        if (movingObject) {
            selectedObject.setAnchorPoint(mouse.x, mouse.y);
            draw();
        }
    };

    document.onmouseup = function(e) {
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

var shift = false; // whether the Shift key is down
var control = false; // whether the Ctrl key is down

document.onkeydown = function(e) {
    var key = crossBrowserKey(e);

    if (key == 16) {
        shift = true;
    } else if (key == 17) {
        control = true;
    } else if(!canvasHasFocus()) {
        // don't read keystrokes when other things have focus
        return true;
    } else if(key == 8) { // backspace key
        if(selectedObject != null && 'text' in selectedObject) {
            selectedObject.text = selectedObject.text.substr(0, selectedObject.text.length - 1);
            resetCaret();
            draw();
        }

        /*if(selectedObject != null) {
            deleteObject(selectedObject);
            selectedObject = null;
            draw();
        }*/

        // backspace is a shortcut for the back button, but do NOT want to change pages
        return false;
    }
};

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
    if(!canvasHasFocus()) {
        // don't read keystrokes when other things have focus
        return true;
    } else if(key >= 0x20 && key <= 0x7E && !e.metaKey && !e.altKey && !e.ctrlKey && selectedObject != null && 'text' in selectedObject) {
        selectedObject.text += String.fromCharCode(key);
        resetCaret();
        draw();

        // don't let keys do their actions (like space scrolls down the page)
        return false;
    } else if(key == 8) {
        // backspace is a shortcut for the back button, but do NOT want to change pages
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
        'x': mouse.x - element.x,
        'y': mouse.y - element.y
    };
}

function getNodeId(node) {
    for(var i = 0; i < nodes.length; i++)
        if(nodes[i] == node)
            return i;
}

function to_json() {
    var g = {'nodes': {}, 'edges': {}};
    var start;
    for(var i = 0; i < links.length; i++) {
        if(links[i] instanceof StartLink)
            start = getNodeId(links[i].node);
    }
    for (var i = 0; i < nodes.length; i++) {
        g.nodes[nodes[i].text] = {
            'start': i == start,
            'accept': nodes[i].isAcceptState
        };
    }
    if (Object.keys(g.nodes).length != nodes.length) {
        message("Every state must have a unique name.");
        return null;
    }
    for(var i = 0; i < links.length; i++) {
        if(links[i] instanceof Link) {
            var u = links[i].nodeA.text;
            var v = links[i].nodeB.text;
            if (!(u in g.edges)) g.edges[u] = {};
            if (!(v in g.edges[u])) g.edges[u][v] = [];
            g.edges[u][v].push({ 'label': links[i].text });
        } else if(links[i] instanceof SelfLink) {
            var v = links[i].node.text;
            if (!(v in g.edges)) g.edges[v] = {};
            if (!(v in g.edges[v])) g.edges[v][v] = [];
            g.edges[v][v].push({ 'label': links[i].text });
        }
    }
    return g;
}

function save(ei) {
    for (var vi=0; vi<nodes.length; vi++)
        if (nodes[vi].text === "") {
            message('Every state must have a nonempty name.');
            return;
        }
    for (var li=0; li<links.length; li++)
        if ((links[li] instanceof Link || links[li] instanceof SelfLink) && links[li].text === "") {
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
    }
}

function from_json(g) {
    // Clear the current graph
    nodes = [];
    links = [];
    selectedObject = null;

    // Transform from graphviz coordinates to ours
    var eps = Math.min(canvas.width, canvas.height)*0.03; 
    function tx(x) { return (x-g.xmin+eps) / (g.xmax-g.xmin+2*eps) * canvas.width; }
    function ty(y) { return (g.ymax-y+eps) / (g.ymax-g.ymin+2*eps) * canvas.height; }

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
        newnode.text = label;
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
                newlink.text = g.edges[u][v][i].label;
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
    }
}

