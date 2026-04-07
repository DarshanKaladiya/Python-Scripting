// Central POS cart state
let cart = [];
let allCategories = [];
let allItems = [];

// Fetching functions
async function fetchMenuData() {
    try {
        const response = await fetch('/api/categories/');
        const data = await response.json();
        allCategories = data;
        renderCategories(allCategories);
        
        // Default to first category or all
        renderItems('all');
    } catch (err) {
        console.error("Error loading menu:", err);
    }
}

// UI Rendering functions
function renderCategories(categories) {
    const rail = document.querySelector('.cat-rail');
    rail.innerHTML = '';
    
    // Add "All" category
    const allBtn = document.createElement('div');
    allBtn.className = 'cat-btn active';
    allBtn.id = 'cat-all';
    allBtn.innerText = 'All Items';
    allBtn.onclick = () => filterByCategory('all');
    rail.appendChild(allBtn);

    categories.forEach(cat => {
        const btn = document.createElement('div');
        btn.className = 'cat-btn';
        btn.id = `cat-${cat.id}`;
        btn.innerText = cat.name;
        btn.onclick = () => filterByCategory(cat.id);
        rail.appendChild(btn);
    });
}

function filterByCategory(categoryId) {
    // Update active class
    document.querySelectorAll('.cat-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`cat-${categoryId}`).classList.add('active');
    
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
        card.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 0.5rem;">${item.name}</div>
            <div style="color: var(--primary); font-weight: 700;">₹${item.base_price}</div>
        `;
        grid.appendChild(card);
    });
}

function addToCart(item) {
    const existing = cart.find(i => i.id === item.id);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({
            id: item.id,
            name: item.name,
            price: parseFloat(item.base_price),
            quantity: 1
        });
    }
    updateCartUI();
}

function updateCartUI() {
    const cartList = document.getElementById('cart-list');
    cartList.innerHTML = '';
    
    if (cart.length === 0) {
        cartList.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-muted);">Cart is empty</div>';
    }

    let total = 0;
    cart.forEach((item, index) => {
        const row = document.createElement('div');
        row.style.padding = '1rem';
        row.style.borderBottom = '1px solid var(--border-color)';
        row.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <div style="font-weight: 600;">${item.name}</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted);">
                        ${item.quantity} x ₹${item.price.toFixed(2)}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 600;">₹${(item.price * item.quantity).toFixed(2)}</div>
                    <button onclick="removeFromCart(${index})" style="background: none; border: none; color: #ef4444; cursor: pointer; font-size: 0.75rem;">Remove</button>
                </div>
            </div>
        `;
        cartList.appendChild(row);
        total += item.price * item.quantity;
    });

    document.getElementById('cart-total').innerText = total.toFixed(2);
}

function removeFromCart(index) {
    cart.splice(index, 1);
    updateCartUI();
}

async function handleCheckout() {
    if (cart.length === 0) {
        alert("Cart is empty!");
        return;
    }
    
    // 1. Calculate totals
    let subtotal = 0;
    cart.forEach(item => subtotal += item.price * item.quantity);
    
    // 2. Prepare payload
    const selectedTableId = document.getElementById('selected-table-id').value;
    const payload = {
        order_number: "ORD" + Date.now(),
        order_type: selectedTableId ? "dine_in" : "takeaway",
        status: selectedTableId ? "kot_sent" : "completed",
        table: selectedTableId || null,
        subtotal: subtotal,
        tax: subtotal * 0.05, // 5% tax
        total_amount: subtotal * 1.05,
        items: cart.map(item => ({
            menu_item: item.id,
            quantity: item.quantity,
            price: item.price
        }))
    };

    try {
        const response = await fetch('/api/orders/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const data = await response.json();
            alert("Order Success! Order ID: " + data.order_number);
            
            // 3. Clear cart and refresh
            cart = [];
            updateCartUI();
            
            // 4. Option to print bill
            if (confirm("Would you like to print the bill?")) {
                printBill(data);
            }
        } else {
            const errData = await response.json();
            console.error("Order failed:", errData);
            alert("Order failed! Check console.");
        }
    } catch (err) {
        console.error("Checkout error:", err);
    }
}

function printBill(orderData) {
    // Basic printer-friendly window for now
    const printWindow = window.open('', '_blank', 'width=350,height=600');
    printWindow.document.write(`
        <html>
        <head><title>Bill - ${orderData.order_number}</title></head>
        <body style="font-family: monospace; padding: 20px; width: 300px;">
            <h2 style="text-align:center;">RESTAURANT POS</h2>
            <div style="text-align:center;">Tax Invoice</div>
            <hr>
            <div>Order: ${orderData.order_number}</div>
            <div>Date: ${new Date().toLocaleString()}</div>
            <hr>
            <table style="width:100%;">
                ${orderData.items.map(i => `
                    <tr><td>${i.quantity} x ${i.menu_item_name || 'Item'}</td><td style="text-align:right;">₹${(i.price * i.quantity).toFixed(2)}</td></tr>
                `).join('')}
            </table>
            <hr>
            <div style="display:flex; justify-content:space-between;"><b>Total</b> <b>₹${parseFloat(orderData.total_amount).toFixed(2)}</b></div>
            <hr>
            <div style="text-align:center; margin-top:20px;">THANK YOU!</div>
        </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// Utility to get CSRF token
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


// Initializing
document.addEventListener('DOMContentLoaded', () => {
    fetchMenuData();
});
