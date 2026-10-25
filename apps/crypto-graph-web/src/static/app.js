let cy = null;
let currentAddress = "";
let currentElements = { nodes: [], edges: [] };

document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("address-input");
  if (input && input.value) {
    loadAddressGraph(input.value.trim());
  }
});

function searchCurrentAddress() {
  const input = document.getElementById("address-input");
  if (input && input.value) {
    const address = input.value.trim();
    loadAddressGraph(address);
    // Record search in tenant history if logged in
    fetch("/api/v1/investigations/history", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address: address, chain: "ethereum" })
    }).catch(() => {});

    // Trigger HTMX refreshes for side panels
    htmx.ajax("GET", `/partials/address-summary?address=${encodeURIComponent(address)}`, "#address-summary-container");
    htmx.ajax("GET", `/partials/persona-card?address=${encodeURIComponent(address)}`, "#persona-card-container");
    htmx.ajax("GET", `/partials/counterparties?address=${encodeURIComponent(address)}`, "#counterparties-container");
    htmx.ajax("GET", `/partials/cross-chain?address=${encodeURIComponent(address)}`, "#cross-chain-container");
    htmx.ajax("GET", `/partials/investigation-panel`, "#investigation-container");
  }
}

function setAddress(addr) {
  const input = document.getElementById("address-input");
  if (input) {
    input.value = addr;
    searchCurrentAddress();
  }
}

async function loadAddressGraph(address) {
  currentAddress = address.toLowerCase();
  const cyContainer = document.getElementById("cy");
  if (!cyContainer) return;

  try {
    const resp = await fetch(`/api/graph-data?address=${encodeURIComponent(address)}`);
    if (!resp.ok) throw new Error("Failed to load graph data");
    const data = await resp.json();
    currentElements = data.elements;
    initCytoscape(data.elements);
  } catch (err) {
    console.error("Error loading graph:", err);
  }
}

function initCytoscape(elements) {
  if (cy) {
    cy.destroy();
  }

  cy = cytoscape({
    container: document.getElementById("cy"),
    elements: elements,
    style: [
      {
        selector: "node",
        style: {
          "label": "data(label)",
          "color": "#f9fafb",
          "font-size": "10px",
          "text-valign": "bottom",
          "text-margin-y": 6,
          "background-color": "#4b5563",
          "width": "mapData(degree, 0, 10, 24, 52)",
          "height": "mapData(degree, 0, 10, 24, 52)",
          "border-width": 2,
          "border-color": "#374151",
          "transition-property": "background-color, border-color, width, height",
          "transition-duration": "0.2s"
        }
      },
      {
        selector: 'node[node_type = "target"]',
        style: {
          "background-color": "#38bdf8",
          "border-color": "#7dd3fc",
          "border-width": 4,
          "width": 64,
          "height": 64,
          "font-weight": "bold",
          "font-size": "12px",
          "color": "#38bdf8"
        }
      },
      {
        selector: 'node[node_type = "bridge"]',
        style: {
          "shape": "diamond",
          "background-color": "#a855f7",
          "border-color": "#c084fc",
          "border-width": 3,
          "width": 42,
          "height": 42
        }
      },
      {
        selector: 'node[node_type = "exchange"]',
        style: {
          "shape": "round-rectangle",
          "background-color": "#f59e0b",
          "border-color": "#fbbf24",
          "border-width": 3,
          "width": 52,
          "height": 38
        }
      },
      {
        selector: 'node[node_type = "mixer"]',
        style: {
          "shape": "hexagon",
          "background-color": "#ef4444",
          "border-color": "#f87171",
          "border-width": 4,
          "width": 54,
          "height": 54,
          "font-weight": "bold",
          "color": "#fca5a5"
        }
      },
      {
        selector: 'node[node_type = "defi"]',
        style: {
          "shape": "barrel",
          "background-color": "#10b981",
          "border-color": "#34d399",
          "border-width": 3,
          "width": 50,
          "height": 46
        }
      },
      {
        selector: 'node[node_type = "whale"]',
        style: {
          "shape": "star",
          "background-color": "#ec4899",
          "border-color": "#f472b6",
          "border-width": 3,
          "width": 56,
          "height": 56
        }
      },
      {
        selector: 'node[risk_level = "HIGH"]',
        style: {
          "shadow-blur": 15,
          "shadow-color": "#ef4444",
          "shadow-opacity": 0.8
        }
      },
      {
        selector: 'node[persona_id]',
        style: {
          "border-color": "#a855f7",
          "border-width": 3
        }
      },
      {
        selector: "edge",
        style: {
          "width": "mapData(volume, 0, 50, 1.5, 6)",
          "line-color": "#4b5563",
          "target-arrow-color": "#4b5563",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
          "arrow-scale": 0.9,
          "opacity": 0.8
        }
      },
      {
        selector: "edge[?is_cross_chain]",
        style: {
          "line-color": "#a855f7",
          "target-arrow-color": "#a855f7",
          "line-style": "dashed",
          "width": 3,
          "opacity": 1.0
        }
      },
      {
        selector: "node:selected",
        style: {
          "border-color": "#10b981",
          "border-width": 5,
          "background-color": "#059669"
        }
      }
    ],
    layout: {
      name: "cose",
      animate: true,
      animationDuration: 800,
      idealEdgeLength: 100,
      nodeOverlap: 20,
      refresh: 20,
      fit: true,
      padding: 30
    }
  });

  cy.on("tap", "node", (evt) => {
    const node = evt.target;
    const data = node.data();
    if (data.id && data.id !== currentAddress && data.node_type !== "bridge") {
      setAddress(data.id);
    }
  });
}

function zoomIn() {
  if (cy) cy.zoom(cy.zoom() * 1.25);
}

function zoomOut() {
  if (cy) cy.zoom(cy.zoom() * 0.8);
}

function fitGraph() {
  if (cy) cy.fit(null, 30);
}

function switchLayout(layoutName) {
  if (!cy) return;
  cy.layout({ name: layoutName, animate: true, animationDuration: 600 }).run();
}

function filterGraphByVolume(minVolumeStr) {
  if (!cy) return;
  const minVol = parseFloat(minVolumeStr);
  cy.batch(() => {
    cy.edges().forEach((edge) => {
      const vol = parseFloat(edge.data("volume") || 0);
      if (vol < minVol) {
        edge.style("display", "none");
      } else {
        edge.style("display", "element");
      }
    });
  });
}

function exportGraph() {
  if (!cy) return;
  const pngData = cy.png({ full: true, scale: 2 });
  const a = document.createElement("a");
  a.href = pngData;
  a.download = `crypto-graph-${currentAddress.slice(0, 8)}.png`;
  a.click();
}

function exportTransactionsCsv() {
  if (!currentElements || !currentElements.edges) return;
  let csv = "Source,Target,Volume,TxCount,IsCrossChain,BridgeName\n";
  currentElements.edges.forEach((e) => {
    const d = e.data;
    csv += `"${d.source}","${d.target}",${d.volume},${d.tx_count},${d.is_cross_chain || false},"${d.bridge_name || ''}"\n`;
  });
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `transactions-${currentAddress.slice(0, 8)}.csv`;
  a.click();
}

function exportGraphJson() {
  if (!currentElements) return;
  const jsonStr = JSON.stringify({
    elements: currentElements,
    target_address: currentAddress,
    exported_at_utc: new Date().toISOString()
  }, null, 2);
  const blob = new Blob([jsonStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `graph-${currentAddress.slice(0, 8)}.json`;
  a.click();
}

async function addCurrentToWatchlist() {
  if (!currentAddress) return;
  const label = prompt("Enter a label for this address:", currentAddress.slice(0, 10));
  if (label === null) return;
  try {
    const res = await fetch("/api/v1/investigations/watchlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address: currentAddress, chain: "ethereum", label: label })
    });
    if (res.ok) {
      htmx.ajax("GET", "/partials/investigation-panel", "#investigation-container");
    } else {
      alert("Failed to add to watchlist. Please make sure you are signed in.");
    }
  } catch (err) {
    alert("Error: " + err);
  }
}

async function removeFromWatchlist(address) {
  try {
    const res = await fetch(`/api/v1/investigations/watchlist/${address}`, { method: "DELETE" });
    if (res.ok) {
      htmx.ajax("GET", "/partials/investigation-panel", "#investigation-container");
    }
  } catch (err) {
    console.error(err);
  }
}

async function saveCurrentInvestigation() {
  if (!cy || !currentAddress) return;
  const title = prompt("Enter a title for this saved investigation graph:", `Analysis of ${currentAddress.slice(0, 8)}`);
  if (!title) return;
  try {
    const res = await fetch("/api/v1/investigations/saved", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title,
        target_address: currentAddress,
        graph_data: currentElements
      })
    });
    if (res.ok) {
      alert("Investigation graph saved successfully!");
      htmx.ajax("GET", "/partials/investigation-panel", "#investigation-container");
    } else {
      alert("Failed to save investigation. Are you signed in?");
    }
  } catch (err) {
    alert("Error: " + err);
  }
}

async function loadSavedInvestigation(invId) {
  try {
    const res = await fetch(`/api/v1/investigations/saved/${invId}`);
    if (!res.ok) throw new Error("Failed to load investigation");
    const data = await res.json();
    setAddress(data.target_address);
    if (data.graph_data && data.graph_data.elements) {
      currentElements = data.graph_data.elements;
      initCytoscape(data.graph_data.elements);
    }
  } catch (err) {
    console.error("Error loading saved graph:", err);
  }
}
