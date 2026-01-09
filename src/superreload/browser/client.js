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

    function log() {
        if (config.debug) {
            console.log.apply(console, ['[superreload]'].concat(Array.prototype.slice.call(arguments)));
        }
    }

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
                setTimeout(function() {
                    window.location.reload();
                }, 100);
                break;

            case 'error':
                console.error('[superreload] Server error:', msg.data.message);
                showIndicator('error', msg.data.message);
                break;

            default:
                log('Unknown message type:', msg.type);
        }
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
            indicator.style.cssText = 'position:fixed;bottom:10px;right:10px;padding:8px 12px;' +
                'border-radius:4px;font-family:sans-serif;font-size:12px;z-index:999999;' +
                'transition:opacity 0.3s;pointer-events:none;';
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
        config: config
    };
})();
