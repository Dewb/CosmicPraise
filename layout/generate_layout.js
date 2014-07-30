var striptypes = [
	{ group: "middle-cw", p0: [0.016, 0.855, 4.143], p1: [-0.82, 0.254, 7.713], pixels: 113, radialrepeat: 12 },
	{ group: "middle-ccw", p0: [0.016, 0.855, 4.143], p1: [0.824, 0.238, 7.702], pixels: 113, radialrepeat: 12 },
	{ group: "top-cw", p0: [0.582, 0.607, 7.788], p1: [0.552, 0.956, 8.961], pixels: 40, radialrepeat: 12 },
	{ group: "top-ccw", p0: [0.607, 0.582, 7.788], p1: [0.956, 0.552, 8.961], pixels: 40, radialrepeat: 12 },
	{ group: "roofline", p0: [-1.204, 0.68, 11.261], p1: [-1.204, -0.68, 11.261], pixels: 70, radialrepeat: 6, arch: 0.5 },
	{ group: "spire-outer", p0: [0, 0.159, 12.7], pixels: 1, radialrepeat: 30, zrepeat: 16 },
	{ group: "spire-inner", p0: [0, 0.079, 12.72], pixels: 1, radialrepeat: 15, zrepeat: 16 },
    { group: "base", quad: [[0.052, 0.862, 3.986], [0.02, 1.788, 0], [ 0.482, 1.72, 0 ], [0.27, 0.819, 3.986]], pixels: 1, radialrepeat: 24 },
    { group: "railing", quad: [[-1.204, 0.324, 10.011], [-1.204, 0.324, 9.301], [-1.204, -0.324, 9.301], [-1.204, -0.324, 10.011]], pixels: 1, radialrepeat: 12 },
    { group: "floodlight", point: [0, 0, 12.25], size: 0.4, pixels: 1, radialrepeat: 1 }
];

var center = [0, 0, 0];

var points = [];

function lerp(a, b, s) {
	return a + (b - a) * s;
}

function lerp3(va, vb, s) {
	return [lerp(va[0], vb[0], s), lerp(va[1], vb[1], s), lerp(va[2], vb[2], s)];
}

function rotate(v, r, center) {
	var d = [v[0] - center[0], v[1] - center[1], v[2] - center[2]];
	var s = Math.sin(r);
	var c = Math.cos(r);

	// rotate around z-axis
	var dn = [d[0] * c - d[1] * s, d[0] * s + d[1] * c, d[2]];
	return [dn[0] + center[0], dn[1] + center[1], dn[2] + center[2]];
}

for (var tt = 0; tt < striptypes.length; tt++) {
	var type = striptypes[tt];
	var rrepeat = type.radialrepeat ? type.radialrepeat : 1;
	var zrepeat = type.zrepeat ? type.zrepeat : 1;

	for (var zz = 0; zz < zrepeat; zz++) {
		for (var ii = 0; ii < rrepeat; ii++) {
			var r = ii * Math.PI * 2 / type.radialrepeat;
			for (var pp = 0; pp < type.pixels; pp++) {
				var item = {
					group: type.group
				};
				if ("p0" in type) {
					var p;
					var p0 = rotate(type.p0, r, center);
					if ("p1" in type) {
						var p1 = rotate(type.p1, r, center);
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
					item.point = rotate(type.point, r, center);
				}
				if ("quad" in type) {
					item.quad = [
						rotate(type.quad[0], r, center),
						rotate(type.quad[1], r, center),
						rotate(type.quad[2], r, center),
						rotate(type.quad[3], r, center),
					];
				}
				if ("size" in type) {
					item.size = type.size;
				}

				points.push(item);
			}
		}
	}
}

console.log(JSON.stringify(points, null, '\t'));