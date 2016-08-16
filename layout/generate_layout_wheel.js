// Script to generate layout JSON for Cosmic Praise from CAD model coordinates
//
// usage: node generate_layout.js > cosmicpraise.json

/*
wheel-right
wheel-left
door-right
door-left
mid-left-long-low
mid-left-long-mid
mid-left-long-high
mid-left-short-low
mid-left-short-mid
mid-left-short-high
mid-right-long-low
mid-right-long-mid
mid-right-long-high
mid-right-short-low
mid-right-short-mid
mid-right-short-high
*/

var lightTypes = [
	{ 
		group: "wheel-right", 
		proto: "opc", address: "10.0.0.32:7890", 
		ports: [0, 1],
	  	p0: [25.92, 24.764, 17.292], center: [25.92, 0, 58.089], pixels: 1, 
	  	arclength: Math.PI * 5/3, radialrepeat: 113, axis: "x", striplength: 120,
	  	size: 0.1
	},
	{ 
		group: "wheel-left", 
		proto: "opc", address: "10.0.0.32:7890", 
		ports: [2, 3],
	  	p0: [-25.92, 24.764, 17.292], center: [-25.92, 0, 58.089], pixels: 1, 
	  	arclength: Math.PI * 5/3, radialrepeat: 113, axis: "x", striplength: 120,
	  	size: 0.1
	},
/*
	{ 
		group: "door-right", 
		proto: "opc", address: "10.0.0.32:7890", 
		ports: [4],
		shape: "ellipse",
	  	p0: [0.956, 0.552, 8.875], p1: [0,0,0], pixels: 1, radialrepeat: 113, axis: "x", striplength: 120
	},
	{ 
		group: "door-left", 
		proto: "opc", address: "10.0.0.32:7890", 
		ports: [5],
		shape: "ellipse",
	  	p0: [0.956, 0.552, 8.875], p1: [0,0,0], pixels: 1, radialrepeat: 113, axis: "x", striplength: 120
	},
	{
		group: "entry-left",
		proto: "opc", address: "10.0.0.32:7890",
		ports: [6],
		p0: [0,0,0], p1: [0,0,0], pixels: 113, arch: 0.75
	},
	{
		group: "entry-right",
		proto: "opc", address: "10.0.0.32:7890",
		ports: [7],
		p0: [0,0,0], p1: [0,0,0], pixels: 113, arch: 0.75
	}
	*/
];

var pixelsPerStrip = 120

var center = [0, 0, 0];

var points = [];

function lerp(a, b, s) {
	return a + (b - a) * s;
}

function lerp3(va, vb, s) {
	return [lerp(va[0], vb[0], s), lerp(va[1], vb[1], s), lerp(va[2], vb[2], s)];
}

function rotate(v, r, center, axis) {
	axis = axis || "z";
	var d = [v[0] - center[0], v[1] - center[1], v[2] - center[2]];
	var s = Math.sin(r);
	var c = Math.cos(r);

	var dn = [0, 0, 0];
	if (axis == "z") {
		dn = [d[0] * c - d[1] * s, d[0] * s + d[1] * c, d[2]];
	}
	else if (axis == "x") {
		dn = [d[0], d[1] * c - d[2] * s, d[1] * s + d[2] * c];
	}
	if (axis == "y") {
		dn = [d[2] * s + d[0] * c, d[1], d[2] * c - d[0] * s];
	}
	
	return [dn[0] + center[0], dn[1] + center[1], dn[2] + center[2]];
}

for (var tt = 0; tt < lightTypes.length; tt++) {
	var type = lightTypes[tt];
	var rrepeat = type.radialrepeat ? type.radialrepeat : 1;
	var zrepeat = type.zrepeat ? type.zrepeat : 1;
	var arclength = type.arclength || Math.PI * 2;

	for (var zz = 0; zz < zrepeat; zz++) {
		for (var ii = 0; ii < rrepeat; ii++) {
			var r = ii * arclength / rrepeat + ("startangle" in type ? type.startangle : 0);
			for (var pp = 0; pp < type.pixels; pp++) {
				var item = {
					group: type.group,
					protocol: type.proto
				};

				var address = "127.0.0.1:7890";
				if ("address" in type) {
					address = type.address;
				} else if ("addresses" in type) {
					var addrindex = Math.floor(type.addresses.length * (zz * rrepeat + ii) / (zrepeat * rrepeat));
					address = type.addresses[addrindex];
				}
				item.address = address;

				if (type.proto == "opc") {
					var port = 0;
					if ("port" in type) {
						port = type.port;
					} else if ("ports" in type) {
						var portindex = Math.floor(type.ports.length * (zz * rrepeat + ii) / (zrepeat * rrepeat));
						port = type.ports[portindex];
					}
					item.strip = port;
					pixelIndex = pp;
					if ("striplength" in type && type.striplength != type.pixels) {
						pixelIndex = (zz * rrepeat * type.pixels + ii * type.pixels + pp) % type.striplength;
					}
					item.index = port * pixelsPerStrip + pixelIndex;
				} else if (type.proto == "kinet") {
					if ("address" in type) {
						item.index = zz * rrepeat + ii;
					} else if ("addresses" in type) {
						// do a bunch of unnecessary math because Chooch is playing the Spin Doctors and I can't think straight
						//var pixelsPerAddress = zrepeat * rrepeat / type.addresses.length;
						var overallIndex = zz * rrepeat + ii;
						//var addrindex = Math.floor(type.addresses.length * (zz * rrepeat + ii) / (zrepeat * rrepeat));
						//item.index = overallIndex - pixelsPerAddress * addrindex;
                                                item.index = overallIndex
					}
				}

				if ("p0" in type) {
					var p;
					var p0 = rotate(type.p0, r, type.center || center, type.axis);
					if ("p1" in type) {
						var p1 = rotate(type.p1, r, type.center || center);
						p = lerp3(p0, p1, pp / type.pixels);
					} else {
						p = p0;
					}
					p[2] = p[2] + 0.15 * zz;
					if ("arch" in type) {
						p[2] = p[2] + (1 - Math.abs(pp - type.pixels/2) / type.pixels/2) * type.arch;
					}
					item.point = p;
				}
				if ("point" in type) {
					item.point = rotate(type.point, r, type.center || center, type.axis);
				}
				if ("quad" in type) {
					item.quad = [
						rotate(type.quad[0], r, type.center || center, type.axis),
						rotate(type.quad[1], r, type.center || center, type.axis),
						rotate(type.quad[2], r, type.center || center, type.axis),
						rotate(type.quad[3], r, type.center || center, type.axis),
					];
				}
				if ("size" in type) {
					item.size = type.size;
				}

				item.point[0] = item.point[0] / 10;
				item.point[1] = item.point[1] / 10;
				item.point[2] = item.point[2] / 10;
				points.push(item);
			}
		}
	}
}

console.log(JSON.stringify(points, null, '\t'));
