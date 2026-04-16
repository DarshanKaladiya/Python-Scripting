let cart = [];
let allCategories = [];
let allItems = [];
let currentOrderStatus = '';
let currentTableUUID = '';

const iconMap = {
    'Starter': 'fa-bowl-food',
    'Main Course': 'fa-utensils',
    'Beverage': 'fa-glass-water',
    'Dessert': 'fa-ice-cream',
    'Pizza': 'fa-pizza-slice',
    'Burger': 'fa-burger'
};

// Fetching functions
async function fetchMenuData() {
    try {
        const response = await fetch('/api/categories/');
        const data = await response.json();
        allCategories = data;
        renderCategories(allCategories);
        
        // Default to all items
        filterByCategory('all');
    } catch (err) {
        console.error("Error loading menu:", err);
    }
}

// UI Rendering functions
function renderCategories(categories) {
    const list = document.getElementById('category-list');
    if (!list) return;
    list.innerHTML = '';
    
    // Add "All" category
    const allBtn = document.createElement('div');
    allBtn.className = 'cat-btn active';
    allBtn.id = 'cat-all';
    allBtn.innerHTML = `<i class="fas fa-th-large"></i><span>All</span>`;
    allBtn.onclick = () => filterByCategory('all');
    list.appendChild(allBtn);

    categories.forEach(cat => {
        const btn = document.createElement('div');
        btn.className = 'cat-btn';
        btn.id = `cat-${cat.id}`;
        const icon = iconMap[cat.name] || 'fa-utensils';
        btn.innerHTML = `<i class="fas ${icon}"></i><span>${cat.name}</span>`;
        btn.onclick = () => filterByCategory(cat.id);
        list.appendChild(btn);
    });
}

function filterByCategory(categoryId) {
    document.querySelectorAll('.cat-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById(`cat-${categoryId}`);
    if (activeBtn) activeBtn.classList.add('active');
    
    renderItems(categoryId);
}

function renderItems(categoryId) {
    const grid = document.getElementById('items-grid');
    grid.innerHTML = '';
    
    let itemsToDisplay = [];
    if (categoryId === 'all') {
        allCategories.forEach(cat => {
            itemsToDisplay = [...itemsToDisplay, ...cat.items];
        });
    } else {
        const category = allCategories.find(c => c.id === categoryId);
        itemsToDisplay = category ? category.items : [];
    }

    itemsToDisplay.forEach(item => {
        const card = document.createElement('div');
        card.className = 'item-card';
        card.onclick = () => addToCart(item);
        
        let dietClass = 'dot-nv';
        if (item.item_type === 'veg') dietClass = 'dot-v';
        else if (item.item_type === 'egg') dietClass = 'dot-e';

        let imageHtml = '';
        if (item.image) {
            imageHtml = `<div class="item-img" style="background-image: url('${item.image}')"></div>`;
        } else {
            imageHtml = `<div class="item-img fallback"><span>${item.name.charAt(0)}</span></div>`;
        }

        card.innerHTML = `
            ${imageHtml}
            <div class="item-details">
                <div style="font-weight: 700; margin-bottom: 0.5rem; display: flex; align-items: start; gap: 8px; text-align: left; line-height: 1.2;">
                    <span class="diet-dot ${dietClass}" style="flex-shrink:0; margin-top:2px;"><i class="fa-solid fa-circle"></i></span>
                    ${item.name}
                </div>
                <div style="color: var(--primary); font-weight: 800; font-size: 1.1rem; text-align: left;">₹${parseFloat(item.base_price).toFixed(2)}</div>
            </div>
        `;
        grid.appendChild(card);
    });
}

function addToCart(item) {
    const existing = cart.find(i => i.id === item.id && !i.isExisting);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({
            id: item.id,
            name: item.name,
            price: parseFloat(item.base_price),
            item_type: item.item_type,
            image: item.image,
            quantity: 1,
            isExisting: false
        });
    }
    updateCartUI();
}

function updateQty(itemId, delta) {
    const item = cart.find(i => i.id === itemId && !i.isExisting);
    if (item) {
        item.quantity += delta;
        if (item.quantity <= 0) {
            cart = cart.filter(i => !(i.id === itemId && !i.isExisting));
        }
    }
    updateCartUI();
}

function updateCartUI() {
    const cartList = document.getElementById('cart-list');
    cartList.innerHTML = '';
    
    if (cart.length === 0) {
        cartList.innerHTML = `
            <div style="padding: 4rem 2rem; text-align: center; color: var(--text-muted);">
                <i class="fas fa-shopping-cart fa-3x" style="opacity: 0.1; margin-bottom: 1.5rem;"></i>
                <p style="font-weight: 600;">Your cart is empty</p>
            </div>
        `;
        resetBillTotals();
        return;
    }

    const selectedOrderId = document.getElementById('selected-order-id')?.value;
    const isAppendMode = !!selectedOrderId;
    const settleBtn = document.getElementById('settle-btn');
    const directBillBtn = document.getElementById('direct-bill-btn');
    const kotBtn = document.getElementById('kot-btn');
    
    if (isAppendMode) {
        if (kotBtn) {
            kotBtn.innerHTML = '<i class="fas fa-receipt"></i> UPDATE KOT';
            kotBtn.style.flex = "1";
        }
    } else {
        if (settleBtn) settleBtn.style.display = 'none';
        if (directBillBtn) directBillBtn.style.display = 'flex';
        if (kotBtn) {
            kotBtn.innerHTML = '<i class="fas fa-receipt"></i> KOT';
            kotBtn.style.flex = "1";
        }
    }

    // "SERVE" Button Logic for Waiters
    const serveBtnId = 'waiter-serve-btn';
    let serveBtn = document.getElementById(serveBtnId);
    if (currentOrderStatus === 'ready') {
        if (!serveBtn) {
            serveBtn = document.createElement('button');
            serveBtn.id = serveBtnId;
            serveBtn.className = 'checkout-btn';
            serveBtn.style.background = '#818cf8';
            serveBtn.style.marginTop = '1rem';
            serveBtn.style.width = '100%';
            serveBtn.innerHTML = '<i class="fas fa-hand-holding-heart"></i> MARK AS SERVED';
            serveBtn.onclick = () => changeOrderStatus(selectedOrderId, 'completed');
            kotBtn.parentNode.parentNode.appendChild(serveBtn);
        }
    } else if (serveBtn) {
        serveBtn.remove();
    }

    let subtotal = 0;
    cart.forEach((item) => {
        const card = document.createElement('div');
        card.className = 'cart-item-card';
        if (item.isExisting) card.style.opacity = '0.7';

        let dietClass = 'dot-nv';
        if (item.item_type === 'veg') dietClass = 'dot-v';
        else if (item.item_type === 'egg') dietClass = 'dot-e';

        card.innerHTML = `
            <div class="cic-header">
                <div>
                    <div class="cic-name" style="display:flex; align-items:center;">
                        <span class="diet-dot ${dietClass}" style="margin-top:0px;"><i class="fa-solid fa-circle"></i></span>
                        ${item.name}
                        ${item.isExisting ? '<span style="font-size: 0.6rem; color: rgba(255,255,255,0.7); background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; margin-left: 6px;">KOT</span>' : ''}
                    </div>
                </div>
                <div class="cic-price">₹${(item.price * item.quantity).toFixed(2)}</div>
            </div>
            <div class="cic-controls">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    ${!item.isExisting ? `
                        <button class="qty-btn" onclick="updateQty('${item.id}', -1)">-</button>
                        <span style="font-weight: 800; font-size: 1rem; min-width: 20px; text-align: center; color: white;">${item.quantity}</span>
                        <button class="qty-btn" onclick="updateQty('${item.id}', 1)">+</button>
                    ` : `<span style="font-weight: 700; color: var(--text-muted);">Qty: ${item.quantity}</span>`}
                </div>
                ${!item.isExisting ? `
                    <button onclick="updateQty('${item.id}', -${item.quantity})" style="background: none; border: none; color: #ef4444; font-weight: 700; cursor: pointer; font-size: 0.75rem; transition: color 0.2s;" onmouseover="this.style.color='#f87171'" onmouseout="this.style.color='#ef4444'">REMOVE</button>
                ` : `<span style="font-size: 0.65rem; font-weight: 800; color: var(--text-muted); opacity:0.8;">LOCKED</span>`}
            </div>
        `;
        cartList.appendChild(card);
        subtotal += item.price * item.quantity;
    });

    const tax = subtotal * 0.05;
    const total = subtotal + tax;

    document.getElementById('bill-subtotal').innerText = '₹' + subtotal.toFixed(2);
    document.getElementById('bill-cgst').innerText = '₹' + (tax/2).toFixed(2);
    document.getElementById('bill-sgst').innerText = '₹' + (tax/2).toFixed(2);
    document.getElementById('cart-total').innerText = total.toFixed(2);
}

function resetBillTotals() {
    document.getElementById('bill-subtotal').innerText = '₹0.00';
    document.getElementById('bill-cgst').innerText = '₹0.00';
    document.getElementById('bill-sgst').innerText = '₹0.00';
    document.getElementById('cart-total').innerText = '0.00';
}

async function handleCheckout() {
    const selectedOrderId = document.getElementById('selected-order-id').value;
    const newItems = cart.filter(item => !item.isExisting);
    
    if (cart.length === 0) {
        alert("Cart is empty!");
        return;
    }

    if (selectedOrderId && newItems.length === 0) {
        alert("No new items added. Use 'Settle' to complete bill.");
        return;
    }

    let url = '/api/orders/';
    let method = 'POST';
    const selectedTableId = document.getElementById('selected-table-id').value;
    
    const custName = document.getElementById('pos-cust-name-sidebar').value;
    const custPhone = document.getElementById('pos-cust-phone-sidebar').value;

    let payload = {
        order_number: "ORD" + Date.now(),
        order_type: selectedTableId ? "dine_in" : "takeaway",
        status: "kot_sent",
        table: selectedTableId || null,
        customer_name: custName || null,
        customer_phone: custPhone || null,
        items: cart.map(item => ({ menu_item: item.id, quantity: item.quantity, price: item.price }))
    };

    if (selectedOrderId) {
        url = `/api/orders/${selectedOrderId}/add_items/`;
        payload = { items: newItems.map(item => ({ menu_item: item.id, quantity: item.quantity, price: item.price })) };
    }

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const data = await response.json();
            alert(selectedOrderId ? "Added to KOT!" : "Order Success!");
            if (selectedTableId) {
                window.location.href = '/tables/floor/';
            } else {
                // For Takeaway, load the new order so Tracking is visible
                window.location.href = `/pos/?order_id=${data.id}`;
            }
        }
    } catch (err) { console.error(err); }
}

function toggleSettleModal(show) {
    const modal = document.getElementById('settle-modal');
    if (modal) modal.classList.toggle('active', show);
}

function toggleQRModal(show) {
    const modal = document.getElementById('qr-modal');
    if (modal) {
        const amount = document.getElementById('cart-total').innerText;
        const amountEl = document.getElementById('qr-amount-pos');
        if (amountEl) amountEl.innerText = amount;
        modal.classList.toggle('active', show);
    }
}

async function settleAndRelease() {
    const orderId = document.getElementById('selected-order-id').value;
    if (!orderId) return;
    toggleSettleModal(true);
}

function handleSettleChoice(method) {
    posSetPayment(method);
}

function posSetPayment(method) {
    const hiddenInput = document.getElementById('pos-selected-payment');
    if (hiddenInput) hiddenInput.value = method;
    
    document.querySelectorAll('#settle-modal .pay-btn').forEach(b => b.classList.remove('active'));
    const activeBtn = document.getElementById(`pos-pay-${method}`);
    if (activeBtn) activeBtn.classList.add('active');
}

function executeSettle() {
    const hiddenInput = document.getElementById('pos-selected-payment');
    if (!hiddenInput) return;
    const method = hiddenInput.value;
    
    toggleSettleModal(false);
    if (method === 'upi') {
        toggleQRModal(true);
    } else {
        if (confirm(`Settle this bill via ${method.toUpperCase()} and release table?`)) {
            confirmSettle(method);
        }
    }
}

function openTakeawaySettle() {
    if (cart.length === 0) {
        alert("Cart is empty!");
        return;
    }
    toggleSettleModal(true);
}

async function confirmSettle(method) {
    const orderId = document.getElementById('selected-order-id').value;
    const custName = document.getElementById('pos-cust-name-sidebar').value;
    const custPhone = document.getElementById('pos-cust-phone-sidebar').value;
    const selectedTableId = document.getElementById('selected-table-id').value;
    
    if (!orderId) {
        // Direct Takeaway Settle
        const payload = {
            order_number: "ORD" + Date.now(),
            order_type: selectedTableId ? "dine_in" : "takeaway",
            status: "completed",
            payment_method: method,
            payment_status: "paid",
            customer_name: custName || null,
            customer_phone: custPhone || null,
            table: selectedTableId || null,
            items: cart.map(item => ({ menu_item: item.id, quantity: item.quantity, price: item.price }))
        };

        const resp = await fetch('/api/orders/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify(payload)
        });

        if (resp.ok) {
            const data = await resp.json();
            toggleQRModal(false);
            alert("Direct Bill Created & Settled!");
            // Load the settled order so we can access tracking or print invoice
            window.location.href = `/pos/?order_id=${data.id}`;
        }
        return;
    }

    // Existing Order Settle
    const resp = await fetch(`/api/orders/${orderId}/update_status/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ 
            status: 'completed',
            payment_method: method,
            payment_status: 'paid',
            customer_name: custName || undefined,
            customer_phone: custPhone || undefined
        })
    });
    if (resp.ok) {
        toggleQRModal(false);
        alert("Bill Settled successfully!");
        window.location.href = '/tables/floor/';
    }
}


function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function fetchPendingOrders() {
    try {
        const response = await fetch('/api/orders/pending/');
        if (response.ok) {
            const data = await response.json();
            renderPendingOrders(data);
            updateAlertBadge(data.length);
        }
    } catch (err) {
        console.error("Error fetching pending orders:", err);
    }
}

function updateAlertBadge(count) {
    const badge = document.getElementById('pending-count-badge');
    if (badge) {
        if (count > 0) {
            badge.innerText = count;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }
}

function renderPendingOrders(orders) {
    const list = document.getElementById('pending-orders-list');
    if (!list) return;
    
    list.innerHTML = '';
    
    if (orders.length === 0) {
        list.innerHTML = '<div style="padding: 2rem; text-align: center; color: #94a3b8;">No pending customer orders</div>';
        return;
    }

    orders.forEach(order => {
        const row = document.createElement('div');
        row.className = 'pending-row';
        row.innerHTML = `
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: 800; color: #1e293b;">Order #${order.order_number.slice(-6)}</div>
                    <div style="font-size: 0.75rem; background: #fee2e2; color: #ef4444; padding: 2px 8px; border-radius: 4px; font-weight: 800;">
                        ${order.payment_method.toUpperCase()}
                    </div>
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">
                    ${order.customer_name ? `<i class="fas fa-user"></i> ${order.customer_name} • ` : ''}
                    ${order.order_type.replace('_', ' ').toUpperCase()} • ₹${order.total_amount}
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--primary); font-weight: 700;">
                    ${order.items.map(i => `${i.quantity}x ${i.menu_item_name}`).join(', ')}
                </div>
            </div>
            <div style="margin-left: 1rem;">
                <button onclick="confirmOrder(${order.id})" style="background: var(--primary); color: white; border: none; padding: 0.8rem 1rem; border-radius: 12px; font-weight: 800; cursor: pointer; white-space: nowrap;">
                    CONFIRM
                </button>
            </div>
        `;
        list.appendChild(row);
    });
}

async function confirmOrder(orderId) {
    try {
        const response = await fetch(`/api/orders/${orderId}/update_status/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json', 
                'X-CSRFToken': getCookie('csrftoken') 
            },
            body: JSON.stringify({ status: 'kot_sent' })
        });
        if (response.ok) {
            fetchPendingOrders();
        }
    } catch (err) {
        console.error("Error confirming order:", err);
    }
}

// Tracker Sharing Modal Logic
function toggleTrackerModal(show) {
    const modal = document.getElementById('tracker-modal');
    if (modal) modal.classList.toggle('active', show);
}

async function showTrackerModal() {
    const tableId = document.getElementById('selected-table-id').value;
    const orderId = document.getElementById('selected-order-id').value;
    
    if (!tableId && !orderId) return;

    let uuid = '';
    
    try {
        if (tableId) {
            // For Dine-in, prioritize Table-based tracking (standard QR on table)
            const resp = await fetch(`/tables/api/tables/${tableId}/`);
            if (resp.ok) {
                const table = await resp.json();
                uuid = table.qr_code_uuid;
            }
        } else if (orderId) {
            // For Takeaway, use the specific Order's tracking UUID
            const resp = await fetch(`/api/orders/${orderId}/`);
            if (resp.ok) {
                const order = await resp.json();
                uuid = order.tracking_uuid;
            }
        }

        if (!uuid) {
            alert("No tracking ID available for this selection.");
            return;
        }

        const trackUrl = `${window.location.origin}/track/${uuid}/`;
        document.getElementById('tracker-url-input').value = trackUrl;
        
        // Generate QR via qrserver.com
        const qrImg = document.getElementById('tracker-qr-img');
        qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(trackUrl)}`;
        
        toggleTrackerModal(true);
    } catch (err) { console.error("Error fetching tracking ID:", err); }
}

function copyTrackerLink() {
    const input = document.getElementById('tracker-url-input');
    input.select();
    document.execCommand('copy');
    alert("Tracking link copied to clipboard!");
}

async function changeOrderStatus(orderId, status) {
    if (!confirm(`Mark this order as ${status.toUpperCase()}?`)) return;
    try {
        const resp = await fetch(`/api/orders/${orderId}/update_status/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ status: status })
        });
        if (resp.ok) {
            alert("Order status updated!");
            location.reload(); // Refresh to catch new state
        }
    } catch (err) { console.error(err); }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchMenuData();
    fetchPendingOrders();
    setInterval(fetchPendingOrders, 20000); // Poll every 20 seconds
});
