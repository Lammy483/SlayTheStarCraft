"""Offline geometry test for wider mission labels without Kivy or SC2."""
import ast
from collections import defaultdict
from pathlib import Path
import random
import unittest

source=Path(__file__).resolve().parents[1]/'Payload'/'slay_command_ui.py'
module=ast.parse(source.read_text(encoding='utf-8'))
function=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='resolve_route_positions')
context={'dp':lambda value:value,'defaultdict':defaultdict,'ROUTE_FLOOR_SPACING':178}
exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),'<chart-layout>','exec'),context)
resolve=context['resolve_route_positions']


class MissionChartLayoutTests(unittest.TestCase):
    def test_wide_node_titles_do_not_overlap_or_leave_chart(self):
        for seed in range(1000):
            rng=random.Random(seed)
            count=rng.randint(1,4)
            widths={i:rng.uniform(205,550) for i in range(count)}
            nodes={i:{'layer':0,'lane':i} for i in widths}
            chart_width=max(950,sum(widths.values())+30*(count-1)+240)
            preferred={i:rng.uniform(.12,.88) for i in widths}
            positions=resolve(nodes,chart_width,preferred,widths)
            ordered=sorted(widths,key=lambda mid:positions[mid][0])
            for left,right in zip(ordered,ordered[1:]):
                between=positions[right][0]-positions[left][0]-(widths[left]+widths[right])/2
                self.assertGreaterEqual(between,24.999,(seed,widths,positions))
            for mid in widths:
                center=positions[mid][0]
                self.assertGreaterEqual(center-widths[mid]/2,17.999,(seed,mid))
                self.assertLessEqual(center+widths[mid]/2,chart_width-17.999,(seed,mid))


if __name__=='__main__':
    unittest.main()
