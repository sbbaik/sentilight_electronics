"""End-to-end checks of the catalogue gate on the path a real request takes.

test_policy_catalogue.py exercises the gate object. This file exercises the service: a request arrives at the
FastAPI endpoint, the registry runs an adapter, the gate decides, and the client's bulb-command step consumes the
response. The property under test is that a withheld tuple never becomes a Tasmota command.
"""
import json
import logging
import sys
from pathlib import Path

import importlib.util
import pytest
import yaml
from fastapi.testclient import TestClient

from common.config_loader import load_config
from common.lighting_schema import LightingValues
from common.model_registry import ModelRegistry
from common.policy_catalogue import get_catalogue

# The client lives in a sibling tree that has its own `common` package, so it is loaded by path rather than by
# putting that tree on sys.path, which would shadow the backend's `common` for the rest of the session.
_FRONTEND = Path(__file__).resolve().parents[2] / "frontend"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


TasmotaController = _load("_fe_tasmota", _FRONTEND / "common/tasmota_controller.py").TasmotaController

CATALOGUE = get_catalogue()
IN_POLICY = LightingValues(*CATALOGUE._rows[0])
# Same fields, one step off the lattice: schema-valid, range-valid, and not an executable command.
OFF_POLICY = LightingValues(IN_POLICY.H, IN_POLICY.S, (IN_POLICY.B + 7) % 101, IN_POLICY.Dimmer, IN_POLICY.CT)


class ScriptedAdapter:
    """Returns whatever the test asks for, including output the parser cannot read."""

    def __init__(self, behaviour):
        self.behaviour = behaviour

    def predict(self, text: str):
        from server.adapters.base import AdapterPrediction
        if self.behaviour == "malformed":
            raise ValueError("Could not parse lighting values from model response")
        lighting = IN_POLICY if self.behaviour == "in_policy" else OFF_POLICY
        return AdapterPrediction(lighting=lighting, raw=f"[COMMAND: {lighting.to_tasmota_command()}]")


@pytest.fixture
def service(tmp_path):
    def build(behaviour):
        model_dir = tmp_path / "models" / "m"
        model_dir.mkdir(parents=True, exist_ok=True)
        cfg = tmp_path / "models.yaml"
        cfg.write_text(yaml.safe_dump({"models": [{
            "id": "m", "name": "M", "enabled": True, "mode": "local_adapter",
            "adapter": "mock", "model_dir": str(model_dir)}]}), encoding="utf-8")
        registry = ModelRegistry(load_config(cfg, allow_example_fallback=False))
        registry.models["m"].adapter = ScriptedAdapter(behaviour)
        registry.models["m"].load_error = None
        from server.main import PredictRequest  # noqa: F401  (ensures the module imports cleanly)
        from fastapi import FastAPI
        app = FastAPI()

        @app.post("/predict/{model_id}")
        def predict(model_id: str, request: dict):
            return registry.predict(model_id, request["text"])

        return TestClient(app)
    return build


def _client_would_send(result: dict):
    """The client's own gate on sending: frontend/app/main.py control_bulbs() skips a result that is not a success
    or carries no lighting values. Reproduced here so the test asserts the real condition rather than a paraphrase."""
    if not result.get("success") or not result.get("lighting"):
        return None
    from dataclasses import asdict
    return asdict(TasmotaController(timeout_seconds=1).send("10.0.0.101", result["lighting"], dry_run=True))


def _post(client):
    r = client.post("/predict/m", json={"text": "테스트"})
    assert r.status_code == 200
    return r.json()


def test_in_policy_tuple_passes_and_reaches_the_command_step(service, monkeypatch):
    monkeypatch.delenv("SENTILIGHT_POLICY_GATE", raising=False)
    body = _post(service("in_policy"))
    assert body["success"] is True
    assert body["policy_gate"]["in_policy"] is True
    assert body["lighting"] == IN_POLICY.to_dict()

    sent = _client_would_send(body)
    assert sent is not None and sent["command"]


def test_off_policy_tuple_is_withheld_and_sends_no_command(service, monkeypatch):
    monkeypatch.delenv("SENTILIGHT_POLICY_GATE", raising=False)
    body = _post(service("off_policy"))
    assert body["success"] is False
    assert body["policy_gate"]["in_policy"] is False
    assert body["lighting"] is None
    assert "not one of the 240" in body["error"]

    assert _client_would_send(body) is None


def test_unparseable_output_sends_no_command(service):
    body = _post(service("malformed"))
    assert body["success"] is False and body["lighting"] is None
    assert _client_would_send(body) is None


def test_digest_mismatch_withholds_every_tuple(service, tmp_path, monkeypatch):
    import common.policy_catalogue as pc
    tampered = tmp_path / "tampered.json"
    rows = [list(r) for r in CATALOGUE._rows]
    rows[0][2] = (rows[0][2] + 3) % 101                     # edit one tuple, leave the recorded digest alone
    tampered.write_text(json.dumps({"policy": "K240", "count": 240,
                                    "sha256": CATALOGUE.sha256, "tuples": rows}), encoding="utf-8")
    monkeypatch.setattr(pc, "CATALOGUE_PATH", tampered)
    monkeypatch.setattr(pc, "_cache", None)

    body = _post(service("in_policy"))
    assert body["success"] is False and body["lighting"] is None
    assert body["policy_gate"]["mode"] == "unavailable"
    assert "digest mismatch" in body["error"]


def test_missing_catalogue_withholds_every_tuple(service, tmp_path, monkeypatch):
    import common.policy_catalogue as pc
    monkeypatch.setattr(pc, "CATALOGUE_PATH", tmp_path / "absent.json")
    monkeypatch.setattr(pc, "_cache", None)
    body = _post(service("in_policy"))
    assert body["success"] is False and body["lighting"] is None
    assert "not readable" in body["error"]


def test_snap_acts_only_when_explicitly_selected(service, monkeypatch):
    monkeypatch.delenv("SENTILIGHT_POLICY_GATE", raising=False)
    assert _post(service("off_policy"))["policy_gate"]["substituted"] is False

    monkeypatch.setenv("SENTILIGHT_POLICY_GATE", "snap")
    body = _post(service("off_policy"))
    assert body["policy_gate"]["substituted"] is True
    assert body["success"] is True
    assert CATALOGUE.contains(LightingValues(**body["lighting"]))
    assert body["policy_gate"]["original"] == OFF_POLICY.to_dict()


def test_every_gate_decision_is_logged(service, caplog, monkeypatch):
    monkeypatch.delenv("SENTILIGHT_POLICY_GATE", raising=False)
    with caplog.at_level(logging.WARNING, logger="sentilight.policy_gate"):
        _post(service("off_policy"))
    messages = [r.getMessage() for r in caplog.records]
    assert any("policy gate withheld" in m for m in messages), caplog.text
    assert any("not one of the 240" in m for m in messages), caplog.text
