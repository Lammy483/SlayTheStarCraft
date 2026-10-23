"""Crew native production reservation policy (pure-Python test harness).

A future SC2 handler must advance a queued order ONLY after one distinct Crew
copy has been reserved, and must independently verify the finished unit tag.
No Galaxy train/build command is enabled by this module alone.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class CrewOrder:
    key: str
    native_type: str
    producer_tag: int
    supply: float = 0.0

class CrewQueueBudget:
    def __init__(self, copies, supply_available):
        self.unused = {str(k):str(v) for k,v in copies.items()}
        self.supply_available = float(supply_available)
        self.reserved = {}
        self.completed = {}

    def plan(self, orders):
        """Reserve at most one copy/order, one-to-one even with parallel queues."""
        commands=[]
        claimed=set(self.reserved.values())|set(self.completed.values())
        for order in orders:
            if order.key in self.reserved or order.key in self.completed:
                continue
            if order.supply > self.supply_available:
                continue
            selected=next((c for c,t in self.unused.items() if c not in claimed and t==order.native_type),None)
            if selected is None: continue
            self.reserved[order.key]=selected
            claimed.add(selected)
            self.supply_available-=order.supply
            commands.append((order.key,selected,99))
        return tuple(commands)

    def confirm(self, key, *, observed_type, observed_tag, verified_tag):
        """Only complete a reservation after SC2 and Galaxy identify same actor."""
        if key in self.completed:
            raise ValueError('Already completed')
        copy_id=self.reserved.get(key)
        if (copy_id is None or self.unused.get(copy_id)!=observed_type or
                type(observed_tag) is not int or observed_tag<=0 or
                type(verified_tag) is not int or verified_tag!=observed_tag):
            raise ValueError('Unverified Crew production receipt')
        self.completed[key]=copy_id
        del self.reserved[key]
        del self.unused[copy_id]
        return copy_id
