#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Attachment Extractor - Main Entry Point
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Direkte Imports ohne relative Pfade
from src.cli.argparser import parse_arguments, validate_arguments
from src.cli.interactive import interactive_setup, get_save_path_interactive
from src.utils.config_loader import prepare_config
from src.utils.colors import Colors
from src.core.extractor import EmailAttachmentExtractor
from src.utils.debug import enable_debug, dprint, dump_config

def main():
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()
    
    # Helper to mirror stdout/stderr to a log file
    log_setup = False
    def _setup_logging(path: str) -> bool:
        nonlocal log_setup
        try:
            log_path = os.path.expanduser(path)
            os.makedirs(os.path.dirname(log_path) or '.', exist_ok=True)
            log_fh = open(log_path, 'a', encoding='utf-8')

            class _TeeStream:
                def __init__(self, original, fh):
                    self._orig = original
                    self._fh = fh
                    self.encoding = getattr(original, 'encoding', 'utf-8')

                def write(self, s):
                    self._orig.write(s)
                    try:
                        from src.utils.colors import Colors as _C
                        self._fh.write(_C.strip_colors(s))
                    except Exception:
                        self._fh.write(s)

                def flush(self):
                    try:
                        self._orig.flush()
                    finally:
                        self._fh.flush()

                def isatty(self):
                    return getattr(self._orig, 'isatty', lambda: False)()

            sys.stdout = _TeeStream(sys.stdout, log_fh)
            sys.stderr = _TeeStream(sys.stderr, log_fh)
            print(Colors.info(f"Logging enabled. Mirroring output to: {log_path}"))
            log_setup = True
            return True
        except Exception as e:
            print(Colors.warning(f"Could not open log file '{path}': {e}"))
            return False

    # CLI-provided log file takes precedence and is set up immediately
    if hasattr(args, 'log_file') and args.log_file:
        _setup_logging(args.log_file)
    
    # Enable debug if requested
    if hasattr(args, 'debug') and args.debug:
        enable_debug(True)
        import imaplib
        imaplib.Debug = 4
        dprint("Debug mode enabled; imaplib.Debug=4", tag="INIT")
    
    # Validate arguments
    if not validate_arguments(args):
        sys.exit(1)
    
    # Prepare configuration
    if not args.config and not args.server:
        # Interactive mode
        print(Colors.info("No configuration provided. Starting interactive setup..."))
        config = interactive_setup()
        if not config:
            print(Colors.warning("Setup cancelled"))
            sys.exit(0)
    else:
        # Load from file/args
        config = prepare_config(args)
        if not config:
            print(Colors.error("Configuration failed"))
            sys.exit(1)
        # Emit configuration details in debug mode
        dump_config(config)
        # If logging was not set up via CLI, honor config value
        if not log_setup and config.get('log_file'):
            _setup_logging(config['log_file'])
    
    # Get save path if not specified
    if not config.get('save_path'):
        config['save_path'] = get_save_path_interactive()
        if not config['save_path']:
            print(Colors.warning("No save path selected"))
            sys.exit(0)
    
    # Initialize extractor
    extractor = EmailAttachmentExtractor(
        server=config['server'],
        port=config['port'],
        username=config['username'],
        password=config['password'],
        use_ssl=config.get('use_ssl', True)
    )
    
    # Connect
    print("\n" + "="*60)
    print(Colors.info("STARTING EMAIL ATTACHMENT EXTRACTION"))
    print("="*60)
    
    if not extractor.connect():
        sys.exit(1)
    
    try:
        # Process emails
        if config.get('recursive'):
            dprint("Recursive processing enabled for INBOX subfolders", tag="RUN")
            stats = extractor.process_all_inbox_folders(
                save_path=config['save_path'],
                search_criteria=config.get('search_criteria', 'ALL'),
                organize_by_sender=config.get('organize_by_sender', False),
                organize_by_date=config.get('organize_by_date', True),
                limit_per_folder=config.get('limit_per_folder'),
                total_limit=config.get('total_limit') or config.get('limit'),
                save_metadata=config.get('save_metadata', True),
                allowed_extensions=config.get('allowed_extensions'),
                excluded_extensions=config.get('excluded_extensions')
            )
        else:
            # Process single mailbox
            if not extractor.select_mailbox(config.get('mailbox', 'INBOX')):
                print(Colors.error(f"Could not select mailbox '{config.get('mailbox')}'"))
                sys.exit(1)
            
            dprint(
                f"Processing mailbox='{config.get('mailbox', 'INBOX')}', search='{config.get('search_criteria', 'ALL')}', limit={config.get('limit')}",
                tag="RUN",
            )
            stats = extractor.process_emails(
                save_path=config['save_path'],
                search_criteria=config.get('search_criteria', 'ALL'),
                organize_by_sender=config.get('organize_by_sender', False),
                organize_by_date=config.get('organize_by_date', True),
                limit=config.get('limit'),
                save_metadata=config.get('save_metadata', True),
                allowed_extensions=config.get('allowed_extensions'),
                excluded_extensions=config.get('excluded_extensions')
            )
        
        # Print statistics
        extractor.print_statistics()
        print(Colors.success(f"\nAttachments saved to: {config['save_path']}"))
        
    except KeyboardInterrupt:
        print(Colors.warning("\n\nProcessing interrupted by user"))
    except Exception as e:
        print(Colors.error(f"\nUnexpected error: {e}"))
        import traceback
        if hasattr(args, 'debug') and args.debug:
            traceback.print_exc()
    finally:
        extractor.disconnect()

if __name__ == "__main__":
    main()
