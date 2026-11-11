(() => {
  "use strict";

  const state = {
    briefing: null,
    catalog: null,
    geojson: null,
    selectedCode: null,
    compareCode: null,
    focusOnly: true,
    agendaIndex: 0,
    activeInsight: null,
    emphasisCodes: null,
    mapMode: "insight",
    catalogLayerOn: null,
    catalogPins: null,
    map: null,
    layer: null,
    pins: null,
    labels: null,
    trips: [],
    provinceBounds: null,
    mapReady: false,
    syncingUrl: false,
  };

  const CATALOG_COLORS = {
    "parent-capability-building": "#2f5d50",
    "identification-routing": "#8a5a2b",
    "short-term-interventions": "#3d5a80",
    "foster-care": "#6b4f3a",
    "residential-institutional-care": "#5a6b3d",
    "reintegration-reunification-adoption": "#4a6b6b",
  };

  const $ = (sel) => document.querySelector(sel);
  const isFullMap = () => state.mapMode === "full";

  function fmt(n) {
    if (n === null || n === undefined || Number.isNaN(n)) return "—";
    return Number(n).toLocaleString("en-US");
  }

  function minutesText(n) {
    if (n === null || n === undefined || Number.isNaN(n)) return "—";
    if (n < 60) return `${Number.isInteger(n) ? n : n.toFixed(1)} min`;
    const h = Math.floor(n / 60);
    const m = Math.round(n - h * 60);
    return m === 0 ? `${h} h` : `${h} h ${m} min`;
  }

  function tripSummaryText(d) {
    const name = d.access.nearest_organisation || "unnamed provider";
    return `${minutesText(d.access.car_minutes)} by car to the nearest service provider (${name}) from the district centre`;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function districtByCode(code) {
    return state.briefing.districts.find((d) => d.district_code === code);
  }

  function destinationById(markerId) {
    return state.briefing.destinations.find((d) => d.marker_id === markerId);
  }

  function insightById(id) {
    return state.briefing.insights.find((m) => m.id === id);
  }

  function activeInsight() {
    return state.briefing?.insights?.[state.agendaIndex] || null;
  }

  function isEmphasis(code) {
    if (state.emphasisCodes && state.emphasisCodes.size) {
      return state.emphasisCodes.has(code);
    }
    return Boolean(districtByCode(code)?.in_focus);
  }

  function trackKind(code) {
    const insight = activeInsight();
    const accents = insight?.track_accents;
    if (!accents) return null;
    if ((accents.finding || []).includes(code)) return "finding";
    if ((accents.follow_up || []).includes(code)) return "follow_up";
    return null;
  }

  function updateUrl() {
    if (state.syncingUrl) return;
    const params = new URLSearchParams();
    const insight = activeInsight();
    if (insight) params.set("insight", insight.id);
    if (state.selectedCode) params.set("district", state.selectedCode);
    if (state.compareCode) params.set("compare", state.compareCode);
    if (isFullMap()) params.set("map", "full");
    history.replaceState(null, "", `${location.pathname}?${params.toString()}`);
  }

  function readUrl() {
    const params = new URLSearchParams(location.search);
    let insight = params.get("insight");
    // Legacy redirects
    if (!insight && params.get("view") === "moves") {
      const step = Number(params.get("step") || "1");
      const last = Math.max(0, (state.briefing?.insights?.length || 1) - 1);
      const idx = Math.max(0, Math.min(last, step - 1));
      insight = state.briefing?.insights?.[idx]?.id || null;
    }
    if (!insight && (params.get("view") === "family" || params.get("view") === "education")) {
      insight = state.briefing?.insights?.[0]?.id || null;
    }
    return {
      insight,
      district: params.get("district"),
      compare: params.get("compare"),
      map: params.get("map") === "full" ? "full" : "insight",
    };
  }

  function syncModeToggle() {
    const insightBtn = $("#mode-insight");
    const fullBtn = $("#mode-full");
    if (!insightBtn || !fullBtn) return;
    const full = isFullMap();
    insightBtn.classList.toggle("is-active", !full);
    fullBtn.classList.toggle("is-active", full);
    insightBtn.setAttribute("aria-pressed", full ? "false" : "true");
    fullBtn.setAttribute("aria-pressed", full ? "true" : "false");
  }

  function renderLegend() {
    const legend = $("#legend-insight");
    if (!legend) return;

    if (isFullMap()) {
      const layers = state.catalog?.layers || [];
      const rows = layers
        .map((layer) => {
          const on = state.catalogLayerOn?.has(layer.id);
          const color = CATALOG_COLORS[layer.id] || "#2f5d50";
          return `<label class="legend-layer">
            <input type="checkbox" data-layer-id="${escapeHtml(layer.id)}" ${
              on ? "checked" : ""
            } />
            <span class="swatch door" style="background:${color};border-color:${color}"></span>
            <span>${escapeHtml(layer.name)}</span>
          </label>`;
        })
        .join("");
      legend.classList.add("is-interactive");
      legend.innerHTML = `<h3>Map layers</h3>${rows}`;
      legend.querySelectorAll("input[data-layer-id]").forEach((input) => {
        input.addEventListener("change", () => {
          const id = input.dataset.layerId;
          if (!state.catalogLayerOn) state.catalogLayerOn = new Set();
          if (input.checked) state.catalogLayerOn.add(id);
          else state.catalogLayerOn.delete(id);
          refreshCatalogPins();
        });
      });
      return;
    }

    legend.classList.remove("is-interactive");
    const LBL = state.briefing.legend;
    const insight = activeInsight();
    const pinRow =
      insight?.show_pins === "all_delivery"
        ? `<div class="legend-row"><span class="swatch door"></span><span>${escapeHtml(LBL.site)}</span></div>`
        : insight?.show_pins === "family_public"
          ? `<div class="legend-row"><span class="swatch door"></span><span>${escapeHtml(LBL.door)}</span></div>`
          : "";
    const tripRows = state.selectedCode
      ? `
      <div class="legend-row"><span class="swatch nearest"></span><span>Nearest service provider for the selected district</span></div>
      <div class="legend-row"><span class="swatch centre"></span><span>${escapeHtml(LBL.centre)}</span></div>
      <div class="legend-row"><span class="swatch trip"></span><span>${escapeHtml(LBL.trip)}</span></div>`
      : "";
    const body = `${pinRow}${tripRows}`;
    legend.innerHTML = body ? `<h3>Map key</h3>${body}` : "";
  }

  function renderInsights() {
    $("#reading-rules").innerHTML = state.briefing.reading_rules
      .map((r) => `<div>${escapeHtml(r)}</div>`)
      .join("");

    const list = $("#insights-list");
    list.innerHTML = state.briefing.insights
      .map(
        (insight, i) => `
      <button type="button" class="insight-card${
        i === state.agendaIndex ? " is-agenda" : ""
      }" data-insight-id="${insight.id}" aria-expanded="${
          i === state.agendaIndex ? "true" : "false"
        }">
        <h2>${i + 1}. ${escapeHtml(insight.title)}</h2>
        <div class="insight-body">
          <p class="problem">${escapeHtml(insight.problem)}</p>
          <p class="action">${escapeHtml(insight.action)}</p>
        </div>
      </button>`
      )
      .join("");

    list.querySelectorAll(".insight-card").forEach((card) => {
      card.addEventListener("click", () => {
        const idx = state.briefing.insights.findIndex(
          (m) => m.id === card.dataset.insightId
        );
        state.agendaIndex = Math.max(0, idx);
        if (isFullMap()) setMapMode("insight");
        openInsight(card.dataset.insightId);
      });
    });

    $("#sources").textContent = `Sources: ${state.briefing.sources.join(" · ")}`;
    updateAgendaLabel();
  }

  function updateAgendaLabel() {
    const i = state.agendaIndex;
    document.querySelectorAll(".insight-card").forEach((card, idx) => {
      const on = idx === i;
      card.classList.toggle("is-agenda", on);
      card.setAttribute("aria-expanded", on ? "true" : "false");
    });
  }

  function fillSelects() {
    const sorted = [...state.briefing.districts].sort((a, b) =>
      a.district_code.localeCompare(b.district_code)
    );
    const options = sorted
      .map(
        (d) =>
          `<option value="${d.district_code}">${d.district_code} · ${escapeHtml(
            d.district_en
          )}</option>`
      )
      .join("");
    $("#compare-district").innerHTML = `<option value="">None</option>${options}`;

    $("#compare-district").addEventListener("change", (e) => {
      setCompare(e.target.value || null);
    });
  }

  function familyBodyHtml(d) {
    const orgs = (d.family.family_support_organisations || "")
      .split(";")
      .map((s) => s.trim())
      .filter(Boolean);
    const approxNote =
      d.district_code === "5005"
        ? `<p class="note">Seven homes are recorded only as the district. They are not pins. The family-support count is 0.</p>`
        : d.family.n_approximated > 0
          ? `<p class="note">${fmt(d.family.n_approximated)} of the delivery sites are approximated locations, not exact public service providers.</p>`
          : "";
    const maeAiNote =
      d.district_code === "5010"
        ? `<p class="note">The line ends at the Mae Rim family shelter. No drive to the after-school sites was estimated.</p>`
        : "";
    return `
      <h3>Family support statistics</h3>
      <div class="stat-grid">
        <div class="stat"><span class="value">${fmt(d.family.n_family_support_sites)}</span><span class="label">Family-support sites</span></div>
        <div class="stat"><span class="value">${fmt(d.family.tpmap_target_poor)}</span><span class="label">People in poverty count</span></div>
        <div class="stat"><span class="value">${fmt(d.family.thai_reg_age_0_17)}</span><span class="label">Registered Thai children 0–17</span></div>
        <div class="stat"><span class="value">${fmt(d.family.n_delivery_or_mixed)}</span><span class="label">All delivery / mixed sites</span></div>
        <div class="stat"><span class="value">${minutesText(d.access.car_minutes)}</span><span class="label">Car from district centre</span></div>
        <div class="stat"><span class="value">${minutesText(d.access.walk_minutes)}</span><span class="label">Same trip on foot</span></div>
      </div>
      ${
        orgs.length
          ? `<h3>Identified family-support organisations</h3><ul class="org-list">${orgs
              .map((o) => `<li>${escapeHtml(o)}</li>`)
              .join("")}</ul>`
          : `<p class="note">No family-support organisation on this list for this district.</p>`
      }
      ${approxNote}${maeAiNote}
    `;
  }

  function educationBodyHtml(d) {
    const afterSchool = (d.education.after_school_organisations || "")
      .split(";")
      .map((s) => s.trim())
      .filter(Boolean);
    const campus = (d.education.school_campus_organisations || "")
      .split(";")
      .map((s) => s.trim())
      .filter(Boolean);
    return `
      <h3>School-list columns</h3>
      <div class="stat-grid">
        <div class="stat"><span class="value">${fmt(d.education.home_not_found)}</span><span class="label">Houses not found</span></div>
        <div class="stat"><span class="value">${fmt(d.education.consented)}</span><span class="label">Agreed to share information</span></div>
        <div class="stat"><span class="value">${fmt(d.education.help_wanted)}</span><span class="label">Help wanted</span></div>
        <div class="stat"><span class="value">${fmt(d.education.never_studied)}</span><span class="label">Never studied</span></div>
        <div class="stat is-aside"><span class="value">${fmt(d.education.moved_away)}</span><span class="label">Moved away — set aside</span></div>
        <div class="stat is-aside"><span class="value">${fmt(d.education.already_enrolled)}</span><span class="label">Already enrolled — set aside</span></div>
      </div>
      <p class="note">Headline total ${fmt(d.education.dole_total)}. That total includes moved-away and already-enrolled records.</p>
      <h3>After-school service providers identified</h3>
      <div class="stat-grid">
        <div class="stat"><span class="value">${fmt(d.education.n_after_school)}</span><span class="label">After-school sites</span></div>
        <div class="stat"><span class="value">${fmt(d.education.n_school_campus)}</span><span class="label">School campus sites</span></div>
      </div>
      ${
        afterSchool.length
          ? `<ul class="org-list">${afterSchool
              .map((o) => `<li>After-school: ${escapeHtml(o)}</li>`)
              .join("")}</ul>`
          : ""
      }
      ${
        campus.length
          ? `<ul class="org-list">${campus
              .map((o) => `<li>School campus: ${escapeHtml(o)}</li>`)
              .join("")}</ul>`
          : ""
      }
    `;
  }

  function renderPanel(code) {
    const d = districtByCode(code);
    const panel = $("#panel-insight");
    if (!d || !panel) return;
    const insight = activeInsight();
    const fields = insight?.panel_fields || "both";
    let body = "";
    if (fields === "family" || fields === "both") body += familyBodyHtml(d);
    if (fields === "education" || fields === "both") body += educationBodyHtml(d);
    panel.innerHTML = `
      <div class="panel-title">
        <h2>${escapeHtml(d.district_en)}</h2>
        <p class="note">${escapeHtml(d.district_th)} · ${d.district_code}</p>
      </div>
      <p class="action-sentence">${escapeHtml(d.action_sentence)}</p>
      ${
        fields !== "education"
          ? `<p class="trip-summary">${escapeHtml(tripSummaryText(d))}</p>`
          : ""
      }
      ${body}
    `;
  }

  function renderComparePanel() {
    const wrap = $("#panels-insight");
    const panel = $("#panel-insight-compare");
    if (!state.compareCode) {
      panel.hidden = true;
      panel.innerHTML = "";
      wrap.classList.remove("has-compare");
      return;
    }
    const d = districtByCode(state.compareCode);
    if (!d) return;
    const insight = activeInsight();
    const fields = insight?.panel_fields || "both";
    let body = "";
    if (fields === "family" || fields === "both") body += familyBodyHtml(d);
    if (fields === "education" || fields === "both") body += educationBodyHtml(d);
    panel.hidden = false;
    wrap.classList.add("has-compare");
    panel.innerHTML = `
      <p class="note">Compare</p>
      <div class="panel-title">
        <h2>${escapeHtml(d.district_en)}</h2>
        <p class="note">${escapeHtml(d.district_th)} · ${d.district_code}</p>
      </div>
      <p class="action-sentence">${escapeHtml(d.action_sentence)}</p>
      ${
        fields !== "education"
          ? `<p class="trip-summary">${escapeHtml(tripSummaryText(d))}</p>`
          : ""
      }
      ${body}
    `;
  }

  function styleFeature(feature) {
    const code = feature.properties.district_code;
    const emphasis = isFullMap() ? false : isEmphasis(code);
    const selected = code === state.selectedCode;
    const compare = code === state.compareCode;
    const faded =
      !isFullMap() && state.focusOnly && !emphasis && !selected && !compare;
    const track = isFullMap() ? null : trackKind(code);

    if (compare && !selected) {
      return {
        color: "#5b4a8a",
        weight: 2.5,
        fillColor: "#cfc4e6",
        fillOpacity: 0.55,
        opacity: 1,
      };
    }
    if (selected) {
      return {
        color: "#1f3d36",
        weight: 2.5,
        fillColor: "#2f5d50",
        fillOpacity: 0.55,
        opacity: 1,
      };
    }
    if (track === "finding") {
      return {
        color: "#8a5a2b",
        weight: 2,
        fillColor: "#c4a882",
        fillOpacity: faded ? 0.12 : 0.5,
        opacity: faded ? 0.25 : 1,
      };
    }
    if (track === "follow_up") {
      return {
        color: "#3d5a80",
        weight: 2,
        fillColor: "#b7c4d6",
        fillOpacity: faded ? 0.12 : 0.5,
        opacity: faded ? 0.25 : 1,
      };
    }
    return {
      color: "#6f7f76",
      weight: 1,
      fillColor: emphasis ? "#b7cfc4" : "#dfe8e3",
      fillOpacity: faded ? 0.12 : emphasis ? 0.45 : 0.28,
      opacity: faded ? 0.25 : 1,
    };
  }

  function clearTrips() {
    state.trips.forEach((t) => {
      if (t.line) t.line.remove();
      if (t.origin) t.origin.remove();
    });
    state.trips = [];
  }

  function tripLabelText(d) {
    return tripSummaryText(d);
  }

  function nearestMarkerId() {
    const d = districtByCode(state.selectedCode);
    return d?.access?.nearest_marker_id || null;
  }

  function providerPinOptions(dest, highlighted) {
    if (highlighted) {
      return {
        radius: 9,
        color: "#8a5a2b",
        weight: 3,
        fillColor: "#e6c48a",
        fillOpacity: 1,
      };
    }
    const family = dest.is_family_support !== false;
    return {
      radius: family ? 6 : 5,
      color: "#1f3d36",
      weight: 2,
      fillColor: family ? "#2f5d50" : "#6f7f76",
      fillOpacity: family ? 0.95 : 0.9,
    };
  }

  function addProviderPin(dest) {
    const highlighted = dest.marker_id === nearestMarkerId();
    const marker = L.circleMarker(
      [dest.lat, dest.lon],
      providerPinOptions(dest, highlighted)
    );
    marker._markerId = dest.marker_id;
    marker._isNearest = highlighted;
    marker.bindTooltip(
      `${dest.organisation}<br>${dest.marker_id} · ${dest.district_en}`,
      { className: "door-tooltip", direction: "top", offset: [0, -8], opacity: 0.96 }
    );
    state.pins.addLayer(marker);
    return marker;
  }

  function drawTripForCode(code) {
    const map = state.map;
    if (!map) return;
    const d = districtByCode(code);
    if (!d) return;
    const dest = destinationById(d.access.nearest_marker_id);
    if (!dest) return;
    const latlngs = [
      [d.centroid.lat, d.centroid.lon],
      [dest.lat, dest.lon],
    ];
    const line = L.polyline(latlngs, {
      color: "#8a5a2b",
      weight: 3,
      dashArray: "6 6",
      opacity: 0.95,
      interactive: true,
    }).addTo(map);
    line.bindTooltip(tripLabelText(d), {
      sticky: true,
      direction: "top",
      opacity: 0.95,
      className: "trip-tooltip",
    });
    const origin = L.circleMarker(latlngs[0], {
      radius: 5,
      color: "#8a5a2b",
      weight: 2,
      fillColor: "#f7f5f1",
      fillOpacity: 1,
      interactive: false,
    }).addTo(map);
    state.trips.push({ line, origin, code });
  }

  function raiseMarkersAboveDistricts() {
    state.trips.forEach((t) => {
      t.line?.bringToFront();
      t.origin?.bringToFront();
    });
    if (state.catalogPins) {
      state.catalogPins.eachLayer((layer) => layer.bringToFront());
    }
    if (!state.pins) return;
    let nearest = null;
    state.pins.eachLayer((layer) => {
      if (layer._isNearest) nearest = layer;
      else layer.bringToFront();
    });
    nearest?.bringToFront();
  }

  function refreshTrips() {
    clearTrips();
    if (isFullMap()) return;
    if (state.selectedCode) drawTripForCode(state.selectedCode);
    raiseMarkersAboveDistricts();
  }

  function clearCatalogPins() {
    if (state.catalogPins) state.catalogPins.clearLayers();
  }

  function catalogPopupHtml(place) {
    const bits = [
      `<strong>${escapeHtml(place.name)}</strong>`,
      place.address ? `<div>${escapeHtml(place.address)}</div>` : "",
      place.stage ? `<div>${escapeHtml(place.stage)}</div>` : "",
      place.location_precision
        ? `<div class="note">${escapeHtml(place.location_precision)}</div>`
        : "",
      place.safeguarding_reason
        ? `<div class="note">${escapeHtml(place.safeguarding_reason)}</div>`
        : "",
    ];
    return bits.filter(Boolean).join("");
  }

  function refreshCatalogPins() {
    const map = state.map;
    if (!map || !state.catalog) return;
    if (!state.catalogPins) state.catalogPins = L.layerGroup().addTo(map);
    state.catalogPins.clearLayers();
    if (!isFullMap()) return;

    (state.catalog.layers || []).forEach((layer) => {
      if (!state.catalogLayerOn?.has(layer.id)) return;
      const color = CATALOG_COLORS[layer.id] || "#2f5d50";
      (layer.places || []).forEach((place) => {
        if (place.lat == null || place.lon == null) return;
        const marker = L.circleMarker([place.lat, place.lon], {
          radius: 6,
          color,
          weight: 2,
          fillColor: color,
          fillOpacity: 0.9,
        });
        marker.bindPopup(catalogPopupHtml(place), {
          className: "catalog-popup",
          maxWidth: 280,
        });
        marker.bindTooltip(place.name, {
          className: "door-tooltip",
          direction: "top",
          offset: [0, -8],
          opacity: 0.96,
        });
        state.catalogPins.addLayer(marker);
      });
    });
    raiseMarkersAboveDistricts();
  }

  function refreshPins() {
    const map = state.map;
    if (!map) return;
    if (state.pins) {
      state.pins.clearLayers();
    } else {
      state.pins = L.layerGroup().addTo(map);
    }
    if (isFullMap()) {
      raiseMarkersAboveDistricts();
      return;
    }
    const insight = activeInsight();
    const mode = insight?.show_pins || "none";
    if (mode === "none") return;

    if (mode === "family_public") {
      state.briefing.destinations.forEach((dest) => addProviderPin(dest));
      raiseMarkersAboveDistricts();
      return;
    }

    (state.briefing.delivery_pins || []).forEach((dest) => addProviderPin(dest));
    raiseMarkersAboveDistricts();
  }

  function refreshLabels() {
    const map = state.map;
    if (!map) return;
    if (state.labels) {
      state.labels.clearLayers();
    } else {
      state.labels = L.layerGroup().addTo(map);
    }
    const zoom = map.getZoom();
    const showEmphasisLabels = zoom >= 9;
    state.briefing.districts.forEach((d) => {
      const selected = d.district_code === state.selectedCode;
      const compare = d.district_code === state.compareCode;
      const emphasis = isEmphasis(d.district_code);
      if (!selected && !compare && !(showEmphasisLabels && emphasis)) return;
      if (state.focusOnly && !emphasis && !selected && !compare) return;
      const cls = [
        "district-label",
        selected ? "is-selected" : "",
        compare && !selected ? "is-compare" : "",
      ]
        .filter(Boolean)
        .join(" ");
      const marker = L.marker([d.centroid.lat, d.centroid.lon], {
        interactive: false,
        keyboard: false,
        icon: L.divIcon({
          className: "",
          html: `<div class="${cls}">${escapeHtml(d.district_en)}</div>`,
          iconSize: [0, 0],
          iconAnchor: [0, 0],
        }),
      });
      state.labels.addLayer(marker);
    });
  }

  function restyleMap() {
    if (!state.layer) return;
    state.layer.eachLayer((lyr) => {
      if (!lyr.feature) return;
      lyr.setStyle(styleFeature(lyr.feature));
    });
    refreshLabels();
  }

  function selectDistrict(code) {
    if (!code || !districtByCode(code)) return;
    if (state.compareCode === code) state.compareCode = null;
    state.selectedCode = code;
    restyleMap();
    renderPanel(code);
    renderComparePanel();
    refreshPins();
    refreshTrips();
    renderLegend();
    if (!isFullMap()) focusInsightOnMap();
    const sel = $("#compare-district");
    if (sel && state.compareCode) sel.value = state.compareCode;
    updateUrl();
  }

  function setCompare(code) {
    if (code && code === state.selectedCode) code = null;
    state.compareCode = code || null;
    restyleMap();
    renderComparePanel();
    if (!isFullMap()) focusInsightOnMap();
    updateUrl();
  }

  function fitProvinceOnce() {
    const map = state.map;
    if (!map) return;
    map.invalidateSize();
    map.fitBounds(provinceBounds().pad(0.08), {
      animate: false,
      padding: [28, 28],
    });
  }

  function setMapMode(mode) {
    const next = mode === "full" ? "full" : "insight";
    const changed = state.mapMode !== next;
    state.mapMode = next;
    syncModeToggle();

    if (isFullMap()) {
      if (!state.catalogLayerOn && state.catalog?.layers) {
        state.catalogLayerOn = new Set(state.catalog.layers.map((l) => l.id));
      }
      clearTrips();
      if (state.pins) state.pins.clearLayers();
      state.focusOnly = false;
      restyleMap();
      refreshCatalogPins();
      renderLegend();
      if (changed) fitProvinceOnce();
    } else {
      clearCatalogPins();
      state.focusOnly = true;
      restyleMap();
      refreshPins();
      refreshTrips();
      renderLegend();
      if (changed) focusInsightOnMap();
    }
    updateUrl();
  }

  function provinceBounds() {
    if (state.provinceBounds) return state.provinceBounds;
    const focusCodes = new Set(state.briefing.focus_district_codes);
    const focusFeatures = state.geojson.features.filter((f) =>
      focusCodes.has(f.properties.district_code)
    );
    state.provinceBounds = L.geoJSON({
      type: "FeatureCollection",
      features: focusFeatures.length ? focusFeatures : state.geojson.features,
    }).getBounds();
    return state.provinceBounds;
  }

  function emphasisBounds() {
    const codes = state.emphasisCodes;
    if (!codes || !codes.size) return provinceBounds();
    const features = state.geojson.features.filter((f) =>
      codes.has(f.properties.district_code)
    );
    if (!features.length) return provinceBounds();
    return L.geoJSON({ type: "FeatureCollection", features }).getBounds();
  }

  function insightViewBounds() {
    const points = [];
    const codes = state.emphasisCodes;
    if (codes && codes.size) {
      state.geojson.features.forEach((feature) => {
        if (!codes.has(feature.properties.district_code)) return;
        const box = L.geoJSON(feature).getBounds();
        points.push(box.getSouthWest(), box.getNorthEast());
      });
    }
    if (state.selectedCode) {
      const selected = districtByCode(state.selectedCode);
      if (selected) {
        points.push(L.latLng(selected.centroid.lat, selected.centroid.lon));
        const dest = destinationById(selected.access.nearest_marker_id);
        if (dest) points.push(L.latLng(dest.lat, dest.lon));
      }
      const feature = state.geojson.features.find(
        (f) => f.properties.district_code === state.selectedCode
      );
      if (feature) {
        const box = L.geoJSON(feature).getBounds();
        points.push(box.getSouthWest(), box.getNorthEast());
      }
    }
    if (state.compareCode) {
      const feature = state.geojson.features.find(
        (f) => f.properties.district_code === state.compareCode
      );
      if (feature) {
        const box = L.geoJSON(feature).getBounds();
        points.push(box.getSouthWest(), box.getNorthEast());
      }
    }
    if (!points.length) return provinceBounds();
    return L.latLngBounds(points);
  }

  function focusInsightOnMap() {
    const map = state.map;
    if (!map) return;
    const fit = () => {
      map.invalidateSize();
      map.fitBounds(insightViewBounds().pad(0.12), {
        animate: false,
        padding: [28, 28],
      });
    };
    fit();
    requestAnimationFrame(fit);
    state.mapReady = true;
  }

  function openInsight(insightId) {
    const insight = insightById(insightId);
    if (!insight) return;
    const idx = state.briefing.insights.findIndex((m) => m.id === insightId);
    if (idx >= 0) state.agendaIndex = idx;

    if (isFullMap()) {
      state.mapMode = "insight";
      syncModeToggle();
      clearCatalogPins();
    }

    state.activeInsight = insight;
    state.emphasisCodes = new Set(insight.emphasis_codes || insight.district_codes || []);
    state.focusOnly = true;

    updateAgendaLabel();
    renderLegend();
    refreshPins();
    refreshTrips();
    restyleMap();

    const code = insight.default_district || insight.district_codes[0];
    if (code) selectDistrict(code);
    requestAnimationFrame(() => {
      focusInsightOnMap();
      refreshTrips();
    });
    updateUrl();
  }

  function initMap() {
    const map = L.map("map-insight", {
      scrollWheelZoom: true,
      zoomControl: false,
      preferCanvas: true,
      inertia: true,
      zoomSnap: 0.25,
      zoomDelta: 0.5,
      wheelPxPerZoomLevel: 120,
    }).setView([18.8, 98.95], 8);

    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      {
        maxZoom: 16,
        attribution: "Tiles &copy; Esri",
      }
    ).addTo(map);
    L.control.zoom({ position: "topright" }).addTo(map);
    L.control.scale({ metric: true, imperial: false }).addTo(map);

    const layer = L.geoJSON(state.geojson, {
      style: (feat) => styleFeature(feat),
      onEachFeature: (feature, lyr) => {
        lyr.on({
          click: () => selectDistrict(feature.properties.district_code),
          mouseover: (e) => {
            const code = feature.properties.district_code;
            if (code !== state.selectedCode && code !== state.compareCode) {
              e.target.setStyle({
                weight: 2,
                fillOpacity: Math.min(
                  0.7,
                  (styleFeature(feature).fillOpacity || 0.3) + 0.15
                ),
              });
              if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
                e.target.bringToFront();
              }
            }
            raiseMarkersAboveDistricts();
          },
          mouseout: (e) => {
            e.target.setStyle(styleFeature(feature));
          },
        });
      },
    }).addTo(map);

    state.map = map;
    state.layer = layer;
    state.pins = L.layerGroup().addTo(map);
    state.labels = L.layerGroup().addTo(map);
    state.catalogPins = L.layerGroup().addTo(map);
    map.on("zoomend", () => refreshLabels());
    renderLegend();

    $("#mode-insight")?.addEventListener("click", () => setMapMode("insight"));
    $("#mode-full")?.addEventListener("click", () => setMapMode("full"));
    syncModeToggle();
  }

  async function boot() {
    const [briefing, geojson, catalog] = await Promise.all([
      fetch("data/briefing.json?v=6").then((r) => r.json()),
      fetch("data/districts.geojson").then((r) => r.json()),
      fetch("data/catalog.json?v=1").then((r) => r.json()),
    ]);
    state.briefing = briefing;
    state.geojson = geojson;
    state.catalog = catalog;
    state.catalogLayerOn = new Set((catalog.layers || []).map((l) => l.id));

    $("#data-badge").textContent = `Data as of ${briefing.data_as_of}`;
    $("#audience").textContent = briefing.audience || "";

    renderInsights();
    fillSelects();
    initMap();

    const initial = readUrl();
    state.syncingUrl = true;
    let startId = initial.insight || state.briefing.insights[0].id;
    if (!insightById(startId)) startId = state.briefing.insights[0].id;
    openInsight(startId);
    if (initial.district) selectDistrict(initial.district);
    if (initial.compare) setCompare(initial.compare);
    if (initial.map === "full") setMapMode("full");
    state.syncingUrl = false;
    updateUrl();
  }

  boot().catch((err) => {
    document.body.innerHTML = `<main style="padding:2rem;font-family:sans-serif"><h1>Preview failed to load</h1><p>${escapeHtml(
      err.message
    )}</p><p>Serve the preview folder over HTTP so the JSON files can load.</p></main>`;
  });
})();
