"""CLI figure input validation, using the primary rules in CONVENTIONS.md section 5.

Invalid input must return exit code 2 in a JSON envelope, and unknown fields must
be rejected rather than ignored. A figure key is a string (the same input type
as the MCP get_figure tool); null, booleans, numbers and containers are invalid.
These are interface expectations, with no calculated tax amounts as an oracle.
"""

import json

import pytest

from au_tax.cli import main


@pytest.mark.parametrize("key", [
    pytest.param(None, id="null"),
    pytest.param(True, id="boolean"),
    pytest.param(123, id="integer"),
    pytest.param(1.25, id="float"),
    pytest.param([], id="array"),
    pytest.param({}, id="object"),
])
def test_figure_rejects_non_string_key_with_invalid_input_envelope(key, capsys):
    code = main(["figure", "--year", "2026-27", "--json", json.dumps({"key": key})])

    out = json.loads(capsys.readouterr().out)
    assert code == 2
    assert out["exit_code"] == 2
    assert "invalid input" in out["error"]
    assert "key" in out["error"]
    assert "value" not in out


def test_figure_rejects_unknown_field_with_invalid_input_envelope(capsys):
    # Section 5 requires extra="forbid": a valid key must not hide a misspelt field.
    code = main(["figure", "--year", "2026-27", "--json",
                 json.dumps({"key": "gst.rate", "allow_darft": True})])

    out = json.loads(capsys.readouterr().out)
    assert code == 2
    assert out["exit_code"] == 2
    assert "invalid input" in out["error"]
    assert "allow_darft" in out["error"]
    assert "value" not in out
