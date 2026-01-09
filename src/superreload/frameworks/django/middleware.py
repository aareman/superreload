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
    var overlay = null;

    // Create stylesheet
    var style = document.createElement('style');
    style.textContent = `
        .superreload-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.95);
            z-index: 999999;
            overflow-y: auto;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Droid Sans Mono', 'Source Code Pro', monospace;
            color: #e4e4e7;
            animation: superreload-fadein 0.2s ease-out;
        }

        @keyframes superreload-fadein {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .superreload-overlay-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px 80px;
        }

        .superreload-header {
            border-left: 4px solid #ef4444;
            padding-left: 20px;
            margin-bottom: 32px;
            animation: superreload-slideright 0.3s ease-out;
        }

        @keyframes superreload-slideright {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .superreload-title {
            font-size: 18px;
            font-weight: 600;
            color: #ef4444;
            margin: 0 0 12px 0;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .superreload-error-type {
            font-size: 42px;
            font-weight: 700;
            color: #fca5a5;
            margin: 0 0 12px 0;
            letter-spacing: -0.02em;
            line-height: 1.1;
        }

        .superreload-error-message {
            font-size: 20px;
            color: #fecaca;
            margin: 0 0 8px 0;
            line-height: 1.4;
        }

        .superreload-module {
            font-size: 14px;
            color: #a1a1aa;
            font-style: italic;
        }

        .superreload-section {
            background: #18181b;
            border: 1px solid #27272a;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
            animation: superreload-slideup 0.4s ease-out;
            animation-fill-mode: both;
        }

        @keyframes superreload-slideup {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        .superreload-section:nth-child(2) { animation-delay: 0.1s; }
        .superreload-section:nth-child(3) { animation-delay: 0.15s; }
        .superreload-section:nth-child(4) { animation-delay: 0.2s; }

        .superreload-section-title {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #71717a;
            padding: 16px 20px;
            background: #09090b;
            border-bottom: 1px solid #27272a;
            margin: 0;
        }

        .superreload-frame {
            padding: 16px 20px;
            border-bottom: 1px solid #27272a;
            transition: background 0.15s ease;
        }

        .superreload-frame:last-child {
            border-bottom: none;
        }

        .superreload-frame:hover {
            background: #0f0f10;
        }

        .superreload-frame-location {
            font-size: 13px;
            color: #a1a1aa;
            margin-bottom: 6px;
            font-weight: 500;
        }

        .superreload-frame-function {
            color: #60a5fa;
            font-weight: 600;
        }

        .superreload-frame-code {
            font-size: 13px;
            color: #d4d4d8;
            padding: 8px 12px;
            background: #09090b;
            border-radius: 4px;
            border-left: 2px solid #3f3f46;
            margin-top: 8px;
            white-space: pre-wrap;
            word-break: break-all;
        }

        .superreload-locals {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #27272a;
        }

        .superreload-locals-title {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #71717a;
            margin-bottom: 8px;
        }

        .superreload-local-var {
            font-size: 12px;
            margin: 4px 0;
            display: flex;
            gap: 8px;
        }

        .superreload-local-name {
            color: #c084fc;
            font-weight: 600;
            min-width: 120px;
        }

        .superreload-local-value {
            color: #a3e635;
            flex: 1;
            word-break: break-all;
        }

        .superreload-source-line {
            display: flex;
            padding: 4px 20px;
            font-size: 13px;
            line-height: 1.6;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', 'Droid Sans Mono', 'Source Code Pro', monospace;
        }

        .superreload-source-line:hover {
            background: #0f0f10;
        }

        .superreload-line-number {
            color: #52525b;
            text-align: right;
            min-width: 50px;
            padding-right: 16px;
            user-select: none;
            font-weight: 600;
        }

        .superreload-line-code {
            color: #d4d4d8;
            white-space: pre;
            flex: 1;
        }

        .superreload-source-line-error {
            background: rgba(239, 68, 68, 0.15);
            border-left: 3px solid #ef4444;
        }

        .superreload-source-line-error .superreload-line-number {
            color: #ef4444;
            font-weight: 700;
        }

        .superreload-source-line-error .superreload-line-code {
            color: #fecaca;
            font-weight: 600;
        }

        .superreload-close {
            position: fixed;
            top: 24px;
            right: 24px;
            width: 40px;
            height: 40px;
            background: #27272a;
            border: 1px solid #3f3f46;
            border-radius: 8px;
            color: #a1a1aa;
            font-size: 24px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            z-index: 1000000;
        }

        .superreload-close:hover {
            background: #3f3f46;
            color: #ef4444;
            border-color: #ef4444;
            transform: rotate(90deg);
        }

        .superreload-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #09090b;
            border-top: 1px solid #27272a;
            padding: 16px;
            text-align: center;
            font-size: 12px;
            color: #71717a;
            letter-spacing: 0.05em;
        }

        .superreload-kbd {
            display: inline-block;
            padding: 4px 8px;
            background: #27272a;
            border: 1px solid #3f3f46;
            border-radius: 4px;
            font-family: inherit;
            font-size: 11px;
            font-weight: 600;
            color: #a1a1aa;
            margin: 0 4px;
        }
    `;
    document.head.appendChild(style);

    function createOverlay(errorData) {
        if (overlay) {
            document.body.removeChild(overlay);
        }

        overlay = document.createElement('div');
        overlay.className = 'superreload-overlay';

        var errors = errorData.details && errorData.details.errors ? errorData.details.errors : [];

        if (errors.length === 0) {
            // Fallback for simple error messages
            overlay.innerHTML = `
                <div class="superreload-overlay-content">
                    <div class="superreload-header">
                        <div class="superreload-title">🔥 Reload Error</div>
                        <div class="superreload-error-type">Error</div>
                        <div class="superreload-error-message">${escapeHtml(errorData.message)}</div>
                    </div>
                </div>
                <button class="superreload-close" onclick="this.parentElement.remove(); overlay = null;">×</button>
                <div class="superreload-footer">Press <span class="superreload-kbd">ESC</span> to dismiss</div>
            `;
        } else {
            var html = '<div class="superreload-overlay-content">';

            for (var i = 0; i < errors.length; i++) {
                var error = errors[i];

                html += '<div class="superreload-header">';
                html += '<div class="superreload-title">🔥 Reload Error</div>';
                html += '<div class="superreload-error-type">' + escapeHtml(error.type || 'Error') + '</div>';
                html += '<div class="superreload-error-message">' + escapeHtml(error.message || 'Unknown error') + '</div>';
                if (error.module) {
                    html += '<div class="superreload-module">in ' + escapeHtml(error.module) + '</div>';
                }
                html += '</div>';

                // Stack trace
                if (error.frames && error.frames.length > 0) {
                    html += '<div class="superreload-section">';
                    html += '<h3 class="superreload-section-title">Stack Trace</h3>';

                    for (var j = 0; j < error.frames.length; j++) {
                        var frame = error.frames[j];
                        html += '<div class="superreload-frame">';
                        html += '<div class="superreload-frame-location">';
                        html += '<span class="superreload-frame-function">' + escapeHtml(frame.name) + '</span> ';
                        html += 'at ' + escapeHtml(frame.filename) + ':' + frame.lineno;
                        html += '</div>';

                        if (frame.line) {
                            html += '<div class="superreload-frame-code">' + escapeHtml(frame.line) + '</div>';
                        }

                        // Local variables
                        if (frame.locals && Object.keys(frame.locals).length > 0) {
                            html += '<div class="superreload-locals">';
                            html += '<div class="superreload-locals-title">Local Variables</div>';
                            for (var varName in frame.locals) {
                                html += '<div class="superreload-local-var">';
                                html += '<span class="superreload-local-name">' + escapeHtml(varName) + '</span>';
                                html += '<span class="superreload-local-value">' + escapeHtml(frame.locals[varName]) + '</span>';
                                html += '</div>';
                            }
                            html += '</div>';
                        }

                        html += '</div>';
                    }

                    html += '</div>';
                }

                // Source code context
                if (error.sourceContext && error.sourceContext.length > 0) {
                    html += '<div class="superreload-section">';
                    html += '<h3 class="superreload-section-title">Source Code</h3>';

                    for (var k = 0; k < error.sourceContext.length; k++) {
                        var line = error.sourceContext[k];
                        var isErrorLine = line.lineno === error.errorLine;
                        var lineClass = isErrorLine ? 'superreload-source-line superreload-source-line-error' : 'superreload-source-line';

                        html += '<div class="' + lineClass + '">';
                        html += '<span class="superreload-line-number">' + line.lineno + '</span>';
                        html += '<span class="superreload-line-code">' + escapeHtml(line.code) + '</span>';
                        html += '</div>';
                    }

                    html += '</div>';
                }
            }

            html += '</div>';
            html += '<button class="superreload-close" onclick="this.parentElement.remove(); overlay = null;">×</button>';
            html += '<div class="superreload-footer">Press <span class="superreload-kbd">ESC</span> to dismiss</div>';

            overlay.innerHTML = html;
        }

        document.body.appendChild(overlay);

        // Focus for keyboard events
        overlay.setAttribute('tabindex', '-1');
        overlay.focus();
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function dismissOverlay() {
        if (overlay && overlay.parentElement) {
            overlay.parentElement.removeChild(overlay);
            overlay = null;
        }
    }

    // Keyboard handler
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && overlay) {
            dismissOverlay();
        }
    });

    function connect() {
        var wsUrl = 'ws://' + window.location.hostname + ':9877';
        ws = new WebSocket(wsUrl);

        ws.onopen = function() {
            console.log('[superreload] Connected');
            reconnectAttempts = 0;
            dismissOverlay(); // Auto-hide overlay on successful connection
        };

        ws.onmessage = function(event) {
            var msg = JSON.parse(event.data);
            if (msg.type === 'reload') {
                console.log('[superreload] Reloading...', msg.data.files);
                dismissOverlay(); // Hide overlay before reload
                window.location.reload();
            } else if (msg.type === 'error') {
                console.error('[superreload] Error:', msg.data.message);
                createOverlay(msg.data);
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
