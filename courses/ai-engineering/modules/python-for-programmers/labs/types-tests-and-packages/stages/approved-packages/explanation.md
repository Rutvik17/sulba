```python
def unapproved(lock: str, approved: dict[str, str]) -> list[str]:
    listed = {canonicalize_name(name): versions for name, versions in approved.items()}
    problems = []
    for package in tomllib.loads(lock)["package"]:
        if "editable" in package["source"]:
            continue
        name, version = package["name"], package["version"]
        versions = listed.get(canonicalize_name(name))
        if versions is None:
            problems.append(f"{name} {version} isn't on the approved list")
        elif version not in SpecifierSet(versions):
            problems.append(f"{name} {version} is outside the approved {versions}")
    return problems
```

The list's names go through `canonicalize_name` once, as the list is read, and each locked name as it's looked up. uv writes `PyYAML` as `pyyaml` and `python_dateutil` as `python-dateutil`, but people write the list, and the standards make names that differ only in case and in runs of `-`, `_` and `.` one name.

`version not in SpecifierSet(versions)` compares versions as the version specifiers standard does: part by part, as numbers, with a shorter version padded with zeros. As text, `1.17.0` sorts before `1.9`, and `1.17.0` isn't `1.17`. `~=2.4.0` is `>=2.4.0` with `==2.4.*`: any 2.4 release from 2.4.0 on.

Each `[[package]]` table is checked, the service's own aside. A dict from each name to its version would keep one version of a package the lock file holds at several, and leave the others unchecked.

`tomllib.loads` gives a `dict[str, Any]`, so mypy checks nothing the function reads from the lock file, as `any` would in TypeScript. A file that isn't a lock file fails as it's read, with a `KeyError` for a key it doesn't have.
