"""Forbidden dependencies 1-5 from docs/architecture.md, asserted on the import graph of app/."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAMEWORKS = ("fastapi", "starlette")
CLOCK_CALLS = {("date", "today"), ("datetime", "now"), ("datetime", "utcnow")}


def module_name(path: Path) -> str:
    parts = path.relative_to(ROOT).with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def imported_modules(source: str, module: str, is_package: bool = False) -> set[str]:
    """Absolute names of every module `source` imports; `from x import y` also yields `x.y`."""
    package = (module if is_package else module.rpartition(".")[0]).split(".")
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = package[: len(package) - node.level + 1] if node.level else []
            target = ".".join([*base, node.module] if node.module else base)
            found.add(target)
            found.update(f"{target}.{alias.name}" for alias in node.names)
    return found


def clock_calls(source: str) -> set[str]:
    calls = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name | ast.Attribute):
            owner = node.value.id if isinstance(node.value, ast.Name) else node.value.attr
            if (owner, node.attr) in CLOCK_CALLS:
                calls.add(f"{owner}.{node.attr}")
    return calls


def app_files() -> dict[str, tuple[str, set[str]]]:
    files = {}
    for path in sorted((ROOT / "app").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        name = module_name(path)
        files[name] = (source, imported_modules(source, name, path.name == "__init__.py"))
    return files


def in_package(module: str, package: str) -> bool:
    return module == package or module.startswith(package + ".")


def test_scanner_resolves_relative_and_absolute_imports() -> None:
    source = "import sqlite3\nfrom ..http import routes\nfrom app.people.store import x\n"
    found = imported_modules(source, "app.leave.service")
    assert {"sqlite3", "app.http", "app.http.routes", "app.people.store"} <= found
    assert clock_calls("from datetime import date\nd = date.today()\n") == {"date.today"}


def test_domain_never_imports_http() -> None:  # rule 1
    for name, (_, imports) in app_files().items():
        if in_package(name, "app.leave") or in_package(name, "app.people"):
            assert not any(in_package(i, "app.http") for i in imports), name


def test_only_http_and_main_import_frameworks() -> None:  # rule 2
    for name, (_, imports) in app_files().items():
        if in_package(name, "app.http") or name == "app.main":
            continue
        assert not any(in_package(i, f) for i in imports for f in FRAMEWORKS), name


def test_leave_uses_people_only_through_its_package() -> None:  # rule 3
    people = {n for n in app_files() if in_package(n, "app.people")}
    for name, (_, imports) in app_files().items():
        if in_package(name, "app.leave"):
            internal = {i for i in imports if i in people and i != "app.people"}
            assert not internal, f"{name} imports {internal}"


def test_only_db_imports_sqlite3() -> None:  # rule 4
    for name, (_, imports) in app_files().items():
        if not in_package(name, "app.db"):
            assert "sqlite3" not in imports, name


def test_leave_never_reads_the_system_clock() -> None:  # rule 5
    for name, (source, _) in app_files().items():
        if in_package(name, "app.leave"):
            assert not clock_calls(source), name
