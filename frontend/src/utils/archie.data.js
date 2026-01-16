const logData = {
  depth: [],
  GR: [],
  RHOB: [],
  NPHI: []
};

// generate mock data
for (let d = 1000; d <= 2000; d += 0.5) {
  logData.depth.push(d);
  logData.GR.push(50 + 30 * Math.sin(d / 50));
  logData.RHOB.push(2.35 + 0.05 * Math.cos(d / 40));
  logData.NPHI.push(0.25 + 0.05 * Math.sin(d / 60));
}