import pathlib, re, zipfile

def test_dev46(source):
    assert source.count('void APRG_TickNydusWorms(int player, fixed now) {') == 1
    assert 'void APRG_TickNydusWorms(int player, fixed now);' not in source
    for effect in ('NYDUS_WORMS', 'POINT_DEFENSE_DRONES', 'HEAVILY_DEFENDED_DRAKKEN',
                   'MULTIPLE_AIR_BOGIES', 'COVERT_ASSISTANCE', 'HYBRID_RESEARCH', 'FIFTY_IMMORTALS'):
        assert 'APRG_EXT3_' in source and effect in source
    assert 'TTychus03Horner00033' in source
    assert 'unitgroup wave;' not in source
    rx = re.compile(r'(?m)^\s*(?:void|bool|int|fixed|string|point|unit|unitgroup|trigger|actor|text)\s+(APRG_\w+)\s*\([^;{}]*\)\s*([;{])')
    seen={}
    for m in rx.finditer(source):
        name,kind=m.group(1),m.group(2)
        assert not (kind==';' and '{' in seen.get(name,[])), ('declaration after definition',name)
        seen.setdefault(name,[]).append(kind)

if __name__ == '__main__':
    f = pathlib.Path(__file__).resolve().parents[1]/'Payload'/'APRogue.galaxy'
    test_dev46(f.read_text())
    print('PASS Dev46 source regression checks')
