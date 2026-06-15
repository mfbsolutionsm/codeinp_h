let currentProperties = [];
let seenAddresses = [];
let savedThisSession = 0;
let lastPromptSent = '';

function money(value) {
    if (value === null || value === undefined || value === "") return "Needs estimate";
    if (Number(value) === 0) return "Needs estimate";
    return Number(value).toLocaleString("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0
    });
}

function colorClass(color) {
    const value = String(color || "").toLowerCase();
    if (value.includes("dark")) return "dark-green";
    if (value.includes("green")) return "green";
    if (value.includes("yellow")) return "yellow";
    if (value.includes("red")) return "red";
    return "";
}

function dealIcon(color) {
    const value = String(color || "").toLowerCase();
    if (value.includes("green") && !value.includes("dark")) return "✓";
    if (value.includes("dark")) return "✓";
    if (value.includes("yellow")) return "!";
    if (value.includes("red")) return "×";
    return "?";
}

function progressWidth(value) {
    const number = Number(value || 0);
    return Math.max(0, Math.min(100, number * 5));
}

function listingButton(property) {
    if (!property.listing_url) return "";
    return `<a class="listing-link" href="${property.listing_url}" target="_blank" rel="noopener noreferrer">View Listing</a>`;
}

function renderProperties(properties) {
    currentProperties = properties;

    properties.forEach(property => {
        if (property.address && !seenAddresses.includes(property.address)) {
            seenAddresses.push(property.address);
        }
    });

    const grid = document.getElementById("propertyGrid");
    grid.innerHTML = "";

    if (!properties || properties.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <h2>No properties returned</h2>
                <p>The scan returned no usable properties. Try scanning again or increasing the maximum price.</p>
            </div>
        `;
        updateSummary([]);
        return;
    }

    properties.forEach((property, index) => {
        const card = document.createElement("article");
        card.className = `card ${colorClass(property.color)}`;

        card.innerHTML = `
            <div class="deal-banner">
                <span>${dealIcon(property.color)}</span>
                <strong>${property.deal_label || property.rating}</strong>
            </div>

            <div class="card-header-row">
                <div>
                    <h2>${property.address}</h2>
                    <span class="badge">${property.rating} • ${property.risk_level} Risk</span>
                </div>
                <div class="score-circle">
                    <strong>${property.score}</strong>
                    <small>/10</small>
                </div>
            </div>

            ${listingButton(property)}

            <div class="profit-box">
                <div>
                    <small>Profit Margin vs ARV</small>
                    <strong>${property.profit_margin_arv || 0}%</strong>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: ${progressWidth(property.profit_margin_arv)}%"></div>
                </div>
            </div>

            <div class="remodel-box">
                <small>Remodel Signal</small>
                <strong>${property.remodel_signal || "Not classified"}</strong>
                <span>Score: ${property.remodel_signal_score || 0}</span>
            </div>

            <div class="metrics">
                <div class="metric">
                    <small>City</small>
                    <strong>${property.city || "-"}</strong>
                </div>
                <div class="metric">
                    <small>County</small>
                    <strong>${property.county || "-"}</strong>
                </div>
                <div class="metric">
                    <small>Living Area</small>
                    <strong>${property.living_area_sqft || "-"} sqft</strong>
                </div>
                <div class="metric">
                    <small>Lot Size</small>
                    <strong>${property.lot_size_sqft || "-"} sqft</strong>
                </div>
                <div class="metric">
                    <small>Beds / Baths</small>
                    <strong>${property.bedrooms || "-"} / ${property.bathrooms || "-"}</strong>
                </div>
                <div class="metric">
                    <small>Source</small>
                    <strong>${property.source || "-"}</strong>
                </div>
                <div class="metric">
                    <small>Purchase Price</small>
                    <strong>${money(property.purchase_price)}</strong>
                </div>
                <div class="metric">
                    <small>Estimated ARV</small>
                    <strong>${money(property.estimated_arv)}</strong>
                </div>
                <div class="metric">
                    <small>Repair Budget</small>
                    <strong>${money(property.repair_budget)}</strong>
                </div>
                <div class="metric">
                    <small>Renovation Level</small>
                    <strong>${property.renovation_level || "-"}</strong>
                </div>
                <div class="metric">
                    <small>Total Project Cost</small>
                    <strong>${money(property.total_project_cost)}</strong>
                </div>
                <div class="metric">
                    <small>Net Profit</small>
                    <strong>${money(property.estimated_net_profit)}</strong>
                </div>
                <div class="metric">
                    <small>ROI</small>
                    <strong>${property.estimated_roi}%</strong>
                </div>
                <div class="metric highlight-metric">
                    <small>Profit Margin vs ARV</small>
                    <strong>${property.profit_margin_arv || 0}%</strong>
                </div>
                <div class="metric">
                    <small>MAO</small>
                    <strong>${money(property.maximum_allowable_offer || property.max_offer_price)}</strong>
                </div>
                <div class="metric recommendation-metric">
                    <small>Recommended Offer</small>
                    <strong>${money(property.recommended_offer)}</strong>
                </div>
                <div class="metric recommendation-metric">
                    <small>Spread to MAO</small>
                    <strong>${money(property.spread_to_mao)}</strong>
                </div>
                <div class="metric recommendation-metric">
                    <small>MAO Status</small>
                    <strong>${property.mao_status || "-"}</strong>
                </div>
                <div class="metric negotiation-metric">
                    <small>Target Yellow Offer</small>
                    <strong>${money(property.target_offer_for_yellow)}</strong>
                </div>
                <div class="metric negotiation-metric">
                    <small>Target Green Offer</small>
                    <strong>${money(property.target_offer_for_green)}</strong>
                </div>
                <div class="metric">
                    <small>Strategy</small>
                    <strong>${property.strategy}</strong>
                </div>
            </div>

            <p class="keywords"><strong>Renovation keywords:</strong> ${(property.renovation_keywords_found || []).join(", ") || "-"}</p>
            <p class="display-reason"><strong>Why shown:</strong> ${property.display_reason || "Selected for review"}</p>
            ${property.hidden_defect_alert ? `
                <div class="hidden-defect-alert">
                    <strong>⚠ Verify Hidden Defects</strong>
                    <p>${property.hidden_defect_notes}</p>
                </div>
            ` : ""}
            <p class="notes">${property.notes}</p>
            <button class="save-button" onclick="saveProperty(${index}, this)">Save Property</button>
        `;

        grid.appendChild(card);
    });

    updateSummary(properties);
}

function updateSummary(properties) {
    document.getElementById("totalProperties").textContent = properties.length;

    if (!properties.length) {
        document.getElementById("bestScore").textContent = "-";
        return;
    }

    const best = properties.reduce((max, p) => Number(p.score) > Number(max.score) ? p : max, properties[0]);
    document.getElementById("bestScore").textContent = `${best.score}/10`;
}

async function scanProperties() {
    const button = document.getElementById("scanButton");
    const status = document.getElementById("statusText");

    button.disabled = true;
    button.textContent = "Scanning...";
    status.textContent = "Searching Santa Clara County first. If needed, expanding to Bay Area, then all California...";

    document.getElementById("propertyGrid").innerHTML = "";
    currentProperties = [];
    updateSummary([]);

    const maxPrice = document.getElementById("maxPrice").value;

    try {
        const response = await fetch("/scan", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                max_price: maxPrice,
                excluded_addresses: seenAddresses
            })
        });

        const data = await response.json();
        renderProperties(data.properties);
        status.textContent = data.message;
        lastPromptSent = data.prompt_sent || lastPromptSent;
        document.getElementById('promptPreview').textContent = lastPromptSent || 'No prompt available yet.';
        if (data.search_area_used) {
            status.textContent += ` Search area: ${data.search_area_used}`;
        }
    } catch (error) {
        status.textContent = "Error scanning properties.";
        console.error(error);
    }

    button.disabled = false;
    button.textContent = "Scan Properties";
}

async function saveProperty(index, button) {
    const property = currentProperties[index];
    if (!property) return;

    button.disabled = true;
    button.textContent = "Saving...";

    try {
        const response = await fetch("/save-property", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(property)
        });

        const data = await response.json();

        savedThisSession += 1;
        document.getElementById("savedCount").textContent = savedThisSession;

        button.textContent = "Saved";
        button.classList.add("saved");
        document.getElementById("statusText").textContent = data.message;

        await loadSavedProperties();
    } catch (error) {
        button.disabled = false;
        button.textContent = "Save Property";
        document.getElementById("statusText").textContent = "Error saving property.";
        console.error(error);
    }
}

async function loadSavedProperties() {
    try {
        const response = await fetch("/saved-properties");
        const data = await response.json();
        document.getElementById("savedPreview").textContent = data.content;
    } catch (error) {
        document.getElementById("savedPreview").textContent = "Could not load saved properties.";
        console.error(error);
    }
}

window.onload = () => {
    loadSavedProperties();
};


async function showPrompt() {
    const maxPrice = document.getElementById("maxPrice").value;

    try {
        const response = await fetch("/debug-prompt", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                max_price: maxPrice,
                excluded_addresses: seenAddresses
            })
        });

        const data = await response.json();
        document.getElementById("promptPreview").textContent =
            `API Key Found: ${data.has_openai_api_key}\n` +
            `Model: ${data.openai_model}\n` +
            `Search Area: ${data.search_area}\n\n` +
            data.prompt;
    } catch (error) {
        document.getElementById("promptPreview").textContent = "Could not load prompt.";
        console.error(error);
    }
}
