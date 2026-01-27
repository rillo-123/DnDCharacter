/**
 * Console Logger - Captures browser console output and writes to backend file in real-time
 * 
 * Usage:
 * - New timestamped log file created on page load: logs/browser-console-YYYYMMDD-HHMMSS.log
 * - Press Ctrl+Shift+R to start a new log file
 * - Only one active log file at a time
 */

(function() {
    'use strict';
    
    const LOG_ENDPOINT = '/api/console-log';
    const NEW_LOG_ENDPOINT = '/api/console-log/new';
    
    let sendQueue = [];
    let isSending = false;
    let currentLogFile = null;
    
    // Get timestamp for log entries
    function getTimestamp() {
        const now = new Date();
        return now.toISOString();
    }
    
    // Format log entry
    function formatLogEntry(level, args) {
        const timestamp = getTimestamp();
        const message = Array.from(args).map(arg => {
            if (typeof arg === 'object') {
                try {
                    return JSON.stringify(arg, null, 2);
                } catch (e) {
                    return String(arg);
                }
            }
            return String(arg);
        }).join(' ');
        
        return `[${timestamp}] [${level.toUpperCase()}] ${message}`;
    }
    
    // Send logs to backend
    async function sendToBackend(entry) {
        sendQueue.push(entry);
        
        if (isSending) return;
        
        isSending = true;
        while (sendQueue.length > 0) {
            const batch = sendQueue.splice(0, 10); // Send up to 10 at once
            
            try {
                await fetch(LOG_ENDPOINT, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ entries: batch })
                });
            } catch (e) {
                // Silently fail - don't want to create infinite loop
            }
        }
        isSending = false;
    }
    
    // Start a new log file (with timestamp in filename)
    async function startNewLogFile() {
        try {
            const response = await fetch(NEW_LOG_ENDPOINT, { method: 'POST' });
            const data = await response.json();
            if (data.filename) {
                currentLogFile = data.filename;
                console.log(`New log file: ${currentLogFile}`);
            }
        } catch (e) {
            console.error('Failed to start new log file:', e);
        }
    }
    
    // Save original console methods
    const originalConsole = {
        log: console.log,
        info: console.info,
        warn: console.warn,
        error: console.error,
        debug: console.debug
    };
    
    // Intercept console.log
    console.log = function(...args) {
        sendToBackend(formatLogEntry('log', args));
        originalConsole.log.apply(console, args);
    };
    
    // Intercept console.info
    console.info = function(...args) {
        sendToBackend(formatLogEntry('info', args));
        originalConsole.info.apply(console, args);
    };
    
    // Intercept console.warn
    console.warn = function(...args) {
        sendToBackend(formatLogEntry('warn', args));
        originalConsole.warn.apply(console, args);
    };
    
    // Intercept console.error
    console.error = function(...args) {
        sendToBackend(formatLogEntry('error', args));
        originalConsole.error.apply(console, args);
    };
    
    // Intercept console.debug
    console.debug = function(...args) {
        sendToBackend(formatLogEntry('debug', args));
        originalConsole.debug.apply(console, args);
    };
    
    // Capture uncaught errors
    window.addEventListener('error', function(event) {
        const entry = formatLogEntry('error', [
            'Uncaught Error:',
            event.message,
            `at ${event.filename}:${event.lineno}:${event.colno}`,
            event.error?.stack || ''
        ]);
        sendToBackend(entry);
    });
    
    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        const entry = formatLogEntry('error', [
            'Unhandled Promise Rejection:',
            event.reason
        ]);
        sendToBackend(entry);
    });
    
    // Keyboard shortcut: Ctrl+Shift+R to start new log file
    document.addEventListener('keydown', function(event) {
        if (event.ctrlKey && event.shiftKey && event.key === 'R') {
            event.preventDefault();
            startNewLogFile().then(() => {
                sendToBackend(formatLogEntry('info', ['=== NEW LOG SESSION (Ctrl+Shift+R) ===']));
            });
        }
    });
    
    // Start new log file when page loads
    startNewLogFile().then(() => {
        sendToBackend(formatLogEntry('info', ['=== PAGE LOADED - NEW SESSION ===']));
    });
    
    // Expose function globally
    window.startNewLogFile = startNewLogFile;
    
})();
