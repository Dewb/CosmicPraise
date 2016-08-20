// Script to generate layout JSON for Cosmic Praise from CAD model coordinates
//
// usage: node generate_layout.js > cosmicpraise.json

var fs = require('fs');
var path = require('path');
var curves = JSON.parse(fs.readFileSync(path.resolve(__dirname, 'wheel_strip_curves.json'), 'utf8'));

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

var wheel_right_inner = curves["wheel_right_inner0"];
var wheel_right_outer = curves["wheel_right_outer0"];
var wheel_left_inner = scale(wheel_right_inner, [-1, 1, 1]);
var wheel_left_outer = scale(wheel_right_outer, [-1, 1, 1]);
var back_door_right = curves["back_door_right0"];
var back_door_left = scale(back_door_right, [-1, 1, 1]);
var ceiling_center = curves["ceiling_center0"];
var ceiling_right_high = curves["ceiling_right_high0"];
var ceiling_right_low = curves["ceiling_right_low0"]
var ceiling_left_high = scale(ceiling_right_high, [-1, 1, 1]);
var ceiling_left_low = scale(ceiling_right_low, [-1, 1, 1]);

var lightTypes = [
	{ 
		group: "wheel-right", 
		proto: "opc", address: "10.0.0.32:7890", 
		ports: { 0: wheel_right_inner, 1: wheel_right_outer },
	},
	{ 
		group: "wheel-left", 
		proto: "opc", address: "10.0.0.32:7890", 
		ports: { 2: wheel_left_inner, 3: wheel_left_outer },
	},
	{ 
		group: "door-right", 
		proto: "opc", address: "10.0.0.32:7890", 
		ports: { 4: back_door_right },
	},
	{ 
		group: "door-left", 
		proto: "opc", address: "10.0.0.32:7890", 
		ports: { 5: back_door_left },
	},
	{
		group: "ceiling",
		proto: "opc", address: "10.0.0.32:7890",
		ports: { 6: ceiling_right_low, 7: ceiling_right_high, 8: ceiling_center, 9: ceiling_left_high, 10: ceiling_left_low },
	}
];

var pixelsPerStrip = 120;
var pixeldata = [];

function transformPt(point_in) {
	var point_out = [0,-50,0];
	point_out[0] += point_in[0] * 0.25;
	point_out[1] += point_in[2] * 0.25;
	point_out[2] += point_in[1] * 0.25;
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
			data.size = 2;
			pixeldata.push(data);	
		}
	}
}

console.log(JSON.stringify(pixeldata, null, '\t'));
