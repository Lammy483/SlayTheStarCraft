"""Optional local SC2 art with usable drawn fallbacks; no network access or global patches."""
from functools import lru_cache
import hashlib
import math
import os
from pathlib import Path
import random
import time

from kivy.graphics import Color, Line, Rectangle
from kivy.graphics.texture import Texture
from kivy.metrics import dp

ASSETS = Path(os.environ.get("SLAY_UI_ASSETS", str(Path(__file__).with_name("slay_assets"))))
LANGUAGE = "enUS"


def tr(text):
    # Explicit presentation boundary for future locale catalogues.
    return str(text)


def related_tech(ctx, unit):
    from worlds.sc2 import slay_the_starcraft as slay
    from worlds.sc2.item.item_parents import parent_item_to_children
    counts = slay._logic_owned_item_counts(ctx)
    table = slay._item_table()
    return [(name, int(counts.get(name, 0)))
            for name in sorted(set(parent_item_to_children.get(unit, ())))
            if name in table and table[name].code is not None]


@lru_cache(maxsize=64)
def fallback_planet(name):
    """Deterministic, original procedural art when a local campaign texture is absent."""
    seed = int.from_bytes(hashlib.sha256(name.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(seed)
    tint = rng.choice(((.34,.52,.72),(.65,.39,.23),(.31,.53,.38),(.46,.40,.66)))
    size = 96
    pixels = bytearray()
    for y in range(size):
        for x in range(size):
            nx, ny = (x-size/2)/(size*.47), (y-size/2)/(size*.47)
            radius = nx*nx+ny*ny
            if radius > 1:
                pixels.extend((0,0,0,0)); continue
            nz = math.sqrt(1-radius)
            light = max(.10, -.55*nx+.35*ny+.65*nz)
            terrain = .72+.18*math.sin(nx*21+math.sin(ny*14))+.10*rng.random()
            pixels.extend([min(255, int(255*channel*light*terrain)) for channel in tint]+[255])
    tex = Texture.create(size=(size,size), colorfmt="rgba")
    tex.blit_buffer(bytes(pixels), colorfmt="rgba", bufferfmt="ubyte")
    return tex


@lru_cache(maxsize=1)
def fallback_icon():
    return fallback_planet("unidentified supply")


@lru_cache(maxsize=1)
def starfield():
    size=256; rng=random.Random(483)
    pixels=bytearray([3,8,14,255]*(size*size))
    for _ in range(180):
        index=(rng.randrange(size)*size+rng.randrange(size))*4
        strength=rng.randrange(45,135)
        pixels[index:index+4]=bytes((int(strength*.55),int(strength*.75),strength,255))
    tex=Texture.create(size=(size,size),colorfmt="rgba")
    tex.blit_buffer(bytes(pixels),colorfmt="rgba",bufferfmt="ubyte")
    tex.wrap="repeat"
    return tex


def panel(widget, image=None, color=(.025,.055,.10,.98), border=True):
    source=ASSETS/image if image else None
    with widget.canvas.before:
        Color(*color)
        bg=Rectangle(source=str(source) if source and source.is_file() else "",pos=widget.pos,size=widget.size)
        if image and not (source and source.is_file()):
            Color(1,1,1,1);bg.texture=starfield()
        Color(.15,.38,.53,.8)
        edge=Line(rectangle=(*widget.pos,*widget.size),width=1) if border else None
    def resize(*_):
        bg.pos,bg.size=widget.pos,widget.size
        if image and not (source and source.is_file()):
            bg.tex_coords=(0,0,widget.width/dp(256),0,widget.width/dp(256),widget.height/dp(256),0,widget.height/dp(256))
        if edge:edge.rectangle=(*widget.pos,*widget.size)
    widget.bind(pos=resize,size=resize);resize()


_SOUNDS={}
_LAST_SOUND=0.0


def _click(widget,*_):
    global _LAST_SOUND
    now=time.monotonic()
    if now-_LAST_SOUND<.075:return
    _LAST_SOUND=now
    kind=getattr(widget,"slay_sound","nav")
    if kind not in _SOUNDS:
        filename={"command":"ui_commandcardbuttonselect.wav","nav":"ui_navbuttonselect.wav"}.get(kind,"ui_pushbuttonselect.wav")
        source=ASSETS/"sounds"/filename
        from kivy.core.audio import SoundLoader
        _SOUNDS[kind]=SoundLoader.load(str(source)) if source.is_file() else None
    sound=_SOUNDS[kind]
    if sound:sound.stop();sound.volume=.04;sound.play()


def button(widget):
    up=ASSETS/"sc2_ui_glues_bluebuttons_taskbarbuttonup.png"
    down=ASSETS/"sc2_ui_glues_bluebuttons_taskbarbuttondown.png"
    widget.background_normal=str(up) if up.is_file() else ""
    widget.background_down=str(down) if down.is_file() else ""
    widget.background_color=(1,1,1,1) if up.is_file() else (.025,.12,.20,1)
    widget.color=(.88,.96,1,1)
    widget.font_size=dp(15)
    if not getattr(widget,"_slay_ui_styled",False):
        if not up.is_file():panel(widget,color=(0,0,0,0))
        widget.bind(on_release=_click)
        widget._slay_ui_styled=True
