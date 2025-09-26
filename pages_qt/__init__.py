"""pages_qt package

Avoid importing submodules at package import time to prevent hard failures
if any single page module is missing or has import errors. The router loads
each page module explicitly as needed.
"""

__all__ = [
    # modules are imported lazily by router_qt.RouterQt
]
