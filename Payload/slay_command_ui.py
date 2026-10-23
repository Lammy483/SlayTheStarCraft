"""SC2 star chart and card consoles. All gameplay identities/callbacks remain original."""
from pathlib import Path
from collections import defaultdict, OrderedDict
import math,re
import os
import traceback
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse, Mesh
from kivy.graphics.instructions import InstructionGroup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scatter import Scatter
from kivy.uix.slider import Slider
import json
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from slay_ui_support import tr, LANGUAGE, related_tech
from slay_ui_support import ASSETS, button, panel, fallback_planet, fallback_icon

ICON_MAP=json.loads(Path(__file__).with_name('slay_ui_icons.json').read_text(encoding='utf-8'))
# The Archipelago SC2 item-docs site is authoritative when its illustration
# differs from a themed UI placeholder. Keep a usable local fallback offline.
DOCS_ICON_MAP=json.loads(Path(__file__).with_name('slay_docs_icon_overrides.json').read_text(encoding='utf-8'))
TEXTURES=OrderedDict()
_DOC_ICON_DOWNLOAD_PENDING=set()
_DOC_ICON_QUEUE=None
_DOC_ICON_WORKERS_STARTED=False
_DOC_ICON_LOCK=None

def _queue_documented_icon(relative_path):
    """Cache the original docs illustration without ever blocking the Kivy UI."""
    global _DOC_ICON_QUEUE, _DOC_ICON_WORKERS_STARTED, _DOC_ICON_LOCK
    import queue, threading
    if _DOC_ICON_LOCK is None:
        _DOC_ICON_LOCK=threading.Lock()
    with _DOC_ICON_LOCK:
        if relative_path in _DOC_ICON_DOWNLOAD_PENDING:return
        if not _DOC_ICON_WORKERS_STARTED:
            _DOC_ICON_QUEUE=queue.Queue()
            _DOC_ICON_WORKERS_STARTED=True
            def worker():
                import urllib.request, urllib.parse
                while True:
                    relative=_DOC_ICON_QUEUE.get()
                    try:
                        # Only static PNG assets from the exact user-specified docs site.
                        url='https://archipelago-sc2.github.io/content-docs/'+urllib.parse.quote(relative,safe='/')
                        request=urllib.request.Request(url,headers={'User-Agent':'SlayTheStarCraft-IconCache/1.1'})
                        with urllib.request.urlopen(request,timeout=7) as response:
                            binary=response.read(262145)
                        if len(binary)>262144 or not binary.startswith(b'\x89PNG\r\n\x1a\n'):continue
                        destination=ASSETS/'icons'/Path(relative).name
                        destination.parent.mkdir(parents=True,exist_ok=True)
                        temporary=destination.with_name(destination.name+'.partial')
                        temporary.write_bytes(binary)
                        temporary.replace(destination)
                    except Exception:
                        # Offline play must not depend on the icon site.
                        pass
                    finally:
                        _DOC_ICON_QUEUE.task_done()
            for _ in range(4):
                threading.Thread(target=worker,name='APSC2IconCache',daemon=True).start()
        _DOC_ICON_DOWNLOAD_PENDING.add(relative_path)
        _DOC_ICON_QUEUE.put(relative_path)

CYAN=(.28,.78,1,1)
SECTIONS=('Terran Units','Terran Upgrades','Zerg Units','Zerg Upgrades','Protoss Units','Protoss Upgrades',
          'Defensive Structures & Detectors','General Upgrades','Mercenary Contracts','Mercenaries','Kerrigan','Spear of Adun','Boons','Consumables','Blessings','Mutations')
STATUS={'available':('Available',CYAN),'selected':('Current Mission',(.3,1,.64,1)),'completed':('Completed',(.3,.85,.52,1)),
        'future':('Locked',(.3,.47,.61,1)),'abandoned':('Unavailable',(.48,.38,.43,1)),'loading':('Loading',(.52,.63,.7,1))}

DEFAULT_ROUTE_SCALE=.60
NODE_PLANET_CENTER_Y=58
ROUTE_FLOOR_SPACING=178
NODE_CARD_HEIGHT=116
NODE_PLANET_X=57
SHOP_SECTION_COLUMNS={
    'Terran Units':0,'Terran Upgrades':0,'Defensive Structures & Detectors':0,
    'Zerg Units':1,'Zerg Upgrades':1,'General Upgrades':1,
    'Protoss Units':2,'Protoss Upgrades':2,'Boons':2,
    'Terran Structures':0,'Zerg Structures':1,'Protoss Structures':2,
    'Mercenary Contracts':3,'Mercenaries':3,'Kerrigan':3,'Spear of Adun':3,'Consumables':3,
}
INVENTORY_SECTION_COLUMNS=dict(SHOP_SECTION_COLUMNS,**{'Blessings':2,'Mutations':2})
SECTION_PALETTE={
    'Terran Units':(.155,.178,.198,1),'Terran Upgrades':(.170,.191,.211,1),
    'Defensive Structures & Detectors':(.155,.190,.188,1),
    'Zerg Units':(.184,.158,.194,1),'Zerg Upgrades':(.198,.170,.206,1),
    'General Upgrades':(.184,.184,.184,1),
    'Protoss Units':(.199,.190,.158,1),'Protoss Upgrades':(.211,.201,.170,1),
    'Mercenary Contracts':(.145,.175,.215,1),'Mercenaries':(.160,.190,.168,1),
    'Kerrigan':(.198,.164,.181,1),'Spear of Adun':(.225,.195,.120,1),'Consumables':(.125,.205,.215,1),
    'Boons':(.215,.145,.150,1),'Blessings':(.180,.155,.205,1),'Mutations':(.205,.150,.160,1),
    'Terran Structures':(.155,.190,.188,1),'Zerg Structures':(.184,.158,.194,1),
    'Protoss Structures':(.199,.190,.158,1),
}


def _command_ui_log(message):
    root=os.environ.get('SLAY_PORTABLE_ROOT','').strip()
    if not root:return
    try:
        path=Path(root)/'Runtime'/'Logs'/'SlayCommandUI.log'
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('a',encoding='utf-8',errors='replace') as handle:
            handle.write(message.rstrip()+'\n')
    except Exception:
        pass

def texture(source):
    source=str(source)
    if source in TEXTURES:
        TEXTURES.move_to_end(source);return TEXTURES[source]
    if not source:return fallback_icon()
    if source.startswith(('http:','https:')) or not Path(source).is_file():return None
    try:tex=CoreImage(source,nocache=True).texture
    except Exception:return None
    TEXTURES[source]=tex
    while len(TEXTURES)>320:TEXTURES.popitem(last=False)
    return tex

def label(text,**kwargs):
    auto_height=kwargs.pop('auto_height',False)
    options=dict(markup=True,font_size=dp(14),color=(.83,.93,1,1));options.update(kwargs)
    w=Label(text=tr(text),**options)
    if auto_height:w.bind(width=lambda obj,width:setattr(obj,'text_size',(width,None)))
    else:w.bind(size=lambda obj,size:setattr(obj,'text_size',size))
    return w

def control(text,callback=None,**kwargs):
    b=Button(text=tr(text),**kwargs);button(b)
    b.slay_sound='nav'
    if callback:b.bind(on_release=callback)
    return b

class ReliableCloseButton(Button):
    """Close a Kivy popup even when its release event is swallowed.

    Large ScrollViews and modal focus changes can prevent on_release after a
    perfectly valid press. Treat the initial hit-tested touch as sufficient for
    a Close action; on_press/on_release remain redundant fallbacks. Logging
    separates touch routing from a Popup dismissal failure in live tests.
    """
    def __init__(self, close_action, **kwargs):
        super().__init__(**kwargs)
        self._slay_close_action = close_action
        button(self)
        self.bind(on_press=lambda *_:close_action('press'))
        self.bind(on_release=lambda *_:close_action('release'))

    def on_touch_down(self, touch):
        inside = (not self.disabled and self.collide_point(*touch.pos) and
                  getattr(touch, 'button', None) not in ('scrollup', 'scrolldown'))
        handled = super().on_touch_down(touch)
        if inside:
            self._slay_close_action('touch-down')
            return True
        return handled


def race_icon(category):
    race='zerg' if ('Zerg' in category or category in ('Kerrigan','Mutations')) else 'prot' if ('Protoss' in category or category in ('Spear of Adun','Boons','Blessings')) else 'terr'
    return ASSETS/f'ui_battlenet_glue_campaign_floatingraceicon_{race}.png'

def local_icon(item,source='',category=''):
    # No misleading Immortal portrait for the Spear of Adun ship unlock.
    if str(item).endswith('spear_unlock') or str(item) == 'Unlock Spear of Adun':
        return ''
    # Prefer the exact Archipelago documentation art whenever that upgrade
    # has a documented image. Older themed thumbnails are only offline fallbacks.
    docs_path=DOCS_ICON_MAP.get(str(item))
    if docs_path:
        preferred=ASSETS/'icons'/Path(docs_path).name
        if preferred.is_file():return str(preferred)
        _queue_documented_icon(docs_path)
    mapped=ICON_MAP.get(str(item))
    if mapped and (ASSETS/'icons'/mapped).is_file():return str(ASSETS/'icons'/mapped)
    if source:
        candidate=ASSETS/'icons'/Path(source).name
        if candidate.is_file():return str(candidate)
    return ''


def shop_icon_texture(item, source='', category=''):
    # No suitable icon for the Spear ship unlock; leave it blank rather than
    # showing an unrelated Immortal portrait.
    if str(item).endswith('spear_unlock') or str(item) == 'Unlock Spear of Adun':
        return None
    return texture(local_icon(item, source, category))


def technology_grid(ctx,unit):
    from slay_ui_support import related_tech
    from worlds.sc2 import slay_the_starcraft as slay
    from worlds.sc2.client_gui import HoverableButton
    from kivymd.uix.tooltip import MDTooltip
    from kivy.graphics import RenderContext
    from kivy.properties import StringProperty
    from kvui import ServerToolTip
    class TechButton(HoverableButton,MDTooltip):
        tooltip_text=StringProperty('')
        def __init__(self,**kwargs):
            super().__init__(**kwargs)
            self._tooltip=ServerToolTip(text=self.tooltip_text,markup=True)
            self._tooltip.padding=[5,2,5,2]
        def on_enter(self):
            self._tooltip.text=self.tooltip_text
            self.display_tooltip()
        def on_leave(self):self.remove_tooltip()
    technologies=related_tech(ctx,unit)
    if not technologies:return None
    grid=GridLayout(cols=4,size_hint_y=None,spacing=dp(5),row_default_height=dp(46),row_force_default=True)
    grid.bind(minimum_height=grid.setter('height'))
    for name,count in technologies:
        title=tr(slay.shop_entry_display_name(name));description=tr(slay.shop_entry_description(name))
        status=tr('Owned' if count else 'Not Owned')
        b=TechButton(text='',background_normal='',background_color=(.03,.12,.2,1),tooltip_text=title+'\n'+status+'\n'+description)
        icon=Image(texture=texture(local_icon(name,slay.shop_entry_icon(name))))
        if not count:
            icon.canvas=RenderContext(use_parent_projection=True,use_parent_modelview=True)
            # Use the native BTN texture; desaturate on the GPU, with no duplicate image files.
            icon.canvas.shader.fs='''$HEADER$
void main(void) {
    vec4 pixel=texture2D(texture0,tex_coord0)*frag_color;
    float grey=dot(pixel.rgb,vec3(0.299,0.587,0.114));
    gl_FragColor=vec4(vec3(grey)*0.60,pixel.a);
}'''
            # Image canvas instructions are built during construction, so add the textured quad explicitly.
            with icon.canvas:
                Color(1,1,1,1)
                quad=Rectangle(texture=icon.texture,pos=icon.pos,size=icon.size)
            icon.bind(pos=lambda w,v,q=quad:setattr(q,'pos',v),size=lambda w,v,q=quad:setattr(q,'size',v))
        b.add_widget(icon)
        def size_icon(w,*_,image=icon):image.pos=(w.x+dp(3),w.y+dp(3));image.size=(w.width-dp(6),w.height-dp(6))
        b.bind(pos=size_icon,size=size_icon);size_icon(b)
        def detail(*_,item=name):
            body=BoxLayout(orientation='vertical',padding=dp(15),spacing=dp(8));panel(body,border=False)
            body.add_widget(Image(texture=texture(local_icon(item,slay.shop_entry_icon(item))),size_hint_y=None,height=dp(80)))
            text=label(tr(slay.shop_entry_description(item)),halign='left',valign='top',auto_height=True,size_hint_y=None)
            text.bind(texture_size=lambda w,v:setattr(w,'height',v[1]+dp(12)))
            scroll=ScrollView(do_scroll_x=False);scroll.add_widget(text);body.add_widget(scroll)
            pop=Popup(title=tr(slay.shop_entry_display_name(item)),content=body,size_hint=(.48,.55))
            body.add_widget(control('Close',pop.dismiss,size_hint_y=None,height=dp(35)));pop.open()
        b.bind(on_release=detail);grid.add_widget(b)
    return grid

def unit_technology_popup(entry):
    from kivy.app import App
    body=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(10));panel(body,border=False)
    grid=technology_grid(App.get_running_app().ctx,entry.get('canonical_name',entry['id']))
    scroll=ScrollView(do_scroll_x=False)
    if grid:scroll.add_widget(grid)
    body.add_widget(scroll)
    pop=Popup(title=entry['name']+' · '+tr('Related Technology'),content=body,size_hint=(.5,.65))
    body.add_widget(control('Close',pop.dismiss,size_hint_y=None,height=dp(36)));pop.open()



def stroke_mesh(points,width,mesh=None):
    # Alpha Line uses its own stencil in Kivy; mesh strips preserve ScrollView clipping.
    if mesh is None:mesh=Mesh(vertices=[],indices=[],mode='triangle_strip')
    vertices=[]
    for index,(x,y) in enumerate(points):
        previous=points[max(0,index-1)];following=points[min(len(points)-1,index+1)]
        dx=following[0]-previous[0];dy=following[1]-previous[1];length=max(.001,math.hypot(dx,dy))
        nx=-dy/length*width/2;ny=dx/length*width/2
        vertices.extend((x+nx,y+ny,0,0,x-nx,y-ny,0,0))
    mesh.vertices=vertices;mesh.indices=list(range(len(points)*2));return mesh

def frame(widget,accent=CYAN):
    with widget.canvas.before:
        Color(.025,.075,.135,1);bg=Rectangle(pos=widget.pos,size=widget.size)
        honeycomb = texture(ASSETS/'ui_planetpanel_honeycomb.png')
        Color(.32,.6,.83,.30 if honeycomb else 0);hexes=Rectangle(texture=honeycomb,pos=widget.pos,size=widget.size)
        Color(.04,.14,.24,1);outer=Mesh(vertices=[],indices=[],mode='triangle_strip')
        Color(*accent);edge=Mesh(vertices=[],indices=[],mode='triangle_strip')
        Color(.17,.48,.72,.5);inner=Mesh(vertices=[],indices=[],mode='triangle_strip')
    def update(*_):
        x,y=widget.pos;w,h=widget.size;c=dp(9)
        bg.pos=hexes.pos=(x,y);bg.size=hexes.size=(w,h)
        points=[x+c,y,x+w-c,y,x+w,y+c,x+w,y+h-c,x+w-c,y+h,x+c,y+h,x,y+h-c,x,y+c,x+c,y]
        pairs=list(zip(points[::2],points[1::2]))
        stroke_mesh(pairs,dp(6),outer);stroke_mesh(pairs,dp(2.2),edge)
        left,bottom,right,top=x+dp(5),y+dp(5),x+w-dp(5),y+h-dp(5)
        stroke_mesh([(left,bottom),(right,bottom),(right,top),(left,top),(left,bottom)],dp(1.2),inner)
    widget.bind(pos=update,size=update);update()

class RelicCard(BoxLayout):
    def __init__(self,entry,category,select,shop=False,purchase=None,**kwargs):
        super().__init__(orientation='vertical',spacing=dp(6),padding=dp(13),**kwargs)
        self.entry=entry;self.category=category
        self.select_entry=select
        accent=(.4,.72,1,1)
        frame(self,accent)
        # SALE cards share the soft green fill of list rows, without a green frame.
        if shop and entry.get('sale'):
            with self.canvas.before:
                Color(.12,.24,.14,.48);sale_background=RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(9)]*4)
            self.bind(pos=lambda w,v:setattr(sale_background,'pos',v),
                      size=lambda w,v:setattr(sale_background,'size',v))
        with self.canvas.before:
            Color(.14,.48,.7,.13);dial=Mesh(vertices=[],indices=[],mode='triangle_strip')
            Color(.25,.58,.85,.16);dial2=Line(circle=(0,0,1,30,310),width=dp(1))
            Color(.18,.44,.68,.22);header=Rectangle(pos=self.pos,size=(0,0))
        def instrument(*_):
            radius=min(self.width*.44,self.height*.34)
            stroke_mesh([(self.center_x+radius*math.cos(math.radians(20+i*6.3)),self.center_y+radius*math.sin(math.radians(20+i*6.3))) for i in range(50)],dp(10),dial)
            dial2.points=[v for i in range(45) for v in (self.center_x+radius*.8*math.cos(math.radians(40+i*6.3)),self.center_y+radius*.8*math.sin(math.radians(40+i*6.3)))]
            header.pos=(self.x+dp(7),self.top-dp(64));header.size=(self.width-dp(14),dp(56))
        self.bind(pos=instrument,size=instrument);instrument()
        head=BoxLayout(size_hint_y=None,height=dp(47),spacing=dp(8))
        icon=Image(texture=shop_icon_texture(entry.get('canonical_name',entry['id']),entry.get('icon',''),category),size_hint_x=None,width=dp(44))
        # A missing portrait is genuinely absent (not a white default-image tile).
        # The Spear of Adun unlock deliberately has no icon.
        if icon.texture is not None:
            head.add_widget(icon)
        card_title = '[b]'+entry['name']+'[/b]'
        if shop and entry.get('sale'):
            card_title += '  [color=7CFF9B][b]SALE[/b][/color]'
        if shop and entry.get('frozen'):
            card_title += '  [color=82DFF5][b]FROZEN[/b][/color]'
        self.title_label=label(card_title,halign='left',valign='middle',font_size=dp(15))
        head.add_widget(self.title_label)
        self.add_widget(head)
        desc=tr(entry.get('description',''))
        # Full text remains available in the right-side inspector on selection.
        preview=desc[:108]+('…' if len(desc)>108 else '')
        self.add_widget(label(preview,halign='left',valign='top',font_size=dp(13)))
        summary=('Limited-time Discount' if entry.get('sale') else tr(category)) if shop else f"Owned ×{entry.get('total',1)}"
        self.add_widget(label(summary,color=(.44,.78,1,1),size_hint_y=None,height=dp(24),halign='left'))
        actions=BoxLayout(size_hint_y=None,height=dp(35),spacing=dp(5))
        detail=control('Details',lambda *_:select(entry),size_hint_x=.30)
        actions.add_widget(detail)
        if shop:
            buy=control('',lambda *_:purchase(entry['id'],1),font_size=dp(13))
            buy.slay_sound='command'
            buy.slay_item_id=entry['id'];self.purchase_button=buy;actions.add_widget(buy)
            self.buy5_button=None
            if entry.get('buy_five'):
                self.buy5_button=control('Buy 5',lambda *_:purchase(entry['id'],5),font_size=dp(12))
                self.buy5_button.slay_sound='command'
                actions.add_widget(self.buy5_button)
        else:
            if entry.get('revive_cost') is not None and entry.get('destroyed',0)>0:
                cost=entry['revive_cost']
                actions.add_widget(control(f'Revive 1 · {cost}c',
                    lambda *_:purchase(entry['id'],1),font_size=dp(9),size_hint_x=.5,
                    size_hint_y=None,height=dp(18)))
                if entry['destroyed']>=5:
                    actions.add_widget(control(f'Revive 5 · {cost*5}c',
                        lambda *_:purchase(entry['id'],5),font_size=dp(9),size_hint_x=.5,
                        size_hint_y=None,height=dp(18)))
            origins=[]
            if entry.get('ap_count'):origins.append(f"Supplies {entry['ap_count']}")
            if entry.get('shop_count'):origins.append(f"Purchased {entry['shop_count']}")
            actions.add_widget(label(' · '.join(origins) or 'Acquired',font_size=dp(12)))
        self.add_widget(actions)

    def on_touch_up(self,touch):
        if super().on_touch_up(touch):return True
        if self.collide_point(*touch.pos):
            self.select_entry(self.entry);return True
        return False

class RelicRow(BoxLayout):
    def __init__(self,entry,category,select,shop=False,purchase=None,compact=False,**kwargs):
        super().__init__(orientation='horizontal',spacing=dp(5 if compact else 12),padding=dp(4 if compact else 10),**kwargs)
        self.entry = entry
        self.select_entry = select
        panel(self,color=(.13,.23,.16,1) if shop and entry.get('sale') else SECTION_PALETTE.get(category,(.025,.065,.105,1)))
        portrait = shop_icon_texture(entry.get('canonical_name',entry['id']), entry.get('icon',''), category)
        if portrait is not None:
            self.add_widget(Image(texture=portrait,size_hint_x=None,width=dp(42 if compact else 48)))
        text=BoxLayout(orientation='vertical',spacing=dp(4))
        row_title='[b]'+entry['name']+'[/b]'
        if shop and entry.get('sale'):
            row_title+='  [color=7CFF9B][b]SALE[/b][/color]'
        if shop and entry.get('frozen'):
            row_title+='  [color=82DFF5][b]FROZEN[/b][/color]'
        title=label(row_title,halign='left',valign='top',auto_height=True,size_hint_y=None,height=dp(23 if compact else 26),font_size=dp(14 if compact else 15))
        self.title_label=title
        title.bind(texture_size=lambda w,s:setattr(w,'height',max(dp(23 if compact else 26),s[1])))
        text.add_widget(title)
        description=label(entry.get('description',''),halign='left',valign='top',auto_height=True,size_hint_y=None)
        description.bind(texture_size=lambda w,s:setattr(w,'height',max(dp(22 if compact else 28),s[1])))
        text.add_widget(description)
        text.bind(minimum_height=lambda w,h:setattr(self,'height',max(dp(88 if compact else 108),h+dp(14 if compact else 20))))
        self.add_widget(text)
        actions=BoxLayout(orientation='vertical',spacing=dp(6),size_hint_x=None,width=dp(200 if entry.get('crew_inventory') else (155 if compact else 174)))
        if not compact:actions.add_widget(control('Details',lambda *_:select(entry),size_hint_y=None,height=dp(32)))
        if not shop and entry.get('crew_inventory') and entry.get('revive_cost') is not None and entry.get('destroyed',0)>0:
            cost=entry['revive_cost']
            row=BoxLayout(orientation='horizontal',size_hint_y=None,height=dp(23),spacing=dp(4))
            row.add_widget(control(f'Revive 1 · {cost}c',
                lambda *_:purchase(entry['id'],1),font_size=dp(10)))
            row.add_widget(control(f'Revive 5 · {cost*5}c',
                lambda *_:purchase(entry['id'],5),font_size=dp(10),
                disabled=entry['destroyed']<5))
            actions.add_widget(row)
        if shop:
            self.purchase_button=control('',lambda *_:purchase(entry['id'],1),font_size=dp(12),size_hint_y=None,height=dp(40 if compact else 46),halign='center',valign='middle')
            self.purchase_button.bind(size=lambda w,s:setattr(w,'text_size',(max(dp(1),s[0]-dp(10)),s[1])))
            self.purchase_button.slay_sound='command'
            self.purchase_button.slay_item_id=entry['id']
            actions.add_widget(self.purchase_button)
            self.buy5_button=None
            if entry.get('buy_five'):
                self.buy5_button=control('Buy 5',lambda *_:purchase(entry['id'],5),font_size=dp(12),size_hint_y=None,height=dp(35))
                self.buy5_button.slay_sound='command'
                actions.add_widget(self.buy5_button)
        else:
            if not entry.get('crew_inventory') and entry.get('revive_cost') is not None and entry.get('destroyed',0)>0:
                cost=entry['revive_cost']
                actions.add_widget(control(f'Revive 1 · {cost}c',
                    lambda *_:purchase(entry['id'],1),font_size=dp(9),size_hint_x=None,
                    width=dp(77),size_hint_y=None,height=dp(19)))
                if entry['destroyed']>=5:
                    actions.add_widget(control(f'Revive 5 · {cost*5}c',
                        lambda *_:purchase(entry['id'],5),font_size=dp(9),size_hint_x=None,
                        width=dp(77),size_hint_y=None,height=dp(19)))
            actions.add_widget(label(f"Owned ×{entry.get('total',1)}",size_hint_y=None,height=dp(24)))
            origins=[]
            if entry.get('ap_count'):origins.append(f"Supplies {entry['ap_count']}")
            if entry.get('shop_count'):origins.append(f"Purchased {entry['shop_count']}")
            actions.add_widget(label(' · '.join(origins) or 'Acquired',size_hint_y=None,height=dp(24),font_size=dp(12)))
        # No secondary Technology buttons on units, structures, detectors, or
        # other shop rows. The detail inspector can still display relevant
        # upgrades without consuming vertical room in every list entry.
        self.add_widget(actions)

    def on_touch_up(self, touch):
        if super().on_touch_up(touch):
            return True
        if self.collide_point(*touch.pos):
            self.select_entry(self.entry)
            return True
        return False

class CardConsole:
    def __init__(self,manager,shop,sections,entries,sale_items=(),crew=False):
        self.manager=manager;self.shop=shop;self.sections=sections;self.entries=entries
        self.crew=crew
        self.category=getattr(manager,'slay_card_shop_category' if shop else 'slay_card_inventory_category',None)
        self.page=0;self.page_size=8;self.card_widgets={};self.sale_items=set(sale_items)
        self.freeze_select_mode = False
        self.view_key='slay_shop_view_mode' if shop else 'slay_inventory_view_mode'
        self.view_mode='list' if crew else getattr(manager,self.view_key,'list')
        self.page_size=16 if self.view_mode=='list' else 8
        # Stock Popup's default nine-slice modal frame and empty background
        # produced a wide light rim around the otherwise dark Slay shop.
        # The custom title row below owns the heading; omit the Kivy title bar.
        self.popup=Popup(title='', size_hint=(.998,.998),
                         background=str(ASSETS/'shop_popup_background.png'),
                         background_color=(1,1,1,1), border=(0,0,0,0),
                         separator_height=0, title_size=0)
        root=BoxLayout(orientation='vertical',spacing=dp(3),padding=[dp(2),0,dp(2),dp(1)]);panel(root,border=False)
        top=BoxLayout(size_hint_y=None,height=dp(34),spacing=dp(8))
        top.add_widget(BoxLayout(size_hint_x=None,width=dp(17)))
        top.add_widget(label('[b]Shop[/b]' if shop else ('[b]Crew Reserves[/b]' if crew else '[b]Supply Inventory[/b]'),font_size=dp(23),halign='left'))
        self.credit=label('',halign='right');top.add_widget(self.credit)
        if crew and not shop:
            from worlds.sc2 import slay_the_starcraft as slay
            self.credit.text=f'[b]Credits: {slay.credits(manager.ctx)}[/b]'
        self.view_button=control('',lambda *_:self.toggle_view(),size_hint_x=None,width=dp(145))
        if not crew:top.add_widget(self.view_button)
        if shop:
            self.freeze_button = control('Freeze', lambda *_: self.toggle_freeze(), size_hint_x=None, width=dp(170))
            top.add_widget(self.freeze_button)
            top.add_widget(control('Inventory',lambda *_:self.navigate_to('inventory'),size_hint_x=None,width=dp(145)))
            top.add_widget(control('Exit Shop',lambda *_:self.close(),size_hint_x=None,width=dp(170)))
        else:
            # View mode -> Shop -> Exit Inventory. Keep navigation explicit;
            # never bind one-off screen changes to the same dismissal event
            # that rerolls and standard Close use.
            top.add_widget(control('Shop',lambda *_:self.navigate_to('shop'),size_hint_x=None,width=dp(145)))
            top.add_widget(control('Exit Inventory',lambda *_:self.close(),size_hint_x=None,width=dp(170)))
        root.add_widget(top)
        body=BoxLayout(spacing=dp(14))
        sidebar_scroll=ScrollView(size_hint_x=None,width=dp(170),do_scroll_x=False)
        self.sidebar=BoxLayout(orientation='vertical',size_hint_y=None,spacing=dp(6))
        self.sidebar.bind(minimum_height=self.sidebar.setter('height'))
        self.category_buttons={}
        for category,names in sections:
            b=control(f'{tr(category)}  {len(names)}',lambda _,c=category:self.change_category(c),size_hint_y=None,height=dp(42))
            self.category_buttons[category]=b;self.sidebar.add_widget(b)
        sidebar_scroll.add_widget(self.sidebar);body.add_widget(sidebar_scroll)
        center=BoxLayout(orientation='vertical',spacing=dp(10))
        self.heading=label('',size_hint_y=None,height=dp(29),halign='left',font_size=dp(18));center.add_widget(self.heading)
        self.scroll=ScrollView(do_scroll_x=False)
        self.grid=GridLayout(cols=4,size_hint_y=None,spacing=dp(10),padding=dp(4),row_default_height=dp(255),row_force_default=True)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid);center.add_widget(self.scroll)
        pages=BoxLayout(size_hint_y=None,height=dp(37),spacing=dp(10))
        self.prev=control('Previous',lambda *_:self.change_page(-1));self.counter=label('');self.next=control('Next',lambda *_:self.change_page(1))
        for w in (self.prev,self.counter,self.next):pages.add_widget(w)
        self.pages=pages;self.sidebar_scroll=sidebar_scroll
        center.add_widget(pages);body.add_widget(center)
        inspect=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(10),size_hint_x=None,width=dp(240));frame(inspect)
        self.inspect_icon=Image(size_hint_y=None,height=dp(112))
        self.inspect_title=label('Select a card to view details',size_hint_y=None,height=dp(65),font_size=dp(19),halign='left')
        self.inspect_text=label('Select a category on the left. Prices and quantities appear below each card.',halign='left',valign='top',size_hint_y=None,auto_height=True)
        self.inspect_text.bind(texture_size=lambda w,s:setattr(w,'height',max(dp(100),s[1]+dp(8))))
        self.inspect_text.bind(width=lambda w,v:setattr(w,'text_size',(v,None)))
        detail_scroll=ScrollView(do_scroll_x=False);detail_scroll.add_widget(self.inspect_text)
        for w in (self.inspect_icon,self.inspect_title,detail_scroll):inspect.add_widget(w)
        self.tech_panel=BoxLayout(orientation='vertical',size_hint_y=None,height=0)
        inspect.add_widget(self.tech_panel)
        body.add_widget(inspect);self.inspector=inspect;root.add_widget(body)
        self.popup.content=root;self.popup.slay_scroll=self.scroll;self.popup.slay_purchase_buttons={}
        self.popup.slay_credit_label=self.credit;self.popup.slay_console=self
        self.popup.bind(size=self.resize)
        if not self.category or self.category not in dict(sections):self.category=sections[0][0] if sections else ''
        self.render()
        self.resize()

    def purchase(self, item_id, quantity=1):
        from worlds.sc2 import slay_the_starcraft as slay
        if not self.crew:
            return self.manager._slay_buy(item_id,self.popup)
        if not self.shop:
            e=self.entries.get(item_id)
            if not e or e.get('revive_cost') is None:return
            try:
                amount,ids=slay.crew_revive_destroyed(self.manager.ctx,
                    e['roster_name'],e['race'],e['crew_kind'],quantity)
                self.crew_feedback=f'Revived {len(ids)} × {e["name"]} for {amount} credits.'
                # Reopen a fresh inventory to recalculate lost/ready counts.
                self.popup.slay_navigate_to='inventory'
                self.popup.dismiss()
            except Exception as exc:
                self.credit.text='Revive unavailable: '+str(exc)
            return
        entry=self.entries.get(item_id)
        if entry is None or not self.shop:return
        try:
            kind=entry.get('crew_kind')
            if kind in ('unit','structure'):
                cost,ids=slay.crew_purchase_roster_copy(self.manager.ctx,entry['roster_name'],
                    entry['race'],kind,entry['supply'],entry['minerals'],entry['gas'],quantity=quantity)
                msg=f'Purchased {len(ids)} × {entry["name"]} for {cost} credits; added to Reserves.'
            elif kind=='upgrade':
                if quantity!=1:return
                ok,msg=slay.crew_purchase_upgrade(self.manager.ctx,item_id)
                if not ok:raise ValueError(msg)
            elif kind=='boon':
                if quantity!=1:return
                ok,msg=slay.crew_purchase_boon(self.manager.ctx,item_id)
                if not ok:raise ValueError(msg)
            else:return
            # Preserve the normal Standard shop renderer; only refresh the
            # Crew-specific purchase eligibility and credit caption.
            self.crew_feedback=msg
            roster=slay.crew_roster(self.manager.ctx)
            for row in self.entries.values():
                row_kind=row.get('crew_kind')
                if row_kind in ('unit','structure'):
                    name=row.get('roster_name')
                    count=sum(c['name']==name and c.get('status')!='lost'
                              for c in roster['copies'])
                elif row_kind=='upgrade':
                    count=slay.purchased_count(self.manager.ctx,row['id'])
                else:continue
                row['owned_count']=count
                display=row.get('roster_name') or slay.shop_entry_display_name(row['id'])
                row['name']=str(display)+(f'  (already owned: {count})' if row.get('show_owned_count',True) else '')
            # Buying does not change the rolled offers or rebuild textures/widgets.
            # Reroll/victory is the only event that rebuilds Crew's whole shop.
            for ident,card in self.card_widgets.items():
                e=self.entries[ident]
                title=getattr(card,'title_label',None)
                if title is not None:
                    caption='[b]'+e['name']+'[/b]'
                    if e.get('frozen'):caption+='  [color=82DFF5][b]FROZEN[/b][/color]'
                    title.text=caption
            self.refresh_crew_controls()
        except Exception as exc:
            self.crew_feedback='Purchase unavailable: '+str(exc)
            self.refresh_crew_controls()

    def refresh_crew_controls(self):
        if not self.crew or not self.shop:return
        from worlds.sc2 import slay_the_starcraft as slay
        # Some legacy embedded shop adapters expose costs but no live roster.
        # Production Crew always has a ledger; this guard retains compatibility.
        roster_provider=getattr(slay,'crew_roster',None)
        roster=roster_provider(self.manager.ctx) if callable(roster_provider) else None
        for ident,e in self.entries.items() if roster is not None else ():
            card=self.card_widgets.get(ident)
            kind=e.get('crew_kind')
            if kind in ('unit','structure'):
                new_count=sum(c['name']==e.get('roster_name') and c.get('status')!='lost'
                              for c in roster.get('copies',()))
            elif kind=='upgrade':
                new_count=slay.purchased_count(self.manager.ctx,ident)
            else:continue
            if e.get('owned_count')!=new_count:
                e['owned_count']=new_count
                display=e.get('roster_name') or slay.shop_entry_display_name(ident)
                e['name']=str(display)+(f'  (already owned: {new_count})' if e.get('show_owned_count',True) else '')
                title=getattr(card,'title_label',None) if card is not None else None
                if title is not None:title.text='[b]'+e['name']+'[/b]'
        budget=slay.credits(self.manager.ctx)
        self.credit.text=f'[b]Credits: {budget}[/b]  {getattr(self,"crew_feedback","")}'
        # The popup owns a frozen offer snapshot. Recomputing the entire AP
        # shop candidate pool on every refresh was both slow and capable of
        # disabling unrelated offers when a purchase changed eligibility.
        # Use the rolled offers from this popup, not a new random shop roll.
        # Dev69 accidentally removed this binding, raising NameError when
        # opening a Crew shop (and interrupting the surrounding modal).
        boon_ids={ident for ident,row in self.entries.items()
                  if row.get('crew_kind')=='boon'}
        table=None
        for ident,card in self.card_widgets.items():
            e=self.entries[ident]
            kind=e.get('crew_kind')
            if kind in ('unit','structure'):
                cost=e['credits']
                allowed=True
            elif kind=='boon':
                cost=e['credits']
                allowed=ident in boon_ids and slay.can_buy_shop_item(self.manager.ctx,ident)
            elif kind=='upgrade':
                cost=slay.crew_upgrade_price(self.manager.ctx, ident)
                e['credits']=cost
                # This offer was valid when the cycle was rolled. Only this
                # item's OWN purchase cap can disable it; a different upgrade
                # must never invalidate the active card.
                if table is None:table=slay._item_table()
                data=table.get(ident)
                cap=slay._max_owned_copies(data) if data is not None else None
                count=slay.purchased_count(self.manager.ctx,ident)
                allowed=(data is not None and (cap is None or
                    slay._effective_shop_copies(ident,count)<cap))
            else:
                continue
            btn=card.purchase_button
            btn.text=f'Buy 1 ({cost} credits)'
            btn.disabled=not allowed or budget<cost
            if getattr(card,'buy5_button',None) is not None:
                card.buy5_button.disabled=budget<5*cost
                card.buy5_button.text=f'Buy 5 ({5*cost} credits)'

    def toggle_freeze(self):
        self.freeze_select_mode = not self.freeze_select_mode
        self.render()

    def choose_entry(self, entry):
        if not self.shop or not self.freeze_select_mode:
            self.inspect(entry)
            return
        from worlds.sc2 import slay_the_starcraft as slay
        name = entry.get('freeze_name',entry['id']) if self.crew else entry['id']
        # Selecting another frozen offer automatically unfreezes the old one.
        # Selecting the same offer again clears its frozen status.
        selected = "" if name == slay.frozen_shop_item(self.manager.ctx) else name
        if slay.freeze_shop_item(self.manager.ctx, selected):
            for row in self.entries.values():
                row['frozen'] = bool(selected and (row.get('freeze_name',row['id']) if self.crew else row['id']) == selected)
            self.freeze_select_mode = False
            self.render()
            self.inspect(entry)

    def navigate_to(self, destination):
        # A single authoritative transition, handled by the popup's regular
        # dismissal listener. Never attach an accumulating on_dismiss lambda.
        if destination not in ('inventory', 'shop'):
            return
        self.popup.slay_navigate_to = destination
        if self.shop:
            self.manager.slay_shop_reopen_pending = False
        self.popup.dismiss()

    def close(self):
        self.popup.slay_navigate_to = None
        if self.shop:
            self.manager.slay_shop_reopen_pending = False
        _command_ui_log('Card shop/inventory close requested')
        # A dismissal veto or the current touch-dispatch frame must not strand
        # a nearly fullscreen modal above the command interface.
        Clock.schedule_once(lambda _dt: self.popup.dismiss(force=True), 0)

    def resize(self,*_):
        # Keep all eight cards on comfortable desktop widths; narrow windows use three columns.
        width=self.popup.width
        overview=self.view_mode=='list'
        self.inspector.width=0 if overview else dp(240) if width>dp(1200) else dp(195)
        self.inspector.opacity=0 if overview else 1
        self.inspector.disabled=overview
        self.sidebar_scroll.width=0 if overview else dp(170) if width>dp(1200) else dp(140)
        self.sidebar_scroll.opacity=0 if overview else 1
        self.sidebar_scroll.disabled=overview
        self.pages.height=0 if overview else dp(37)
        self.pages.opacity=0 if overview else 1
        self.pages.disabled=overview
        # List overview already has category headings in each column.
        # Hide the redundant "All Categories" strip and reclaim its height.
        self.heading.height=0 if overview and self.shop else dp(29)
        self.heading.opacity=0 if overview and self.shop else 1
        # The list overview mirrors the original four-column shop/inventory layout.
        # Keep four columns even during the Popup's tiny pre-open geometry pass; otherwise
        # the first render permanently creates too few column holders until view toggling.
        cols=4 if overview else (4 if width>dp(1350) else 3 if width>dp(1000) else 2)
        if self.grid.cols!=cols:self.grid.cols=cols
        self.grid.row_force_default=self.view_mode!='list'
        self.grid.row_default_height=0 if self.view_mode=='list' else dp(250) if self.popup.height>dp(760) else dp(235)

    def toggle_view(self):
        self.view_mode='list' if self.view_mode=='cards' else 'cards'
        setattr(self.manager,self.view_key,self.view_mode)
        self.page_size=16 if self.view_mode=='list' else 8
        self.page=0
        self.resize()
        self.render()

    def change_category(self,category):
        self.category=category;self.page=0;self.render()

    def change_page(self,delta):
        self.page+=delta;self.render()

    def inspect(self,entry):
        self.inspect_icon.texture=shop_icon_texture(entry.get('canonical_name',entry['id']),entry.get('icon',''),self.category)
        has_icon = self.inspect_icon.texture is not None
        self.inspect_icon.height=dp(112) if has_icon else 0
        self.inspect_icon.opacity=1 if has_icon else 0
        self.inspect_title.text=entry['name']
        self.inspect_text.text=entry.get('description','') or 'This relic is active.'
        self.tech_panel.clear_widgets()
        grid=None if self.crew else technology_grid(self.manager.ctx,entry.get('canonical_name',entry['id']))
        self.tech_panel.height=dp(180) if grid else 0
        if grid:
            self.tech_panel.add_widget(label('Related Technology',size_hint_y=None,height=dp(22),font_size=dp(12),halign='left'))
            scroll=ScrollView(do_scroll_x=False);scroll.add_widget(grid);self.tech_panel.add_widget(scroll)

    def render(self):
        from worlds.sc2 import slay_the_starcraft as slay
        self.view_button.text=('Show Cards' if self.view_mode=='list' else 'Show List') if LANGUAGE=='zhCN' else ('Show Cards' if self.view_mode=='list' else 'Show List')
        if self.shop:
            from worlds.sc2 import slay_the_starcraft as slay
            self.freeze_button.text = ('Select Item...' if self.freeze_select_mode
                                       else 'Freeze (1)' if slay.frozen_shop_item(self.manager.ctx)
                                       else 'Freeze Item')
        self.resize()
        if self.view_mode=='list':
            self.render_overview()
            return
        names=dict(self.sections).get(self.category,[]);pages=max(1,math.ceil(len(names)/self.page_size));self.page=max(0,min(self.page,pages-1))
        setattr(self.manager,'slay_card_shop_category' if self.shop else 'slay_card_inventory_category',self.category)
        self.heading.text='[b]'+tr(self.category or 'Supplies')+'[/b]'
        self.counter.text=f'{self.page+1} / {pages}';self.prev.disabled=self.page==0;self.next.disabled=self.page>=pages-1
        for c,b in self.category_buttons.items():b.background_color=(.45,.85,1,1) if c==self.category else (1,1,1,1)
        page_names=names[self.page*self.page_size:(self.page+1)*self.page_size]
        # Decode every image first, then replace the entire card page in one event.
        for name in page_names:
            entry=self.entries[name]
            texture(local_icon(entry.get('canonical_name',name),entry.get('icon',''),self.category))
        self.grid.clear_widgets();self.popup.slay_purchase_buttons={};self.card_widgets={}
        for name in page_names:
            entry=self.entries[name]
            widget_class=RelicRow if self.view_mode=='list' else RelicCard
            card=widget_class(entry,self.category,self.choose_entry,self.shop,self.purchase,size_hint_y=None,height=dp(108 if self.view_mode=='list' else 255))
            self.grid.add_widget(card);self.card_widgets[name]=card
            if self.shop:self.popup.slay_purchase_buttons[name]=card.purchase_button
        if not page_names:self.grid.add_widget(label('No supplies in this category.',size_hint_y=None,height=dp(180)))
        if page_names:self.inspect(self.entries[page_names[0]])
        self.scroll.scroll_y=1
        if self.shop:
            if self.crew:self.refresh_crew_controls()
            else:self.manager._slay_refresh_shop_controls(self.popup)
        else:
            if self.crew:self.credit.text=f'[b]Credits: {slay.credits(self.manager.ctx)}[/b]'
            else:self.credit.text=f'Catalogued {len(self.entries)} supply types'

    def render_overview(self):
        from worlds.sc2 import slay_the_starcraft as slay
        for name,entry in self.entries.items():texture(local_icon(entry.get('canonical_name',name),entry.get('icon','')))
        self.grid.clear_widgets();self.popup.slay_purchase_buttons={};self.card_widgets={}
        self.heading.text='' if self.shop else 'All Categories'
        columns=[];holders=[]
        for _ in range(self.grid.cols):
            holder=FloatLayout(size_hint_y=None,height=dp(1))
            column=BoxLayout(orientation='vertical',size_hint_y=None,spacing=dp(10),pos_hint={'x':0,'top':1})
            column.bind(minimum_height=column.setter('height'))
            holder.add_widget(column);self.grid.add_widget(holder)
            holders.append(holder);columns.append(column)
        def align_columns(*_):
            height=max(dp(1),*(column.height for column in columns))
            for holder in holders:holder.height=height
        for column in columns:column.bind(height=align_columns)
        section_columns=SHOP_SECTION_COLUMNS if self.shop else INVENTORY_SECTION_COLUMNS
        for category,names in self.sections:
            if category=='Current Discounts' or not names:continue
            # Crew's four-column overview: structures fill columns 1 and 2,
            # all racial units/upgrades fill column 3, boons column 4.
            # Standard shop/inventory is unchanged.
            chunks=[(min(section_columns.get(category,2),len(columns)-1),names,category)]
            if self.crew:
                if category.endswith('Structures'):
                    half=(len(names)+1)//2
                    chunks=[(0,names[:half],category+' (1/2)'),
                            (1,names[half:],category+' (2/2)')]
                elif category.endswith('Units') or category.endswith('Upgrades'):
                    chunks=[(2,names,category)]
                elif category=='Boons':
                    chunks=[(3,names,category)]
            for index,names,display_category in chunks:
                if not names:continue
                self._render_overview_group(columns,index,category,display_category,names)
        align_columns()
        self.scroll.scroll_y=1
        if self.shop:
            if self.crew:self.refresh_crew_controls()
            else:self.manager._slay_refresh_shop_controls(self.popup)
        else:
            if self.crew:self.credit.text=f'[b]Credits: {slay.credits(self.manager.ctx)}[/b]'
            else:self.credit.text=f'Catalogued {len(self.entries)} supply types'

    def _render_overview_group(self, columns, index, category, display_category, names):
        group=BoxLayout(orientation='vertical',size_hint_y=None,padding=dp(4),spacing=dp(3))
        group.bind(minimum_height=group.setter('height'))
        panel(group,color=SECTION_PALETTE.get(category,(.18,.18,.18,1)))
        heading = '[b]'+tr(display_category)+'[/b]'
        if category == 'Consumables':
            from worlds.sc2 import slay_the_starcraft as slay
            count = len(slay.potion_inventory(self.manager.ctx))
            heading += f'     [color=82DFF5]Available slots: {max(0, slay.POTION_CAPACITY - count)}/{slay.POTION_CAPACITY}[/color]'
        heading_label=label(heading,size_hint_y=None,height=dp(26),font_size=dp(13))
        if category == 'Consumables' and self.shop:
            self.popup.slay_consumable_slots_label=heading_label
        group.add_widget(heading_label)
        for name in names:
            entry=self.entries[name]
            row=RelicRow(entry,category,self.choose_entry,self.shop,self.purchase,compact=True,size_hint_y=None,height=dp(156 if entry.get('revive_cost') is not None and entry.get('destroyed',0)>=5 else 132 if entry.get('revive_cost') is not None and entry.get('destroyed',0)>0 else 105 if entry.get('buy_five') else 88))
            group.add_widget(row);self.card_widgets[name]=row
            if self.shop:self.popup.slay_purchase_buttons[name]=row.purchase_button
        columns[index].add_widget(group)

def open_crew_console(manager, shop):
    """Crew uses Standard's CardConsole, not a separate prototype UI.

    Credits, purchases and Reserves are Crew-specific; palette, artwork,
    descriptions, layout, navigation and inspector are the Standard renderer.
    """
    from worlds.sc2 import slay_the_starcraft as slay
    if not slay.state_ready(manager.ctx):return
    def racial_section(race,kind):
        prefix={'terran':'Terran','zerg':'Zerg','protoss':'Protoss'}.get(race,'Terran')
        return prefix+' '+kind
    sections=OrderedDict()
    entries={}
    if shop:
        # Capture the roster once. Its normalization and SC2 receipt status
        # checks are expensive and are identical for every displayed offer.
        roster=slay.crew_roster(manager.ctx)
        groups=slay.crew_catalog_offers(manager.ctx)
        for source in ('Structures','Units','Unit Upgrades'):
            for index,offer in enumerate(groups.get(source,())):
                race=offer.get('race','terran')
                kind=('Structures' if source=='Structures' else
                      'Units' if source=='Units' else 'Upgrades')
                category=racial_section(race,kind)
                key=('crew:'+race+':'+offer['name'] if source!='Unit Upgrades'
                     else offer['id'])
                if source=='Unit Upgrades':
                    desc=offer.get('description','') or slay.shop_entry_description(offer['id'])
                    item_kind='upgrade'
                else:
                    desc=slay.crew_shop_description(offer)
                    item_kind=('unit' if offer['category']=='unit' or
                               offer['name'] in ('SCV','Probe','Drone') else 'structure')
                count=(slay.purchased_count(manager.ctx,offer['id']) if item_kind=='upgrade'
                       else sum(c['name']==offer['name'] and c.get('status')!='lost'
                                for c in roster['copies']))
                entry={'id':key,'canonical_name':offer.get('id',offer['name']),
                       'name':offer['name']+(f'  (already owned: {count})' if (item_kind!='upgrade' or offer.get('show_owned_count',True)) else ''),'description':desc,
                       'icon':slay.shop_entry_icon(offer.get('id',offer['name'])),
                       'credits':int(offer['credits']),
                       'race':race,'crew_kind':item_kind,
                       'buy_five':item_kind=='unit',
                       'roster_name':offer['name'], 'owned_count':count,
                       'show_owned_count':(item_kind!='upgrade' or offer.get('show_owned_count',True)),
                       'freeze_name':offer['name'] if item_kind in ('unit','structure') else key,
                       'frozen':slay.frozen_shop_item(manager.ctx)==(offer['name'] if item_kind in ('unit','structure') else key),
                       'minerals':offer.get('minerals',0),'gas':offer.get('gas',0),
                       'supply':offer.get('supply',0)}
                entries[key]=entry
                sections.setdefault(category,[]).append(key)
        for offer in slay.crew_boon_offers(manager.ctx):
            key=offer['id']
            entries[key]={'id':key,'canonical_name':key,'name':offer['name'],
                          'description':offer.get('description',''),
                          'icon':slay.shop_entry_icon(key),
                          'credits':int(offer['credits']),
                          'crew_kind':'boon','race':'boon','buy_five':False,
                          'frozen':slay.frozen_shop_item(manager.ctx)==key}
            sections.setdefault('Boons',[]).append(key)
    else:
        for idx,entry in enumerate(slay.crew_inventory_groups(manager.ctx)):
            kind=entry['kind']
            category=racial_section(entry['race'],'Units' if kind=='unit' else 'Structures')
            key='reserves:'+str(idx)
            desc=(f"Reserves: {entry['ready']}     On field: {entry['on_field']}     "
                  f"Pending verification: {entry['claimed']}     Destroyed: {entry['destroyed']}")
            revive_cost=(slay.crew_revive_unit_price(entry['name'], entry['race'])
                         if kind=='unit' else None)
            entries[key]={'id':key,'canonical_name':entry['name'],
                          'crew_kind':kind,'roster_name':entry['name'],'race':entry['race'],
                          'destroyed':entry['destroyed'],'revive_cost':revive_cost,
                          'crew_inventory':True,
                          'name':entry['name'],'description':desc,
                          'total':entry['available_total'],'icon':slay.shop_entry_icon(entry['name'])}
            sections.setdefault(category,[]).append(key)
        for category,items in slay.crew_owned_effects(manager.ctx).items():
            for idx,name in enumerate(items):
                key=f'crew-owned:{category}:{idx}'
                entries[key]={'id':key,'canonical_name':name,'name':name,
                              'description':slay.shop_entry_description(name),
                              'icon':slay.shop_entry_icon(name),'total':1}
                sections.setdefault(category,[]).append(key)
    # Persist the same card/list toggle across Crew and Standard modes.
    manager._slay_begin_modal()
    console=CardConsole(manager,shop,list(sections.items()),entries,crew=True)
    popup=console.popup
    if shop:manager.slay_shop_popup=popup
    else:manager.slay_inventory_popup=popup
    current_description={k:e.get('description') for k,e in entries.items()}
    if not shop:
        initial_inventory_names=tuple((r['name'],r['race'],r['kind'])
                                      for r in slay.crew_inventory_groups(manager.ctx))
        def refresh_inventory(_dt):
            if not getattr(popup,'_is_open',False):return
            console.credit.text=f'[b]Credits: {slay.credits(manager.ctx)}[/b]'
            rows=slay.crew_inventory_groups(manager.ctx)
            # New mid-mission prizes/adopted types introduce new inventory
            # categories and rows, not just updated counters. A simple
            # description rerender cannot create them; reopen the same panel.
            keys=tuple((r['name'],r['race'],r['kind']) for r in rows)
            if keys!=initial_inventory_names:
                popup.slay_navigate_to='inventory'
                popup.dismiss()
                return
            for idx,row in enumerate(rows):
                key='reserves:'+str(idx)
                e=console.entries.get(key)
                if e is None:return
                desc=(f"Reserves: {row['ready']}     On field: {row['on_field']}     "
                      f"Pending verification: {row['claimed']}     Destroyed: {row['destroyed']}")
                if current_description.get(key)!=desc:
                    current_description[key]=desc
                    e['description']=desc
                    e['total']=row['available_total']
                    # Only rerender when counts change; avoid an every-second
                    # scroll reset while inspecting a large inventory.
                    previous_scroll=console.scroll.scroll_y
                    console.render()
                    console.scroll.scroll_y=previous_scroll
                    return
        watcher=Clock.schedule_interval(refresh_inventory,1.0)
    else:
        # A reroll can be purchased from the main Slay UI while this popup
        # remains open. Rebuild immediately on the next UI poll, rather than
        # leaving disabled/stale cards until the player manually closes it.
        start_cycle=(slay.victory_count(manager.ctx),
            int(slay.state(manager.ctx).get('shop_reroll_nonce',0)),
            int(slay.state(manager.ctx).get('shop_expansion',0)))
        def refresh_shop_cycle(_dt):
            if not getattr(popup,'_is_open',False):return
            now_cycle=(slay.victory_count(manager.ctx),
                int(slay.state(manager.ctx).get('shop_reroll_nonce',0)),
                int(slay.state(manager.ctx).get('shop_expansion',0)))
            if now_cycle==start_cycle:
                console.refresh_crew_controls()
                return
            popup.slay_navigate_to='shop'
            popup.dismiss()
        watcher=Clock.schedule_interval(refresh_shop_cycle,0.35)
    def dismissed(_pop):
        if watcher is not None:watcher.cancel()
        if getattr(manager,'slay_shop_popup',None) is popup:manager.slay_shop_popup=None
        if getattr(manager,'slay_inventory_popup',None) is popup:manager.slay_inventory_popup=None
        manager._slay_end_modal()
        dest=getattr(popup,'slay_navigate_to',None)
        if dest in ('shop','inventory'):
            Clock.schedule_once(lambda _dt:open_console(manager,dest=='shop'),0)
    popup.bind(on_dismiss=dismissed)
    popup.open()

def open_console(manager,shop):
    from worlds.sc2 import slay_the_starcraft as slay
    if not slay.enabled(manager.ctx):return
    if slay.crew_mode(manager.ctx):
        if (shop and getattr(manager,'slay_shop_popup',None)) or (not shop and getattr(manager,'slay_inventory_popup',None)):
            return
        return open_crew_console(manager,shop)
    if shop and getattr(manager,'slay_shop_popup',None):return
    if not shop and getattr(manager,'slay_inventory_popup',None):return
    if not slay.state_ready(manager.ctx):
        pop=Popup(title='Loading Adventure',content=label('Adventure data is loading. Please try again shortly.'),size_hint=(.55,.35));pop.open();return
    # Bank acknowledgement is authoritative and may have changed since a
    # previous in-game HUD poll. Refresh *before* building shop headings.
    slay.refresh_consumable_slots(manager.ctx)
    manager._slay_begin_modal()
    entries={}
    if shop:
        # Initialize actual stock first. Otherwise the first shop visit can
        # calculate a sale for stale stock and then rebuild stock during prewarm.
        slay.shop_stock(manager.ctx)
        sales=set(slay.shop_sale_items(manager.ctx,preserve=True))
        signature=manager._slay_shop_cache_signature();cache=getattr(manager,'slay_shop_cache',None)
        if not cache or cache.get('signature')!=signature or set(cache.get('sale_items',()))!=sales:
            manager._slay_prewarm_shop();cache=getattr(manager,'slay_shop_cache',None)
        sections=cache['sections'] if cache else slay.shop_sections(manager.ctx)
        # The authoritative sale set and the actual prices must agree even
        # after stock initialization and cache mutations. Only discount-priced
        # entries get the SALE label and green background.
        sales=set(slay.shop_sale_items(manager.ctx,preserve=True))
        priced_sales=set()
        for category,names in sections:
            for name in names:
                desc,display,icon=cache['entry_data'][name] if cache and name in cache['entry_data'] else (slay.shop_entry_description(name),slay.shop_entry_display_name(name),slay.shop_entry_icon(name))
                discounted=(name in sales and slay.price_for_item(name,manager.ctx) < slay._price_for_item_before_sale(name,manager.ctx))
                if discounted:priced_sales.add(name)
                entries[name]={'id':name,'canonical_name':name,'name':tr(display),'description':tr(desc),'icon':icon,'sale':discounted, 'frozen':name == slay.frozen_shop_item(manager.ctx)}
        sales=priced_sales
    else:
        sales=set();by_section=defaultdict(list)
        cache=getattr(manager,'slay_shop_cache',None)
        rows=cache['inventory_rows'] if cache and cache.get('signature')==manager._slay_shop_cache_signature() and 'inventory_rows' in cache else slay.inventory_rows(manager.ctx)
        for i,row in enumerate(rows):
            name='inventory:'+str(i);category=row.get('section','General Upgrades')
            canonical=row.get('canonical_name',row['name'])
            entry=dict(row,id=name,canonical_name=canonical,name=tr(row['name']),description=tr(row.get('description','')),icon=local_icon(canonical,row.get('icon',''),category))
            entries[name]=entry;by_section[category].append(name)
        sections=[(c,by_section[c]) for c in SECTIONS if c in by_section]
        sections += [(c,n) for c,n in by_section.items() if c not in SECTIONS]
    if shop:
        # Add a second view, never move or remove a unit from its normal category.
        discounted=[name for _,names in sections for name in names if name in sales]
        sections=list(sections)+[('Current Discounts',list(dict.fromkeys(discounted)))]
    console=CardConsole(manager,shop,sections,entries,sales)
    if shop:
        manager.slay_shop_popup=console.popup
        console.popup.bind(on_dismiss=lambda pop:manager._slay_shop_dismissed(pop))
    else:
        manager.slay_inventory_popup=console.popup
        def dismissed(pop):
            if manager.slay_inventory_popup is pop:
                manager.slay_inventory_popup = None
            manager._slay_end_modal()
            if getattr(pop, 'slay_navigate_to', None) == 'shop':
                Clock.schedule_once(lambda _dt:manager.open_slay_shop(), 0)
        console.popup.bind(on_dismiss=dismissed)
    console.popup.open()

# Mission locations refer to the campaign setting even when its playable race changes.
PLANET_GROUPS={
 'aiur':('For Aiur!','The Growing Shadow','The Spear of Adun','Echoes of the Future','Templar\'s Return','The Host','Salvation'),
 'korhal':('Media Blitz','Planetfall','Death From Above','The Reckoning','Sky Shield','Brothers in Arms'),
 'shakuras':('Amon\'s Reach','Last Stand'),
 'slayn':('Rak\'Shir','Steps of the Rite'),
 'glacious':('Forbidden Weapon',),
 'trion':(),
}

WORLD_TEXTURES={
 'planetviewagria_diff.png':('Evacuation','The Evacuation'),
 'planetviewhaven_diffuse2.png':('Safe Haven',"Haven's Fall"),
 'planetviewmeinhoff_diffuse.png':('Outbreak',),
 'planetviewmonlyth_diffuse.png':('Smash and Grab',),
 'planetview_marsaradiffuse2.png':('Liberation Day','The Outlaws','Zero Hour'),
 'planetview_belshirdiffuse.png':('Welcome to the Jungle',),
 'planetview_newfolsomdiffuse.png':('Breakout','Ghost of a Chance'),
 'planetview_valhalla_diffuse.png':('Engine of Destruction',),
 'planetview_xildiffuse.png':('The Dig',),
 'planetviewportzion_diffuse.png':('Cutthroat',),
 'planetviewredstone_diffuse.png':('Devil\'s Playground',),
 'planetviewtarsonis.png':('The Great Train Robbery',),
 'planetviewtyradordiffuse.png':('The Moebius Factor','Trouble In Paradise'),
 'planetviewulaan_diffuse.png':('Maw of the Void','Whispers of Doom'),
 'planetviewzhakuldas_diffuse.png':('A Sinister Turn',),
 'planetviewkaldr_diffuse.png':('Harvest of Screams','Shoot the Messenger','Enemy Within'),
 'planetviewzerusgrass_diff.png':('Waking the Ancient','The Crucible','Supreme'),
 'charplanetviewex1_diffuse.png':('Gates of Hell','Belly of the Beast','Shatter the Sky','All-In','Domination','Fire in the Sky','Old Soldiers'),
 'planetviewcastanar_herodiffuse2.png':('Piercing the Shroud',),
 'smx2_starmap_ui_mission_ulnarplanet_top_diff.png':('Temple of Unification','The Infinite Cycle','Harbinger of Oblivion'),
 'smx2_desertplanet_dif.png':('The Silent Scream','A Sudden Strike'),
}

def planet_source(name):
    name=re.sub(r' \((Terran|Zerg|Protoss)\)$','',name)
    for source,missions in WORLD_TEXTURES.items():
        if name in missions:return ASSETS/'planets'/source
    for planet,missions in PLANET_GROUPS.items():
        if name in missions:
            p=ASSETS/'planets'/f'smx2_starmap_ui_mission_{planet}planet_dif.png'
            if planet=='korhal':p=ASSETS/'planets/smx2_starmap_ui_mission_korhalplanet_diff.png'
            return p
    # Remaining missions use an SC2 surface matching the world environment.
    if name in ('Harvest of Screams','Shoot the Messenger','Enemy Within','Cold Void'):
        return ASSETS/'planets/smx2_starmap_ui_mission_glaciousplanet_icecap_dif.png'
    return ASSETS/'planets/planet_trev.png'

def decorate_node(manager,b):
    """Planet on the left; unobstructed, naturally sized text on the right.

    Keep one MissionButton for the entire clickable card. The native mission
    click/tooltip behavior therefore remains unchanged.
    """
    from worlds.sc2 import slay_the_starcraft as slay
    from worlds.sc2.mission_tables import lookup_id_to_mission
    old_update=getattr(b,'_slay_node_update',None)
    if old_update:b.unbind(pos=old_update,size=old_update)
    b.clear_widgets()
    b.slay_sound='command'
    data=slay.node(manager.ctx,int(b.mission_id)) or {}
    native=lookup_id_to_mission[int(b.mission_id)]
    name=str(data.get('mission_name') or native.mission_name)
    race=str(data.get('race') or native.race.get_title()).strip().title()
    display_name=re.sub(r' \((?:Terran|Zerg|Protoss)\)$','',name)
    status=str(data.get('_display_status') or slay.node_status(manager.ctx,int(b.mission_id)))
    caption,accent=STATUS.get(status,STATUS['future'])
    danger=slay.mission_is_difficulty_outlier(manager.ctx,int(b.mission_id))
    b.text='';b.background_normal='';b.background_down='';b.background_color=(0,0,0,0)
    b.canvas.before.clear();b.canvas.after.clear()
    race_colors={'Terran':(.52,.75,1,1),'Zerg':(.85,.59,.98,1),'Protoss':(1,.83,.42,1)}
    # The tinted fill is intentionally subdued, not a saturated race-color slab.
    race_fills={'Terran':(.068,.091,.113,.50),'Zerg':(.091,.069,.109,.50),
                'Protoss':(.105,.096,.067,.50)}
    fill=race_fills.get(race,(.10,.12,.14,.50))
    race_color=race_colors.get(race,(.85,.90,.96,1))
    # These must be standalone Labels: the generic label() helper binds
    # text_size to *both* dimensions, clipping glyphs when card sizes change.
    title=Label(text='[b]'+tr(display_name)+'[/b]',markup=True,font_size=dp(21),
                color=(.83,.93,1,1),halign='left',valign='middle',size_hint=(None,None))
    race_label=Label(text=tr(race),markup=True,font_size=dp(17),color=race_color,
                     halign='left',valign='middle',size_hint=(None,None))
    risk_suffix=' [color=FF5353]· High Risk[/color]' if danger else ''
    status_label=Label(text=tr(caption)+risk_suffix,markup=True,
                       font_size=dp(16),color=accent,halign='left',valign='middle',size_hint=(None,None))
    # Measure unwrapped titles, then allow up to two complete lines for long
    # names. Never shorten the text or crop its leading words.
    title.text_size=(None,None);title.texture_update()
    race_label.text_size=(None,None);race_label.texture_update()
    status_label.text_size=(None,None);status_label.texture_update()
    text_width=max(dp(175),min(dp(520),title.texture_size[0]+dp(8)),
                   race_label.texture_size[0]+dp(8),status_label.texture_size[0]+dp(8))
    for _ in range(4):
        title.text_size=(text_width,None);title.texture_update()
        if title.texture_size[1]<=dp(47):break
        text_width=min(dp(590),text_width+dp(36))
        if text_width>=dp(590) and title.texture_size[1]>dp(47):
            title.font_size=max(dp(17),title.font_size-dp(2))
    title.text_size=(text_width,None)
    b.size=(max(dp(294),dp(121)+text_width),dp(NODE_CARD_HEIGHT))
    for widget in (title,race_label,status_label):b.add_widget(widget)
    # Card rectangles are painted by draw_edges on the chart's background
    # layer. Its connections therefore sit over the rectangle, but behind the
    # planets and captions in the buttons' own canvases.
    with b.canvas.before:
        Color(*fill[:3],0);nameplate=RoundedRectangle(pos=(0,0),size=(0,0),radius=[dp(18)]*4)
        Color(*race_color[:3],0);card_edge=Line(rounded_rectangle=(0,0,0,0,dp(18)),width=dp(1))
        Color(.05,.18,.28,.45);halo=Ellipse(pos=(0,0),size=(0,0))
        Color(1,1,1,.42 if status=='abandoned' else 1)
        planet=Rectangle(texture=texture(planet_source(name)) or fallback_planet(name),pos=(0,0),size=(0,0))
        Color(*accent);ring=Line(circle=(0,0,1),width=dp(2.4 if status=='available' else 1.2))
        Color(.25,.6,.8,.28);orbit=Line(circle=(0,0,1),width=dp(.7))
        Color(.95,.29,.24,1 if danger else 0);warning=Line(circle=(0,0,1),width=dp(3))
        Color(*accent);marker=Line(points=[],width=dp(2));marker_cross=Line(points=[],width=dp(2))
    def update(*_):
        cx=b.x+dp(NODE_PLANET_X);cy=b.y+dp(NODE_PLANET_CENTER_Y);radius=dp(39)
        nameplate.pos=(b.x,b.y);nameplate.size=b.size
        card_edge.rounded_rectangle=(b.x+dp(1),b.y+dp(1),max(0,b.width-dp(2)),max(0,b.height-dp(2)),dp(18))
        halo.pos=(cx-radius-dp(6),cy-radius-dp(6));halo.size=(2*(radius+dp(6)),)*2
        planet.pos=(cx-dp(44),cy-dp(44));planet.size=(dp(88),dp(88))
        ring.circle=(cx,cy,radius+dp(5));orbit.circle=(cx,cy,radius+dp(11));warning.circle=(cx,cy,radius+dp(11))
        text_x=b.x+dp(110);text_width=max(dp(40),b.width-dp(121))
        status_label.pos=(text_x,b.y+dp(81));status_label.size=(text_width,dp(24))
        race_label.pos=(text_x,b.y+dp(56));race_label.size=(text_width,dp(23))
        title.pos=(text_x,b.y+dp(8));title.size=(text_width,dp(47))
        if status=='completed':
            marker.points=[cx-7,cy-2,cx-1,cy-8,cx+10,cy+7];marker_cross.points=[]
        elif status=='abandoned':
            marker.points=[cx-14,cy-14,cx+14,cy+14];marker_cross.points=[cx-14,cy+14,cx+14,cy-14]
        else:marker.points=[];marker_cross.points=[]
    b._slay_node_update=update
    b.bind(pos=update,size=update);update()
    b.slay_planet_source=str(planet_source(name));b.slay_node_caption=title
    b.slay_node_race_caption=race_label
    if getattr(b,'_tooltip',None) is not None:b._tooltip.md_bg_color=(.014,.041,.067,.98)

def build_chart(manager):
    from worlds.sc2 import slay_the_starcraft as slay
    buttons=manager.mission_buttons
    if not buttons:return
    scroll=manager.campaign_scroll_panel
    if not getattr(manager,'slay_chart_container',False):
        # Attach through the known ScrollView instead of trusting old_panel.parent.
        # During the first themed refresh Kivy can briefly report parent=None;
        # marking the chart installed at that point used to leave every route
        # widget in a detached container and produce a silent black screen.
        old_panel=manager.campaign_panel
        replacement=GridLayout(cols=1,size_hint=(None,None),padding=0)
        try:
            if old_panel is not None and old_panel.parent is not None:
                old_panel.parent.remove_widget(old_panel)
            for child in list(getattr(scroll,'children',())):
                if child is not replacement:
                    scroll.remove_widget(child)
            scroll.add_widget(replacement)
        except Exception:
            _command_ui_log('Chart container attach failed:\n'+traceback.format_exc())
            Clock.schedule_once(lambda _dt: build_chart(manager),0)
            return
        manager.campaign_panel=replacement
        manager.slay_chart_container=True
        _command_ui_log(f'Chart container attached: scroll={scroll.size} replacement_parent={type(replacement.parent).__name__ if replacement.parent else None}')
    else:
        # A previous refresh may have run while the mission screen was detached.
        # Reattach the existing chart container before taking any early-return.
        panel_widget=manager.campaign_panel
        if panel_widget.parent is not scroll:
            try:
                if panel_widget.parent is not None:
                    panel_widget.parent.remove_widget(panel_widget)
                for child in list(getattr(scroll,'children',())):
                    if child is not panel_widget:
                        scroll.remove_widget(child)
                scroll.add_widget(panel_widget)
                _command_ui_log('Reattached detached chart container to campaign scroll')
            except Exception:
                _command_ui_log('Chart container reattach failed:\n'+traceback.format_exc())
                Clock.schedule_once(lambda _dt: build_chart(manager),0)
                return
    if getattr(manager,'slay_chart_buttons',())==tuple(buttons) and getattr(manager,'slay_chart',None) and manager.slay_chart.parent:
        # Original refreshes can restore the compact rectangular-table height.
        # Keep the scroll extent owned by the taller planet chart.
        manager.campaign_panel.height=manager.slay_chart_scene.height
        return
    rows=defaultdict(list)
    for b in buttons:rows[int((slay.node(manager.ctx,int(b.mission_id)) or {}).get('layer',0))].append(b)
    layers=sorted(rows);max_width=max(map(len,rows.values()))
    chart=FloatLayout(size_hint=(None,None),size=(dp(max(1100,max_width*362+175)),dp((len(layers))*ROUTE_FLOOR_SPACING+120)))
    for b in buttons:
        if b.parent:b.parent.remove_widget(b)
        b.size_hint=(None,None);b.size=(dp(294),dp(NODE_CARD_HEIGHT));decorate_node(manager,b);chart.add_widget(b)
    # Preserve lane spacing after widening title/nameplate widgets. Different
    # floors can have different name lengths, so use the densest floor.
    chart_min_width=max(dp(1100),max(
        (sum(b.width for b in row)+dp(44)*max(0,len(row)-1)+dp(240))
        for row in rows.values()
    ))
    chart.width=max(chart.width,chart_min_width)
    chart.rows=rows;chart.layers=layers
    legend_text='[color=64CAFF]◉ Available[/color]\n[color=65DB8A]◉ Completed[/color]\n[color=EF6E61]◉ High Risk[/color]'
    legend=getattr(manager,'slay_fixed_legend',None)
    if legend is None:
        strip=BoxLayout(size_hint_y=None,height=dp(104),padding=[dp(18),dp(4)],spacing=dp(8))
        # Only the left key has a background; the zoom controls float directly
        # above the star field instead of sitting inside a full-width band.
        key_panel=BoxLayout(size_hint_x=None,width=dp(170),padding=[dp(12),dp(4)])
        panel(key_panel,color=(.018,.048,.075,.96),border=False)
        legend=label(legend_text,font_size=dp(15),halign='left',valign='middle')
        legend.bind(size=lambda widget,value:setattr(widget,'text_size',value))
        key_panel.add_widget(legend)
        strip.add_widget(key_panel)
        warning=label('[color=FFAA66]Map or mod data is out of date. Run /download_data to update.[/color]' if manager.ctx.data_out_of_date else '',font_size=dp(13),halign='left',valign='middle')
        strip.add_widget(warning)
        manager.slay_data_warning_label=warning
        controls=BoxLayout(size_hint_x=None,width=dp(390),spacing=dp(8))
        def change_zoom(factor=None,fit=False):
            manager.slay_zoom_fit=fit
            if not fit:manager.slay_zoom=max(.05,min(1.5,(getattr(manager,'slay_chart_scatter',None).scale if factor else 1)* (factor or 1)))
            resize=getattr(manager,'slay_chart_resize',None)
            if resize:resize()
        manager.slay_set_zoom=change_zoom
        slider=Slider(min=.05,max=1.5,value=getattr(manager,'slay_zoom',DEFAULT_ROUTE_SCALE),size_hint_x=1)
        percent=label('100%',size_hint_x=None,width=dp(60),valign='middle')
        def slide(_,value):
            if getattr(manager,'slay_sync_zoom',False):return
            manager.slay_zoom_fit=False;manager.slay_zoom=value
            resize=getattr(manager,'slay_chart_resize',None)
            if resize:resize()
        slider.bind(value=slide)
        controls.add_widget(slider);controls.add_widget(percent)
        controls.add_widget(control('Fit All Floors',lambda *_:change_zoom(fit=True),size_hint_x=None,width=dp(104)))
        manager.slay_zoom_slider=slider;manager.slay_zoom_percent=percent
        strip.add_widget(controls)
        # IMPORTANT: the old strip was added as a sibling above the map in the
        # vertical campaign_root BoxLayout. Although visually transparent, it
        # consumed 104dp of viewport height and exposed a differently tinted
        # background band. Instead overlay the key/zoom controls on the chart
        # without reducing the area available to CampaignScroll.
        campaign_root=manager.slay_mission_tab.content
        shell=manager.slay_mission_shell
        shell_index=campaign_root.children.index(shell)
        campaign_root.remove_widget(shell)
        overlay=FloatLayout(size_hint=(1,1))
        shell.size_hint=(1,1)
        shell.pos_hint={'x':0,'y':0}
        overlay.add_widget(shell)
        strip.size_hint=(1,None)
        strip.pos_hint={'top':1}
        overlay.add_widget(strip)
        campaign_root.add_widget(overlay,index=shell_index)
        manager.slay_chart_overlay=overlay
        manager.slay_fixed_legend=legend
        panel(manager.slay_mission_shell,'ui_screens_zeratul_prologue_starfield_generic_diff.png',color=(.85,.90,1,1),border=False)
    legend.text=legend_text
    warning=getattr(manager,'slay_data_warning_label',None)
    if warning is not None:
        warning.text=('[color=FFAA66]Map or mod data is out of date. Run /download_data to update.[/color]' if manager.ctx.data_out_of_date else '')
    manager.campaign_panel.clear_widgets();manager.campaign_panel.cols=1
    scene=FloatLayout(size_hint=(None,None))
    scaled=Scatter(size_hint=(None,None),size=chart.size,do_translation=False,do_rotation=False,do_scale=False,auto_bring_to_front=False)
    scaled.add_widget(chart);scene.add_widget(scaled)
    manager.campaign_panel.add_widget(scene)
    manager.slay_chart_scene=scene;manager.slay_chart_scatter=scaled
    # Remove the legacy table's side gutters and expose the full lower viewport.
    if scroll.parent:
        for sibling in list(scroll.parent.children):
            if sibling is not scroll:scroll.parent.remove_widget(sibling)
    scroll.size_hint_x=1
    scroll.do_scroll_x=True;scroll.do_scroll_y=True
    scroll.scroll_type=['content'];scroll.bar_width=0
    scroll.scroll_x=.5;scroll.scroll_y=0
    # Leave mouse-wheel events to ScrollView so the wheel scrolls vertically.
    scroll.scroll_wheel_distance=dp(45)
    manager.campaign_panel.size_hint_x=None
    manager.slay_chart=chart;manager.slay_chart_buttons=tuple(buttons)
    manager.slay_chart_lines=None
    graph_data={int(b.mission_id):dict(slay.node(manager.ctx,int(b.mission_id)) or {}) for b in buttons}
    preferred=slay.route_layout_x_fractions(manager.ctx)
    topology=slay.route_horizontal_positions(manager.ctx) if not preferred else {}
    if not preferred and topology:
        low=min(topology.values());span=max(1.0,max(topology.values())-low)
        preferred={mid:.12+.76*(value-low)/span for mid,value in topology.items()}
    floor_labels = {}
    def layout(*_):
        chart.width=max(manager.campaign_scroll_panel.width,chart_min_width)
        scale=min(manager.campaign_scroll_panel.width/chart.width,manager.campaign_scroll_panel.height/chart.height) if getattr(manager,'slay_zoom_fit',False) else getattr(manager,'slay_zoom',DEFAULT_ROUTE_SCALE)
        scene.size=(max(chart.width*scale,scroll.width),max(chart.height*scale,scroll.height))
        scaled.size=chart.size;scaled.scale=scale
        chart.pos=(0,0)
        # Scatter.pos is its transformed bounding-box origin (not the unscaled origin).
        scaled.pos=((scene.width-chart.width*scale)/2,(scene.height-chart.height*scale)/2)
        manager.campaign_panel.size=scene.size
        manager.slay_sync_zoom=True
        manager.slay_zoom_slider.min=min(.05,scroll.height/chart.height,scroll.width/chart.width)
        manager.slay_zoom_slider.value=scale
        manager.slay_zoom_percent.text=f'{scale/DEFAULT_ROUTE_SCALE:.0%}'
        manager.slay_sync_zoom=False
        scroll.scroll_x=.5
        positions=resolve_route_positions(graph_data,chart.width,preferred,{int(b.mission_id):b.width for b in buttons})
        for b in buttons:
            cx,y=positions[int(b.mission_id)]
            b.pos=(cx-b.width/2,y)
        for index, layer in enumerate(layers):
            if layer in floor_labels:floor_labels[layer].pos=(dp(8),dp(95+index*205))
        manager.draw_slay_edges()
    manager.campaign_scroll_panel.bind(size=layout)
    # Unbind the previous chart's resize callback when it is replaced.
    old=getattr(manager,'slay_chart_resize',None)
    if old:manager.campaign_scroll_panel.unbind(size=old)
    manager.slay_chart_resize=layout
    layout()
    _command_ui_log(f'Chart built: buttons={len(buttons)} layers={len(layers)} chart={chart.size} scene={scene.size} scroll={scroll.size} panel_parent={type(manager.campaign_panel.parent).__name__ if manager.campaign_panel.parent else None}')
    header=getattr(manager,'slay_header',None)
    if header:
        for w in header.children:
            if isinstance(w,Button):button(w)



def resolve_route_positions(nodes,width,preferred=None,node_widths=None):
    """Keep original branch positions; separate widened labels without overlaps."""
    preferred=preferred or {};node_widths=node_widths or {};rows=defaultdict(list)
    for mid,data in nodes.items():rows[int(data.get('layer',0))].append(mid)
    lanes=[float(data.get('lane',0)) for data in nodes.values()];lo=min(lanes,default=0);span=max(1,max(lanes,default=1)-lo)
    out={};margin=dp(120)
    def radius(mid):return float(node_widths.get(mid,dp(306)))/2
    for index,layer in enumerate(sorted(rows)):
        targets={}
        for mid in rows[layer]:
            data=nodes[mid];fraction=preferred.get(mid,.12+.76*(float(data.get('lane',0))-lo)/span)
            offset=((int(mid)*37+layer*19)%61-30)*dp(1)
            left=margin+max(0,radius(mid)-dp(153))
            targets[mid]=max(left,min(width-left,float(fraction)*width+offset))
        ordered=sorted(rows[layer],key=lambda mid:(targets[mid],float(nodes[mid].get('lane',0)),mid))
        xs=[targets[mid] for mid in ordered]
        for i in range(1,len(xs)):
            gap=radius(ordered[i-1])+radius(ordered[i])+dp(40)
            xs[i]=max(xs[i],xs[i-1]+gap)
        if xs and xs[-1]+radius(ordered[-1])>width-dp(18):
            xs[-1]=width-dp(18)-radius(ordered[-1])
            for i in range(len(xs)-2,-1,-1):
                gap=radius(ordered[i])+radius(ordered[i+1])+dp(40)
                xs[i]=min(xs[i],xs[i+1]-gap)
        if xs and xs[0]-radius(ordered[0])<dp(18):
            # Compact from the left rather than translating the whole row:
            # a translation could send the last widened title off the chart.
            xs[0]=dp(18)+radius(ordered[0])
            for i in range(1,len(xs)):
                gap=radius(ordered[i-1])+radius(ordered[i])+dp(40)
                xs[i]=max(xs[i],xs[i-1]+gap)
        if xs and xs[-1]+radius(ordered[-1])>width-dp(18):
            xs[-1]=width-dp(18)-radius(ordered[-1])
            for i in range(len(xs)-2,-1,-1):
                gap=radius(ordered[i])+radius(ordered[i+1])+dp(40)
                xs[i]=min(xs[i],xs[i+1]-gap)
        for mid,x in zip(ordered,xs):
            vertical=((int(mid)*23+layer*11)%19-9)*dp(1)
            out[mid]=(x,dp(30+index*ROUTE_FLOOR_SPACING)+vertical)
    return out

def draw_edges(manager,*_):
    from worlds.sc2 import slay_the_starcraft as slay
    chart=getattr(manager,'slay_chart',None)
    if chart is None or chart.parent is None:return
    old=getattr(manager,'slay_chart_lines',None)
    if old:chart.canvas.before.remove(old)
    group=InstructionGroup();by_id={int(b.mission_id):b for b in manager.mission_buttons};traversed=slay.traversed_edge_pairs(manager.ctx);count=0
    # First paint race-tinted rectangles, then routes on the SAME chart layer.
    # Kivy draws the child mission buttons (and their planet graphics) later,
    # masking the final part of each line behind the planet itself.
    race_fills={'Terran':(.068,.091,.113,.50),'Zerg':(.091,.069,.109,.50),
                'Protoss':(.105,.096,.067,.50)}
    race_edges={'Terran':(.52,.75,1,.095),'Zerg':(.85,.59,.98,.095),
                'Protoss':(1,.83,.42,.095)}
    for mission_id,b in by_id.items():
        data=slay.node(manager.ctx,mission_id) or {}
        race=str(data.get('race') or '').strip().title()
        group.add(Color(*race_fills.get(race,(.10,.12,.14,.50))))
        group.add(RoundedRectangle(pos=b.pos,size=b.size,radius=[dp(18)]*4))
        group.add(Color(*race_edges.get(race,(.85,.90,.96,.095))))
        group.add(Line(rounded_rectangle=(b.x+dp(1),b.y+dp(1),max(0,b.width-dp(2)),
                                          max(0,b.height-dp(2)),dp(18)),width=dp(1)))
    for src,dst in slay.edge_pairs(manager.ctx):
        a=by_id.get(src);b=by_id.get(dst)
        if not a or not b:continue
        # End 10-12dp *inside* each planet silhouette. The planets render after
        # this canvas group and cover the endpoints; only emerging angled stems
        # remain visible, instead of a line across the face of the planet.
        sx,sy=a.x+dp(NODE_PLANET_X),a.y+dp(NODE_PLANET_CENTER_Y+27)
        dx,dy=b.x+dp(NODE_PLANET_X),b.y+dp(NODE_PLANET_CENTER_Y-27)
        bend=max(dp(15),(dy-sy)*.52)
        sway=(dx-sx)*.18
        selected=(src,dst) in traversed
        color=(.30,.90,.59) if selected else (.24,.58,.79)
        points=[]
        for i in range(33):
            t=i/32;u=1-t
            points.append((u*u*u*sx+3*u*u*t*(sx+sway)+3*u*t*t*(dx-sway)+t*t*t*dx,
                           u*u*u*sy+3*u*u*t*(sy+bend)+3*u*t*t*(dy-bend)+t*t*t*dy))
        group.add(Color(*color,.12));group.add(stroke_mesh(points,dp(6)))
        group.add(Color(*color,.95 if selected else .6));group.add(stroke_mesh(points,dp(2.5)))
        # No triangular arrowhead: the connection curve is the route indicator.
        # Routes are in front of the background cards, but behind planet images.
        count+=1
    chart.canvas.before.add(group);manager.slay_chart_lines=group;manager.slay_chart_edge_count=count


def install(module):
    """Change presentation only; retain native callbacks, stock and reward handling."""
    cls = module.SC2Manager
    if getattr(cls, '_slay_command_ui_installed', False):
        return
    original_build = cls.build_mission_table
    def _restore_classic(manager):
        replacement=getattr(manager,'campaign_panel',None)
        legacy=getattr(manager,'_slay_command_ui_legacy_panel',None)
        scroll=getattr(manager,'campaign_scroll_panel',None)
        if legacy is not None and scroll is not None:
            try:
                if replacement is not None and replacement is not legacy and replacement.parent is scroll:
                    scroll.remove_widget(replacement)
                if legacy.parent is None:
                    scroll.add_widget(legacy)
                manager.campaign_panel=legacy
            except Exception:
                _command_ui_log('Fallback panel restore failed:\n'+traceback.format_exc())
        manager.slay_chart=None
        manager.slay_chart_container=False
        manager.slay_chart_buttons=()
        manager.first_check=True
        manager.refresh_from_launching=False
        try:
            original_build(manager,0)
        except Exception:
            _command_ui_log('Classic fallback redraw failed:\n'+traceback.format_exc())

    def build_mission_table(manager, dt):
        original_build(manager, dt)
        from worlds.sc2 import slay_the_starcraft as slay
        if slay.enabled(manager.ctx) and not manager.launching and not getattr(manager,'_slay_command_ui_disabled',False):
            if getattr(manager,'_slay_command_ui_legacy_panel',None) is None:
                manager._slay_command_ui_legacy_panel=manager.campaign_panel
            try:
                build_chart(manager)
            except Exception:
                manager._slay_command_ui_disabled=True
                _command_ui_log('Command UI disabled after build_chart exception:\n'+traceback.format_exc())
                _restore_classic(manager)
    cls.build_mission_table = build_mission_table
    original_edges = cls.draw_slay_edges
    def draw_slay_edges(manager, *args):
        if getattr(manager, 'slay_chart', None) is not None:
            return draw_edges(manager, *args)
        return original_edges(manager, *args)
    cls.draw_slay_edges = draw_slay_edges
    def open_slay_shop(manager, *args, **kwargs):
        return open_console(manager, True)
    def open_slay_inventory(manager, *args, **kwargs):
        return open_console(manager, False)
    cls.open_slay_shop = open_slay_shop
    cls.open_slay_inventory = open_slay_inventory
    # Cards use bounded local textures; skip the native remote AsyncImage prefetch.
    cls._slay_schedule_shop_prewarm = lambda manager, *args, **kwargs: None
    cls._slay_command_ui_installed = True
