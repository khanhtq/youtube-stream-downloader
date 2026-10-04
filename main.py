"""
YouTube Stream & Video Downloader
Main Entry Point (CLI & GUI)
"""

import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def main():
    cli_flags = {"--cli", "-u", "--url", "-s", "--start", "-e", "--end", "-c", "--cutoff", "-h", "--help", "-i", "--info"}
    
    # If any CLI arguments are passed, route to CLI mode
    if any(arg in cli_flags for arg in sys.argv[1:]):
        from cli import run_cli
        sys.exit(run_cli())
    else:
        # Launch modern minimalist GUI
        try:
            from ui.app import App
            app = App()
            app.mainloop()
        except ImportError as e:
            print(f"Failed to launch GUI: {e}")
            print("Falling back to CLI mode...")
            from cli import run_cli
            sys.exit(run_cli())

if __name__ == "__main__":
    main()
