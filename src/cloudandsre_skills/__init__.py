"""Production-shaped Agent Skills for SRE work: catalog, contract checks, evals, MCP server."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cloudandsre-skills")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.0.0.dev0"
