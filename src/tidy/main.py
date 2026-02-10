"""Main entry point for the tidy CLI."""

import argparse
import os
import sys
from pathlib import Path

import libcst as cst

from tidy.transformers import (
    AssertRemover,
    DocstringRemover,
    HeaderCommentRemover,
    InlineCommentRemover,
    LeadingCommentRemover,
    LogRemover,
    PrintRemover,
)


def find_python_files(start_dir: str) -> list[str]:
    """Recursively find all .py files, excluding specified directories."""
    skip_dirs = {".git", ".venv", "venv", "__pycache__"}
    python_files = []
    
    for root, dirs, files in os.walk(start_dir):
        # Remove skip directories from in-place traversal
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    return python_files


def process_file(file_path: str, remove_prints: bool = False, remove_comments: bool = False, 
                 remove_docstrings: bool = False, remove_asserts: bool = False, remove_logs: bool = False,
                 comment_options: dict = None, log_levels: set[str] = None) -> tuple[int, int, int, int, int]:
    """Process a single file and return counts of removed items."""
    prints_removed = 0
    comments_removed = 0
    docstrings_removed = 0
    asserts_removed = 0
    logs_removed = 0
    
    if comment_options is None:
        comment_options = {}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        
        module = cst.parse_module(source_code)
        
        if remove_prints:
            print_remover = PrintRemover()
            module = module.visit(print_remover)
            prints_removed = print_remover.removed_count
        
        if remove_comments:
            # Handle different comment removal options
            if comment_options.get("all", False):
                # Remove all types of comments
                inline_remover = InlineCommentRemover(remove_all=True)
                leading_remover = LeadingCommentRemover()
                header_remover = HeaderCommentRemover()
                
                module = module.visit(inline_remover)
                comments_removed += inline_remover.removed_count
                
                module = module.visit(leading_remover)
                comments_removed += leading_remover.removed_count
                
                module = module.visit(header_remover)
                comments_removed += header_remover.removed_count
            else:
                # Handle individual comment types
                if comment_options.get("inline", False):
                    inline_remover = InlineCommentRemover(remove_all=True)
                    module = module.visit(inline_remover)
                    comments_removed += inline_remover.removed_count
                
                if comment_options.get("leading", False):
                    leading_remover = LeadingCommentRemover()
                    module = module.visit(leading_remover)
                    comments_removed += leading_remover.removed_count
                
                if comment_options.get("header", False):
                    header_remover = HeaderCommentRemover()
                    module = module.visit(header_remover)
                    comments_removed += header_remover.removed_count
                
                if comment_options.get("default", False):
                    inline_remover = InlineCommentRemover(remove_all=False)
                    module = module.visit(inline_remover)
                    comments_removed += inline_remover.removed_count
        
        if remove_docstrings:
            docstring_remover = DocstringRemover()
            module = module.visit(docstring_remover)
            docstrings_removed = docstring_remover.removed_count
        
        if remove_asserts:
            assert_remover = AssertRemover()
            module = module.visit(assert_remover)
            asserts_removed = assert_remover.removed_count
        
        if remove_logs:
            log_remover = LogRemover(log_levels)
            module = module.visit(log_remover)
            logs_removed = log_remover.removed_count
        
        # Write back to file if any changes were made
        if prints_removed > 0 or comments_removed > 0 or docstrings_removed > 0 or asserts_removed > 0 or logs_removed > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(module.code)
    
    except Exception:
        # Skip files that can't be parsed or written
        pass
    
    return prints_removed, comments_removed, docstrings_removed, asserts_removed, logs_removed


def main() -> int:
    """Main entry point for the tidy CLI."""
    parser = argparse.ArgumentParser(description="Remove print statements, comments, docstrings, asserts, and logs from Python files.")
    parser.add_argument("command", choices=["comments", "prints", "docstrings", "asserts", "logs"], help="What to remove")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress per-file output (verbose is default)")
    
    # Comment-specific options
    parser.add_argument("--inline", action="store_true", help="Remove all inline comments, including noqa, type, pragma")
    parser.add_argument("--leading", action="store_true", help="Remove standalone/full-line comments")
    parser.add_argument("--header", action="store_true", help="Remove shebang & coding comments")
    parser.add_argument("--default", action="store_true", help="Remove inline comments only (preserve noqa, type:, pragma)")
    
    # Log-specific options
    parser.add_argument("--trace", action="store_true", help="Remove trace level logs")
    parser.add_argument("--debug", action="store_true", help="Remove debug level logs")
    parser.add_argument("--info", action="store_true", help="Remove info level logs")
    parser.add_argument("--warning", action="store_true", help="Remove warning level logs")
    parser.add_argument("--success", action="store_true", help="Remove success level logs")
    parser.add_argument("--error", action="store_true", help="Remove error level logs")
    parser.add_argument("--exception", action="store_true", help="Remove exception level logs")
    parser.add_argument("--critical", action="store_true", help="Remove critical level logs")
    parser.add_argument("--all", action="store_true", help="Remove all types (for comments) or all log levels (for logs)")
    
    args = parser.parse_args()
    
    # Validate comment options
    if args.command == "comments":
        comment_flags = {
            "inline": args.inline,
            "leading": args.leading, 
            "header": args.header,
            "default": args.default,
            "all": args.all
        }
        
        # Require at least one flag
        if not any(comment_flags.values()):
            return 1
    
    # Validate log options
    if args.command == "logs":
        log_flags = {
            "trace": args.trace,
            "debug": args.debug,
            "info": args.info,
            "warning": args.warning,
            "success": args.success,
            "error": args.error,
            "exception": args.exception,
            "critical": args.critical,
            "all": args.all
        }
        
        # Require at least one flag
        if not any(log_flags.values()):
            return 1
    
    # Determine what to remove
    remove_prints = args.command == "prints"
    remove_comments = args.command == "comments"
    remove_docstrings = args.command == "docstrings"
    remove_asserts = args.command == "asserts"
    remove_logs = args.command == "logs"
    
    # Build comment options
    comment_options = {}
    if remove_comments:
        # If --all is specified, ignore other flags
        if args.all:
            comment_options["all"] = True
        else:
            if args.inline:
                comment_options["inline"] = True
            if args.leading:
                comment_options["leading"] = True
            if args.header:
                comment_options["header"] = True
            if args.default:
                comment_options["default"] = True
    
    # Build log levels
    log_levels = None
    if remove_logs:
        log_flags = {
            "trace": args.trace,
            "debug": args.debug,
            "info": args.info,
            "warning": args.warning,
            "success": args.success,
            "error": args.error,
            "exception": args.exception,
            "critical": args.critical,
            "all": args.all
        }
        
        # If --all is specified, ignore other flags and use all log levels
        if args.all:
            log_levels = {"trace", "debug", "info", "warning", "success", "error", "exception", "critical"}
        # If any specific log level flags are specified, only remove those levels
        elif any(log_flags.values()):
            log_levels = {level for level, enabled in log_flags.items() if enabled and level != "all"}
        # No need for default case since validation requires at least one flag
    
    # Find all Python files
    python_files = find_python_files(".")
    
    total_prints_removed = 0
    total_comments_removed = 0
    total_docstrings_removed = 0
    total_asserts_removed = 0
    total_logs_removed = 0
    files_with_prints = 0
    files_with_comments = 0
    files_with_docstrings = 0
    files_with_asserts = 0
    files_with_logs = 0
    
    # Verbose is default, quiet mode suppresses per-file output
    verbose_mode = not args.quiet
    
    # Process each file
    for file_path in python_files:
        prints_removed, comments_removed, docstrings_removed, asserts_removed, logs_removed = process_file(
            file_path, remove_prints, remove_comments, remove_docstrings, remove_asserts, remove_logs, comment_options, log_levels
        )
        
        if prints_removed > 0:
            files_with_prints += 1
            total_prints_removed += prints_removed
            if verbose_mode:
                relative_path = os.path.relpath(file_path, ".")
                print(f"{prints_removed} prints removed\t\t\033[90m{relative_path}\033[0m")
        
        if comments_removed > 0:
            files_with_comments += 1
            total_comments_removed += comments_removed
            if verbose_mode:
                relative_path = os.path.relpath(file_path, ".")
                print(f"{comments_removed} comments removed\t\t\033[90m{relative_path}\033[0m")
        
        if docstrings_removed > 0:
            files_with_docstrings += 1
            total_docstrings_removed += docstrings_removed
            if verbose_mode:
                relative_path = os.path.relpath(file_path, ".")
                print(f"{docstrings_removed} docstrings removed\t\t\033[90m{relative_path}\033[0m")
        
        if asserts_removed > 0:
            files_with_asserts += 1
            total_asserts_removed += asserts_removed
            if verbose_mode:
                relative_path = os.path.relpath(file_path, ".")
                print(f"{asserts_removed} asserts removed\t\t\033[90m{relative_path}\033[0m")
        
        if logs_removed > 0:
            files_with_logs += 1
            total_logs_removed += logs_removed
            if verbose_mode:
                relative_path = os.path.relpath(file_path, ".")
                print(f"{logs_removed} logs removed\t\t\033[90m{relative_path}\033[0m")
    
    # Print summary
    if remove_prints:
        pass
    if remove_comments:
        pass
    if remove_docstrings:
        pass
    if remove_asserts:
        pass
    if remove_logs:
        pass
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
