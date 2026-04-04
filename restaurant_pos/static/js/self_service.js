(function () {
    const config = window.SELF_SERVICE_CONFIG || {};
    const menuItemCatalog = JSON.parse(document.getElementById("self-service-menu-item-catalog").textContent || "{}");
    const cart = [];
    let activeCategory = "";
    let customizerState = null;

    function csrfToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : "";
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

    function currentPaymentOption() {
        const select = document.getElementById("self-payment-method-id");
        return select.options[select.selectedIndex];
    }

    function paymentIsCash() {
        return currentPaymentOption()?.dataset.isCash === "1";
    }

    function updatePaymentNote() {
        document.getElementById("self-payment-note").textContent = paymentIsCash()
            ? "Cash selected: the cashier will confirm this order before it reaches the kitchen."
            : "Digital payment selected: the order will go directly to the kitchen after successful payment.";
    }

    function selectedOrderType() {
        return document.getElementById("self-order-type").value;
    }

    function updateVisibleItems() {
        const term = document.getElementById("self-menu-search").value.toLowerCase().trim();
        let visibleCount = 0;
        document.querySelectorAll(".self-item-card").forEach((card) => {
            const matchesCategory = !activeCategory || card.dataset.category === activeCategory;
            const matchesSearch = !term || card.dataset.name.includes(term);
            const visible = matchesCategory && matchesSearch;
            card.style.display = visible ? "" : "none";
            if (visible) {
                visibleCount += 1;
            }
        });
        document.getElementById("self-visible-items-count").textContent = `${visibleCount} items`;
    }

    function computeLineSubtotal(item) {
        const modifierTotal = (item.modifiers || []).reduce((total, modifier) => total + Number(modifier.price_delta || 0), 0);
        return (Number(item.base_price || 0) + modifierTotal) * Number(item.quantity || 1);
    }

    function computeLineTax(item) {
        return computeLineSubtotal(item) * (Number(item.tax_rate || 0) / 100);
    }

    function renderCart() {
        const cartItemsNode = document.getElementById("self-cart-items");
        if (!cart.length) {
            cartItemsNode.innerHTML = `
                <div class="pos-empty-cart">
                    <strong>No items added yet</strong>
                    <span>Pick from the menu to start your order.</span>
                </div>
            `;
        } else {
            cartItemsNode.innerHTML = cart.map((item, index) => `
                <div class="cart-line">
                    <div>
                        <strong>${escapeHtml(item.name)}</strong>
                        <div class="cart-line-meta">
                            <span>Qty ${escapeHtml(item.quantity)}</span>
                            <button class="self-remove-line-btn" type="button" data-cart-index="${index}">Remove</button>
                        </div>
                        ${item.modifiers?.length ? `
                            <div class="cart-line-tags">
                                ${item.modifiers.map((modifier) => `
                                    <span>${escapeHtml(modifier.group_name)}: ${escapeHtml(modifier.option_name)}${Number(modifier.price_delta) > 0 ? ` (+Rs. ${Number(modifier.price_delta).toFixed(2)})` : ""}</span>
                                `).join("")}
                            </div>
                        ` : ""}
                        ${item.notes ? `<div class="cart-line-note">Note: ${escapeHtml(item.notes)}</div>` : ""}
                    </div>
                    <div class="fw-semibold">${formatCurrency(computeLineSubtotal(item) + computeLineTax(item))}</div>
                </div>
            `).join("");
        }

        const subtotal = cart.reduce((total, item) => total + computeLineSubtotal(item), 0);
        const tax = cart.reduce((total, item) => total + computeLineTax(item), 0);
        const grandTotal = subtotal + tax;
        const itemCount = cart.reduce((total, item) => total + Number(item.quantity || 1), 0);

        document.getElementById("self-cart-count").textContent = itemCount;
        document.getElementById("self-cart-badge").textContent = itemCount;
        document.getElementById("self-cart-total").textContent = formatCurrency(grandTotal);
        document.getElementById("self-subtotal-amount").textContent = formatCurrency(subtotal);
        document.getElementById("self-tax-amount").textContent = formatCurrency(tax);
        document.getElementById("self-total-amount").textContent = formatCurrency(grandTotal);

        document.querySelectorAll(".self-remove-line-btn").forEach((button) => {
            button.addEventListener("click", () => {
                cart.splice(Number(button.dataset.cartIndex), 1);
                renderCart();
            });
        });
    }

    function selectedModifierIds() {
        return Array.from(document.querySelectorAll("[data-self-modifier-option]:checked")).map((input) => input.value);
    }

    function selectedModifierSnapshot(itemConfig) {
        const optionIds = selectedModifierIds();
        const selectedByGroup = {};
        const snapshot = [];

        for (const group of itemConfig.modifier_groups || []) {
            const chosenOptions = group.options.filter((option) => optionIds.includes(String(option.id)));
            if (group.is_required && !chosenOptions.length) {
                throw new Error(`Please choose an option for ${group.name}.`);
            }
            if (group.selection_type === "single" && chosenOptions.length > 1) {
                throw new Error(`Choose only one option for ${group.name}.`);
            }
            selectedByGroup[group.id] = chosenOptions;
        }

        Object.values(selectedByGroup).forEach((options) => {
            options.forEach((option) => {
                const group = (itemConfig.modifier_groups || []).find((candidate) => candidate.options.some((item) => item.id === option.id));
                snapshot.push({
                    group_name: group?.name || "",
                    option_name: option.name,
                    price_delta: option.price_delta,
                });
            });
        });
        return {
            modifierIds: optionIds,
            modifierSnapshot: snapshot,
        };
    }

    function closeCustomizer() {
        customizerState = null;
        document.getElementById("self-item-customizer-backdrop").classList.add("d-none");
        document.getElementById("self-customizer-error").classList.add("d-none");
        document.getElementById("self-customizer-error").textContent = "";
        document.getElementById("self-customizer-note").value = "";
        document.getElementById("self-customizer-modifier-groups").innerHTML = "";
    }

    function updateCustomizerPrice() {
        if (!customizerState) {
            return;
        }
        const itemConfig = menuItemCatalog[String(customizerState.menuItemId)] || {base_price: "0", modifier_groups: []};
        const modifierTotal = selectedModifierIds().reduce((total, optionId) => {
            for (const group of itemConfig.modifier_groups || []) {
                const option = group.options.find((candidate) => String(candidate.id) === String(optionId));
                if (option) {
                    return total + Number(option.price_delta || 0);
                }
            }
            return total;
        }, 0);
        document.getElementById("self-customizer-base-price").textContent = formatCurrency(itemConfig.base_price);
        document.getElementById("self-customizer-modifier-price").textContent = formatCurrency(modifierTotal);
        document.getElementById("self-customizer-total-price").textContent = formatCurrency(Number(itemConfig.base_price || 0) + modifierTotal);
    }

    function openCustomizer(menuItemId) {
        const itemConfig = menuItemCatalog[String(menuItemId)];
        if (!itemConfig) {
            return;
        }
        customizerState = {menuItemId};
        document.getElementById("self-item-customizer-backdrop").classList.remove("d-none");
        document.getElementById("self-customizer-item-name").textContent = itemConfig.name;
        document.getElementById("self-customizer-item-description").textContent = itemConfig.description || "Choose modifiers and notes before adding this item.";
        document.getElementById("self-customizer-note").value = "";
        document.getElementById("self-customizer-error").classList.add("d-none");
        document.getElementById("self-customizer-error").textContent = "";
        document.getElementById("self-customizer-modifier-groups").innerHTML = itemConfig.modifier_groups.length
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
                                    name="self-modifier-group-${group.id}"
                                    value="${option.id}"
                                    data-self-modifier-option
                                >
                                <span>${escapeHtml(option.name)}</span>
                                <strong>${Number(option.price_delta) > 0 ? `+Rs. ${Number(option.price_delta).toFixed(2)}` : "Included"}</strong>
                            </label>
                        `).join("")}
                    </div>
                </section>
            `).join("")
            : '<div class="pos-customizer-empty">No modifiers for this item. Add an optional note if you want.</div>';
        document.querySelectorAll("[data-self-modifier-option]").forEach((input) => {
            input.addEventListener("change", updateCustomizerPrice);
        });
        updateCustomizerPrice();
    }

    function addLine(menuItemId, options = {}) {
        const itemConfig = menuItemCatalog[String(menuItemId)];
        if (!itemConfig) {
            return;
        }
        cart.push({
            menu_item_id: Number(menuItemId),
            name: itemConfig.name,
            quantity: 1,
            base_price: itemConfig.base_price,
            tax_rate: itemConfig.tax_rate,
            modifiers: options.modifierSnapshot || [],
            modifier_ids: options.modifierIds || [],
            notes: options.notes || "",
        });
        renderCart();
    }

    function setFeedback(message, type) {
        const node = document.getElementById("self-order-feedback");
        node.className = `alert alert-${type} mb-0`;
        node.textContent = message;
        node.classList.remove("d-none");
    }

    async function placeOrder() {
        if (!cart.length) {
            setFeedback("Add at least one item before placing the order.", "warning");
            return;
        }
        if (selectedOrderType() === "dine_in" && !document.getElementById("self-table-id").value) {
            setFeedback("Choose a table for dine-in self ordering.", "warning");
            return;
        }

        const button = document.getElementById("self-place-order-btn");
        button.disabled = true;
        setFeedback("Submitting your order...", "info");

        try {
            const response = await fetch(config.submitUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken(),
                },
                body: JSON.stringify({
                    order_type: selectedOrderType(),
                    table_id: document.getElementById("self-table-id").value || null,
                    payment_method_id: document.getElementById("self-payment-method-id").value,
                    phone_number: document.getElementById("self-customer-phone").value.trim(),
                    customer_name: document.getElementById("self-customer-name").value.trim(),
                    notes: document.getElementById("self-order-notes").value.trim(),
                    items: cart.map((item) => ({
                        menu_item_id: item.menu_item_id,
                        quantity: item.quantity,
                        modifiers: item.modifier_ids,
                        notes: item.notes,
                    })),
                }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || "Unable to place the order.");
            }
            const methodLabel = currentPaymentOption()?.textContent || "payment";
            setFeedback(`${data.message} Order ${data.order.order_number} placed with ${methodLabel}.`, data.direct_to_kitchen ? "success" : "warning");
            cart.length = 0;
            renderCart();
            document.getElementById("self-order-notes").value = "";
        } catch (error) {
            setFeedback(error.message, "danger");
        } finally {
            button.disabled = false;
        }
    }

    document.querySelectorAll("[data-self-order-type]").forEach((button) => {
        button.addEventListener("click", () => {
            document.querySelectorAll("[data-self-order-type]").forEach((chip) => chip.classList.remove("active"));
            button.classList.add("active");
            document.getElementById("self-order-type").value = button.dataset.selfOrderType;
        });
    });

    document.querySelectorAll("[data-self-category]").forEach((button) => {
        button.addEventListener("click", () => {
            document.querySelectorAll("[data-self-category]").forEach((chip) => chip.classList.remove("active"));
            button.classList.add("active");
            activeCategory = button.dataset.selfCategory;
            document.getElementById("self-selected-category-label").textContent = button.querySelector(".category-name").textContent;
            updateVisibleItems();
        });
    });

    document.getElementById("self-menu-search").addEventListener("input", updateVisibleItems);
    document.getElementById("self-payment-method-id").addEventListener("change", updatePaymentNote);
    document.getElementById("self-clear-cart-btn").addEventListener("click", () => {
        cart.length = 0;
        renderCart();
    });
    document.getElementById("self-place-order-btn").addEventListener("click", placeOrder);

    document.querySelectorAll(".self-item-btn").forEach((button) => {
        button.addEventListener("click", () => {
            if (button.dataset.hasModifiers === "1") {
                openCustomizer(button.dataset.itemId);
                return;
            }
            addLine(button.dataset.itemId);
        });
    });

    document.querySelectorAll(".self-customize-btn").forEach((button) => {
        button.addEventListener("click", () => openCustomizer(button.dataset.customizeItemId));
    });

    document.getElementById("self-customizer-close-btn").addEventListener("click", closeCustomizer);
    document.getElementById("self-customizer-cancel-btn").addEventListener("click", closeCustomizer);
    document.getElementById("self-item-customizer-backdrop").addEventListener("click", (event) => {
        if (event.target.id === "self-item-customizer-backdrop") {
            closeCustomizer();
        }
    });
    document.getElementById("self-customizer-add-btn").addEventListener("click", () => {
        if (!customizerState) {
            return;
        }
        const errorNode = document.getElementById("self-customizer-error");
        try {
            const itemConfig = menuItemCatalog[String(customizerState.menuItemId)] || {};
            const selection = selectedModifierSnapshot(itemConfig);
            addLine(customizerState.menuItemId, {
                modifierIds: selection.modifierIds,
                modifierSnapshot: selection.modifierSnapshot,
                notes: document.getElementById("self-customizer-note").value.trim(),
            });
            closeCustomizer();
        } catch (error) {
            errorNode.textContent = error.message;
            errorNode.classList.remove("d-none");
        }
    });

    updateVisibleItems();
    updatePaymentNote();
    renderCart();
})();
