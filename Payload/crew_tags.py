"""Crew Galaxy integer tag wire format versus SC2 observation unit tags.

Galaxy UnitGetTag() and BankValueSetFromInt() expose the low 32 bits of the
64-bit unit tag that python-sc2 receives. Never store a truncated tag in the
persistent Crew roster: resolve it using independent observed identity, and
fail closed on missing/ambiguous mappings.
"""
from __future__ import annotations
from typing import Iterable

_MASK = (1 << 32) - 1


def wire_tag(full_tag: int) -> int:
    """Return Galaxy's unsigned low-32-bit identifier, not a roster tag."""
    if type(full_tag) is not int or not 0 < full_tag < (1 << 64):
        raise ValueError('Invalid SC2 unit tag')
    result = full_tag & _MASK
    if result == 0 or result >= 1 << 31:
        # Raw Galaxy uses signed int chat parsing. Don't emit a command that
        # would be truncated or parsed as negative, even if the bank can store
        # unsigned values. Add signed handling separately if encountered.
        raise ValueError('Galaxy signed integer tag is not representable safely')
    return result


def matching_full_tags(wire: int, full_tags: Iterable[int]) -> tuple[int, ...]:
    if type(wire) is not int or not 0 < wire < (1 << 31):
        raise ValueError('Invalid Galaxy bank tag')
    return tuple(sorted(set(tag for tag in full_tags
                            if type(tag) is int and 0 < tag < (1 << 64)
                            and (tag & _MASK) == wire)))


def require_unique_tag(wire: int, full_tags: Iterable[int], *, label: str) -> int:
    matches = matching_full_tags(wire, full_tags)
    if len(matches) != 1:
        raise RuntimeError(f'Crew {label} tag is missing or ambiguous: Galaxy={wire}, SC2={matches}')
    return matches[0]
