(function() {
    'use strict';

    var config = {
        wsPort: 9877,
        maxReconnectAttempts: 10,
        reconnectDelay: 1000,
        debug: false
    };

    var ws = null;
    var reconnectAttempts = 0;
    var overlay = null;

    var style = document.createElement('style');
    style.textContent = [
        '.superreload-overlay {',
        '    position: fixed;',
        '    top: 0;',
        '    left: 0;',
        '    right: 0;',
        '    bottom: 0;',
        '    background: rgba(0, 0, 0, 0.95);',
        '    z-index: 999999;',
        '    overflow-y: auto;',
        '    font-family: "SF Mono", "Monaco", "Inconsolata", "Fira Code", "Droid Sans Mono", "Source Code Pro", monospace;',
        '    color: #e4e4e7;',
        '    animation: superreload-fadein 0.2s ease-out;',
        '}',
        '@keyframes superreload-fadein {',
        '    from { opacity: 0; }',
        '    to { opacity: 1; }',
        '}',
        '.superreload-overlay-content {',
        '    max-width: 1200px;',
        '    margin: 0 auto;',
        '    padding: 40px 20px 80px;',
        '}',
        '.superreload-header {',
        '    border-left: 4px solid #ef4444;',
        '    padding-left: 20px;',
        '    margin-bottom: 32px;',
        '    animation: superreload-slideright 0.3s ease-out;',
        '}',
        '@keyframes superreload-slideright {',
        '    from { transform: translateX(-20px); opacity: 0; }',
        '    to { transform: translateX(0); opacity: 1; }',
        '}',
        '.superreload-title {',
        '    font-size: 18px;',
        '    font-weight: 600;',
        '    color: #ef4444;',
        '    margin: 0 0 12px 0;',
        '    letter-spacing: 0.05em;',
        '    text-transform: uppercase;',
        '}',
        '.superreload-error-type {',
        '    font-size: 42px;',
        '    font-weight: 700;',
        '    color: #fca5a5;',
        '    margin: 0 0 12px 0;',
        '    letter-spacing: -0.02em;',
        '    line-height: 1.1;',
        '}',
        '.superreload-error-message {',
        '    font-size: 20px;',
        '    color: #fecaca;',
        '    margin: 0 0 8px 0;',
        '    line-height: 1.4;',
        '}',
        '.superreload-module {',
        '    font-size: 14px;',
        '    color: #a1a1aa;',
        '    font-style: italic;',
        '}',
        '.superreload-section {',
        '    background: #18181b;',
        '    border: 1px solid #27272a;',
        '    border-radius: 8px;',
        '    margin-bottom: 20px;',
        '    overflow: hidden;',
        '    animation: superreload-slideup 0.4s ease-out;',
        '    animation-fill-mode: both;',
        '}',
        '@keyframes superreload-slideup {',
        '    from { transform: translateY(20px); opacity: 0; }',
        '    to { transform: translateY(0); opacity: 1; }',
        '}',
        '.superreload-section:nth-child(2) { animation-delay: 0.1s; }',
        '.superreload-section:nth-child(3) { animation-delay: 0.15s; }',
        '.superreload-section:nth-child(4) { animation-delay: 0.2s; }',
        '.superreload-section-title {',
        '    font-size: 12px;',
        '    font-weight: 600;',
        '    text-transform: uppercase;',
        '    letter-spacing: 0.1em;',
        '    color: #71717a;',
        '    padding: 16px 20px;',
        '    background: #09090b;',
        '    border-bottom: 1px solid #27272a;',
        '    margin: 0;',
        '}',
        '.superreload-frame {',
        '    padding: 16px 20px;',
        '    border-bottom: 1px solid #27272a;',
        '    transition: background 0.15s ease;',
        '}',
        '.superreload-frame:last-child {',
        '    border-bottom: none;',
        '}',
        '.superreload-frame:hover {',
        '    background: #0f0f10;',
        '}',
        '.superreload-frame-location {',
        '    font-size: 13px;',
        '    color: #a1a1aa;',
        '    margin-bottom: 6px;',
        '    font-weight: 500;',
        '}',
        '.superreload-frame-function {',
        '    color: #60a5fa;',
        '    font-weight: 600;',
        '}',
        '.superreload-frame-code {',
        '    font-size: 13px;',
        '    color: #d4d4d8;',
        '    padding: 8px 12px;',
        '    background: #09090b;',
        '    border-radius: 4px;',
        '    border-left: 2px solid #3f3f46;',
        '    margin-top: 8px;',
        '    white-space: pre-wrap;',
        '    word-break: break-all;',
        '}',
        '.superreload-locals {',
        '    margin-top: 12px;',
        '    padding-top: 12px;',
        '    border-top: 1px solid #27272a;',
        '}',
        '.superreload-locals-title {',
        '    font-size: 11px;',
        '    font-weight: 600;',
        '    text-transform: uppercase;',
        '    letter-spacing: 0.1em;',
        '    color: #71717a;',
        '    margin-bottom: 8px;',
        '}',
        '.superreload-local-var {',
        '    font-size: 12px;',
        '    margin: 4px 0;',
        '    display: flex;',
        '    gap: 8px;',
        '}',
        '.superreload-local-name {',
        '    color: #c084fc;',
        '    font-weight: 600;',
        '    min-width: 120px;',
        '}',
        '.superreload-local-value {',
        '    color: #a3e635;',
        '    flex: 1;',
        '    word-break: break-all;',
        '}',
        '.superreload-source-line {',
        '    display: flex;',
        '    padding: 4px 20px;',
        '    font-size: 13px;',
        '    line-height: 1.6;',
        '    font-family: "SF Mono", "Monaco", "Inconsolata", "Fira Code", "Droid Sans Mono", "Source Code Pro", monospace;',
        '}',
        '.superreload-source-line:hover {',
        '    background: #0f0f10;',
        '}',
        '.superreload-line-number {',
        '    color: #52525b;',
        '    text-align: right;',
        '    min-width: 50px;',
        '    padding-right: 16px;',
        '    user-select: none;',
        '    font-weight: 600;',
        '}',
        '.superreload-line-code {',
        '    color: #d4d4d8;',
        '    white-space: pre;',
        '    flex: 1;',
        '}',
        '.superreload-source-line-error {',
        '    background: rgba(239, 68, 68, 0.15);',
        '    border-left: 3px solid #ef4444;',
        '}',
        '.superreload-source-line-error .superreload-line-number {',
        '    color: #ef4444;',
        '    font-weight: 700;',
        '}',
        '.superreload-source-line-error .superreload-line-code {',
        '    color: #fecaca;',
        '    font-weight: 600;',
        '}',
        '.superreload-close {',
        '    position: fixed;',
        '    top: 24px;',
        '    right: 24px;',
        '    width: 40px;',
        '    height: 40px;',
        '    background: #27272a;',
        '    border: 1px solid #3f3f46;',
        '    border-radius: 8px;',
        '    color: #a1a1aa;',
        '    font-size: 24px;',
        '    cursor: pointer;',
        '    display: flex;',
        '    align-items: center;',
        '    justify-content: center;',
        '    transition: all 0.2s ease;',
        '    z-index: 1000000;',
        '}',
        '.superreload-close:hover {',
        '    background: #3f3f46;',
        '    color: #ef4444;',
        '    border-color: #ef4444;',
        '    transform: rotate(90deg);',
        '}',
        '.superreload-footer {',
        '    position: fixed;',
        '    bottom: 0;',
        '    left: 0;',
        '    right: 0;',
        '    background: #09090b;',
        '    border-top: 1px solid #27272a;',
        '    padding: 16px;',
        '    text-align: center;',
        '    font-size: 12px;',
        '    color: #71717a;',
        '    letter-spacing: 0.05em;',
        '}',
        '.superreload-kbd {',
        '    display: inline-block;',
        '    padding: 4px 8px;',
        '    background: #27272a;',
        '    border: 1px solid #3f3f46;',
        '    border-radius: 4px;',
        '    font-family: inherit;',
        '    font-size: 11px;',
        '    font-weight: 600;',
        '    color: #a1a1aa;',
        '    margin: 0 4px;',
        '}',
        '.superreload-indicator {',
        '    position: fixed;',
        '    bottom: 10px;',
        '    right: 10px;',
        '    padding: 8px 12px;',
        '    border-radius: 4px;',
        '    font-family: sans-serif;',
        '    font-size: 12px;',
        '    z-index: 999998;',
        '    transition: opacity 0.3s;',
        '    pointer-events: none;',
        '}'
    ].join('\n');
    document.head.appendChild(style);

    function log() {
        if (config.debug) {
            console.log.apply(console, ['[superreload]'].concat(Array.prototype.slice.call(arguments)));
        }
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function createOverlay(errorData) {
        if (overlay) {
            document.body.removeChild(overlay);
        }

        overlay = document.createElement('div');
        overlay.className = 'superreload-overlay';

        var errors = errorData.details && errorData.details.errors ? errorData.details.errors : [];

        if (errors.length === 0) {
            overlay.innerHTML = [
                '<div class="superreload-overlay-content">',
                '    <div class="superreload-header">',
                '        <div class="superreload-title">🔥 Reload Error</div>',
                '        <div class="superreload-error-type">Error</div>',
                '        <div class="superreload-error-message">' + escapeHtml(errorData.message) + '</div>',
                '    </div>',
                '</div>',
                '<button class="superreload-close" onclick="this.parentElement.remove();">×</button>',
                '<div class="superreload-footer">Press <span class="superreload-kbd">ESC</span> to dismiss</div>'
            ].join('\n');
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
            html += '<button class="superreload-close" onclick="this.parentElement.remove();">×</button>';
            html += '<div class="superreload-footer">Press <span class="superreload-kbd">ESC</span> to dismiss</div>';

            overlay.innerHTML = html;
        }

        document.body.appendChild(overlay);
        overlay.setAttribute('tabindex', '-1');
        overlay.focus();
    }

    function dismissOverlay() {
        if (overlay && overlay.parentElement) {
            overlay.parentElement.removeChild(overlay);
            overlay = null;
        }
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && overlay) {
            dismissOverlay();
        }
    });

    function connect() {
        var wsUrl = 'ws://' + window.location.hostname + ':' + config.wsPort;

        try {
            ws = new WebSocket(wsUrl);
        } catch (e) {
            log('Failed to create WebSocket:', e);
            scheduleReconnect();
            return;
        }

        ws.onopen = function() {
            log('Connected to', wsUrl);
            reconnectAttempts = 0;
            showIndicator('connected');
            dismissOverlay();
        };

        ws.onmessage = function(event) {
            var msg;
            try {
                msg = JSON.parse(event.data);
            } catch (e) {
                log('Invalid message:', event.data);
                return;
            }

            handleMessage(msg);
        };

        ws.onclose = function() {
            log('Disconnected');
            showIndicator('disconnected');
            scheduleReconnect();
        };

        ws.onerror = function(error) {
            log('WebSocket error:', error);
        };
    }

    function handleMessage(msg) {
        switch (msg.type) {
            case 'connected':
                log('Server acknowledged connection');
                break;

            case 'reload':
                log('Reloading page...', msg.data.files);
                showIndicator('reloading');
                dismissOverlay();
                setTimeout(function() {
                    window.location.reload();
                }, 100);
                break;

            case 'css_reload':
                log('CSS reload:', msg.data.files);
                reloadCSS(msg.data.files);
                break;

            case 'js_reload':
                log('JS reload:', msg.data.files);
                reloadJS(msg.data.files);
                break;

            case 'error':
                console.error('[superreload] Server error:', msg.data.message);
                createOverlay(msg.data);
                break;

            default:
                log('Unknown message type:', msg.type);
        }
    }

    function reloadCSS(files) {
        var links = Array.prototype.slice.call(document.querySelectorAll('link[rel="stylesheet"]'));
        var reloadedCount = 0;

        links.forEach(function(oldLink) {
            var href = oldLink.getAttribute('href');
            if (!href) return;

            var shouldReload = files.length === 0;
            for (var j = 0; j < files.length; j++) {
                var filename = files[j];
                if (href.indexOf(filename) !== -1) {
                    shouldReload = true;
                    break;
                }
            }

            if (shouldReload) {
                var newLink = document.createElement('link');
                newLink.rel = 'stylesheet';
                newLink.type = 'text/css';

                var baseHref = href.replace(/[?&]_superreload=\d+/, '');
                var separator = baseHref.indexOf('?') !== -1 ? '&' : '?';
                newLink.href = baseHref + separator + '_superreload=' + Date.now();

                newLink.onload = function() {
                    if (oldLink.parentNode) {
                        oldLink.parentNode.removeChild(oldLink);
                    }
                };

                newLink.onerror = function() {
                    if (newLink.parentNode) {
                        newLink.parentNode.removeChild(newLink);
                    }
                    log('Failed to load CSS:', newLink.href);
                };

                if (oldLink.parentNode) {
                    oldLink.parentNode.insertBefore(newLink, oldLink.nextSibling);
                }
                reloadedCount++;
            }
        });

        if (reloadedCount > 0) {
            showToast('CSS Updated', '#10b981');
        } else if (files.length > 0) {
            links.forEach(function(link) {
                var href = link.getAttribute('href');
                if (href) {
                    var baseHref = href.replace(/[?&]_superreload=\d+/, '');
                    var separator = baseHref.indexOf('?') !== -1 ? '&' : '?';
                    link.href = baseHref + separator + '_superreload=' + Date.now();
                }
            });
            showToast('CSS Updated', '#10b981');
        }
    }

    function reloadJS(files) {
        showToast('JS Updated - Reloading...', '#f59e0b');
        setTimeout(function() {
            window.location.reload();
        }, 500);
    }

    function showToast(message, color) {
        var toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = 'position:fixed;top:20px;right:20px;padding:12px 20px;background:' + color + ';color:#fff;border-radius:8px;font-family:sans-serif;font-size:14px;font-weight:600;z-index:999999;animation:superreload-fadein 0.2s ease-out;box-shadow:0 4px 12px rgba(0,0,0,0.3);';
        document.body.appendChild(toast);
        setTimeout(function() {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s ease-out';
            setTimeout(function() {
                if (toast.parentElement) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, 2000);
    }

    function scheduleReconnect() {
        if (reconnectAttempts >= config.maxReconnectAttempts) {
            log('Max reconnection attempts reached');
            return;
        }

        reconnectAttempts++;
        var delay = config.reconnectDelay * reconnectAttempts;
        log('Reconnecting in', delay, 'ms (attempt', reconnectAttempts + ')');

        setTimeout(connect, delay);
    }

    function showIndicator(status, message) {
        var indicator = document.getElementById('superreload-indicator');

        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'superreload-indicator';
            indicator.className = 'superreload-indicator';
            document.body.appendChild(indicator);
        }

        switch (status) {
            case 'connected':
                indicator.style.backgroundColor = '#22c55e';
                indicator.style.color = 'white';
                indicator.textContent = '🔥 Hot Reload Active';
                fadeOut(indicator, 2000);
                break;

            case 'disconnected':
                indicator.style.backgroundColor = '#eab308';
                indicator.style.color = 'black';
                indicator.textContent = '⚠️ Reconnecting...';
                indicator.style.opacity = '1';
                break;

            case 'reloading':
                indicator.style.backgroundColor = '#3b82f6';
                indicator.style.color = 'white';
                indicator.textContent = '🔄 Reloading...';
                indicator.style.opacity = '1';
                break;

            case 'error':
                indicator.style.backgroundColor = '#ef4444';
                indicator.style.color = 'white';
                indicator.textContent = '❌ ' + (message || 'Reload Error');
                indicator.style.opacity = '1';
                break;
        }
    }

    function fadeOut(element, delay) {
        setTimeout(function() {
            element.style.opacity = '0';
        }, delay);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', connect);
    } else {
        connect();
    }

    window.superreload = {
        connect: connect,
        config: config,
        dismissOverlay: dismissOverlay
    };
})();
