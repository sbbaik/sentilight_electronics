"""The catalogue gate is on the path to the device, so its failure modes matter as much as its happy path."""
import json
import pytest

from common.lighting_schema import LightingValues
from common.policy_catalogue import (
    CatalogueError, DEFAULT_MODE, PolicyCatalogue, configured_mode, get_catalogue,
)


@pytest.fixture(scope="module")
def catalogue():
    return get_catalogue()


def test_catalogue_matches_the_policy_the_paper_reports(catalogue):
    assert len(catalogue) == 240


def test_digest_is_verified_on_load(tmp_path):
    doc = {"policy": "test", "count": 1, "sha256": "0" * 64, "tuples": [[1, 2, 3, 4, 200]]}
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(CatalogueError, match="digest mismatch"):
        PolicyCatalogue.load(p)


def test_declared_count_is_verified_on_load(tmp_path):
    rows = [[1, 2, 3, 4, 200], [5, 6, 7, 8, 300]]
    cat = PolicyCatalogue(rows)
    doc = {"policy": "test", "count": 99, "sha256": cat.sha256, "tuples": rows}
    p = tmp_path / "count.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(CatalogueError, match="declares 99"):
        PolicyCatalogue.load(p)


def test_missing_catalogue_raises_rather_than_passing_everything(tmp_path):
    with pytest.raises(CatalogueError, match="not readable"):
        PolicyCatalogue.load(tmp_path / "absent.json")


def test_in_policy_tuple_is_executed_unchanged(catalogue):
    member = LightingValues(*catalogue._rows[0])
    for mode in ("off", "reject", "snap"):
        r = catalogue.gate(member, mode)
        assert r.in_policy and not r.substituted
        assert r.executed == member


def test_reject_withholds_a_schema_valid_but_unexecutable_tuple(catalogue):
    member = LightingValues(*catalogue._rows[0])
    off_policy = LightingValues(member.H, member.S, (member.B + 7) % 101, member.Dimmer, member.CT)
    assert not catalogue.contains(off_policy)
    r = catalogue.gate(off_policy, "reject")
    assert not r.in_policy and r.executed is None and "not one of the 240" in r.reason


def test_snap_substitutes_a_catalogue_member(catalogue):
    member = LightingValues(*catalogue._rows[0])
    off_policy = LightingValues(member.H, member.S, (member.B + 7) % 101, member.Dimmer, member.CT)
    r = catalogue.gate(off_policy, "snap")
    assert r.substituted and catalogue.contains(r.executed)
    assert r.original == off_policy and r.distance is not None


def test_hue_distance_wraps_around_the_circle(catalogue):
    a, b = catalogue.nearest(LightingValues(359, 54, 14, 8, 358))
    c, d = catalogue.nearest(LightingValues(1, 54, 14, 8, 358))
    assert catalogue.contains(a) and catalogue.contains(c)
    assert b < 0.2 and d < 0.2


def test_unknown_mode_is_rejected(catalogue):
    with pytest.raises(ValueError, match="unknown gate mode"):
        catalogue.gate(LightingValues(*catalogue._rows[0]), "passthrough")


def test_configured_mode_defaults_and_ignores_garbage(monkeypatch):
    monkeypatch.delenv("SENTILIGHT_POLICY_GATE", raising=False)
    assert configured_mode() == DEFAULT_MODE
    monkeypatch.setenv("SENTILIGHT_POLICY_GATE", "SNAP")
    assert configured_mode() == "snap"
    monkeypatch.setenv("SENTILIGHT_POLICY_GATE", "nonsense")
    assert configured_mode() == DEFAULT_MODE


def test_gate_result_serialises_for_the_api_response(catalogue):
    member = LightingValues(*catalogue._rows[0])
    off_policy = LightingValues(member.H, member.S, (member.B + 7) % 101, member.Dimmer, member.CT)
    d = catalogue.gate(off_policy, "reject").to_dict()
    assert d["in_policy"] is False and d["executed"] is None
    assert set(d) == {"in_policy", "mode", "substituted", "distance", "reason", "original", "executed"}
    json.dumps(d)
