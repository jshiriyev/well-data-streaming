import { fetchWells } from "@api/fetch.wells.js";
import { SessionState } from "./Session.State.js";

const getLayerGroup = () => {
  if (typeof window !== "undefined" && window.wellPointFeatureGroup) {
    return window.wellPointFeatureGroup;
  }
  return null;
};

export async function updateMap(layerGroup) {
  const targetGroup = layerGroup ?? getLayerGroup();
  if (!targetGroup) {
    throw new Error("wellPointFeatureGroup is not initialized");
  }

  const wells = await fetchWells(SessionState.horizon, SessionState.time);
  // convert them to markers
  targetGroup.clearLayers();
  wells.forEach(w => {
    L.circleMarker([w.lat, w.lon], {
      bubblingMouseEvents: true,
			color: '#CC5500',
			dashArray: null,
			dashOffset: null,
			fill: true,
			fillColor: '#CC5500',
			fillOpacity: 1.,
			fillRule: "evenodd",
			lineCap: "round",
			lineJoin: "round",
			opacity: 1.0,
			radius: 4,
			weight: 1,
			stroke: true,
    })
    .bindPopup(`${w.well} (${w.horizon})<br>Spud: ${w.spud_date}`)
    .addTo(targetGroup);
  });
}
