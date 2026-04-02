(function () {
    const QUEUE_KEY = "restaurant-pos-offline-queue";

    async function replayQueue() {
        const raw = localStorage.getItem(QUEUE_KEY);
        if (!raw) {
            return;
        }
        const queue = JSON.parse(raw);
        const remaining = [];
        for (const request of queue) {
            try {
                const response = await fetch(request.url, request.options);
                if (!response.ok) {
                    remaining.push(request);
                }
            } catch (error) {
                remaining.push(request);
            }
        }
        localStorage.setItem(QUEUE_KEY, JSON.stringify(remaining));
    }

    window.posSafeFetch = async function (url, options) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error("Request failed");
            }
            return response;
        } catch (error) {
            const queue = JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");
            queue.push({url, options});
            localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
            throw error;
        }
    };

    window.addEventListener("online", replayQueue);
    replayQueue();
})();
