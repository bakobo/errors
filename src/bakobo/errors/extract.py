"""Lift registry entries out of source code without importing it.

Importing a repo to read its registry would mean installing its dependencies, and would let a
module's import side effects decide what the catalog says. So the catalog is read by static
analysis, which is exactly what ``error-codes.md`` says the module-scope-literal rule is for. That
rule is enforced here rather than worked around (``this.i`` @tjs63f): a field this cannot read as a
literal becomes a :class:`Problem`, never a guess and never a silent omission.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field

from .taxonomy import validate_code

FIELDS = ("code", "title", "detail", "args", "hint")
"""The ``ErrorCode`` signature, in declaration order. Positional arguments bind in this order."""


@dataclass(frozen=True)
class Entry:
    """One registry entry as the catalog sees it: the declaration, plus where it was declared."""

    code: str
    title: str
    repo: str
    path: str
    line: int
    symbol: str
    detail: str | None = None
    args: tuple[str, ...] = field(default_factory=tuple)
    hint: str | None = None


@dataclass(frozen=True)
class Problem:
    """A declaration the catalog refuses to read, and why."""

    repo: str
    path: str
    line: int
    symbol: str | None
    reason: str


def _binding_names(tree: ast.Module) -> set[str]:
    """Every local name that refers to ``ErrorCode``, however it was imported."""
    names = {"ErrorCode"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "ErrorCode":
                    names.add(alias.asname or alias.name)
    return names


def _is_construction(node: ast.Call, names: set[str]) -> bool:
    """Whether this call constructs an ``ErrorCode``, bare or qualified through its module."""
    callee = node.func
    if isinstance(callee, ast.Name):
        return callee.id in names
    if isinstance(callee, ast.Attribute):
        return callee.attr == "ErrorCode"
    return False


def _literal(node: ast.expr):
    """The literal value of ``node``, or :data:`NotImplemented` if it is not one."""
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return NotImplemented


def _read_call(node: ast.Call) -> dict | str:
    """Bind a construction's arguments to :data:`FIELDS`, or return why it cannot be read."""
    values: dict = {}
    if len(node.args) > len(FIELDS):
        return f"it is given {len(node.args)} positional arguments and ErrorCode takes 5"
    for name, arg in zip(FIELDS, node.args):
        values[name] = arg
    for keyword in node.keywords:
        if keyword.arg is None:
            return "its arguments are splatted from a mapping rather than written out"
        if keyword.arg not in FIELDS:
            return f"{keyword.arg!r} is not one of ErrorCode's fields, which are {FIELDS}"
        if keyword.arg in values:
            return f"{keyword.arg!r} is given both positionally and by keyword"
        values[keyword.arg] = keyword.value

    for name in ("code", "title"):
        if name not in values:
            return f"it declares no {name}, which every entry carries"

    read = {}
    for name, expr in values.items():
        value = _literal(expr)
        if value is NotImplemented:
            return (
                f"its {name} is assembled rather than declared as a literal, so a catalog cannot "
                f"read it — see error-codes.md, The registry"
            )
        read[name] = value
    return read


UNBOUND = "it is constructed without being bound to a name, so nothing can raise it"
NESTED = (
    "it is constructed below module scope, in a function, class, or loop. A registry declared by a "
    "factory is one a catalog cannot read — see error-codes.md, The registry"
)


def _entry_or_problem(
    node: ast.Call, symbol: str | None, repo: str, path: str, reason: str = UNBOUND
) -> Entry | Problem:
    if symbol is None:
        return Problem(repo, path, node.lineno, None, reason)
    read = _read_call(node)
    if isinstance(read, str):
        return Problem(repo, path, node.lineno, symbol, read)
    try:
        validate_code(read["code"])
    except ValueError as refusal:
        return Problem(repo, path, node.lineno, symbol, str(refusal))
    args = read.get("args") or ()
    return Entry(
        code=read["code"],
        title=read["title"],
        repo=repo,
        path=path,
        line=node.lineno,
        symbol=symbol,
        detail=read.get("detail"),
        args=tuple(args),
        hint=read.get("hint"),
    )


def _symbol(statement: ast.stmt) -> str | None | type[NotImplemented]:
    """The single name a construction is bound to, if it is bound to exactly one."""
    if isinstance(statement, ast.AnnAssign):
        target = statement.target
        return target.id if isinstance(target, ast.Name) else NotImplemented
    if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
        return NotImplemented
    return statement.targets[0].id


def extract_module(source: str, *, repo: str, path: str) -> tuple[list[Entry], list[Problem]]:
    """Read every registry entry declared at module scope in one file of source."""
    try:
        tree = ast.parse(source)
    except SyntaxError as broken:
        return [], [Problem(repo, path, broken.lineno or 1, None, f"it does not parse: {broken.msg}")]

    names = _binding_names(tree)
    entries: list[Entry] = []
    problems: list[Problem] = []

    declared: set[int] = set()
    for statement in tree.body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        value = statement.value
        if not isinstance(value, ast.Call) or not _is_construction(value, names):
            continue
        declared.add(id(value))
        symbol = _symbol(statement)
        if symbol is NotImplemented:
            problems.append(Problem(
                repo, path, value.lineno, None,
                "it is bound to more than one name at once, so the catalog cannot say which one "
                "raises it",
            ))
            continue
        found = _entry_or_problem(value, symbol, repo, path)
        (entries if isinstance(found, Entry) else problems).append(found)

    at_module_level = {
        id(statement.value)
        for statement in tree.body
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_construction(node, names) and id(node) not in declared:
            reason = UNBOUND if id(node) in at_module_level else NESTED
            problems.append(_entry_or_problem(node, None, repo, path, reason))

    return entries, problems
