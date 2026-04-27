#!/usr/bin/env python3
"""
FastAPI server for PySheet.

Run:
    python backend_fastapi.py
    python -m uvicorn backend_fastapi:app --host localhost --port 8080 --reload
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re
import sys
import traceback
from typing import Any
import zipfile

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response


PROJECT_ROOT = Path(__file__).parent
STATIC_DIR = PROJECT_ROOT / "static"
CONFIG_FILE = PROJECT_ROOT / "config.json"


def load_config() -> dict[str, Any]:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "autoexport": {
            "enabled": True,
            "autosave_dir": "./exports/autosaves",
            "watch_interval_seconds": 5,
            "export_format": "json",
        },
        "logging": {"level": "INFO", "log_dir": "./logs"},
        "server": {"host": "127.0.0.1", "port": 5000, "debug": False},
    }


config = load_config()

LOG_DIR = PROJECT_ROOT / config["logging"]["log_dir"]
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / "fastapi_server.log"
logger = logging.getLogger("pysheet.fastapi")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if not logger.handlers:
    file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


EXPORT_DIR = PROJECT_ROOT / config.get("exports", {}).get(
    "dir",
    config["autoexport"].get("autosave_dir", "exports/autosaves"),
)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="PySheet API", version="0.1.0")

_current_console_log: Path | None = None


def cleanup_old_exports_for_character(filename: str) -> None:
    """Keep only 10 most recent exports per character, archive older ones to zip."""
    try:
        match = re.match(r"([A-Za-z0-9_]+?)_", filename)
        character_prefix = match.group(1) if match else "Unknown"

        char_files = sorted(
            [f for f in EXPORT_DIR.glob(f"{character_prefix}_*.json") if f.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if len(char_files) > 10:
            old_files = char_files[10:]
            zip_path = EXPORT_DIR / f"{character_prefix}_old.zip"

            logger.info(
                "Character '%s' has %s exports, archiving %s older files",
                character_prefix,
                len(char_files),
                len(old_files),
            )

            with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_DEFLATED) as zf:
                for old_file in old_files:
                    zf.write(old_file, arcname=old_file.name)
                    logger.info("Archived to %s: %s", zip_path.name, old_file.name)
    except Exception as exc:
        logger.warning("Export cleanup error (non-critical): %s", exc)


def resolve_static_path(path: str) -> Path:
    candidate = (STATIC_DIR / path).resolve()
    static_root = STATIC_DIR.resolve()
    if not candidate.is_relative_to(static_root) or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return candidate


async def read_json_body(request: Request) -> dict[str, Any] | None:
    try:
        data = await request.json()
    except Exception:
        return None
    return data if isinstance(data, dict) else None


@app.get("/")
async def index() -> FileResponse:
    """Serve index.html."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico")
async def favicon() -> Response:
    """Return a tiny svg favicon to avoid 404."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
        '<rect width="16" height="16" fill="#2b6cb0"/>'
        "</svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")


@app.post("/api/export")
async def export_character(request: Request) -> JSONResponse:
    """Save a character export file."""
    try:
        data = await read_json_body(request)

        if not data:
            return JSONResponse({"error": "No JSON data provided"}, status_code=400)

        filename = data.get("filename")
        content = data.get("content")

        if not filename:
            return JSONResponse({"error": "Missing filename"}, status_code=400)

        if content is None:
            return JSONResponse({"error": "Missing content"}, status_code=400)

        filename = Path(str(filename)).name
        file_path = EXPORT_DIR / filename

        logger.info("Writing file: %s to %s", filename, file_path)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

        file_size = file_path.stat().st_size
        logger.info("[OK] %s successfully written to disk (%s bytes)", filename, file_size)

        cleanup_old_exports_for_character(filename)

        return JSONResponse(
            {
                "success": True,
                "filename": filename,
                "path": f"/exports/{filename}",
                "size": file_size,
            },
            status_code=200,
        )

    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        logger.error("Export error: %s", error_msg)
        logger.debug(traceback.format_exc())
        return JSONResponse({"error": error_msg}, status_code=500)


@app.get("/api/export")
async def export_character_get_not_allowed() -> JSONResponse:
    """Return method-not-allowed for accidental GET requests."""
    return JSONResponse({"error": "Method not allowed"}, status_code=405)


@app.get("/api/exports")
async def list_exports() -> JSONResponse:
    """List exported JSON files."""
    try:
        files = []
        for file_path in sorted(EXPORT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            files.append(
                {
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                }
            )

        return JSONResponse({"success": True, "count": len(files), "exports": files}, status_code=200)

    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/console-log")
async def write_console_log(request: Request) -> JSONResponse:
    """Receive browser console logs and append them to the current timestamped file."""
    global _current_console_log

    try:
        data = await read_json_body(request)
        if not data or "entries" not in data:
            return JSONResponse({"error": "Missing entries"}, status_code=400)

        entries = data.get("entries", [])
        if not entries:
            return JSONResponse({"success": True}, status_code=200)

        if _current_console_log is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            _current_console_log = LOG_DIR / f"browser-console-{timestamp}.log"

        with open(_current_console_log, "a", encoding="utf-8") as f:
            for entry in entries:
                f.write(str(entry) + "\n")

        return JSONResponse({"success": True, "count": len(entries)}, status_code=200)

    except Exception as exc:
        logger.error("Console log write error: %s", exc)
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/console-log/new")
async def new_console_log() -> JSONResponse:
    """Start a new timestamped console log file and clean up old log files."""
    global _current_console_log

    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        _current_console_log = LOG_DIR / f"browser-console-{timestamp}.log"
        _current_console_log.write_text("", encoding="utf-8")

        logger.info("Started new console log: %s", _current_console_log.name)

        try:
            log_files = sorted(
                LOG_DIR.glob("browser-console-*.log"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for old_file in log_files[10:]:
                old_file.unlink()
                logger.info("Deleted old console log: %s", old_file.name)
        except Exception as cleanup_error:
            logger.warning("Console log cleanup error: %s", cleanup_error)

        return JSONResponse(
            {
                "success": True,
                "filename": _current_console_log.name,
                "path": str(_current_console_log.relative_to(PROJECT_ROOT)),
            },
            status_code=200,
        )

    except Exception as exc:
        logger.error("Console log new file error: %s", exc)
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/exports/{filename:path}")
async def serve_export(filename: str) -> FileResponse:
    """Serve saved export files by filename."""
    candidate = (EXPORT_DIR / filename).resolve()
    export_root = EXPORT_DIR.resolve()
    if not candidate.is_relative_to(export_root) or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(candidate)


@app.get("/{path:path}")
async def serve_static(path: str) -> FileResponse:
    """Serve static files from the static directory."""
    return FileResponse(resolve_static_path(path))


def main() -> None:
    parser = argparse.ArgumentParser(description="FastAPI server for DnD Character Sheet")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging and reload")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn auto-reload")

    args = parser.parse_args()

    logger.info("Export directory: %s", EXPORT_DIR.absolute())
    logger.info("Starting FastAPI server at http://%s:%s", args.host, args.port)
    logger.info("API endpoint: POST /api/export")
    logger.info("Debug mode: %s", "enabled" if args.debug else "disabled")
    logger.info("Log file: %s", log_file)

    import uvicorn

    reload = args.reload or args.debug
    target: str | FastAPI = "backend_fastapi:app" if reload else app
    uvicorn.run(
        target,
        host=args.host,
        port=args.port,
        reload=reload,
        log_level="debug" if args.debug else "info",
    )


if __name__ == "__main__":
    main()
