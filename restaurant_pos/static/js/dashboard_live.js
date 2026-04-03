(function () {
    const config = window.DASHBOARD_CONFIG;
    if (!config || !config.summaryUrl) {
        return;
    }

    const fields = {
        heroSales: document.getElementById("dashboard-hero-sales"),
        heroOpenTables: document.getElementById("dashboard-hero-open-tables"),
        sales: document.getElementById("dashboard-sales-value"),
        orders: document.getElementById("dashboard-orders-value"),
        openTables: document.getElementById("dashboard-open-tables-value"),
        lowStock: document.getElementById("dashboard-low-stock-value"),
        recentOrdersMeta: document.getElementById("dashboard-recent-orders-meta"),
        recentOrdersBody: document.getElementById("dashboard-recent-orders-body"),
        lowStockMeta: document.getElementById("dashboard-low-stock-meta"),
        lowStockList: document.getElementById("dashboard-low-stock-list"),
        tableStatusMeta: document.getElementById("dashboard-table-status-meta"),
        tableStatusList: document.getElementById("dashboard-table-status-list"),
    };

    function formatCurrency(value) {
        return `Rs. ${value}`;
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function orderStatusClass(status) {
        if (status === "completed") return "status-success";
        if (status === "ready") return "status-info";
        if (status === "cancelled") return "status-danger";
        if (status === "kot_sent" || status === "in_progress") return "status-warning";
        return "status-neutral";
    }

    function tableStatusClass(status) {
        if (status === "occupied") return "is-busy";
        if (status === "available") return "is-open";
        if (status === "reserved") return "is-held";
        return "is-attention";
    }

    function updateText(node, nextValue) {
        if (!node || node.textContent === nextValue) {
            return;
        }
        node.textContent = nextValue;
        node.classList.remove("dashboard-live-flash");
        void node.offsetWidth;
        node.classList.add("dashboard-live-flash");
    }

    function updateHtml(node, nextHtml) {
        if (!node || node.innerHTML === nextHtml) {
            return;
        }
        node.innerHTML = nextHtml;
        node.classList.remove("dashboard-live-flash");
        void node.offsetWidth;
        node.classList.add("dashboard-live-flash");
    }

    function renderRecentOrders(orders) {
        if (!orders.length) {
            return '<tr><td colspan="6" class="text-center py-5 text-muted">No orders yet. The live order stream will appear here once billing starts.</td></tr>';
        }
        return orders.map((order) => `
            <tr>
                <td><strong>${escapeHtml(order.order_number)}</strong></td>
                <td>${escapeHtml(order.order_type_display)}</td>
                <td>${escapeHtml(order.table_name)}</td>
                <td><span class="status-pill ${orderStatusClass(order.status)}">${escapeHtml(order.status_display)}</span></td>
                <td>${formatCurrency(order.total_amount)}</td>
                <td>${escapeHtml(order.created_time)}</td>
            </tr>
        `).join("");
    }

    function renderLowStockItems(items) {
        if (!items.length) {
            return '<div class="dashboard-empty-state">All ingredient levels are healthy.</div>';
        }
        return items.map((item) => `
            <div class="dashboard-list-row">
                <div>
                    <strong>${escapeHtml(item.name)}</strong>
                    <span>${escapeHtml(item.sku)}</span>
                </div>
                <div class="text-end">
                    <strong class="text-danger">${escapeHtml(item.current_stock)} ${escapeHtml(item.unit)}</strong>
                    <span>Reorder at ${escapeHtml(item.reorder_level)} ${escapeHtml(item.unit)}</span>
                </div>
            </div>
        `).join("");
    }

    function renderTableStatus(rows) {
        if (!rows.length) {
            return '<div class="dashboard-empty-state">No floor tables created yet.</div>';
        }
        return rows.map((row) => `
            <div class="dashboard-list-row">
                <div>
                    <strong>${escapeHtml(row.status_display)}</strong>
                    <span>Tables in this state right now</span>
                </div>
                <span class="table-state-pill ${tableStatusClass(row.status)}">${escapeHtml(row.total)}</span>
            </div>
        `).join("");
    }

    async function refreshSummary() {
        try {
            const response = await fetch(config.summaryUrl, {
                headers: {"X-Requested-With": "XMLHttpRequest"},
                cache: "no-store",
            });
            if (!response.ok) {
                return;
            }
            const data = await response.json();
            updateText(fields.heroSales, formatCurrency(data.today_sales));
            updateText(fields.heroOpenTables, String(data.open_tables));
            updateText(fields.sales, formatCurrency(data.today_sales));
            updateText(fields.orders, String(data.orders_today));
            updateText(fields.openTables, String(data.open_tables));
            updateText(fields.lowStock, String(data.low_stock_count));
            updateText(fields.recentOrdersMeta, `Latest ${data.recent_orders.length} orders`);
            updateText(fields.lowStockMeta, `${data.low_stock_count} flagged`);
            updateText(fields.tableStatusMeta, `${data.table_status.length} states`);
            updateHtml(fields.recentOrdersBody, renderRecentOrders(data.recent_orders));
            updateHtml(fields.lowStockList, renderLowStockItems(data.low_stock_items));
            updateHtml(fields.tableStatusList, renderTableStatus(data.table_status));
        } catch (error) {
        }
    }

    refreshSummary();
    const intervalId = window.setInterval(refreshSummary, 10000);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            refreshSummary();
        }
    });
    window.addEventListener("beforeunload", () => window.clearInterval(intervalId));
})();
