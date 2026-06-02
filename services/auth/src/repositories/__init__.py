"""
Repository layer for Auth service.

Repositories own the SQL; services own the business rules.  Every
method takes an :class:`AsyncSession` so it can participate in the
caller's transaction.
"""
from src.repositories.user import UserRepository

__all__ = ["UserRepository"]
