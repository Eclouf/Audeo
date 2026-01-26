#!/usr/bin/env python3
"""
Entry point wrapper for Audeo - Used by PyInstaller
Handles relative imports and provides debug output
"""

import sys
import os
from pathlib import Path

# Setup logging to file for frozen environments
log_file = None
if getattr(sys, 'frozen', False):
    log_file = Path.home() / "Audeo_debug.log"
    # Redirect stderr to file too
    error_log = open(str(log_file) + ".err", "w", encoding='utf-8')
    sys.stderr = error_log
    log_file.write_text(f"Audeo starting (frozen={getattr(sys, 'frozen', False)})...\n", encoding='utf-8')
else:
    log_file = Path.home() / "Audeo_debug.log"
    log_file.write_text(f"Audeo starting (debug mode)...\n", encoding='utf-8')

def log_msg(msg):
    if log_file:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{msg}\n")
    print(msg)

# Get the base directory
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    base_dir = Path(sys.executable).parent
    log_msg(f"Frozen mode: base_dir = {base_dir}")
else:
    # Running as script
    base_dir = Path(__file__).parent
    log_msg(f"Script mode: base_dir = {base_dir}")

# Add src directory to path for imports
src_dir = base_dir / "src" if (base_dir / "src").exists() else base_dir
log_msg(f"src_dir = {src_dir}, exists = {src_dir.exists()}")
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
    log_msg(f"Added to sys.path: {str(src_dir)}")

# Add project root
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))
    log_msg(f"Added to sys.path: {str(base_dir)}")

log_msg(f"sys.path = {sys.path[:3]}")

if __name__ == '__main__':
    try:
        log_msg("Attempting to import audeo2.app...")
        from audeo2.app import main
        log_msg("Successfully imported main()")
        log_msg("Launching Audeo GUI...")
        app = main()
        log_msg("App object created, starting main_loop...")
        app.main_loop()
        log_msg("Audeo exited normally")
    except Exception as e:
        log_msg(f"ERROR: {e}")
        import traceback
        tb_str = traceback.format_exc()
        log_msg(tb_str)
        print(f"Error starting Audeo: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
