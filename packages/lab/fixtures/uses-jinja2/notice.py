import jinja2.sandbox

LINE = "{{ bike }}: {{ work | title }}{% if parts %}, with {{ parts | join(', ') }}{% endif %}"


def notice(repairs: list[dict[str, object]]) -> str:
    """The repairs on a shop's notice, one a line, rendered in a sandbox so the template can't
    reach Python's internals."""
    environment = jinja2.sandbox.ImmutableSandboxedEnvironment(autoescape=True)
    line = environment.from_string(LINE)
    return "\n".join(line.render(**repair) for repair in repairs)
