"""Developer errors must fail for direct calls and every registered entry point."""

import inspect

import pytest
from pydantic import BaseModel

from au_tax import registry
from au_tax.figures import Figures


class ProbeInput(BaseModel):
    pass


@pytest.fixture
def register():
    name = "zz_contract_probe"
    registry.load_all()
    try:
        yield lambda fn: registry.calculator(name, ProbeInput)(fn)
    finally:
        registry.REGISTRY.pop(name, None)


@pytest.mark.parametrize("result,field", [
    (None, "dict"),
    ([], "dict"),
    ({"warnings": []}, "assumptions"),
    ({"assumptions": []}, "warnings"),
    ({"assumptions": None, "warnings": []}, "assumptions"),
    ({"assumptions": [], "warnings": "careful"}, "warnings"),
    ({"assumptions": (), "warnings": []}, "assumptions"),
    ({"assumptions": [], "warnings": [1]}, "warnings"),
    ({"assumptions": [False], "warnings": []}, "assumptions"),
])
@pytest.mark.parametrize("entry", ["direct", "registry"])
def test_malformed_result_is_a_developer_error(register, result, field, entry):
    def broken(figures, inp):
        return result

    wrapped = register(broken)
    with pytest.raises(registry.CalculatorContractError, match=f"zz_contract_probe: .*{field}"):
        if entry == "direct":
            wrapped(Figures("2026-27"), inp=ProbeInput())
        else:
            registry.run("zz_contract_probe", "2026-27", {})


def test_valid_result_and_callable_metadata_survive(register):
    result = {"amount": 10, "assumptions": ["Confirmed facts"], "warnings": []}

    def valid(figures, inp):
        """Probe description."""
        return result

    wrapped = register(valid)
    assert wrapped.__name__ == valid.__name__
    assert inspect.signature(wrapped) == inspect.signature(valid)
    assert registry.REGISTRY["zz_contract_probe"].description == valid.__doc__
    assert wrapped(Figures("2026-27"), ProbeInput()) is result
    code, out = registry.run("zz_contract_probe", "2026-27", {})
    assert code == 0
    assert out["assumptions"] == result["assumptions"]
    assert out["warnings"] == []


def test_dynamic_unknown_refusal_is_rejected(register):
    def broken(figures, inp):
        code = "AU-NOT-999"
        raise registry.Refusal(code=code, detail="unregistered")

    register(broken)
    with pytest.raises(ValueError, match="unknown refusal code AU-NOT-999"):
        registry.run("zz_contract_probe", "2026-27", {})


def test_catalogued_refusal_keeps_fixed_message(register):
    def refused(figures, inp):
        raise registry.Refusal(code="AU-GEN-002", detail="facts unresolved")

    register(refused)
    code, out = registry.run("zz_contract_probe", "2026-27", {})
    assert code == 3
    assert out["refusal"] == {
        "code": "AU-GEN-002", "detail": "facts unresolved",
        "message": registry.refusal_catalogue()["AU-GEN-002"]["message"],
        "route": registry.refusal_catalogue()["AU-GEN-002"]["route"],
    }
