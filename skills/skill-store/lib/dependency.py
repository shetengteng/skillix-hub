"""Dependency resolution with cycle detection."""

from __future__ import annotations

from lib.config import load_index, load_installed


def resolve_dependencies(skill_name: str, registry_alias: str | None = None) -> tuple[list[dict], list[str]]:
    """
    Resolve all dependencies for a skill.
    Returns (install_order, warnings).
    install_order: list of skill index entries in dependency-first order.
    warnings: list of warning messages for missing deps.
    """
    index = load_index()
    installed = load_installed()

    installed_names = {inst["name"] for inst in installed.get("installations", [])}

    index_by_name: dict[str, list[dict]] = {}
    for skill in index.get("skills", []):
        name = skill["name"]
        if name not in index_by_name:
            index_by_name[name] = []
        index_by_name[name].append(skill)

    install_order = []
    visited = set()
    in_stack = set()
    warnings = []

    def _resolve(name: str, preferred_registry: str | None = None):
        if name in installed_names:
            return
        if name in visited:
            return
        if name in in_stack:
            warnings.append(f"Circular dependency detected: {name}")
            return

        in_stack.add(name)

        candidates = index_by_name.get(name, [])
        if not candidates:
            warnings.append(f"Dependency '{name}' not found in index.")
            in_stack.discard(name)
            return

        if len(candidates) == 1:
            skill = candidates[0]
        elif preferred_registry:
            skill = next(
                (s for s in candidates if s["registry_alias"] == preferred_registry),
                None
            )
            if not skill:
                skill = candidates[0]
                warnings.append(
                    f"Dependency '{name}' not found in registry '{preferred_registry}', "
                    f"using '{skill['registry_alias']}' instead."
                )
        else:
            skill = candidates[0]
            if len(candidates) > 1:
                registries = [c["registry_alias"] for c in candidates]
                warnings.append(
                    f"Dependency '{name}' found in multiple registries: {registries}. "
                    f"Using '{skill['registry_alias']}'."
                )

        for dep in skill.get("dependencies", []):
            _resolve(dep, skill["registry_alias"])

        in_stack.discard(name)
        visited.add(name)
        install_order.append(skill)

    _resolve(skill_name, registry_alias)

    return install_order, warnings
