#!/usr/bin/env python3
"""
Flask server for PySheet with backend file export support
Run: python backend.py
Access: http://localhost:8080

Optional arguments:
    --host HOST     Server host (default: localhost)
    --port PORT     Server port (default: 8080)
    --debug         Enable debug mode (default: False)
"""

from flask import Flask, request, jsonify, send_from_directory, Response
from pathlib import Path
import json
from datetime import datetime
import traceback
import argparse
import sys
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__, static_folder='static', static_url_path='/')

# Load configuration
CONFIG_FILE = Path(__file__).parent / 'config.json'
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    config = {
        'autoexport': {'enabled': True, 'autosave_dir': './exports/autosaves', 'watch_interval_seconds': 5, 'export_format': 'json'},
        'logging': {'level': 'INFO', 'log_dir': './logs'},
        'server': {'host': '127.0.0.1', 'port': 5000, 'debug': False}
    }

# Setup logging
LOG_DIR = Path(__file__).parent / config['logging']['log_dir']
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / 'flask_server.log'
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# File handler with rotation
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Add handlers to Flask logger
app.logger.addHandler(file_handler)
app.logger.addHandler(console_handler)
app.logger.setLevel(logging.INFO)

# Export directory configuration (from config or default)
# Use exports.dir if configured, otherwise fall back to autoexport.autosave_dir for backwards compatibility
EXPORT_DIR = Path(__file__).parent / config.get('exports', {}).get('dir', config['autoexport'].get('autosave_dir', 'exports/autosaves'))
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

@app.route('/')
def index():
    """Serve index.html"""
    return send_from_directory('static', 'index.html')

@app.route('/favicon.ico')
def favicon():
    """Return a tiny svg favicon to avoid 404"""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
        '<rect width="16" height="16" fill="#2b6cb0"/>'
        '</svg>'
    )
    return Response(svg, mimetype='image/svg+xml')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/api/export', methods=['POST'])
def export_character():
    """
    API endpoint to save character export file
    
    Request JSON:
    {
        "filename": "Enwer_Cleric_lvl9_20251213_1716.json",
        "content": {...character data...}
    }
    
    Response:
    {
        "success": true,
        "filename": "Enwer_Cleric_lvl9_20251213_1716.json",
        "path": "/exports/Enwer_Cleric_lvl9_20251213_1716.json"
    }
    """
    try:
        data = request.get_json(force=False, silent=True)
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        filename = data.get('filename')
        content = data.get('content')
        
        if not filename:
            return jsonify({'error': 'Missing filename'}), 400
        
        if content is None:
            return jsonify({'error': 'Missing content'}), 400
        
        # Sanitize filename to prevent path traversal
        filename = Path(filename).name
        
        file_path = EXPORT_DIR / filename
        
        app.logger.info(f"Writing file: {filename} to {file_path}")
        # Write file with proper JSON formatting
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        file_size = file_path.stat().st_size
        app.logger.info(f"✓ {filename} successfully written to disk ({file_size} bytes)")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'path': f'/exports/{filename}',
            'size': file_size
        }), 200
    
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        app.logger.error(f"Export error: {error_msg}")
        app.logger.debug(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/api/exports', methods=['GET'])
def list_exports():
    """List all exported files"""
    try:
        files = []
        for file_path in sorted(EXPORT_DIR.glob('*.json'), reverse=True):
            files.append({
                'filename': file_path.name,
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })
        
        return jsonify({
            'success': True,
            'count': len(files),
            'exports': files
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flask server for DnD Character Sheet')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (default: False)')
    
    args = parser.parse_args()
    
    app.logger.info(f"Export directory: {EXPORT_DIR.absolute()}")
    app.logger.info(f"Starting Flask server at http://{args.host}:{args.port}")
    app.logger.info(f"API endpoint: POST /api/export")
    app.logger.info(f"Debug mode: {'enabled' if args.debug else 'disabled'}")
    app.logger.info(f"Log file: {log_file}")
    
    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        app.logger.info("Server stopped by user")
        sys.exit(0)
