(function () {
    const config = window.POS_CONFIG;
    const menuItemCatalog = JSON.parse(document.getElementById("menu-item-catalog").textContent || "{}");
    let currentOrderId = null;
    let activeCategory = "";
    let customizerState = null;
    const initialOrderId = config.initialOrderId || null;
    const initialTableId = config.initialTableId || null;

    function csrfToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : "";
    }

    function urlFor(template, id) {
        return template.replace("/0/", `/${id}/`);
    }

    function humanize(value) {
        return String(value || "")
            .replaceAll("_", " ")
            .replace(/\b\w/g, (char) => char.toUpperCase());
    }

    function escapeHtml(value) {
        return String(value || "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function formatCurrency(value) {
        return `Rs. ${Number(value || 0).toFixed(2)}`;
    }

    function setActionState(enabled) {
        document.getElementById("send-kot-btn").disabled = !enabled;
        document.getElementById("settle-order-btn").disabled = !enabled;
        document.getElementById("hold-order-btn").disabled = !enabled;
        document.getElementById("cancel-order-btn").disabled = !enabled;
    }

    function updateServiceSummary() {
        const orderType = document.getElementById("order-type").value;
        const orderTypeChip = document.querySelector(`.order-type-chip[data-value="${orderType}"]`);
        const tableSelect = document.getElementById("table-id");
        const tableLabel = tableSelect.options[tableSelect.selectedIndex] ? tableSelect.options[tableSelect.selectedIndex].text : "No Table";

        document.getElementById("service-mode-label").textContent = orderTypeChip ? orderTypeChip.textContent : "Dine In";
        document.getElementById("service-table-label").textContent = tableSelect.value ? tableLabel : "No Table";
    }

    function markActiveOrderButton() {
        document.querySelectorAll(".active-order-btn").forEach((button) => {
            button.classList.toggle("is-current", String(button.dataset.orderId) === String(currentOrderId));
        });
    }

    function updateVisibleItems() {
        const term = document.getElementById("menu-search").value.toLowerCase().trim();
        let visibleCount = 0;

        document.querySelectorAll(".item-card").forEach((card) => {
            const matchesCategory = !activeCategory || card.dataset.category === activeCategory;
            const matchesSearch = !term || card.dataset.name.includes(term);
            const visible = matchesCategory && matchesSearch;
            card.style.display = visible ? "" : "none";
            if (visible) {
                visibleCount += 1;
            }
        });

        document.getElementById("visible-items-count").textContent = `${visibleCount} items`;
    }

    function renderOrder(order) {
        currentOrderId = order.id;
        document.getElementById("order-number").textContent = order.order_number;
        document.getElementById("order-status-text").textContent = humanize(order.status);
        document.getElementById("cart-count").textContent = order.items.length;
        document.getElementById("subtotal-amount").textContent = `Rs. ${order.subtotal}`;
        document.getElementById("tax-amount").textContent = `Rs. ${order.tax_amount}`;
        document.getElementById("total-amount").textContent = `Rs. ${order.total_amount}`;
        setActionState(true);
        markActiveOrderButton();
        document.getElementById("customer-phone").value = order.customer_phone || "";
        document.getElementById("customer-name").value = order.customer_name || "";
        if (order.table_id) {
            document.getElementById("table-id").value = order.table_id;
        }
        if (order.order_type) {
            document.getElementById("order-type").value = order.order_type;
            document.querySelectorAll(".order-type-chip").forEach((chip) => {
                chip.classList.toggle("active", chip.dataset.value === order.order_type);
            });
        }
        updateServiceSummary();

        const cart = document.getElementById("cart-items");
        if (!order.items.length) {
            cart.innerHTML = `
                <div class="pos-empty-cart">
                    <strong>No items added yet</strong>
                    <span>Tap a category and select items to build the bill.</span>
                </div>
            `;
            return;
        }
        cart.innerHTML = order.items.map((item) => `
            <div class="cart-line">
                <div>
                    <strong>${item.name}</strong>
                    <div class="cart-line-meta">
                        <span>Qty ${item.quantity}</span>
                        <span>${humanize(item.status)}</span>
                    </div>
                    ${item.modifiers && item.modifiers.length ? `
                        <div class="cart-line-tags">
                            ${item.modifiers.map((modifier) => `
                                <span>${escapeHtml(modifier.group_name)}: ${escapeHtml(modifier.option_name)}${Number(modifier.price_delta) > 0 ? ` (+Rs. ${Number(modifier.price_delta).toFixed(2)})` : ""}</span>
                            `).join("")}
                        </div>
                    ` : ""}
                    ${item.notes ? `<div class="cart-line-note">Note: ${escapeHtml(item.notes)}</div>` : ""}
                </div>
                <div class="fw-semibold">Rs. ${item.price}</div>
            </div>
        `).join("");
    }

    async function createOrder() {
        const body = {
            order_type: document.getElementById("order-type").value,
            table_id: document.getElementById("table-id").value || null,
            phone_number: document.getElementById("customer-phone").value,
            customer_name: document.getElementById("customer-name").value,
        };
        const response = await posSafeFetch(config.createOrderUrl, {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken()},
            body: JSON.stringify(body),
        });
        const data = await response.json();
        renderOrder(data.order);
    }

    function closeCustomizer() {
        customizerState = null;
        document.getElementById("item-customizer-backdrop").classList.add("d-none");
        document.getElementById("customizer-error").classList.add("d-none");
        document.getElementById("customizer-error").textContent = "";
        document.getElementById("customizer-note").value = "";
        document.getElementById("customizer-modifier-groups").innerHTML = "";
    }

    function selectedModifierIds() {
        const ids = [];
        document.querySelectorAll("[data-modifier-option]:checked").forEach((input) => {
            ids.push(input.value);
        });
        return ids;
    }

    function updateCustomizerPrice() {
        if (!customizerState) return;
        const itemConfig = menuItemCatalog[String(customizerState.menuItemId)] || {base_price: "0", modifier_groups: []};
        const modifierTotal = selectedModifierIds().reduce((total, optionId) => {
            for (const group of itemConfig.modifier_groups) {
                const option = group.options.find((candidate) => String(candidate.id) === String(optionId));
                if (option) {
                    return total + Number(option.price_delta || 0);
                }
            }
            return total;
        }, 0);
        document.getElementById("customizer-base-price").textContent = formatCurrency(itemConfig.base_price);
        document.getElementById("customizer-modifier-price").textContent = formatCurrency(modifierTotal);
        document.getElementById("customizer-total-price").textContent = formatCurrency(Number(itemConfig.base_price || 0) + modifierTotal);
    }

    function openCustomizer(menuItemId) {
        const itemConfig = menuItemCatalog[String(menuItemId)];
        if (!itemConfig) {
            return;
        }
        customizerState = {menuItemId};
        document.getElementById("item-customizer-backdrop").classList.remove("d-none");
        document.getElementById("customizer-item-name").textContent = itemConfig.name;
        document.getElementById("customizer-item-description").textContent = itemConfig.description || "Choose modifiers and kitchen notes before adding.";
        document.getElementById("customizer-note").value = "";
        document.getElementById("customizer-error").classList.add("d-none");
        document.getElementById("customizer-error").textContent = "";
        document.getElementById("customizer-modifier-groups").innerHTML = itemConfig.modifier_groups.length
            ? itemConfig.modifier_groups.map((group) => `
                <section class="pos-customizer-group">
                    <div class="pos-customizer-group-head">
                        <strong>${escapeHtml(group.name)}</strong>
                        <span>${group.selection_type === "single" ? "Choose one" : "Choose any"}${group.is_required ? " • Required" : ""}</span>
                    </div>
                    <div class="pos-customizer-options">
                        ${group.options.map((option) => `
                            <label class="pos-customizer-option">
                                <input
                                    type="${group.selection_type === "single" ? "radio" : "checkbox"}"
                                    name="modifier-group-${group.id}"
                                    value="${option.id}"
                                    data-modifier-option
                                >
                                <span>${escapeHtml(option.name)}</span>
                                <strong>${Number(option.price_delta) > 0 ? `+Rs. ${Number(option.price_delta).toFixed(2)}` : "Included"}</strong>
                            </label>
                        `).join("")}
                    </div>
                </section>
            `).join("")
            : '<div class="pos-customizer-empty">No modifiers for this item. Add an optional kitchen note if needed.</div>';
        document.querySelectorAll("[data-modifier-option]").forEach((input) => {
            input.addEventListener("change", updateCustomizerPrice);
        });
        updateCustomizerPrice();
    }

    async function addItem(menuItemId, {modifiers = [], notes = ""} = {}) {
        if (!currentOrderId) {
            await createOrder();
        }
        const response = await fetch(urlFor(config.addItemUrlTemplate, currentOrderId), {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken()},
            body: JSON.stringify({menu_item_id: menuItemId, quantity: 1, modifiers, notes}),
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Unable to add item.");
        }
        renderOrder(data.order);
    }

    async function refreshOrder(orderId) {
        const response = await fetch(urlFor(config.orderStatusUrlTemplate, orderId));
        const data = await response.json();
        renderOrder(data.order);
    }

    document.querySelectorAll(".order-type-chip").forEach((button) => {
        button.addEventListener("click", () => {
            document.querySelectorAll(".order-type-chip").forEach((chip) => chip.classList.remove("active"));
            button.classList.add("active");
            document.getElementById("order-type").value = button.dataset.value;
            updateServiceSummary();
        });
    });

    document.getElementById("table-id").addEventListener("change", updateServiceSummary);
    document.getElementById("new-order-btn").addEventListener("click", createOrder);

    document.querySelectorAll(".pos-item-btn").forEach((button) => {
        button.addEventListener("click", async () => {
            if (button.dataset.hasModifiers === "1") {
                openCustomizer(button.dataset.itemId);
                return;
            }
            try {
                await addItem(button.dataset.itemId);
            } catch (error) {
                alert(error.message);
            }
        });
    });

    document.querySelectorAll("[data-customize-item-id]").forEach((button) => {
        button.addEventListener("click", () => openCustomizer(button.dataset.customizeItemId));
    });

    document.querySelectorAll(".active-order-btn").forEach((button) => {
        button.addEventListener("click", () => refreshOrder(button.dataset.orderId));
    });

    document.querySelectorAll(".category-filter").forEach((button) => {
        button.addEventListener("click", () => {
            document.querySelectorAll(".category-filter").forEach((btn) => btn.classList.remove("active"));
            button.classList.add("active");
            activeCategory = button.dataset.category;
            document.getElementById("selected-category-label").textContent = button.querySelector(".category-name").textContent;
            updateVisibleItems();
        });
    });

    document.getElementById("menu-search").addEventListener("input", (event) => {
        updateVisibleItems();
    });

    document.getElementById("send-kot-btn").addEventListener("click", async () => {
        if (!currentOrderId) return;
        const response = await posSafeFetch(urlFor(config.sendKotUrlTemplate, currentOrderId), {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken()},
            body: "{}",
        });
        const data = await response.json();
        renderOrder(data.order);
        alert(data.kot_number ? `KOT created: ${data.kot_number}` : "No new KOT items to send.");
    });

    document.getElementById("settle-order-btn").addEventListener("click", async () => {
        if (!currentOrderId) return;
        const methodId = document.getElementById("payment-method-id").value;
        const response = await posSafeFetch(urlFor(config.settleOrderUrlTemplate, currentOrderId), {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken()},
            body: JSON.stringify({payments: [{method_id: methodId, amount: document.getElementById("total-amount").textContent.replace("Rs. ", "")}]}),
        });
        const data = await response.json();
        renderOrder(data.order);
        window.open(urlFor(config.receiptUrlTemplate, currentOrderId), "_blank");
    });

    document.getElementById("hold-order-btn").addEventListener("click", async () => {
        if (!currentOrderId) return;
        const response = await posSafeFetch(urlFor(config.holdOrderUrlTemplate, currentOrderId), {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken()},
            body: "{}",
        });
        const data = await response.json();
        renderOrder(data.order);
    });

    document.getElementById("cancel-order-btn").addEventListener("click", async () => {
        if (!currentOrderId) return;
        const response = await posSafeFetch(urlFor(config.cancelOrderUrlTemplate, currentOrderId), {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken()},
            body: "{}",
        });
        const data = await response.json();
        renderOrder(data.order);
    });

    document.getElementById("customizer-close-btn").addEventListener("click", closeCustomizer);
    document.getElementById("customizer-cancel-btn").addEventListener("click", closeCustomizer);
    document.getElementById("item-customizer-backdrop").addEventListener("click", (event) => {
        if (event.target.id === "item-customizer-backdrop") {
            closeCustomizer();
        }
    });
    document.getElementById("customizer-add-btn").addEventListener("click", async () => {
        if (!customizerState) {
            return;
        }
        const errorNode = document.getElementById("customizer-error");
        try {
            await addItem(customizerState.menuItemId, {
                modifiers: selectedModifierIds(),
                notes: document.getElementById("customizer-note").value.trim(),
            });
            closeCustomizer();
        } catch (error) {
            errorNode.textContent = error.message;
            errorNode.classList.remove("d-none");
        }
    });

    updateServiceSummary();
    updateVisibleItems();
    setActionState(false);

    if (initialTableId) {
        document.getElementById("table-id").value = initialTableId;
        document.getElementById("order-type").value = "dine_in";
        document.querySelectorAll(".order-type-chip").forEach((chip) => {
            chip.classList.toggle("active", chip.dataset.value === "dine_in");
        });
        updateServiceSummary();
    }

    if (initialOrderId) {
        refreshOrder(initialOrderId);
    }
})();
