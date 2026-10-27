"""Catalogue-membership gate for model output on the path to the device.

Schema validation answers a different question from policy admissibility. `lighting_schema` guarantees that a
response is a JSON object whose five fields are integers inside the actuator's ranges; it does not guarantee that
the resulting tuple is one the control policy can issue. A model that writes field values rather than a class index
can emit a well-formed tuple that the policy never produces, and the manuscript measures how often that happens.

This module closes that gap in the execution path. The catalogue is the frozen enumeration of the executable action
set (backend/config/policy_catalogue_k240.json, produced by tools/build_policy_catalogue.py). A prediction is
checked against it before it becomes a device command, and the outcome is recorded on the response.

Modes
    off     no gating; the tuple is passed through and only reported on.
    reject  an out-of-policy tuple is not executed. The response carries no command and says why.
    snap    an out-of-policy tuple is replaced by the nearest catalogue member, which is then executed.

`snap` is a convenience for interactive use and changes what the device does, so it is never the default: the
default is `reject`, which is the behaviour the manuscript describes.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .lighting_schema import LightingValues

DIMS = ("H", "S", "B", "Dimmer", "CT")
MODES = ("off", "reject", "snap")
DEFAULT_MODE = "reject"
CATALOGUE_PATH = Path(__file__).resolve().parents[1] / "config" / "policy_catalogue_k240.json"

# Hue is circular and the five fields have very different ranges, so a plain Euclidean distance would be dominated
# by CT. Each field is scaled to its own span before the nearest member is chosen.
_SPANS = {"H": 180.0, "S": 100.0, "B": 100.0, "Dimmer": 100.0, "CT": 347.0}


class CatalogueError(RuntimeError):
    """The frozen catalogue is missing, unreadable, or does not match its recorded digest."""


@dataclass(frozen=True)
class GateResult:
    in_policy: bool
    mode: str
    executed: LightingValues | None
    original: LightingValues
    substituted: bool
    distance: float | None
    reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "in_policy": self.in_policy,
            "mode": self.mode,
            "substituted": self.substituted,
            "distance": None if self.distance is None else round(self.distance, 4),
            "reason": self.reason,
            "original": self.original.to_dict(),
            "executed": None if self.executed is None else self.executed.to_dict(),
        }


def _hue_delta(a: int, b: int) -> float:
    d = abs(int(a) - int(b)) % 360
    return float(min(d, 360 - d))


class PolicyCatalogue:
    def __init__(self, tuples: Iterable[Sequence[int]], *, name: str = "K240", digest: str | None = None) -> None:
        self._rows = tuple(tuple(int(v) for v in row) for row in tuples)
        self._set = frozenset(self._rows)
        self.name = name
        self.sha256 = digest or hashlib.sha256(
            json.dumps([list(r) for r in sorted(self._rows)], separators=(",", ":")).encode()
        ).hexdigest()

    def __len__(self) -> int:
        return len(self._set)

    @classmethod
    def load(cls, path: Path | None = None) -> "PolicyCatalogue":
        p = Path(path or CATALOGUE_PATH)
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except OSError as exc:
            raise CatalogueError(f"catalogue not readable at {p}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise CatalogueError(f"catalogue at {p} is not valid JSON: {exc}") from exc
        rows = doc.get("tuples")
        if not rows:
            raise CatalogueError(f"catalogue at {p} contains no tuples")
        cat = cls(rows, name=doc.get("policy", p.stem), digest=None)
        recorded = doc.get("sha256")
        if recorded and recorded != cat.sha256:
            raise CatalogueError(
                f"catalogue digest mismatch at {p}: file records {recorded[:16]}, contents hash to {cat.sha256[:16]}"
            )
        declared = doc.get("count")
        if declared is not None and declared != len(cat):
            raise CatalogueError(f"catalogue at {p} declares {declared} tuples but holds {len(cat)}")
        return cat

    def key(self, values: LightingValues | Mapping[str, Any]) -> tuple[int, ...]:
        d = values.to_dict() if isinstance(values, LightingValues) else values
        return tuple(int(d[k]) for k in DIMS)

    def contains(self, values: LightingValues | Mapping[str, Any]) -> bool:
        return self.key(values) in self._set

    def nearest(self, values: LightingValues) -> tuple[LightingValues, float]:
        k = self.key(values)
        best, best_d = None, float("inf")
        for row in self._rows:
            d = (_hue_delta(k[0], row[0]) / _SPANS["H"]) ** 2
            for i, name in enumerate(DIMS[1:], start=1):
                d += ((k[i] - row[i]) / _SPANS[name]) ** 2
            if d < best_d:
                best, best_d = row, d
        assert best is not None
        return LightingValues(*best), best_d ** 0.5

    def gate(self, values: LightingValues, mode: str = DEFAULT_MODE) -> GateResult:
        if mode not in MODES:
            raise ValueError(f"unknown gate mode {mode!r}; expected one of {MODES}")
        if self.contains(values):
            return GateResult(True, mode, values, values, False, 0.0, None)
        if mode == "off":
            return GateResult(False, mode, values, values, False, None,
                              "out of policy; gate disabled, tuple passed through")
        if mode == "reject":
            return GateResult(False, mode, None, values, False, None,
                              f"tuple is not one of the {len(self)} executable commands in policy {self.name}")
        snapped, dist = self.nearest(values)
        return GateResult(False, mode, snapped, values, True, dist,
                          f"tuple is not executable in policy {self.name}; replaced by the nearest catalogue member")


_cache: PolicyCatalogue | None = None


def get_catalogue(path: Path | None = None) -> PolicyCatalogue:
    global _cache
    if _cache is None or path is not None:
        cat = PolicyCatalogue.load(path)
        if path is None:
            _cache = cat
        return cat
    return _cache


def configured_mode() -> str:
    """Gate mode from SENTILIGHT_POLICY_GATE; anything unrecognised falls back to the default and is not silent."""
    raw = (os.environ.get("SENTILIGHT_POLICY_GATE") or DEFAULT_MODE).strip().lower()
    return raw if raw in MODES else DEFAULT_MODE
