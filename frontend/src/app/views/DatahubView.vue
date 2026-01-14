<template>
  <div class="datahub-view">
    <div ref="canvasEl" class="datahub-canvas"></div>
    <aside class="datahub-sidebar">
      <h2>Relationships</h2>
      <div class="datahub-relationships">
        <div
          v-for="(rel, index) in relationships"
          :key="`${rel.fromTable}-${rel.fromColumn}-${rel.toTable}-${rel.toColumn}-${index}`"
          class="relationship-row"
        >
          {{ index + 1 }}. {{ rel.fromTable }}.{{ rel.fromColumn }} -> {{ rel.toTable }}.{{
            rel.toColumn
          }}
          (type: {{ rel.joinType }})
        </div>
        <div v-if="relationships.length === 0" class="relationship-empty">
          No relationships yet.
        </div>
      </div>
      <h3>JSON</h3>
      <pre class="datahub-json">{{ relationshipsJson }}</pre>
    </aside>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { loadScriptOnce } from "../utils/loaders.js";

const canvasEl = ref(null);
const relationships = ref([]);
const relationshipsJson = computed(() =>
  JSON.stringify(relationships.value, null, 2)
);

const schema = {
  Customers: ["CustomerID", "Name", "Country"],
  Orders: ["OrderID", "CustomerID", "OrderDate", "Total"],
  OrderLines: ["OrderLineID", "OrderID", "ProductID", "Qty"],
  Products: ["ProductID", "Name", "Price"],
};

let instance = null;
let removeHandlers = null;

function addRelationship(fromTable, fromColumn, toTable, toColumn) {
  relationships.value = relationships.value.concat([
    { fromTable, fromColumn, toTable, toColumn, joinType: "inner" },
  ]);
}

function removeRelationship(fromTable, fromColumn, toTable, toColumn) {
  const idx = relationships.value.findIndex(
    (rel) =>
      rel.fromTable === fromTable &&
      rel.fromColumn === fromColumn &&
      rel.toTable === toTable &&
      rel.toColumn === toColumn
  );
  if (idx !== -1) {
    const next = relationships.value.slice();
    next.splice(idx, 1);
    relationships.value = next;
  }
}

function buildTables(jsPlumbInstance, host) {
  host.innerHTML = "";
  const tableNames = Object.keys(schema);
  const cols = 2;
  const xGap = 260;
  const yGap = 220;

  tableNames.forEach((tableName, idx) => {
    const tableDiv = document.createElement("div");
    tableDiv.className = "table-node";
    tableDiv.id = `table_${tableName}`;
    tableDiv.style.left = `${20 + (idx % cols) * xGap}px`;
    tableDiv.style.top = `${20 + Math.floor(idx / cols) * yGap}px`;

    const titleDiv = document.createElement("div");
    titleDiv.className = "table-title";
    titleDiv.textContent = tableName;
    tableDiv.appendChild(titleDiv);

    const colsDiv = document.createElement("div");
    colsDiv.className = "columns";
    tableDiv.appendChild(colsDiv);

    schema[tableName].forEach((colName) => {
      const colDiv = document.createElement("div");
      colDiv.className = "column";
      colDiv.dataset.table = tableName;
      colDiv.dataset.column = colName;

      const nameSpan = document.createElement("span");
      nameSpan.className = "name";
      nameSpan.textContent = colName;
      colDiv.appendChild(nameSpan);

      const dotSpan = document.createElement("span");
      dotSpan.className = "dot";
      colDiv.appendChild(dotSpan);

      colsDiv.appendChild(colDiv);

      jsPlumbInstance.addEndpoint(colDiv, {
        anchor: "Right",
        isSource: true,
        isTarget: true,
        maxConnections: -1,
        connector: ["Flowchart"],
        parameters: {
          table: tableName,
          column: colName,
        },
      });
    });

    host.appendChild(tableDiv);
    jsPlumbInstance.draggable(tableDiv);
  });
}

async function initDatahub() {
  await loadScriptOnce(
    "https://cdnjs.cloudflare.com/ajax/libs/jsPlumb/2.15.6/js/jsplumb.min.js"
  );

  const jsPlumb = window.jsPlumb;
  if (!jsPlumb || !canvasEl.value) return;

  instance = jsPlumb.getInstance({
    Container: canvasEl.value,
    Connector: ["Flowchart", { cornerRadius: 5 }],
    Endpoint: ["Dot", { radius: 4 }],
    PaintStyle: { strokeWidth: 2 },
    EndpointStyle: { fill: "#ffffff" },
  });

  buildTables(instance, canvasEl.value);

  const handleConnection = (info) => {
    const sourceCol = info.source;
    const targetCol = info.target;
    addRelationship(
      sourceCol.dataset.table,
      sourceCol.dataset.column,
      targetCol.dataset.table,
      targetCol.dataset.column
    );
  };

  const handleDetach = (info) => {
    const sourceCol = info.source;
    const targetCol = info.target;
    removeRelationship(
      sourceCol.dataset.table,
      sourceCol.dataset.column,
      targetCol.dataset.table,
      targetCol.dataset.column
    );
  };

  instance.bind("connection", handleConnection);
  instance.bind("connectionDetached", handleDetach);
  removeHandlers = () => {
    if (instance?.unbind) {
      instance.unbind("connection", handleConnection);
      instance.unbind("connectionDetached", handleDetach);
    }
  };
}

onMounted(() => {
  initDatahub().catch((error) => {
    console.error("Failed to initialize Datahub view", error);
  });
});

onBeforeUnmount(() => {
  removeHandlers?.();
  removeHandlers = null;
  if (instance?.destroy) {
    instance.destroy();
  } else if (instance?.reset) {
    instance.reset();
  }
  instance = null;
  if (canvasEl.value) {
    canvasEl.value.innerHTML = "";
  }
  relationships.value = [];
});
</script>

<style scoped>
.datahub-view {
  display: flex;
  min-height: 100vh;
  width: 100%;
  overflow: hidden;
  background: #f5f5f5;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.datahub-canvas {
  flex: 3;
  position: relative;
  background: #f5f5f5;
  border-right: 1px solid #ddd;
  overflow: auto;
}

.datahub-sidebar {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
  font-size: 13px;
  background: #fff;
}

.table-node {
  position: absolute;
  min-width: 180px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid #ccc;
  padding: 4px 0;
  cursor: move;
}

.table-title {
  font-weight: 600;
  font-size: 14px;
  padding: 4px 8px;
  border-bottom: 1px solid #ddd;
  background: #f0f0f0;
  border-radius: 8px 8px 0 0;
}

.columns {
  padding: 4px 0;
  max-height: 240px;
  overflow-y: auto;
}

.column {
  padding: 2px 8px;
  font-size: 13px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.column .name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.column .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 1px solid #555;
  margin-left: 6px;
}

.datahub-sidebar h2 {
  margin-top: 0;
  font-size: 16px;
}

.datahub-sidebar h3 {
  margin-bottom: 6px;
  font-size: 14px;
}

.relationship-row {
  margin-bottom: 6px;
}

.relationship-empty {
  color: #666;
  font-style: italic;
}

.datahub-json {
  background: #272822;
  color: #f8f8f2;
  padding: 8px;
  border-radius: 4px;
  font-size: 11px;
  overflow-x: auto;
}
</style>
