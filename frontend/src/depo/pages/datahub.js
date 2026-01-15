const defaultSchema = {
  Customers: ["CustomerID", "Name", "Country"],
  Orders: ["OrderID", "CustomerID", "OrderDate", "Total"],
  OrderLines: ["OrderLineID", "OrderID", "ProductID", "Qty"],
  Products: ["ProductID", "Name", "Price"],
};

let instance = null;
let initializing = false;
let relationships = [];
let removeHandlers = null;

function renderRelationships() {
  const listDiv = document.getElementById("relationships-list");
  const jsonPre = document.getElementById("relationships-json");

  if (listDiv) {
    listDiv.innerHTML = "";
    relationships.forEach((rel, index) => {
      const row = document.createElement("div");
      row.textContent = `${index + 1}. ${rel.fromTable}.${rel.fromColumn} -> ` +
        `${rel.toTable}.${rel.toColumn} (type: ${rel.joinType})`;
      listDiv.appendChild(row);
    });
  }

  if (jsonPre) {
    jsonPre.textContent = JSON.stringify(relationships, null, 2);
  }
}

function buildTables(jsPlumbInstance, canvas, schema) {
  canvas.innerHTML = "";

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
        parameters: { table: tableName, column: colName },
      });
    });

    canvas.appendChild(tableDiv);
    jsPlumbInstance.draggable(tableDiv);
  });
}

export function initDatahub({ schema = defaultSchema } = {}) {
  if (instance || initializing) {
    return instance;
  }

  const canvas = document.getElementById("canvas");
  if (!canvas) {
    return null;
  }

  const jsPlumb = window.jsPlumb;
  if (!jsPlumb) {
    console.error("Datahub failed to initialize: jsPlumb is not available.");
    return null;
  }

  initializing = true;
  relationships = [];
  renderRelationships();

  jsPlumb.ready(() => {
    instance = jsPlumb.getInstance({
      Container: "canvas",
      Connector: ["Flowchart", { cornerRadius: 5 }],
      Endpoint: ["Dot", { radius: 4 }],
      PaintStyle: { strokeWidth: 2 },
      EndpointStyle: { fill: "#ffffff" },
    });

    buildTables(instance, canvas, schema);

    const handleConnection = (info) => {
      const sourceCol = info.source;
      const targetCol = info.target;
      relationships.push({
        fromTable: sourceCol.dataset.table,
        fromColumn: sourceCol.dataset.column,
        toTable: targetCol.dataset.table,
        toColumn: targetCol.dataset.column,
        joinType: "inner",
      });
      renderRelationships();
    };

    const handleDetach = (info) => {
      const sourceCol = info.source;
      const targetCol = info.target;
      const idx = relationships.findIndex(
        (rel) =>
          rel.fromTable === sourceCol.dataset.table &&
          rel.fromColumn === sourceCol.dataset.column &&
          rel.toTable === targetCol.dataset.table &&
          rel.toColumn === targetCol.dataset.column
      );
      if (idx !== -1) {
        relationships.splice(idx, 1);
        renderRelationships();
      }
    };

    instance.bind("connection", handleConnection);
    instance.bind("connectionDetached", handleDetach);
    removeHandlers = () => {
      if (instance?.unbind) {
        instance.unbind("connection", handleConnection);
        instance.unbind("connectionDetached", handleDetach);
      }
    };

    renderRelationships();
    initializing = false;
  });

  return instance;
}

export function destroyDatahub() {
  removeHandlers?.();
  removeHandlers = null;

  if (instance?.destroy) {
    instance.destroy();
  } else if (instance?.reset) {
    instance.reset();
  }
  instance = null;
  relationships = [];

  const canvas = document.getElementById("canvas");
  if (canvas) {
    canvas.innerHTML = "";
  }
  renderRelationships();
}

function autoInit() {
  if (typeof document === "undefined") return;
  const body = document.body;
  if (!body || body.dataset.page !== "datahub") return;
  initDatahub();
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", autoInit, { once: true });
  } else {
    autoInit();
  }
}
