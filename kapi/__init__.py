"""Kapı: a falsifiability gate for pre-registered studies (spec v0.5)."""

from .study import Budget, Control, Criterion, Premise, Study, StudyError, Targets, World
from .certificate import KAPI_VERSION as __version__
from .certificate import SPEC_VERSION, run_gate

__all__ = [
    "Study", "Criterion", "World", "Premise", "Control", "Budget", "Targets", "StudyError",
    "run_gate", "__version__", "SPEC_VERSION",
]
