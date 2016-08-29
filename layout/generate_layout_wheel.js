// Script to generate layout JSON for Cosmic Praise from CAD model coordinates
//
// usage: node generate_layout.js > cosmicpraise.json

var fs = require('fs');
var path = require('path');
var curves = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'wheel_strip_curves_113px.json'), 'utf8'));
var curves70 = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'wheel_strip_curves_70px.json'), 'utf8'));

function scale(pts, axes) {
	var newpts = [];
	for(var i = 0; i < pts.length; i++) {
		newpts.push([0,0,0]);
		newpts[i][0] = pts[i][0] * axes[0]; 
		newpts[i][1] = pts[i][1] * axes[1]; 
		newpts[i][2] = pts[i][2] * axes[2]; 
	}
	return newpts;
}

function reverse(pts) {
	var reversed = []
	for (var i = pts.length - 1; i >= 0; i--) {
		reversed.push(pts[i]);
	}
	return reversed;
}

function translate(pts, vec) {
	var newpts = [];
	for (var i = 0; i < pts.length; i++) {
		newpts.push([0,0,0])
		newpts[i][0] = pts[i][0] + vec[0];
		newpts[i][1] = pts[i][1] + vec[1];
		newpts[i][2] = pts[i][2] + vec[2];
	}
	return newpts;
}

// wheel strips start at top and meet at bottom
var wheel_right_inner = curves["wheel_right_inner0"];
var wheel_right_outer = curves["wheel_right_outer0"];
var wheel_left_inner = scale(curves["wheel_right_inner0"], [-1, 1, 1]);
var wheel_left_outer = scale(curves["wheel_right_outer0"], [-1, 1, 1]);

// back door and ceiling strips start on the wheel-side ceiling
var back_door_right = reverse(curves["back_door_right0"]);
var back_door_left = reverse(scale(curves["back_door_right0"], [-1, 1, 1]));
var ceiling_left_high = reverse(scale(curves["ceiling_right_high0"], [-1, 1, 1]));
var ceiling_left_low = reverse(scale(curves["ceiling_right_low0"], [-1, 1, 1]));
var ceiling_center = curves["ceiling_center0"];
var ceiling_right_low = reverse(curves["ceiling_right_low0"]);
var ceiling_right_high = reverse(curves["ceiling_right_high0"]);

// front door strips start at the top center
var front_door_right = curves70["front_door_70px_right0"];
var front_door_left = scale(curves70["front_door_70px_right0"], [-1, 1, 1]);
var front_door_outer_right = translate(front_door_right, [0, -1, 0])
var front_door_outer_left = translate(front_door_left, [0, -1, 0])

var lightTypes = [
	{ 
		group: "wheel-right", 
		proto: "opc", address: "10.0.0.32:7890", 
		ports: { 19: wheel_right_inner, 17: wheel_right_outer },
	},
	{ 
		group: "wheel-left", 
		proto: "opc", address: "10.0.0.32:7890", 
		ports: { 16: wheel_left_inner, 18: wheel_left_outer },
	},
	{ 
		group: "back-door-right", 
		proto: "opc", address: "10.0.0.32:7890", 
		ports: { 14: back_door_right },
	},
	{ 
		group: "back-door-left", 
		proto: "opc", address: "10.0.0.32:7890", 
		ports: { 9: back_door_left },
	},
	{
		group: "ceiling-right-low",
		proto: "opc", address: "10.0.0.32:7890",
		ports: { 15: ceiling_right_low },
	},
	{
		group: "ceiling-right-high",
		proto: "opc", address: "10.0.0.32:7890",
		ports: { 12: ceiling_right_high },
	},
	{
		group: "ceiling-center",
		proto: "opc", address: "10.0.0.32:7890",
		ports: { 10: ceiling_center },
	},
	{
		group: "ceiling-left-high",
		proto: "opc", address: "10.0.0.32:7890",
		ports: { 11: ceiling_left_high },
	},
	{
		group: "ceiling-left-low",
		proto: "opc", address: "10.0.0.32:7890",
		ports: { 8: ceiling_left_low },
	},
	{ 
		group: "front-door",
		proto: "opc", address: "10.0.0.32:7890",
		ports: { 3: front_door_right, 0: front_door_left },
	},
	{ 
		group: "front-door-outer",
		proto: "opc", address: "10.0.0.32:7890",
		ports: { 2: front_door_outer_right, 1: front_door_outer_left },
	},
];

var pixelsPerStrip = 120;
var pixeldata = [];

function transformPt(point_in) {
	var point_out = [0,-20,0];
	point_out[0] += point_in[0] * 0.1;
	point_out[1] += point_in[2] * 0.1;
	point_out[2] += point_in[1] * 0.1;
	return point_out;
}

for (var tt = 0; tt < lightTypes.length; tt++) {
	var ltype = lightTypes[tt];

	var portIds = Object.keys(ltype.ports);
	portIds.sort();

	for (var portId of Object.keys(ltype.ports)) {
		for (var ptidx = 0; ptidx < ltype.ports[portId].length; ptidx++) {
			var data = { strip: portId, point: transformPt(ltype.ports[portId][ptidx]), index: portId * pixelsPerStrip + ptidx };
			data.group = ltype.group;
			data.protocol = ltype.proto;
			data.address = "address" in ltype ? ltype.address : "127.0.0.1:7890";
			data.size = 0.25;
			pixeldata.push(data);	
		}
	}
}

console.log(JSON.stringify(pixeldata, null, '\t'));
