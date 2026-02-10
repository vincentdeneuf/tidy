"""LibCST transformers for removing print statements and comments."""

import libcst as cst
from libcst import matchers as m


class PrintRemover(cst.CSTTransformer):
    """Transformer to remove standalone print() statements."""
    
    def __init__(self):
        self.removed_count = 0
    
    def leave_Expr(self, original_node: cst.Expr, updated_node: cst.Expr) -> cst.RemovalSentinel | cst.Expr:
        # Check if this is a print() call
        if (m.matches(updated_node.value, m.Call(func=m.Name("print"))) and
            not m.matches(updated_node.value, m.Call(func=m.Attribute()))):
            self.removed_count += 1
            return cst.RemovalSentinel.REMOVE
        return updated_node


class InlineCommentRemover(cst.CSTTransformer):
    """Transformer to remove inline (trailing) comments only."""
    
    def __init__(self, remove_all: bool = False):
        self.removed_count = 0
        self.remove_all = remove_all  # If True, removes all inline comments including noqa, type:, pragma
    
    def leave_TrailingWhitespace(self, original_node: cst.TrailingWhitespace, updated_node: cst.TrailingWhitespace) -> cst.TrailingWhitespace:
        # Check if there's an inline comment
        if updated_node.comment:
            comment_text = updated_node.comment.value
            
            # Preserve comments containing: noqa, type:, pragma unless remove_all is True
            if not self.remove_all and any(keyword in comment_text for keyword in ["noqa", "type:", "pragma"]):
                return updated_node
            
            self.removed_count += 1
            # Remove the comment but keep the whitespace
            return updated_node.with_changes(comment=None)
        
        return updated_node


class LeadingCommentRemover(cst.CSTTransformer):
    """Transformer to remove standalone/full-line comments."""
    
    def __init__(self):
        self.removed_count = 0
    
    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        # Remove leading comments from the module
        if updated_node.leading_lines:
            new_lines = []
            for line in updated_node.leading_lines:
                if not isinstance(line, cst.EmptyLine) or not line.comment:
                    new_lines.append(line)
                else:
                    self.removed_count += 1
            updated_node = updated_node.with_changes(leading_lines=new_lines)
        return updated_node
    
    def leave_SimpleStatementLine(self, original_node: cst.SimpleStatementLine, updated_node: cst.SimpleStatementLine) -> cst.RemovalSentinel | cst.SimpleStatementLine:
        # Remove standalone comment statements
        if (len(updated_node.body) == 1 and 
            isinstance(updated_node.body[0], cst.Expr) and
            isinstance(updated_node.body[0].value, cst.SimpleString)):
            # This is a string literal, not a comment
            return updated_node
        
        # Check if this is a comment line (starts with #)
        if (original_node.leading_lines and 
            any(isinstance(line, cst.EmptyLine) and line.comment for line in original_node.leading_lines)):
            # This is a comment line, remove it
            self.removed_count += 1
            return cst.RemovalSentinel.REMOVE
        
        return updated_node


class HeaderCommentRemover(cst.CSTTransformer):
    """Transformer to remove shebang and coding comments."""
    
    def __init__(self):
        self.removed_count = 0
    
    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        # Remove shebang and encoding comments from the beginning of the file
        if updated_node.leading_lines:
            new_lines = []
            for line in updated_node.leading_lines:
                if isinstance(line, cst.EmptyLine) and line.comment:
                    comment_text = line.comment.value.strip()
                    # Check if it's a shebang or encoding comment
                    if (comment_text.startswith('#!') or 
                        'coding' in comment_text.lower() or
                        comment_text.startswith('# -*- coding:') or
                        comment_text.startswith('# vim:')):
                        self.removed_count += 1
                        continue  # Skip this line
                new_lines.append(line)
            updated_node = updated_node.with_changes(leading_lines=new_lines)
        return updated_node


class DocstringRemover(cst.CSTTransformer):
    """Transformer to remove docstrings."""
    
    def __init__(self):
        self.removed_count = 0
    
    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        # Remove module-level docstring
        if (updated_node.body and 
            isinstance(updated_node.body[0], cst.SimpleStatementLine) and
            len(updated_node.body[0].body) == 1 and
            isinstance(updated_node.body[0].body[0], cst.Expr) and
            isinstance(updated_node.body[0].body[0].value, cst.SimpleString)):
            self.removed_count += 1
            new_body = list(updated_node.body[1:])  # Remove first statement (docstring)
            return updated_node.with_changes(body=new_body)
        return updated_node
    
    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        # Remove class docstring
        if (updated_node.body.body and
            isinstance(updated_node.body.body[0], cst.SimpleStatementLine) and
            len(updated_node.body.body[0].body) == 1 and
            isinstance(updated_node.body.body[0].body[0], cst.Expr) and
            isinstance(updated_node.body.body[0].body[0].value, cst.SimpleString)):
            self.removed_count += 1
            new_body = updated_node.body.with_changes(body=list(updated_node.body.body[1:]))
            return updated_node.with_changes(body=new_body)
        return updated_node
    
    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        # Remove function docstring
        if (updated_node.body.body and
            isinstance(updated_node.body.body[0], cst.SimpleStatementLine) and
            len(updated_node.body.body[0].body) == 1 and
            isinstance(updated_node.body.body[0].body[0], cst.Expr) and
            isinstance(updated_node.body.body[0].body[0].value, cst.SimpleString)):
            self.removed_count += 1
            new_body = updated_node.body.with_changes(body=list(updated_node.body.body[1:]))
            return updated_node.with_changes(body=new_body)
        return updated_node


class AssertRemover(cst.CSTTransformer):
    """Transformer to remove assert statements."""
    
    def __init__(self):
        self.removed_count = 0
    
    def leave_SimpleStatementLine(self, original_node: cst.SimpleStatementLine, updated_node: cst.SimpleStatementLine) -> cst.RemovalSentinel | cst.SimpleStatementLine:
        # Check if this is an assert statement
        if (len(updated_node.body) == 1 and
            isinstance(updated_node.body[0], cst.Assert)):
            self.removed_count += 1
            return cst.RemovalSentinel.REMOVE
        return updated_node


class LogRemover(cst.CSTTransformer):
    """Transformer to remove logging statements."""
    
    def __init__(self, log_levels: set[str] = None):
        self.removed_count = 0
        # Default log levels to remove
        self.log_levels = log_levels or {"trace", "debug", "info", "warning", "success", "error", "exception", "critical"}
    
    def leave_Expr(self, original_node: cst.Expr, updated_node: cst.Expr) -> cst.RemovalSentinel | cst.Expr:
        # Check if this is a logging call
        if (m.matches(updated_node.value, m.Call(func=m.Attribute())) and
            isinstance(updated_node.value.func, cst.Attribute)):
            
            attr = updated_node.value.func
            # Check if the attribute name is one of the log levels
            if (isinstance(attr.attr, cst.Name) and 
                attr.attr.value in self.log_levels):
                
                # Check if the base name is log, logger, or logging
                if isinstance(attr.value, cst.Name):
                    base_name = attr.value.value
                    if base_name in {"log", "logger", "logging"}:
                        self.removed_count += 1
                        return cst.RemovalSentinel.REMOVE
        
        return updated_node
