from branca.element import MacroElement, Element
from jinja2 import Template

class MultiFilter(MacroElement):
    """
    Parameters
    ----------
    feature_group : folium.FeatureGroup
    cols : list[str]                 # desired control order (categorical + numeric mixed)
    num_cols : list[str]             # subset of cols that are numeric (double-ended sliders)
    pane_id : str
    container_id : str

    Behavior
    --------
    • Categorical values show "(available/initial)" counts from the start.
    • Categorical choices update other cats and recolor slider availability, but DO NOT move pins.
    • Slider pins only move when the user drags them. JS never changes their values except on "Reset".
    • Slider ranges (rails) stay fixed to initial min/max. Track is colored to show available interval.
    • Slider changes impact categorical availability counts the same way category picks do.
    • "Reset filters" restores full rails + All.

    """
    _template = Template("""
    {% macro script(this, kwargs) %}
    (function(){
      var map    = {{ this._parent.get_name() }};
      var grp    = {{ this.group_name }};
      var orderedCols = {{ this.ordered_cols | tojson }};
      var numSet = {{ this.num_set | tojson }};   // {col: true, ...}
      var paneId = {{ this.pane_id | tojson }};
      var containerId = {{ this.container_id | tojson }};

      var catCols = orderedCols.filter(c => !numSet[c]);
      var numCols = orderedCols.filter(c =>  numSet[c]);

      // ---------- Collect layers ----------
      var allLayers = [];
      grp.eachLayer(function(l){
        if (!l) return;
        if (l instanceof L.Marker || l instanceof L.CircleMarker || l instanceof L.Circle || l.__attrs) {
          allLayers.push(l);
        }
      });

      function getAttr(layer, col){
        return (layer && layer.__attrs) ? layer.__attrs[col] : null;
      }

      // ---------- Initial universes ----------
      function uniq(values){
        var s = new Set();
        for (var i=0;i<values.length;i++){
          var v = values[i];
          if (v !== null && v !== undefined) s.add(String(v));
        }
        return Array.from(s);
      }

      // initial categorical value lists & totals
      var initialCatVals   = {}; // {col: [values... sorted]}
      var initialCatTotals = {}; // {col: {value: count_in_full_universe}}
      catCols.forEach(function(c){
        var vals = allLayers.map(l => getAttr(l, c));
        var list = uniq(vals).sort((a,b)=>a.localeCompare(b, undefined, {numeric:true, sensitivity:"base"}));
        initialCatVals[c] = list;
        var totals = {};
        for (var i=0;i<allLayers.length;i++){
          var k = String(getAttr(allLayers[i], c));
          totals[k] = (totals[k] || 0) + 1;
        }
        initialCatTotals[c] = totals;
      });

      // initial numeric rails
      var rails = {}; // {col: {min,max}}
      numCols.forEach(function(n){
        var vs = [];
        for (var i=0;i<allLayers.length;i++){
          var v = getAttr(allLayers[i], n);
          if (typeof v === "number" && !Number.isNaN(v)) vs.push(v);
        }
        var mn = vs.length ? Math.min.apply(null, vs) : 0;
        var mx = vs.length ? Math.max.apply(null, vs) : 0;
        rails[n] = {min: mn, max: mx};
      });

      // ---------- Active state ----------
      var activeCat = {};   // {col: "all" | value}
      catCols.forEach(c => activeCat[c] = "all");

      var activeNum = {};   // {col: [lo, hi]}  (pins set by user; init to full rails)
      numCols.forEach(function(n){
        activeNum[n] = [rails[n].min, rails[n].max];
      });

      // ---------- Helpers ----------
      function fmt(v){
        if (Math.abs(v) >= 100 || Math.abs(v - Math.round(v)) < 1e-6) return Math.round(v);
        return Math.round(v*100)/100;
      }
      function stepFor(minv, maxv){
        var r = Math.abs(maxv - minv);
        if (r === 0) return 1;
        var pow10 = Math.pow(10, Math.floor(Math.log10(r/100)));
        return pow10;
      }

      function matches_with(overrides){
        // Build a predicate that uses current state with optional overrides
        var cat = overrides && overrides.activeCat ? overrides.activeCat : activeCat;
        var num = overrides && overrides.activeNum ? overrides.activeNum : activeNum;

        return function(layer){
          // cats
          for (var i=0;i<catCols.length;i++){
            var c = catCols[i], want = cat[c];
            if (want !== "all" && String(getAttr(layer, c)) !== String(want)) return false;
          }
          // nums
          for (var j=0;j<numCols.length;j++){
            var col = numCols[j];
            var range = num[col] || [rails[col].min, rails[col].max]; // fallback
            var v = getAttr(layer, col);
            if (typeof v !== "number" || Number.isNaN(v)) return false;
            if (v < range[0] || v > range[1]) return false;
          }
          return true;
        };
      }

      function subset(overrides){
        var pred = matches_with(overrides);
        var out = [];
        for (var i=0;i<allLayers.length;i++){
          var l = allLayers[i]; if (pred(l)) out.push(l);
        }
        return out;
      }

      function applyFilters(){
        // render current subset to the feature group
        grp.clearLayers();
        var s = subset();
        for (var i=0;i<s.length;i++) grp.addLayer(s[i]);
      }

      // ---------- UI ----------
      var pane = document.getElementById(paneId);
      var container = document.getElementById(containerId);
      if(!container){
        container = document.createElement("div");
        container.id = containerId;
        if (pane) pane.appendChild(container);
      }
      container.classList.add("filters-container");
      container.innerHTML = "";

      // Reset button
      var resetWrap = document.createElement("div");
      resetWrap.style.display = "flex";
      resetWrap.style.justifyContent = "flex-end";
      resetWrap.style.margin = "4px 0 10px";
      var resetBtn = document.createElement("button");
      resetBtn.type = "button";
      resetBtn.textContent = "Reset filters";
      resetBtn.className = "mf-reset-btn";
      resetBtn.style.padding = "6px 10px";
      resetBtn.style.border = "1px solid #bbb";
      resetBtn.style.borderRadius = "6px";
      resetBtn.style.cursor = "pointer";
      resetWrap.appendChild(resetBtn);
      container.appendChild(resetWrap);

      // Keep handles
      var catUI = {}; // {col: {ul, items:{val:li}, setActive, getActive}}
      var numUI = {}; // {col: {sMin, sMax, out, label, track, rails}}

      function availabilityRangeFor(col){
        // availability for numeric 'col' based on *other* filters (exclude this col's numeric constraint)
        var overrideNum = Object.assign({}, activeNum);
        overrideNum[col] = [rails[col].min, rails[col].max]; // use full rails for the probed slider
        var s = subset({activeNum: overrideNum});
        var vals = [];
        for (var i=0;i<s.length;i++){
          var v = getAttr(s[i], col);
          if (typeof v === "number" && !Number.isNaN(v)) vals.push(v);
        }
        if (vals.length === 0) return null;
        return [Math.min.apply(null, vals), Math.max.apply(null, vals)];
      }

      function recolorSlider(col){
        var ui = numUI[col]; if (!ui) return;
        var r = rails[col];
        var avail = availabilityRangeFor(col);
        // percent positions along the full rail
        var loPct = 0, hiPct = 100;
        if (avail){
          var span = (r.max - r.min) || 1;
          loPct = Math.max(0, Math.min(100, ( (avail[0]-r.min)/span )*100));
          hiPct = Math.max(0, Math.min(100, ( (avail[1]-r.min)/span )*100));
        }
        // track gradient: grey outside, mid highlighted to show available interval
        var g = "linear-gradient(to right, " +
                "#ddd 0% " + loPct + "%, " +
                "#b5d5ff " + loPct + "% " + hiPct + "%, " +
                "#ddd " + hiPct + "% 100%)";
        ui.sMin.style.background = g;
        ui.sMax.style.background = g;
      }

      function refreshCountsAndStates(changedCol){
        var s = subset(); // current subset under full state

        // --- Update categorical lists with (avail/initial) and disable when avail=0
        catCols.forEach(function(col){
          var ui = catUI[col]; if (!ui) return;
          var counts = {}; // available counts in current subset
          for (var i=0;i<s.length;i++){
            var key = String(getAttr(s[i], col));
            counts[key] = (counts[key] || 0) + 1;
          }
          Object.keys(ui.items).forEach(function(val){
            var li = ui.items[val];
            if (val === "all") { li.textContent = "All"; li.classList.remove("disabled"); return; }
            var initialTotal = (initialCatTotals[col][val] || 0);
            var avail = (counts[val] || 0);
            li.textContent = val + " (" + avail + "/" + initialTotal + ")";
            var isCurrent = (ui.getActive() === val);
            var enable = (avail > 0) || isCurrent; // keep current clickable
            li.classList.toggle("disabled", !enable);
          });
        });

        // --- Recolor numeric sliders to show currently available interval; DO NOT move pins
        numCols.forEach(function(col){
          recolorSlider(col);
          // Update readout to reflect the current pin positions (user-controlled only)
          var ui = numUI[col];
          if (ui){
            var lo = parseFloat(ui.sMin.value), hi = parseFloat(ui.sMax.value);
            ui.out.textContent = fmt(Math.min(lo, hi)) + " – " + fmt(Math.max(lo, hi));
          }
        });
      }

      // ---------- Build controls in requested order ----------
      orderedCols.forEach(function(col){
        if (numSet[col]) {
          // ----- NUMERIC (double slider with availability coloring)
          var r = rails[col];
          var step = stepFor(r.min, r.max);

          var section = document.createElement("div");
          section.className = "sidebar-section";
          section.style.marginBottom = "12px";

          var label = document.createElement("label");
          label.textContent = col + " (" + fmt(r.min) + " – " + fmt(r.max) + ")";
          label.style.display = "block";
          label.style.margin = "12px 0 12px";

          var row = document.createElement("div");
          row.className = "range-row";

          var sMin = document.createElement("input");
          sMin.type = "range";
          sMin.min = String(r.min);
          sMin.max = String(r.max);
          sMin.step = String(step);
          sMin.value = String(r.min);
          sMin.className = "range range-min";

          var sMax = document.createElement("input");
          sMax.type = "range";
          sMax.min = String(r.min);
          sMax.max = String(r.max);
          sMax.step = String(step);
          sMax.value = String(r.max);
          sMax.className = "range range-max";

          var out = document.createElement("div");
          out.className = "range-out";
          out.textContent = fmt(r.min) + " – " + fmt(r.max);

          function onSlide(){
            // DO NOT alter the element values except via user's drag (this handler runs due to user input)
            var lo = Math.min(parseFloat(sMin.value), parseFloat(sMax.value));
            var hi = Math.max(parseFloat(sMin.value), parseFloat(sMax.value));
            activeNum[col] = [lo, hi];
            out.textContent = fmt(lo) + " – " + fmt(hi);
            // Update other controls
            refreshCountsAndStates(col);
            applyFilters();
          }
          sMin.addEventListener("input", onSlide);
          sMax.addEventListener("input", onSlide);

          row.appendChild(sMin);
          row.appendChild(sMax);

          section.appendChild(label);
          section.appendChild(row);
          section.appendChild(out);
          container.appendChild(section);

          numUI[col] = { sMin, sMax, out, label, rails: {min:r.min, max:r.max} };

        } else {
          // ----- CATEGORICAL
          var section = document.createElement("div");
          section.className = "sidebar-section";
          section.style.marginBottom = "10px";

          var label = document.createElement("label");
          label.textContent = col;
          label.htmlFor = "filter-" + col + "-search";
          label.style.display = "block";
          label.style.margin = "8px 0 4px";

          var search = document.createElement("input");
          search.type = "search";
          search.id = "filter-" + col + "-search";
          search.placeholder = "Search " + col + "...";
          search.className = "filter-search";
          search.style.boxSizing = "border-box";

          var ul = document.createElement("ul");
          ul.id = "filter-" + col + "-list";
          ul.className = "filter-list";

          section.appendChild(label);
          section.appendChild(search);
          section.appendChild(ul);
          container.appendChild(section);

          var items = {};
          function addItem(val, labelText){
            var li = document.createElement("li");
            li.textContent = labelText;
            li.dataset.value = val;
            li.tabIndex = 0;
            li.addEventListener("click", function(){
              if (li.classList.contains("disabled")) return;
              setActive(val);
              activeCat[col] = val;
              refreshCountsAndStates(col);
              applyFilters();
            });
            li.addEventListener("keydown", function(e){
              if ((e.key === "Enter" || e.key === " ") && !li.classList.contains("disabled")) li.click();
            });
            ul.appendChild(li);
            items[val] = li;
          }

          var current = "all";
          function setActive(v){
            current = v;
            Array.from(ul.querySelectorAll("li")).forEach(function(li){
              li.classList.toggle("active", li.dataset.value === v);
            });
          }
          function getActive(){ return current; }

          // "All"
          addItem("all", "All");

          // Initial items with (avail/initial) both == initial
          var totals = initialCatTotals[col];
          initialCatVals[col].forEach(function(v){
            var initCount = totals[String(v)] || 0;
            addItem(String(v), String(v) + " (" + initCount + "/" + initCount + ")");
          });

          setActive("all");

          // Client-side text filter
          search.addEventListener("input", function(){
            var q = this.value.trim().toLowerCase();
            Array.from(ul.querySelectorAll("li")).forEach(function(li){
              if (li.dataset.value === "all"){ li.style.display = q ? "none" : "block"; return; }
              // Strip trailing " (x/y)" for matching
              var base = li.textContent.replace(/ \\(\\d+\\/\\d+\\)$/,'');
              li.style.display = (base.toLowerCase().indexOf(q) !== -1) ? "block" : "none";
            });
          });

          catUI[col] = { ul, items, setActive, getActive };
        }
      });

      // Initial availability paint (no movement of pins)
      function initialPaint(){
        // set initial (avail/initial) everywhere and recolor sliders for full universe
        refreshCountsAndStates(null);
        applyFilters();
      }

      // Reset logic
      resetBtn.addEventListener("click", function(){
        // Cats -> All
        catCols.forEach(function(col){
          activeCat[col] = "all";
          if (catUI[col]) catUI[col].setActive("all");
        });
        // Nums -> rails (this is the *only* time JS moves pins)
        numCols.forEach(function(col){
          var ui = numUI[col], r = rails[col];
          ui.sMin.value = String(r.min);
          ui.sMax.value = String(r.max);
          activeNum[col] = [r.min, r.max];
          ui.out.textContent = fmt(r.min) + " – " + fmt(r.max);
        });
        refreshCountsAndStates(null);
        applyFilters();
      });

      // Ensure scrolling if tall
      var paneEl = document.getElementById(paneId);
      if (paneEl){ paneEl.style.overflowY = "auto"; }

      // Kickoff
      initialPaint();
    })();
    {% endmacro %}
    """)

    def __init__(self, feature_group, cols=None, cat_cols=None, num_cols=None,
                 pane_id="filter", container_id="filters-container"):
        super().__init__()
        self._name = "MultiFilter"
        self.group_name = feature_group.get_name()

        if cols:
            ordered = list(cols)
            num_set = set(num_cols or [])
        else:
            ordered = list(cat_cols or []) + list(num_cols or [])
            num_set = set(num_cols or [])

        self.ordered_cols = ordered
        self.num_set = {c: True for c in num_set}
        self.pane_id = pane_id
        self.container_id = container_id

    @staticmethod
    def css():
        # Adds slider availability coloring and basic styles
        return Element("""
<style>
#sidebar .filters-container { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
#sidebar .filter-list {
  list-style: none; margin: 8px 0 0; padding: 0;
  max-height: 150px; overflow: auto; border: 1px solid #ccc; border-radius: 4px;
}
#sidebar .filter-list li { padding: 6px 8px; cursor: pointer; }
#sidebar .filter-list li.active { background: #e6e6e6; font-weight: 600; }
#sidebar .filter-list li.disabled { color:#aaa; cursor:not-allowed; }

#sidebar .sidebar-section .filter-search,
#sidebar .sidebar-section .filter-list,
#sidebar .sidebar-section .range-row input[type="range"],
#sidebar .sidebar-section .range-out {
  box-sizing: border-box; width: 100%;
}

#sidebar .range-row {
  position: relative;
}
#sidebar .range-row input{
  position: absolute;
  top: -5px;
  height: 5px;
  width: 100%;
  background: none;
  pointer-events: none;
  -webkit-appearance: none;
  z-index: 2;
}

#sidebar .range-out { margin-top: 20px; color: #555; font-size: 0.9em; }
#sidebar .mf-reset-btn:hover { background:#f7f7f7; }

/* Minimal cross-browser range styling; gradient set inline per control */
#sidebar input[type="range"] {
  appearance: none; -webkit-appearance: none; height: 6px; border-radius: 6px;
  background: #ddd;
}
#sidebar input[type="range"]::-webkit-slider-thumb {
  height: 16px;
  width: 16px;
  border: 1px solid #666;
  border-radius: 50%;
  pointer-events: auto;
  -webkit-appearance: none;
  background: #fff;
  cursor: pointer;
}
#sidebar input[type="range"]::-moz-range-thumb {
  height: 16px;
  width: 16px;
  border: 1px solid #666;
  border-radius: 50%;
  pointer-events: auto;
  -moz-appearance: none;
  background: #fff;
  cursor: pointer;
}
</style>
""")
