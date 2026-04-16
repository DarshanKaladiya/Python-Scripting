/**
 * EasyServe Live Order Tracker
 * Handles real-time polling and visual state management
 */

const STATUS_MAP = {
    'draft': { progress: 0, steps: [] },
    'awaiting_confirmation': { progress: 5, steps: [] },
    'kot_sent': { progress: 12.5, steps: ['step-ordered'] },
    'preparing': { progress: 41, steps: ['step-ordered', 'step-preparing'] },
    'ready': { progress: 70, steps: ['step-ordered', 'step-preparing', 'step-ready'] },
    'completed': { progress: 100, steps: ['step-ordered', 'step-preparing', 'step-ready', 'step-served'] }
};

function updateTrackerUI(status, displayStatus) {
    const config = STATUS_MAP[status] || { progress: 0, steps: [] };
    
    // Update progress bar
    const progressBar = document.getElementById('progress-line');
    if (progressBar) {
        progressBar.style.width = `${config.progress}%`;
    }

    // Update steps
    document.querySelectorAll('.step').forEach(step => {
        const id = step.id;
        step.classList.remove('active', 'completed');
        
        if (config.steps.includes(id)) {
            const stepIndex = config.steps.indexOf(id);
            if (stepIndex === config.steps.length - 1) {
                step.classList.add('active');
            } else {
                step.classList.add('completed');
            }
        }
    });

    // Update text
    const statusText = document.getElementById('display-status');
    if (statusText) {
        statusText.innerText = displayStatus;
    }
}

async function checkStatus() {
    const orderNumber = document.getElementById('order-number').value;
    if (!orderNumber) return;

    try {
        const response = await fetch(`/api/orders/check_status/?order_number=${orderNumber}`);
        if (response.ok) {
            const data = await response.json();
            updateTrackerUI(data.status, data.display_status);
            
            // If completed or cancelled, we might want to stop polling after some time
            if (data.status === 'completed' || data.status === 'cancelled') {
                console.log("Order finalized. Polling will continue for a few more minutes.");
            }
        }
    } catch (error) {
        console.error("Error polling status:", error);
    }
}

// Initial update on load
document.addEventListener('DOMContentLoaded', () => {
    const rawStatus = document.getElementById('raw-order-status')?.value;
    const initialDisplay = document.getElementById('display-status')?.innerText || 'Order Placed';
    
    if (rawStatus) {
        updateTrackerUI(rawStatus, initialDisplay);
    }

    // Start polling every 15 seconds
    setInterval(checkStatus, 15000);
});
