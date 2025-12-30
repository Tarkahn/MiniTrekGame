"""
Star Trek Tactical Game - Main Entry Point
This launches the graphical version of the game.
"""

import sys
import os
import glob

def cleanup_old_logs():
    """Remove old debug log files, keeping only the most recent one."""
    try:
        logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
        if not os.path.exists(logs_dir):
            return
        
        # Find all debug log files
        log_pattern = os.path.join(logs_dir, 'debug_log_*.txt')
        log_files = glob.glob(log_pattern)
        
        if len(log_files) <= 1:
            return  # Keep the only log file or no files to clean
        
        # Sort by modification time (newest first)
        log_files.sort(key=os.path.getmtime, reverse=True)
        
        # Remove all but the most recent
        for old_log in log_files[1:]:
            try:
                os.remove(old_log)
                print(f"Removed old log: {os.path.basename(old_log)}")
            except OSError as e:
                print(f"Warning: Could not remove log {old_log}: {e}")
                
    except Exception as e:
        print(f"Warning: Log cleanup failed: {e}")

def main():
    """Launch the graphical Star Trek game."""
    print("Star Trek Tactical Game")
    print("=======================")
    print("Launching graphical interface...")
    
    # Clean up old log files before starting
    cleanup_old_logs()
    
    # Add the project root to Python path for imports
    project_root = os.path.abspath(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        # Import and run the wireframe game
        # The game loop runs at module import time and calls sys.exit() when done
        from ui import wireframe
        del wireframe  # Explicitly mark as used (game runs on import)
    except ImportError as e:
        print(f"\nError: Failed to import game modules: {e}")
        print("Please ensthis ure all dependencies are installed:")
        print("  pip install pygame")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()