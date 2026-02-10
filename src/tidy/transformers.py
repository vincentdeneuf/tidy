"""LibCST transformers for removing print statements and comments."""

import libcst as cst
from libcst import matchers as m


def remove_statement_preserve_comments(
    node: cst.SimpleStatementLine,
) -> cst.FlattenSentinel:
    """Remove a statement but move its leading comments forward."""
    new_nodes: list[cst.CSTNode] = []

    for line in node.leading_lines:
        new_nodes.append(line)

    return cst.FlattenSentinel(new_nodes)


class PrintRemover(cst.CSTTransformer):
    """Transformer to remove standalone print() statements."""

    def __init__(self):
        self.removed_count = 0

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ):
        if (
            len(updated_node.body) == 1
            and isinstance(updated_node.body[0], cst.Expr)
            and m.matches(
                updated_node.body[0].value,
                m.Call(func=m.Name("print")),
            )
        ):
            self.removed_count += 1
            return remove_statement_preserve_comments(original_node)

        return updated_node


class InlineCommentRemover(cst.CSTTransformer):
    """Transformer to remove inline (trailing) comments only."""

    def __init__(self, remove_all: bool = False):
        self.removed_count = 0
        self.remove_all = remove_all

    def leave_TrailingWhitespace(
        self,
        original_node: cst.TrailingWhitespace,
        updated_node: cst.TrailingWhitespace,
    ) -> cst.TrailingWhitespace:
        if updated_node.comment:
            comment_text = updated_node.comment.value

            if not self.remove_all and any(
                keyword in comment_text for keyword in ["noqa", "type:", "pragma"]
            ):
                return updated_node

            self.removed_count += 1
            return updated_node.with_changes(comment=None)

        return updated_node


class LeadingCommentRemover(cst.CSTTransformer):
    """Transformer to remove standalone/full-line comments."""

    def __init__(self):
        self.removed_count = 0

    def leave_Module(
        self,
        original_node: cst.Module,
        updated_node: cst.Module,
    ) -> cst.Module:
        if not updated_node.leading_lines:
            return updated_node

        new_lines: list[cst.EmptyLine] = []

        for line in updated_node.leading_lines:
            if isinstance(line, cst.EmptyLine) and line.comment:
                self.removed_count += 1
                continue
            new_lines.append(line)

        return updated_node.with_changes(leading_lines=new_lines)

    def leave_EmptyLine(
        self,
        original_node: cst.EmptyLine,
        updated_node: cst.EmptyLine,
    ) -> cst.EmptyLine:
        if updated_node.comment:
            self.removed_count += 1
            return updated_node.with_changes(comment=None)

        return updated_node


class HeaderCommentRemover(cst.CSTTransformer):
    """Transformer to remove shebang and coding comments."""

    def __init__(self):
        self.removed_count = 0

    def leave_Module(
        self,
        original_node: cst.Module,
        updated_node: cst.Module,
    ) -> cst.Module:
        if not updated_node.leading_lines:
            return updated_node

        new_lines: list[cst.EmptyLine] = []

        for line in updated_node.leading_lines:
            if isinstance(line, cst.EmptyLine) and line.comment:
                comment_text = line.comment.value.strip().lower()

                if (
                    comment_text.startswith("#!")
                    or "coding" in comment_text
                    or comment_text.startswith("# vim:")
                ):
                    self.removed_count += 1
                    continue

            new_lines.append(line)

        return updated_node.with_changes(leading_lines=new_lines)


class DocstringRemover(cst.CSTTransformer):
    """Transformer to remove docstrings."""

    def __init__(self):
        self.removed_count = 0

    def _strip_docstring(
        self,
        body: list[cst.BaseStatement],
    ) -> list[cst.BaseStatement]:
        if (
            body
            and isinstance(body[0], cst.SimpleStatementLine)
            and len(body[0].body) == 1
            and isinstance(body[0].body[0], cst.Expr)
            and isinstance(body[0].body[0].value, cst.SimpleString)
        ):
            self.removed_count += 1
            return body[1:]

        return body

    def leave_Module(
        self,
        original_node: cst.Module,
        updated_node: cst.Module,
    ) -> cst.Module:
        return updated_node.with_changes(
            body=self._strip_docstring(list(updated_node.body)),
        )

    def leave_ClassDef(
        self,
        original_node: cst.ClassDef,
        updated_node: cst.ClassDef,
    ) -> cst.ClassDef:
        new_body = updated_node.body.with_changes(
            body=self._strip_docstring(list(updated_node.body.body)),
        )
        return updated_node.with_changes(body=new_body)

    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ) -> cst.FunctionDef:
        new_body = updated_node.body.with_changes(
            body=self._strip_docstring(list(updated_node.body.body)),
        )
        return updated_node.with_changes(body=new_body)


class AssertRemover(cst.CSTTransformer):
    """Transformer to remove assert statements."""

    def __init__(self):
        self.removed_count = 0

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ):
        if len(updated_node.body) == 1 and isinstance(updated_node.body[0], cst.Assert):
            self.removed_count += 1
            return remove_statement_preserve_comments(original_node)

        return updated_node


class LogRemover(cst.CSTTransformer):
    """Transformer to remove logging statements."""

    def __init__(self, log_levels: set[str] | None = None):
        self.removed_count = 0
        self.log_levels = log_levels or {
            "trace",
            "debug",
            "info",
            "warning",
            "success",
            "error",
            "exception",
            "critical",
        }

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ):
        if (
            len(updated_node.body) == 1
            and isinstance(updated_node.body[0], cst.Expr)
            and isinstance(updated_node.body[0].value, cst.Call)
            and isinstance(updated_node.body[0].value.func, cst.Attribute)
        ):
            attr = updated_node.body[0].value.func

            if (
                isinstance(attr.attr, cst.Name)
                and attr.attr.value in self.log_levels
                and isinstance(attr.value, cst.Name)
                and attr.value.value in {"log", "logger", "logging"}
            ):
                self.removed_count += 1
                return remove_statement_preserve_comments(original_node)

        return updated_node
