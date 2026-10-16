"""The clinic's check of the packages the service installs."""

import tomllib

from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name


def unapproved(lock, approved):
    """A message for each package in the lock file that the approved list doesn't approve,
    in the lock file's order."""
    raise NotImplementedError
