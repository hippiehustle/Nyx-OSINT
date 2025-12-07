"""Nyx Windows Executable Package."""

# Import version info
try:
    from nyx import __version__, VERSION_INFO
except ImportError:
    __version__ = "0.1.0"
    VERSION_INFO = (0, 1, 0, "alpha")

__all__ = ["__version__", "VERSION_INFO"]

