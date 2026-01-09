from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    pass

SUPERRELOAD_JS = """
<script>
(function() {
    var ws = null;
    var reconnectAttempts = 0;
    var maxReconnectAttempts = 10;
    var reconnectDelay = 1000;

    function connect() {
        var wsUrl = 'ws://' + window.location.hostname + ':9877';
        ws = new WebSocket(wsUrl);

        ws.onopen = function() {
            console.log('[superreload] Connected');
            reconnectAttempts = 0;
        };

        ws.onmessage = function(event) {
            var msg = JSON.parse(event.data);
            if (msg.type === 'reload') {
                console.log('[superreload] Reloading...', msg.data.files);
                window.location.reload();
            } else if (msg.type === 'error') {
                console.error('[superreload] Error:', msg.data.message);
            }
        };

        ws.onclose = function() {
            console.log('[superreload] Disconnected');
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                setTimeout(connect, reconnectDelay * reconnectAttempts);
            }
        };

        ws.onerror = function(error) {
            console.error('[superreload] WebSocket error:', error);
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', connect);
    } else {
        connect();
    }
})();
</script>
"""


class SuperReloadMiddleware:
    def __init__(self, get_response: Callable[[Any], Any]) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        response = self.get_response(request)

        if not self._should_inject(request, response):
            return response

        self._inject_script(response)
        return response

    def _should_inject(self, request: Any, response: Any) -> bool:
        content_type = response.get("Content-Type", "")
        if "text/html" not in content_type:
            return False

        if response.status_code != 200:
            return False

        return request.headers.get("X-Requested-With") != "XMLHttpRequest"

    def _inject_script(self, response: Any) -> None:
        if not hasattr(response, "content"):
            return

        try:
            content = response.content.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            return

        if "</body>" in content:
            content = content.replace("</body>", f"{SUPERRELOAD_JS}</body>")
            response.content = content.encode("utf-8")
            if "Content-Length" in response:
                response["Content-Length"] = len(response.content)
