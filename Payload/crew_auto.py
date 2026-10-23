"""Crew Challenge automatic deployment order, independent of SC2 runtime.

Every selected owned copy gets at most one native spawn request, automatically,
when the macro base exists. Prefer to create owned infrastructure before units.
Persistent ownership requires an exact bank receipt + live SC2 tag observation;
unit type / a new unit appearing / a timeout never proves ownership.
"""
from __future__ import annotations
from typing import Any, Iterable, Mapping

# Match deployment starter ordering without overriding mission-owned actors.
TOWNHALLS = frozenset({'CommandCenter', 'Hatchery', 'Nexus'})
SUPPLY = frozenset({'SupplyDepot', 'Pylon', 'Overlord'})


def automatic_plan(manifest: Iterable[Mapping[str, Any]],
                   native_types: Mapping[str, str]) -> list[dict[str, Any]]:
    """Order exact copy IDs; ignore unimplemented native IDs safely.

    The plan is only an instruction queue. All entries must individually
    receive a validated SC2 tag before they enter the persistent roster.
    """
    seen: set[str] = set()
    rows = []
    for m in manifest:
        identifier = str(m['copy_id'])
        if identifier in seen:
            raise ValueError('Repeated Crew manifest copy')
        seen.add(identifier)
        native = native_types.get(str(m['name']))
        if native is None:
            continue  # keep unsupported owned copy in zone for later
        if m.get('kind') not in ('unit', 'structure') or m.get('status') != 'pending':
            raise ValueError('Invalid Crew manifest entry')
        rows.append({**dict(m),'native_type':native})
    def priority(row: Mapping[str, Any]) -> tuple[int,str]:
        native = row['native_type']
        if native in TOWNHALLS: rank=0
        elif native in SUPPLY: rank=1
        elif row['kind']=='structure': rank=2
        elif row['name'] in ('SCV','Drone','Probe'): rank=3
        else: rank=4
        return (rank, str(row['copy_id']))
    return sorted(rows,key=priority)
