"""Verify the real calculators and prove each invariant checker rejects corruption."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

from au_tax.calculators import individual, settlement
from au_tax.figures import Figures

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('verify_invariants', ROOT / 'scripts/verify_invariants.py')
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)


def test_verifier_command():
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/verify_invariants.py')],
                            cwd=ROOT, text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.startswith('PASS individual invariants:')
    assert 'years=2025-26,2026-27,2027-28' in result.stdout


@pytest.fixture
def valid_settlement():
    inp = settlement.IndividualSettlementInput.model_validate({
        **v.payload(), 'tax_withheld': 30_000.01, 'payg_instalment_credit': 100.02,
        'franking': v.franking('2025-26'),
        'private_health_rebate': v.phi_input('2025-26', 'phi_rebate_1jul_to_31mar_under_65',
                                          0, False, 0, 1000.05, 0),
    })
    out = settlement.individual_tax_settlement(Figures('2025-26'), inp)
    v.check_settlement(out, inp, 'valid fixture')
    return out, inp


@pytest.mark.parametrize('field,rule', [
    ('liability_including_phi_excess', 'liability including PHI excess'),
    ('total_credits', 'total credits'),
    ('net_amount_owing', 'settlement balance'),
    ('refund', 'refund sign'),
    ('amount_owing', 'amount owing sign'),
])
def test_accounting_corruption_is_caught(valid_settlement, field, rule):
    out, inp = valid_settlement
    broken = deepcopy(out)
    broken[field] += 0.01
    with pytest.raises(v.InvariantViolation, match=rule):
        v.check_settlement(broken, inp, f'corrupt {field}')


@pytest.mark.parametrize('credit', ['payg_withheld', 'payg_instalments', 'refundable_franking', 'phi_refundable_offset'])
def test_credit_omission_is_caught(valid_settlement, credit):
    out, inp = valid_settlement
    broken = deepcopy(out)
    broken['credits'][credit] = 0
    with pytest.raises(v.InvariantViolation, match=f'{credit} credit'):
        v.check_settlement(broken, inp, 'omitted credit')


@pytest.mark.parametrize('update,rule', [
    ({'refundable_offset': -1}, 'PHI mutual exclusion'),
    ({'excess_rebate_liability': -1}, 'PHI mutual exclusion'),
    ({'excess_rebate_liability': 1}, 'PHI mutual exclusion'),
    ({'entitlement': 99}, 'PHI reconciliation'),
])
def test_phi_corruption_is_caught(valid_settlement, update, rule):
    out, _ = valid_settlement
    phi = {**out['private_health_rebate'], **update}
    with pytest.raises(v.InvariantViolation, match=rule):
        v.check_phi(phi, 'corrupt PHI')


@pytest.mark.parametrize('update,rule', [
    ({'offsets': {'lito': 701}}, 'applied LITO bounds'),
    ({'offsets': {'lito': -1}}, 'applied LITO bounds'),
    ({'offsets': {'lito': 0, 'working_australians_tax_offset': 101}}, 'applied WATO bounds'),
    ({'income_tax_after_offsets': -1}, 'non-refundable offset balance'),
    ({'income_tax_after_offsets': 99.99}, 'non-refundable offset balance'),
])
def test_offset_corruption_is_caught(update, rule):
    tax = {'gross_tax': 100, 'offsets': {'lito': 0}, 'income_tax_after_offsets': 100, **update}
    with pytest.raises(v.InvariantViolation, match=rule):
        v.check_offsets(tax, 700, 'corrupt offsets', 100)


@pytest.mark.parametrize('raw,previous,rule', [(701, 700, 'LITO bounds'), (-1, 0, 'LITO bounds'),
                                              (326, 325, 'LITO shade-out')])
def test_statutory_lito_corruption_is_caught(raw, previous, rule):
    with pytest.raises(v.InvariantViolation, match=rule):
        v.check_lito(raw, previous, 700, 'corrupt LITO')


@pytest.mark.parametrize('gross,net,rule', [(99, 90, 'gross tax monotonicity'),
                                          (100, 89, 'tax after offsets monotonicity')])
def test_monotonicity_corruption_is_caught(gross, net, rule):
    with pytest.raises(v.InvariantViolation, match=rule):
        v.check_monotonic(gross, net, (100, 90), 'decreasing tax')


def test_unsafe_completion_is_caught(monkeypatch):
    monkeypatch.setattr(settlement, 'individual_tax_settlement', lambda *_: {'settlement_complete': True})
    with pytest.raises(v.InvariantViolation, match='unsafe settlement completeness'):
        v.verify_safety('2025-26', v.Counter())


def test_real_calculator_mutation_is_caught(monkeypatch, capsys):
    original = individual.individual_income_tax

    def broken(figures, inp):
        result = original(figures, inp)
        result['income_tax_after_offsets'] = -0.01
        return result

    monkeypatch.setattr(individual, 'individual_income_tax', broken)
    assert v.main() == 1
    assert 'non-refundable offset balance' in capsys.readouterr().out


def test_boundaries_include_whole_dollars_and_cents():
    f = Figures('2025-26')
    grid = set(v.income_grid(f))
    for key in ('resident_rates', 'foreign_resident_rates', 'whm_rates', 'lito'):
        for row in f.get(f'individual.{key}'):
            for edge in (row['from'], row['to']):
                if edge is not None:
                    assert set(v.edges([edge])) <= grid
    assert {0, v.MAX_INCOME, 45_001, 66_666, 66_667, 66_668} <= grid


def test_exact_cents_detect_one_cent_on_large_balance(valid_settlement):
    out, inp = valid_settlement
    broken = deepcopy(out)
    broken['net_amount_owing'] += 0.01
    with pytest.raises(v.InvariantViolation, match='settlement balance'):
        v.check_settlement(broken, inp, 'one cent matters')


@pytest.mark.parametrize('field', ['net_amount_owing', 'total_credits', 'refund'])
def test_fractional_cent_corruption_is_caught(valid_settlement, field):
    out, inp = valid_settlement
    broken = deepcopy(out)
    broken[field] += 0.001
    with pytest.raises(v.InvariantViolation, match='reported money precision'):
        v.check_settlement(broken, inp, 'sub-cent corruption')
