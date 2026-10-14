"""Compatibility exports for the former ``class_`` schema module.

The canonical class schemas live in :mod:`app.schemas.classroom`; this module
remains importable for callers that have not migrated yet.
"""

from app.schemas.classroom import ClassResponse, ClassStudentResponse

__all__ = ["ClassResponse", "ClassStudentResponse"]
