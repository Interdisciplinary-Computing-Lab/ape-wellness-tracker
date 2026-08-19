/** Attach Flask-WTF CSRF tokens to non-GET fetch requests. */
(function () {
    if (!window.fetch) {
        return;
    }
    var originalFetch = window.fetch;
    window.fetch = function (input, init) {
        init = init || {};
        var method = (init.method || "GET").toUpperCase();
        if (method === "GET" || method === "HEAD" || method === "OPTIONS") {
            return originalFetch.call(this, input, init);
        }
        var headers = new Headers(init.headers || {});
        if (!headers.has("X-CSRFToken") && !headers.has("X-CSRF-Token")) {
            var meta = document.querySelector('meta[name="csrf-token"]');
            if (meta && meta.content) {
                headers.set("X-CSRFToken", meta.content);
            }
        }
        init.headers = headers;
        return originalFetch.call(this, input, init);
    };
})();
