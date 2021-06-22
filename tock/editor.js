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

   To do:
   - Change keybinding for delete node/edge
   - Change edge's endpoint
   - Map > and @ to start/accept state?
   - Help
*/

function StartLink(node, start) {
    this.node = node;
    this.deltaX = 0;
    this.deltaY = 0;

    if(start) {
        this.setAnchorPoint(start.x, start.y);
    }
}

StartLink.prototype.setAnchorPoint = function(x, y) {
    this.deltaX = x - this.node.x;
    this.deltaY = y - this.node.y;

    if(Math.abs(this.deltaX) < snapToPadding) {
        this.deltaX = 0;
    }

    if(Math.abs(this.deltaY) < snapToPadding) {
        this.deltaY = 0;
    }
};

StartLink.prototype.getEndPoints = function() {
    var startX = this.node.x + this.deltaX;
    var startY = this.node.y + this.deltaY;
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
    drawArrow(c, stuff.endX, stuff.endY, Math.atan2(-this.deltaY, -this.deltaX));
};

StartLink.prototype.containsPoint = function(x, y) {
    var stuff = this.getEndPoints();
    var dx = stuff.endX - stuff.startX;
    var dy = stuff.endY - stuff.startY;
    var length = Math.sqrt(dx*dx + dy*dy);
    var percent = (dx * (x - stuff.startX) + dy * (y - stuff.startY)) / (length * length);
    var distance = (dx * (y - stuff.startY) - dy * (x - stuff.startX)) / length;
    return (percent > 0 && percent < 1 && Math.abs(distance) < hitTargetPadding);
};

function Link(a, b) {
    this.nodeA = a;
    this.nodeB = b;
    this.text = '';
    this.lineAngleAdjust = 0; // value to add to textAngle when link is straight line

    // make anchor point relative to the locations of nodeA and nodeB
    this.parallelPart = 0.5; // percentage from nodeA to nodeB
    this.perpendicularPart = 0; // pixels from line between nodeA and nodeB
}

Link.prototype.getAnchorPoint = function() {
    var dx = this.nodeB.x - this.nodeA.x;
    var dy = this.nodeB.y - this.nodeA.y;
    var scale = Math.sqrt(dx * dx + dy * dy);
    return {
        'x': this.nodeA.x + dx * this.parallelPart - dy * this.perpendicularPart / scale,
        'y': this.nodeA.y + dy * this.parallelPart + dx * this.perpendicularPart / scale
    };
};

Link.prototype.setAnchorPoint = function(x, y) {
    var dx = this.nodeB.x - this.nodeA.x;
    var dy = this.nodeB.y - this.nodeA.y;
    var scale = Math.sqrt(dx * dx + dy * dy);
    this.parallelPart = (dx * (x - this.nodeA.x) + dy * (y - this.nodeA.y)) / (scale * scale);
    this.perpendicularPart = (dx * (y - this.nodeA.y) - dy * (x - this.nodeA.x)) / scale;
    // snap to a straight line
    if(this.parallelPart > 0 && this.parallelPart < 1 && Math.abs(this.perpendicularPart) < snapToPadding) {
        this.lineAngleAdjust = (this.perpendicularPart < 0) * Math.PI;
        this.perpendicularPart = 0;
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
    var isReversed = (this.perpendicularPart > 0);
    var reverseScale = isReversed ? 1 : -1;
    var startAngle = Math.atan2(this.nodeA.y - circle.y, this.nodeA.x - circle.x) - reverseScale * nodeRadius / circle.radius;
    var endAngle = Math.atan2(this.nodeB.y - circle.y, this.nodeB.x - circle.x) + reverseScale * nodeRadius / circle.radius;
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
        'circleX': circle.x,
        'circleY': circle.y,
        'circleRadius': circle.radius,
        'reverseScale': reverseScale,
        'isReversed': isReversed,
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
        drawArrow(c, stuff.endX, stuff.endY, stuff.endAngle - stuff.reverseScale * (Math.PI / 2));
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
        drawText(c, this.text, textX, textY, textAngle, selectedObject == this);
    } else {
        var textX = (stuff.startX + stuff.endX) / 2;
        var textY = (stuff.startY + stuff.endY) / 2;
        var textAngle = Math.atan2(stuff.endX - stuff.startX, stuff.startY - stuff.endY);
        drawText(c, this.text, textX, textY, textAngle + this.lineAngleAdjust, selectedObject == this);
    }
};

Link.prototype.containsPoint = function(x, y) {
    var stuff = this.getEndPointsAndCircle();
    if(stuff.hasCircle) {
        var dx = x - stuff.circleX;
        var dy = y - stuff.circleY;
        var distance = Math.sqrt(dx*dx + dy*dy) - stuff.circleRadius;
        if(Math.abs(distance) < hitTargetPadding) {
            var angle = Math.atan2(dy, dx);
            var startAngle = stuff.startAngle;
            var endAngle = stuff.endAngle;
            if(stuff.isReversed) {
                var temp = startAngle;
                startAngle = endAngle;
                endAngle = temp;
            }
            if(endAngle < startAngle) {
                endAngle += Math.PI * 2;
            }
            if(angle < startAngle) {
                angle += Math.PI * 2;
            } else if(angle > endAngle) {
                angle -= Math.PI * 2;
            }
            return (angle > startAngle && angle < endAngle);
        }
    } else {
        var dx = stuff.endX - stuff.startX;
        var dy = stuff.endY - stuff.startY;
        var length = Math.sqrt(dx*dx + dy*dy);
        var percent = (dx * (x - stuff.startX) + dy * (y - stuff.startY)) / (length * length);
        var distance = (dx * (y - stuff.startY) - dy * (x - stuff.startX)) / length;
        return (percent > 0 && percent < 1 && Math.abs(distance) < hitTargetPadding);
    }
    return false;
};

function Node(x, y) {
    this.x = x;
    this.y = y;
    this.mouseOffsetX = 0;
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
};

Node.prototype.draw = function(c) {
    // draw the circle
    c.beginPath();
    c.arc(this.x, this.y, nodeRadius, 0, 2 * Math.PI, false);
    c.stroke();

    // draw the text
    drawText(c, this.text, this.x, this.y, null, selectedObject == this, nodeRadius*1.6);

    // draw a double circle for an accept state
    if(this.isAcceptState) {
        c.beginPath();
        c.arc(this.x, this.y, nodeRadius * 0.8, 0, 2 * Math.PI, false);
        c.stroke();
    }
};

Node.prototype.closestPointOnCircle = function(x, y) {
    var dx = x - this.x;
    var dy = y - this.y;
    var scale = Math.sqrt(dx * dx + dy * dy);
    return {
        'x': this.x + dx * nodeRadius / scale,
        'y': this.y + dy * nodeRadius / scale,
    };
};

Node.prototype.containsPoint = function(x, y) {
    return (x - this.x)*(x - this.x) + (y - this.y)*(y - this.y) < nodeRadius*nodeRadius;
};

function SelfLink(node, mouse) {
    this.node = node;
    this.anchorAngle = 0;
    this.mouseOffsetAngle = 0;
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
    // snap to 90 degrees
    var snap = Math.round(this.anchorAngle / (Math.PI / 2)) * (Math.PI / 2);
    if(Math.abs(this.anchorAngle - snap) < 0.1) this.anchorAngle = snap;
    // keep in the range -pi to pi so our containsPoint() function always works
    if(this.anchorAngle < -Math.PI) this.anchorAngle += 2 * Math.PI;
    if(this.anchorAngle > Math.PI) this.anchorAngle -= 2 * Math.PI;
};

SelfLink.prototype.getEndPointsAndCircle = function() {
    var circleX = this.node.x + 1.5 * nodeRadius * Math.cos(this.anchorAngle);
    var circleY = this.node.y + 1.5 * nodeRadius * Math.sin(this.anchorAngle);
    var circleRadius = 0.75 * nodeRadius;
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
    drawText(c, this.text, textX, textY, this.anchorAngle, selectedObject == this);
    // draw the head of the arrow
    drawArrow(c, stuff.endX, stuff.endY, stuff.endAngle + Math.PI * 0.4);
};

SelfLink.prototype.containsPoint = function(x, y) {
    var stuff = this.getEndPointsAndCircle();
    var dx = x - stuff.circleX;
    var dy = y - stuff.circleY;
    var distance = Math.sqrt(dx*dx + dy*dy) - stuff.circleRadius;
    return (Math.abs(distance) < hitTargetPadding);
};

function TemporaryLink(from, to) {
    this.from = from;
    this.to = to;
}

TemporaryLink.prototype.draw = function(c) {
    // draw the line
    c.beginPath();
    c.moveTo(this.to.x, this.to.y);
    c.lineTo(this.from.x, this.from.y);
    c.stroke();

    // draw the head of the arrow
    drawArrow(c, this.to.x, this.to.y, Math.atan2(this.to.y - this.from.y, this.to.x - this.from.x));
};

function det(a, b, c, d, e, f, g, h, i) {
    return a*e*i + b*f*g + c*d*h - a*f*h - b*d*i - c*e*g;
}

function circleFromThreePoints(x1, y1, x2, y2, x3, y3) {
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
        text = text.replace(s, mappings[s]);
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
}

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
var nodes = [];
var links = [];

var cursorVisible = true;
var snapToPadding = 6; // pixels
var hitTargetPadding = 6; // pixels
var selectedObject = null; // either a Link or a Node
var currentLink = null; // a Link
var movingObject = false;
var originalClick;

function drawUsing(c) {
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

function draw() {
    drawUsing(canvas.getContext('2d'));
}

function selectObject(x, y) {
    for(var i = 0; i < nodes.length; i++) {
        if(nodes[i].containsPoint(x, y)) {
            return nodes[i];
        }
    }
    for(var i = 0; i < links.length; i++) {
        if(links[i].containsPoint(x, y)) {
            return links[i];
        }
    }
    return null;
}

function snapNode(node) {
    for(var i = 0; i < nodes.length; i++) {
        if(nodes[i] == node) continue;

        if(Math.abs(node.x - nodes[i].x) < snapToPadding) {
            node.x = nodes[i].x;
        }

        if(Math.abs(node.y - nodes[i].y) < snapToPadding) {
            node.y = nodes[i].y;
        }
    }
}

var message_bar;
function message(s) {
    message_bar.innerHTML = s;
}

function main(ei) {
    canvas = document.createElement("canvas");
    canvas.setAttribute("style", "outline: 1px solid black; width: 600px; height: 600px;");
    canvas.setAttribute("tabindex", -1); // make canvas focusable
    canvas_dpr = window.devicePixelRatio || 1;
    canvas.width = 600 * canvas_dpr;
    canvas.height = 600 * canvas_dpr;
    element.append(canvas);
    
    nodeRadius *= canvas_dpr; arrowSize *= canvas_dpr;
    lineWidth *= canvas_dpr; fontSize *= canvas_dpr;
    snapToPadding *= canvas_dpr; hitTargetPadding *= canvas_dpr;

    load(ei); // bug: if there is an error later in the notebook, this doesn't work
    //draw();

    element.append(document.createElement("br"));

    function make_button(label, callback) {
        var button = document.createElement("button");
        button.setAttribute("style", "margin: 0 10px 0 0;");
        button.innerHTML = label;
        button.onclick = callback;
        element.append(button);
    }
    make_button('Load', function() { load(ei); });
    make_button('Save', function() { save(ei); });

    message_bar = document.createElement("span");
    element.append(message_bar);

    canvas.onmousedown = function(e) {
        var mouse = crossBrowserRelativeMousePos(e);
        selectedObject = selectObject(mouse.x, mouse.y);
        movingObject = false;
        originalClick = mouse;

        if(selectedObject != null) {
            if(shift && selectedObject instanceof Node) {
                currentLink = new SelfLink(selectedObject, mouse);
            } else {
                movingObject = true;
                if(selectedObject.setMouseStart) {
                    selectedObject.setMouseStart(mouse.x, mouse.y);
                }
            }
            resetCaret();
        } else if(shift) {
            currentLink = new TemporaryLink(mouse, mouse);
        }

        draw();

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
        selectedObject = selectObject(mouse.x, mouse.y);

        if(selectedObject == null) {
            selectedObject = new Node(mouse.x, mouse.y);
            if(typeof Jupyter !== 'undefined') Jupyter.keyboard_manager.disable();
            nodes.push(selectedObject);
            resetCaret();
            draw();
        } else if(selectedObject instanceof Node) {
            selectedObject.isAcceptState = !selectedObject.isAcceptState;
            draw();
        }
    };

    canvas.onmousemove = function(e) {
        var mouse = crossBrowserRelativeMousePos(e);

        if(currentLink != null) {
            var targetNode = selectObject(mouse.x, mouse.y);
            if(!(targetNode instanceof Node)) {
                targetNode = null;
            }

            if(selectedObject == null) {
                if(targetNode != null) {
                    currentLink = new StartLink(targetNode, originalClick);
                } else {
                    currentLink = new TemporaryLink(originalClick, mouse);
                }
            } else {
                if(targetNode == selectedObject) {
                    currentLink = new SelfLink(selectedObject, mouse);
                } else if(targetNode != null) {
                    currentLink = new Link(selectedObject, targetNode);
                } else {
                    currentLink = new TemporaryLink(selectedObject.closestPointOnCircle(mouse.x, mouse.y), mouse);
                }
            }
            draw();
        }

        if(movingObject) {
            selectedObject.setAnchorPoint(mouse.x, mouse.y);
            if(selectedObject instanceof Node) {
                snapNode(selectedObject);
            }
            draw();
        }
    };

    canvas.onmouseup = function(e) {
        movingObject = false;

        if(currentLink != null) {
            if(!(currentLink instanceof TemporaryLink)) {
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
}

var shift = false;

document.onkeydown = function(e) {
    var key = crossBrowserKey(e);

    if(key == 16) {
        shift = true;
    } else if(!canvasHasFocus()) {
        // don't read keystrokes when other things have focus
        return true;
    } else if(key == 8) { // backspace key
        if (!shift) {
            if(selectedObject != null && 'text' in selectedObject) {
                selectedObject.text = selectedObject.text.substr(0, selectedObject.text.length - 1);
                resetCaret();
                draw();
            }
        } else {
            if(selectedObject != null) {
                for(var i = 0; i < nodes.length; i++) {
                    if(nodes[i] == selectedObject) {
                        nodes.splice(i--, 1);
                    }
                }
                for(var i = 0; i < links.length; i++) {
                    if(links[i] == selectedObject || links[i].node == selectedObject || links[i].nodeA == selectedObject || links[i].nodeB == selectedObject) {
                        links.splice(i--, 1);
                    }
                }
                selectedObject = null;
                draw();
            }
        }

        // backspace is a shortcut for the back button, but do NOT want to change pages
        return false;
    }
};

document.onkeyup = function(e) {
    var key = crossBrowserKey(e);

    if(key == 16) {
        shift = false;
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
    while (obj) {
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
        var result = google.colab.kernel.invokeFunction('notebook.editor_save', [ei, g]).then(() => message('Save successful'), message);
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
            links.push(new StartLink(newnode, {'x': tx(g.nodes[v].startx),
                                               'y': ty(g.nodes[v].starty)}));
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
