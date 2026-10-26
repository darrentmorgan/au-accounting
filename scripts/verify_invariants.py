#!/usr/bin/env python3
"""Bounded verification of real individual calculators; see the project-local verify skill.

No solver/model substitutes for calculator execution. Exhaustive products are over
explicit finite sets, supplemented by boundary grids and Random(SEED) inputs.
All accounting identities compare exact Decimal cents, never a float tolerance.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from itertools import product
import math
from random import Random
import sys
from time import perf_counter

from au_tax.calculators import individual, settlement
from au_tax.figures import FigureError, Figures, RATES_DIR
from au_tax.registry import Refusal

SEED = 20261026
MAX_INCOME = 500_000
GRID_STEP = 1_000
SEEDED_CASES = 512


class InvariantViolation(Exception):
    """A small, reproducible counterexample in calculator terms."""


def require(condition: bool, rule: str, context: str, detail: str) -> None:
    if not condition:
        raise InvariantViolation(f"{rule}: {context}; {detail}")


def money(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def check_money_fields(data: dict, keys, context: str) -> None:
    for key in keys:
        value = Decimal(str(data[key]))
        require(value.is_finite() and value == money(value), 'reported money precision',
                context, f'{key} must be finite exact cents, got {data[key]}')


def equal(actual, expected, rule: str, context: str) -> None:
    require(actual == expected, rule, context, f"expected {expected}, got {actual}")


def edges(values) -> list[float]:
    """Every whole-dollar and cent neighbour, including the floor transition."""
    return sorted({round(x + d, 2) for x in values if x is not None
                   for d in (-1, -0.01, 0, 0.01, 1) if 0 <= x + d <= MAX_INCOME})


def schedule_edges(rows) -> list[float]:
    return edges([r.get(k) for r in rows for k in ('from', 'to')])


def verified_years() -> list[str]:
    years = []
    for path in sorted(RATES_DIR.glob('*.yaml')):
        data = Figures(path.stem).data
        if all(data['individual'][key]['status'] == 'VERIFIED'
               for key in ('resident_rates', 'foreign_resident_rates', 'whm_rates', 'lito')):
            years.append(path.stem)
    require(bool(years), 'coverage', 'rates', 'no VERIFIED base schedules found')
    return years


def income_grid(figures: Figures) -> list[float]:
    points = set(range(0, MAX_INCOME + 1, GRID_STEP))
    for key in ('resident_rates', 'foreign_resident_rates', 'whm_rates', 'lito'):
        points.update(schedule_edges(figures.get(f'individual.{key}')))
    for domain in ('medicare', 'help'):
        for name, figure in figures.data[domain].items():
            if figure['status'] != 'VERIFIED' or figure['value'] is None:
                continue
            if name == 'repayment_schedule' or name.startswith('mls_') and name.endswith('_tiers'):
                points.update(schedule_edges(figure['value']))
            elif name.startswith('low_income_') and not ('sapto' in name or 'current_law' in name):
                points.update(edges([figure['value']]))
    return sorted(points)


def check_lito(raw: float, previous: float, cap: float, context: str) -> None:
    require(0 <= raw <= cap, 'LITO bounds', context, f'offset {raw} must be between 0 and {cap}')
    require(raw <= previous, 'LITO shade-out', context, f'offset rose from {previous} to {raw}')


def check_monotonic(gross: float, net: float, previous: tuple[float, float], context: str) -> None:
    require(gross >= previous[0], 'gross tax monotonicity', context,
            f'gross tax fell from {previous[0]} to {gross}')
    require(net >= previous[1], 'tax after offsets monotonicity', context,
            f'tax fell from {previous[1]} to {net}')


def check_offsets(tax: dict, cap: float, context: str, wato_cap: float = 0) -> None:
    check_money_fields(tax, ('gross_tax', 'income_tax_after_offsets'), context)
    check_money_fields(tax['offsets'], ('lito',), context)
    if 'working_australians_tax_offset' in tax['offsets']:
        check_money_fields(tax['offsets'], ('working_australians_tax_offset',), context)
    gross = tax['gross_tax']
    lito = tax['offsets']['lito']
    wato = tax['offsets'].get('working_australians_tax_offset', 0)
    require(0 <= lito <= min(cap, gross), 'applied LITO bounds', context,
            f'LITO {lito}, gross tax {gross}, maximum {cap}')
    require(0 <= wato <= min(wato_cap, gross - lito), 'applied WATO bounds', context,
            f'WATO {wato}, tax remaining {gross - lito}, maximum {wato_cap}')
    equal(tax['income_tax_after_offsets'], max(0, round(gross - lito - wato, 2)),
          'non-refundable offset balance', context)


def check_phi(phi: dict, context: str) -> None:
    check_money_fields(phi, ('entitlement', 'rebate_received', 'refundable_offset', 'excess_rebate_liability'), context)
    for row in phi['rows']:
        check_money_fields(row, ('entitlement', 'rebate_received'), context)
    entitlement, received, refundable, excess = (money(phi[k]) for k in
        ('entitlement', 'rebate_received', 'refundable_offset', 'excess_rebate_liability'))
    require(refundable >= 0 and excess >= 0 and min(refundable, excess) == 0,
            'PHI mutual exclusion', context, f'refundable {refundable}, excess {excess}')
    equal(entitlement - received, refundable - excess, 'PHI reconciliation', context)
    for name in ('entitlement', 'rebate_received'):
        equal(money(phi[name]), sum((money(row[name]) for row in phi['rows']), Decimal(0)),
              f'PHI row {name} sum', context)


def check_settlement(out: dict, inp: settlement.IndividualSettlementInput, context: str) -> None:
    check_money_fields(out, ('liability_including_phi_excess', 'total_credits',
                            'net_amount_owing', 'refund', 'amount_owing'), context)
    check_money_fields(out['tax_components'], ('total_liability',), context)
    check_money_fields(out['credits'], ('payg_withheld', 'payg_instalments',
                                       'refundable_franking', 'phi_refundable_offset'), context)
    phi = out['private_health_rebate']
    check_phi(phi, context)
    equal(money(out['liability_including_phi_excess']),
          money(out['tax_components']['total_liability']) + money(phi['excess_rebate_liability']),
          'liability including PHI excess', context)
    credits = out['credits']
    expected = {'payg_withheld': inp.tax_withheld, 'payg_instalments': inp.payg_instalment_credit,
                'refundable_franking': inp.franking.credit if inp.franking else 0,
                'phi_refundable_offset': phi['refundable_offset']}
    for key, value in expected.items():
        equal(money(credits[key]), money(value), f'{key} credit', context)
    equal(money(out['total_credits']), sum((money(credits[k]) for k in expected), Decimal(0)),
          'total credits', context)
    net = money(out['net_amount_owing'])
    equal(net, money(out['liability_including_phi_excess']) - money(out['total_credits']),
          'settlement balance', context)
    refund, owing = money(out['refund']), money(out['amount_owing'])
    equal(refund, max(Decimal(0), -net), 'refund sign', context)
    equal(owing, max(Decimal(0), net), 'amount owing sign', context)
    equal(min(refund, owing), 0, 'refund/owing mutual exclusion', context)
    equal(owing - refund, net, 'refund/owing balance', context)
    equal(out['settlement_complete'], True, 'confirmed settlement completeness', context)


def check_safety_result(out: dict, context: str) -> None:
    require(out.get('settlement_complete') is not True, 'unsafe settlement completeness', context,
            'settlement_complete=True despite unsafe inputs or figures')


def payload(**updates) -> dict:
    return {"taxable_income": 100_000, "private_hospital_cover": True,
            "net_labour_income": 0, "tax_withheld": 0, "payg_instalment_credit": 0,
            "franking": None, "private_health_rebate": None, "unmodelled_inputs": [], **updates}


def franking(year: str, credit: float = 1500.55) -> dict:
    return dict(income_year=year, credit=credit, gross_up_included=True,
                refundable_eligibility_confirmed=True)


def phi_input(year: str, key: str, income: float, family: bool, children: int,
              premium: float, received: float) -> dict:
    # These are the actual public model literals, not age or period approximations.
    period = '1apr_to_30jun' if '1apr_to_30jun' in key else '1jul_to_31mar'
    age = key.removeprefix(f'phi_rebate_{period}_')
    return dict(income_year=year, eligibility_and_allocation_confirmed=True,
                income_for_rebate=income, family=family, dependent_children=children,
                rows=[dict(period=period, age_band=age, eligible_premium=premium,
                           rebate_received=received)])


def verify() -> Counter:
    counts = Counter()
    rng = Random(SEED)
    years = verified_years()
    for year in years:
        figures = Figures(year)
        grid = income_grid(figures)
        cap = max(row['base'] for row in figures.get('individual.lito'))
        wato_cap = (figures.get('individual.working_australians_tax_offset_max')
                    if year >= individual.WATO_FIRST_YEAR else 0)
        # Real base helpers cover low incomes even when that year's Medicare is unpublished.
        for residency, months in (('resident', 1), ('resident', 6), ('resident', 12),
                                  ('foreign', 12), ('whm', 12)):
            inp = individual.IndividualTaxInput(taxable_income=0, residency=residency,
                                              resident_months=months, net_labour_income=0)
            previous_raw, previous = float('inf'), (-1, -1)
            for income in grid:
                context = f'{year} {residency}, months={months}, income={income}'
                ti = math.floor(income)
                gross = individual._income_tax(figures, inp, ti)[0]
                raw = individual._lito(figures, inp, ti)
                check_lito(raw, previous_raw, cap, context)
                # Net here is base tax with statutory LITO; public capping is checked below.
                net = max(0, round(gross - raw, 2))
                check_monotonic(round(gross, 2), net, previous, context)
                previous_raw, previous = raw, (round(gross, 2), net)
                counts['base'] += 1
        # Public outputs, including actual non-refundable caps and WATO execution.
        for residency in ('resident', 'foreign', 'whm'):
            for labour in ((0, MAX_INCOME) if wato_cap and residency == 'resident' else (0,)):
                previous = (-1, -1)
                for income in grid:
                    if (residency == 'resident' and income < 100_000
                            and figures.data['medicare']['low_income_single_lower']['status'] != 'VERIFIED'):
                        continue  # tested as an explicit refusal below, never fabricated
                    context = f'{year} {residency}, income={income}, net_labour_income={labour}'
                    inp = individual.IndividualTaxInput(taxable_income=income, residency=residency,
                                                       private_hospital_cover=True, net_labour_income=labour)
                    out = individual.individual_income_tax(figures, inp)
                    check_offsets(out, cap, context, wato_cap)
                    check_monotonic(out['gross_tax'], out['income_tax_after_offsets'], previous, context)
                    previous = out['gross_tax'], out['income_tax_after_offsets']
                    counts['components'] += 1

        def settle_case(data: dict, category: str, label: str) -> dict:
            inp = settlement.IndividualSettlementInput.model_validate(data)
            context = f'{year} {label}'
            out = settlement.individual_tax_settlement(figures, inp)
            check_offsets(out['tax_components'], cap, context, wato_cap)
            check_settlement(out, inp, context)
            counts[category] += 1
            return out

        # Exercise MLS/HELP and Medicare together on the entire 2025-26 grid.
        # Other years retain real base coverage above; low-income Medicare is
        # unpublished, so their complete low-income settlements must refuse.
        if year == '2025-26':
            for income in grid:
                data = payload(taxable_income=income, private_hospital_cover=False,
                               has_help_debt=True, help_debt_balance=MAX_INCOME)
                settle_case(data, 'boundary_settlements', f'Medicare/MLS/HELP income={income}')
            # Family Medicare shade-in and child-adjusted MLS boundaries. Spouse
            # income is explicitly zero, avoiding unmodelled spouse levy excess.
            for children in (0, 1, 2, 3):
                lower = (figures.get('medicare.low_income_family_lower')
                         + figures.get('medicare.low_income_per_child_lower_add') * children)
                shade_end = lower * figures.get('medicare.low_income_shade_in_rate') / (
                    figures.get('medicare.low_income_shade_in_rate') - figures.get('medicare.levy_rate'))
                shift = figures.get('medicare.mls_family_per_child_after_first') * max(0, children - 1)
                thresholds = [lower, shade_end] + [row['to'] + shift for row in
                    figures.get('medicare.mls_family_tiers') if row['to'] is not None]
                for income in edges(thresholds):
                    data = payload(taxable_income=income, has_spouse=True,
                                   spouse_income_for_mls=0, dependent_children=children,
                                   private_hospital_cover=False, has_help_debt=True,
                                   help_debt_balance=MAX_INCOME)
                    settle_case(data, 'boundary_settlements',
                                f'family Medicare/MLS/HELP children={children}, income={income}')

        # Every published PHI period x age x family/child setting x tier boundary
        # x premium/rebate pair. Later-year cases use high taxable income to avoid
        # unpublished Medicare; PHI income is an independently confirmed input.
        for key, figure in figures.data['medicare'].items():
            if not key.startswith('phi_rebate_') or figure['status'] != 'VERIFIED':
                continue
            for family, children in ((False, 0), (True, 0), (True, 1), (True, 2)):
                shift = figures.get('medicare.mls_family_per_child_after_first') * max(0, children - 1) if family else 0
                thresholds = [0, MAX_INCOME] + [row['family_to' if family else 'to'] + shift
                    for row in figure['value'] if row['to'] is not None]
                for income, (premium, received) in product(edges(thresholds),
                        ((0, 0), (1000.05, 0), (0.01, 2000.01))):
                    phi = phi_input(year, key, income, family, children, premium, received)
                    label = f'PHI {key}, family={family}, children={children}, income={income}, premium={premium}, received={received}'
                    out = settle_case({**payload(), 'private_health_rebate': phi}, 'phi', label)
                    expected_tier = next(row for row in figure['value'] if
                        row['family_to' if family else 'to'] is None or income <= row['family_to' if family else 'to'] + shift)
                    actual_row = out['private_health_rebate']['rows'][0]
                    equal(actual_row['rate'], expected_tier['rate'], 'PHI tier', label)
                    equal(money(actual_row['entitlement']), money(Decimal(str(premium)) * Decimal(str(expected_tier['rate']))),
                          'PHI row rounding', label)

        # Finite credit product includes no credit, zero-valued credit, exact
        # balance, refund, owing, and credits larger than income-tax liability.
        incomes = (0, 18_200, 45_001, 100_000, MAX_INCOME) if year == '2025-26' else (100_000, MAX_INCOME)
        for income, withheld, instalments, credit in product(incomes, (0, 25_348, 500_000.01),
                                                             (0, 1000.99), (None, 0, 1500.55)):
            data = {**payload(), 'taxable_income': income, 'tax_withheld': withheld,
                    'payg_instalment_credit': instalments,
                    'franking': franking(year, credit) if credit is not None else None}
            settle_case(data, 'credits', f'income={income}, PAYG={withheld}/{instalments}, franking={credit}')

        # Seeded joint interactions on a year with all component figures verified.
        if year == '2025-26':
            phi_keys = [k for k in figures.data['medicare'] if k.startswith('phi_rebate_')]
            for index in range(SEEDED_CASES):
                income = rng.choice(grid) if index % 2 else rng.randrange(MAX_INCOME * 100 + 1) / 100
                family = rng.choice((False, True))
                children = rng.randrange(4) if family else 0
                rows = [phi_input(year, rng.choice(phi_keys), 0, False, 0,
                                  rng.randrange(1_000_001) / 100, rng.randrange(500_001) / 100)['rows'][0]
                        for _ in range(rng.randrange(1, 7))]
                phi = phi_input(year, phi_keys[0], income, family, children, 0, 0)
                phi['rows'] = rows
                residency = rng.choice(('resident', 'foreign', 'whm'))
                data = {**payload(), 'taxable_income': income, 'residency': residency,
                        'private_hospital_cover': rng.choice((True, False)),
                        'days_without_cover': rng.choice((0, 1, 182, 365)),
                        'has_spouse': family, 'dependent_children': children,
                        'spouse_taxable_income': rng.randrange(200_001) if family else 0,
                        'spouse_income_for_mls': rng.randrange(200_001) if family else 0,
                        'has_help_debt': residency == 'resident',
                        'help_debt_balance': rng.choice((0, 100.01, 100_000)),
                        'reportable_fringe_benefits': rng.randrange(20_001),
                        'net_investment_losses': rng.randrange(10_001),
                        'reportable_super_contributions': rng.randrange(10_001),
                        'medicare_full_exemption_days': rng.choice((0, 1, 182, 365)),
                        'medicare_half_exemption_days': rng.choice((0, 1, 182, 365)),
                        'tax_withheld': rng.randrange(50_000_001) / 100,
                        'payg_instalment_credit': rng.randrange(1_000_001) / 100,
                        'franking': franking(year) if residency == 'resident' and index % 2 else None,
                        'private_health_rebate': phi}
                # Spouse levy excess is deliberately not a complete settlement.
                try:
                    settle_case(data, 'seeded', f'seed={SEED}, case={index}, income={income}')
                except Refusal as exc:
                    require(exc.code == 'AU-IND-005' and 'spouse_levy_excess' in exc.detail,
                            'unexpected seeded refusal', f'seed={SEED}, case={index}', exc.detail)
                    counts['seeded_refusals'] += 1
        verify_safety(year, counts)
    return counts


def verify_safety(year: str, counts: Counter) -> None:
    figures = Figures(year)
    key = 'phi_rebate_1jul_to_31mar_under_65'
    phi = phi_input(year, key, 100_000, False, 0, 1000, 0)
    unsafe = [
        ('unmodelled input', {**payload(), 'unmodelled_inputs': ['FITO']}),
        ('franking year mismatch', {**payload(), 'franking': franking('1900-01')}),
        ('PHI year mismatch', {**payload(), 'private_health_rebate': {**phi, 'income_year': '1900-01'}}),
        *[(f'{residency} franking', {**payload(), 'residency': residency, 'franking': franking(year)})
          for residency in ('foreign', 'whm')],
    ]
    # Mutate a private copy of actual rate data, never the cached/year files.
    # Exercise draft reads in base tax, Medicare, WATO and PHI independently.
    draft_keys = [('individual', 'resident_rates'), ('medicare', 'levy_rate')]
    if year >= individual.WATO_FIRST_YEAR:
        draft_keys.append(('individual', 'working_australians_tax_offset_max'))
    if figures.data['medicare'][key]['status'] == 'VERIFIED':
        draft_keys.append(('medicare', key))
    for domain, name in draft_keys:
        draft = Figures(year, allow_draft=True)
        draft.data = deepcopy(draft.data)
        draft.data[domain][name]['status'] = 'SOURCE-CITED'
        data = {**payload(), 'private_health_rebate': phi if name == key else None}
        check_unsafe(draft, data, f'{year} draft {domain}.{name}')
        counts['safety'] += 1
    for label, data in unsafe:
        check_unsafe(figures, data, f'{year} {label}')
        counts['safety'] += 1
    if figures.data['medicare']['low_income_single_lower']['status'] != 'VERIFIED':
        check_unsafe(figures, {**payload(), 'taxable_income': 0}, f'{year} unpublished low-income Medicare',
                     expected_code='AU-GEN-003')
        counts['safety'] += 1
    if year != '2025-26':
        missing_phi = phi_input(year, 'phi_rebate_1apr_to_30jun_under_65', 0, False, 0, 1000, 0)
        check_unsafe(figures, {**payload(), 'private_health_rebate': missing_phi},
                     f'{year} unpublished PHI period', expected_code='AU-GEN-003')
        counts['safety'] += 1


def check_unsafe(figures: Figures, data: dict, context: str, expected_code: str = 'AU-IND-005') -> None:
    inp = settlement.IndividualSettlementInput.model_validate(data)
    try:
        out = settlement.individual_tax_settlement(figures, inp)
    except (Refusal, FigureError) as exc:
        equal(exc.code, expected_code, 'refusal code', context)
        return
    check_safety_result(out, context)
    raise InvariantViolation(f'expected refusal: {context}; unsafe input returned a settlement')


def main() -> int:
    start = perf_counter()
    try:
        counts = verify()
    except InvariantViolation as exc:
        print(f'FAIL {exc}')
        return 1
    except Exception as exc:
        print(f'FAIL verifier could not complete: {type(exc).__name__}: {exc}')
        return 1
    print(f'PASS individual invariants: {sum(counts.values())} cases; '
          f'{", ".join(f"{key}={value}" for key, value in sorted(counts.items()))}; '
          f'years={",".join(verified_years())}; income=0..{MAX_INCOME}, step={GRID_STEP} plus boundaries; '
          f'seed={SEED}; {perf_counter() - start:.3f}s')
    return 0


if __name__ == '__main__':
    sys.exit(main())
