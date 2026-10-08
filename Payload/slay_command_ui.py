"""SC2 star chart and card consoles. All gameplay identities/callbacks remain original."""
from pathlib import Path
from collections import defaultdict, OrderedDict
import math,re
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle, Line, Ellipse, Mesh
from kivy.graphics.instructions import InstructionGroup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
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
TEXTURES=OrderedDict()
CYAN=(.28,.78,1,1)
SECTIONS=('Terran Units','Terran Upgrades','Zerg Units','Zerg Upgrades','Protoss Units','Protoss Upgrades',
          'Defensive Structures & Detectors','General Upgrades','Mercenary Contracts','Mercenaries','Kerrigan','Spear of Adun','Boons','Blessings','Mutations')
STATUS={'available':('Available',CYAN),'selected':('Current Mission',(.3,1,.64,1)),'completed':('Completed',(.3,.85,.52,1)),
        'future':('Locked',(.3,.47,.61,1)),'abandoned':('Unavailable',(.48,.38,.43,1)),'loading':('Loading',(.52,.63,.7,1))}

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

def race_icon(category):
    race='zerg' if ('Zerg' in category or category in ('Kerrigan','Mutations')) else 'prot' if ('Protoss' in category or category in ('Spear of Adun','Boons','Blessings')) else 'terr'
    return ASSETS/f'ui_battlenet_glue_campaign_floatingraceicon_{race}.png'

def local_icon(item,source='',category=''):
    # Every card uses a local, semantic SC2 command-button asset.
    mapped=ICON_MAP.get(str(item))
    if mapped and (ASSETS/'icons'/mapped).is_file():return str(ASSETS/'icons'/mapped)
    if source:
        candidate=ASSETS/'icons'/Path(source).name
        if candidate.name.startswith('btn-') and candidate.is_file():return str(candidate)
    return ''


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
        accent=(.4,.72,1,1) if not entry.get('sale') else (.4,.95,.61,1)
        frame(self,accent)
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
        icon=Image(texture=texture(local_icon(entry['id'],entry.get('icon',''),category)),size_hint_x=None,width=dp(44))
        head.add_widget(icon)
        head.add_widget(label('[b]'+entry['name']+'[/b]',halign='left',valign='middle',font_size=dp(15)))
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
            buy=control('',lambda *_:purchase(entry['id']),font_size=dp(13))
            buy.slay_sound='command'
            buy.slay_item_id=entry['id'];self.purchase_button=buy;actions.add_widget(buy)
        else:
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
        super().__init__(orientation='horizontal',spacing=dp(6 if compact else 12),padding=dp(6 if compact else 10),**kwargs)
        panel(self,color=(.025,.065,.105,1))
        self.add_widget(Image(texture=texture(local_icon(entry['id'],entry.get('icon',''),category)),size_hint_x=None,width=dp(48)))
        text=BoxLayout(orientation='vertical',spacing=dp(4))
        title=label('[b]'+entry['name']+'[/b]',halign='left',valign='top',auto_height=True,size_hint_y=None,height=dp(26),font_size=dp(15))
        title.bind(texture_size=lambda w,s:setattr(w,'height',max(dp(26),s[1])))
        text.add_widget(title)
        description=label(entry.get('description',''),halign='left',valign='top',auto_height=True,size_hint_y=None)
        description.bind(texture_size=lambda w,s:setattr(w,'height',max(dp(28),s[1])))
        text.add_widget(description)
        text.bind(minimum_height=lambda w,h:setattr(self,'height',max(dp(108),h+dp(20))))
        self.add_widget(text)
        actions=BoxLayout(orientation='vertical',spacing=dp(6),size_hint_x=None,width=dp(140 if compact else 150))
        if not compact:actions.add_widget(control('Details',lambda *_:select(entry),size_hint_y=None,height=dp(32)))
        if shop:
            self.purchase_button=control('',lambda *_:purchase(entry['id']),font_size=dp(12),size_hint_y=None,height=dp(46),halign='center',valign='middle')
            self.purchase_button.bind(size=lambda w,s:setattr(w,'text_size',(max(dp(1),s[0]-dp(10)),s[1])))
            self.purchase_button.slay_sound='command'
            self.purchase_button.slay_item_id=entry['id']
            actions.add_widget(self.purchase_button)
        else:
            actions.add_widget(label(f"Owned ×{entry.get('total',1)}",size_hint_y=None,height=dp(24)))
            origins=[]
            if entry.get('ap_count'):origins.append(f"Supplies {entry['ap_count']}")
            if entry.get('shop_count'):origins.append(f"Purchased {entry['shop_count']}")
            actions.add_widget(label(' · '.join(origins) or 'Acquired',size_hint_y=None,height=dp(24),font_size=dp(12)))
        if entry.get('canonical_name'):
            from slay_ui_support import related_tech
            if related_tech(__import__('kivy.app',fromlist=['App']).App.get_running_app().ctx,entry['canonical_name']):
                actions.add_widget(control('Technology',lambda *_:unit_technology_popup(entry),size_hint_y=None,height=dp(28),font_size=dp(12)))
        self.add_widget(actions)

class CardConsole:
    def __init__(self,manager,shop,sections,entries,sale_items=()):
        self.manager=manager;self.shop=shop;self.sections=sections;self.entries=entries
        self.category=getattr(manager,'slay_card_shop_category' if shop else 'slay_card_inventory_category',None)
        self.page=0;self.page_size=8;self.card_widgets={};self.sale_items=set(sale_items)
        self.view_key='slay_shop_view_mode' if shop else 'slay_inventory_view_mode'
        self.view_mode=getattr(manager,self.view_key,'cards')
        self.page_size=16 if self.view_mode=='list' else 8
        self.popup=Popup(title='Slay the StarCraft Shop' if shop else 'Slay the StarCraft Inventory',size_hint=(.98,.94),separator_color=CYAN,
                         background='')
        root=BoxLayout(orientation='vertical',spacing=dp(12),padding=dp(10));panel(root,border=False)
        top=BoxLayout(size_hint_y=None,height=dp(54),spacing=dp(10))
        top.add_widget(label('[b]Supply Depot[/b]' if shop else '[b]Supply Inventory[/b]',font_size=dp(24),halign='left'))
        self.credit=label('',halign='right');top.add_widget(self.credit)
        self.view_button=control('',lambda *_:self.toggle_view(),size_hint_x=None,width=dp(145))
        top.add_widget(self.view_button)
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
        footer=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(10))
        footer.add_widget(label('' if shop else 'View acquired supplies, units, upgrades and permanent effects',halign='left',font_size=dp(13)))
        footer.add_widget(control('Return to Route',self.popup.dismiss,size_hint_x=None,width=dp(170)));root.add_widget(footer)
        self.popup.content=root;self.popup.slay_scroll=self.scroll;self.popup.slay_purchase_buttons={}
        self.popup.slay_credit_label=self.credit;self.popup.slay_console=self
        self.popup.bind(size=self.resize)
        if not self.category or self.category not in dict(sections):self.category=sections[0][0] if sections else ''
        self.render()
        self.resize()

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
        cols=4 if width>dp(1350) else 3 if width>dp(1000) else 2
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
        self.inspect_icon.texture=texture(local_icon(entry['id'],entry.get('icon',''),self.category))
        self.inspect_title.text=entry['name']
        self.inspect_text.text=entry.get('description','') or 'This relic is active.'
        self.tech_panel.clear_widgets()
        grid=technology_grid(self.manager.ctx,entry.get('canonical_name',entry['id']))
        self.tech_panel.height=dp(180) if grid else 0
        if grid:
            self.tech_panel.add_widget(label('Related Technology',size_hint_y=None,height=dp(22),font_size=dp(12),halign='left'))
            scroll=ScrollView(do_scroll_x=False);scroll.add_widget(grid);self.tech_panel.add_widget(scroll)

    def render(self):
        from worlds.sc2 import slay_the_starcraft as slay
        self.view_button.text=('Show Cards' if self.view_mode=='list' else 'Show List') if LANGUAGE=='zhCN' else ('Show Cards' if self.view_mode=='list' else 'Show List')
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
        for name in page_names:texture(local_icon(name,self.entries[name].get('icon',''),self.category))
        self.grid.clear_widgets();self.popup.slay_purchase_buttons={};self.card_widgets={}
        for name in page_names:
            entry=self.entries[name]
            widget_class=RelicRow if self.view_mode=='list' else RelicCard
            card=widget_class(entry,self.category,self.inspect,self.shop,lambda item:self.manager._slay_buy(item,self.popup),size_hint_y=None,height=dp(108 if self.view_mode=='list' else 255))
            self.grid.add_widget(card);self.card_widgets[name]=card
            if self.shop:self.popup.slay_purchase_buttons[name]=card.purchase_button
        if not page_names:self.grid.add_widget(label('No supplies in this category.',size_hint_y=None,height=dp(180)))
        if page_names:self.inspect(self.entries[page_names[0]])
        self.scroll.scroll_y=1
        if self.shop:self.manager._slay_refresh_shop_controls(self.popup)
        else:self.credit.text=f'Catalogued {len(self.entries)} supply types'

    def render_overview(self):
        for name,entry in self.entries.items():texture(local_icon(name,entry.get('icon','')))
        self.grid.clear_widgets();self.popup.slay_purchase_buttons={};self.card_widgets={}
        self.heading.text='All Categories' if LANGUAGE=='zhCN' else 'All Categories'
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
        counts=[0]*len(columns)
        for category,names in self.sections:
            if category=='Current Discounts' or not names:continue
            index=0 if category.startswith('Terran') else 1 if category.startswith('Zerg') else 2 if category.startswith('Protoss') else counts.index(min(counts))
            index=min(index,len(columns)-1)
            group=BoxLayout(orientation='vertical',size_hint_y=None,padding=dp(6),spacing=dp(4))
            group.bind(minimum_height=group.setter('height'))
            panel(group,color=(.025,.065,.105,1))
            group.add_widget(label('[b]'+tr(category)+'[/b]',size_hint_y=None,height=dp(30)))
            for name in names:
                entry=self.entries[name]
                row=RelicRow(entry,category,self.inspect,self.shop,lambda item:self.manager._slay_buy(item,self.popup),compact=True,size_hint_y=None,height=dp(108))
                group.add_widget(row);self.card_widgets[name]=row
                if self.shop:self.popup.slay_purchase_buttons[name]=row.purchase_button
            columns[index].add_widget(group);counts[index]+=len(names)
        align_columns()
        self.scroll.scroll_y=1
        if self.shop:self.manager._slay_refresh_shop_controls(self.popup)
        else:self.credit.text=f'Catalogued {len(self.entries)} supply types'

def open_console(manager,shop):
    from worlds.sc2 import slay_the_starcraft as slay
    if not slay.enabled(manager.ctx):return
    if shop and getattr(manager,'slay_shop_popup',None):return
    if not shop and getattr(manager,'slay_inventory_popup',None):return
    if not slay.state_ready(manager.ctx):
        pop=Popup(title='Loading Adventure',content=label('Adventure data is loading. Please try again shortly.'),size_hint=(.55,.35));pop.open();return
    manager._slay_begin_modal()
    entries={}
    if shop:
        sales=set(slay.shop_sale_items(manager.ctx,preserve=True))
        signature=manager._slay_shop_cache_signature();cache=getattr(manager,'slay_shop_cache',None)
        if not cache or cache.get('signature')!=signature or set(cache.get('sale_items',()))!=sales:
            manager._slay_prewarm_shop();cache=getattr(manager,'slay_shop_cache',None)
        sections=cache['sections'] if cache else slay.shop_sections(manager.ctx)
        for category,names in sections:
            for name in names:
                desc,display,icon=cache['entry_data'][name] if cache and name in cache['entry_data'] else (slay.shop_entry_description(name),slay.shop_entry_display_name(name),slay.shop_entry_icon(name))
                entries[name]={'id':name,'canonical_name':name,'name':tr(display),'description':tr(desc),'icon':icon,'sale':name in sales}
    else:
        sales=set();by_section=defaultdict(list)
        cache=getattr(manager,'slay_shop_cache',None)
        rows=cache['inventory_rows'] if cache and cache.get('signature')==manager._slay_shop_cache_signature() and 'inventory_rows' in cache else slay.inventory_rows(manager.ctx)
        for i,row in enumerate(rows):
            name='inventory:'+str(i);category=row.get('section','General Upgrades')
            entry=dict(row,id=name,canonical_name=row['name'],name=tr(row['name']),description=tr(row.get('description','')),icon=local_icon(row['name'],row.get('icon',''),category))
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
        def dismissed(*_):manager.slay_inventory_popup=None;manager._slay_end_modal()
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
    from worlds.sc2 import slay_the_starcraft as slay
    from worlds.sc2.mission_tables import lookup_id_to_mission
    old_update = getattr(b, '_slay_node_update', None)
    if old_update:b.unbind(pos=old_update,size=old_update)
    b.clear_widgets()
    b.slay_sound='command'
    data=slay.node(manager.ctx,int(b.mission_id)) or {}
    name=str(data.get('mission_name') or lookup_id_to_mission[int(b.mission_id)].mission_name)
    status=str(data.get('_display_status') or slay.node_status(manager.ctx,int(b.mission_id)))
    caption,accent=STATUS.get(status,STATUS['future'])
    danger=slay.mission_is_difficulty_outlier(manager.ctx,int(b.mission_id))
    b.text='';b.background_normal='';b.background_down='';b.background_color=(0,0,0,0)
    b.canvas.before.clear();b.canvas.after.clear()
    title=label('[b]'+tr(name)+'[/b]',font_size=dp(14),halign='center',valign='top',size_hint=(None,None))
    b.add_widget(title)
    status_label=label(caption+(' · High Risk' if danger else ''),font_size=dp(11),color=accent,halign='center',size_hint=(None,None))
    b.add_widget(status_label)
    with b.canvas.before:
        Color(.014,.041,.067,.98);nameplate=Rectangle(pos=(0,0),size=(0,0))
        Color(.05,.18,.28,.55);halo=Ellipse(pos=(0,0),size=(0,0))
        Color(1,1,1,.42 if status=='abandoned' else 1);planet=Rectangle(texture=texture(planet_source(name)) or fallback_planet(name),pos=(0,0),size=(0,0))
        Color(*accent);ring=Line(circle=(0,0,1),width=dp(1.2))
        Color(.25,.6,.8,.28);orbit=Line(circle=(0,0,1),width=dp(.7))
        Color(.95,.29,.24,1 if danger else 0);warning=Line(circle=(0,0,1,25,155),width=dp(2))
        Color(*accent);marker=Line(points=[],width=dp(2))
    def update(*_):
        cx=b.center_x;cy=b.y+dp(107);radius=dp(39)
        halo.pos=(cx-radius-dp(6),cy-radius-dp(6));halo.size=(2*(radius+dp(6)),)*2
        planet.pos=(cx-dp(44),cy-dp(44));planet.size=(dp(88),dp(88))
        ring.circle=(cx,cy,radius+dp(5));orbit.circle=(cx,cy,radius+dp(11));warning.circle=(cx,cy,radius+dp(11),25,155)
        title.pos=(b.x,b.y+dp(2));title.size=(b.width,dp(34))
        status_label.pos=(b.x,b.y+dp(38));status_label.size=(b.width,dp(16))
        nameplate.pos=(b.x+dp(6),b.y+dp(2));nameplate.size=(b.width-dp(12),dp(53))
        marker.points=[cx-7,cy-2,cx-1,cy-8,cx+10,cy+7] if status=='completed' else [cx-7,cy-7,cx+7,cy+7,cx-7,cy+7,cx+7,cy-7] if status=='abandoned' else []
    b._slay_node_update=update
    b.bind(pos=update,size=update);update()
    b.slay_planet_source=str(planet_source(name));b.slay_node_caption=title
    if getattr(b,'_tooltip',None) is not None:
        b._tooltip.md_bg_color=(.014,.041,.067,.98)

def build_chart(manager):
    from worlds.sc2 import slay_the_starcraft as slay
    buttons=manager.mission_buttons
    if not buttons:return
    if not getattr(manager,'slay_chart_container',False):
        # The legacy MultiCampaignLayout KV height expression also observes the
        # old table; a plain container gives the chart its own scroll extent.
        old_panel=manager.campaign_panel
        parent=old_panel.parent
        replacement=GridLayout(cols=1,size_hint=(None,None),padding=0)
        if parent:
            parent.remove_widget(old_panel)
            parent.add_widget(replacement)
        manager.campaign_panel=replacement
        manager.slay_chart_container=True
    if getattr(manager,'slay_chart_buttons',())==tuple(buttons) and getattr(manager,'slay_chart',None) and manager.slay_chart.parent:
        # Original refreshes can restore the compact rectangular-table height.
        # Keep the scroll extent owned by the taller planet chart.
        manager.campaign_panel.height=manager.slay_chart_scene.height
        return
    rows=defaultdict(list)
    for b in buttons:rows[int((slay.node(manager.ctx,int(b.mission_id)) or {}).get('layer',0))].append(b)
    layers=sorted(rows);max_width=max(map(len,rows.values()))
    chart=FloatLayout(size_hint=(None,None),size=(dp(max(950,max_width*228+160)),dp((len(layers))*205+125)))
    for b in buttons:
        if b.parent:b.parent.remove_widget(b)
        b.size_hint=(None,None);b.size=(dp(205),dp(165));decorate_node(manager,b);chart.add_widget(b)
    chart.rows=rows;chart.layers=layers
    legend_text='[b]Sector Route[/b]    [color=64CAFF]◉ Available[/color]    [color=65DB8A]◉ Completed[/color]    [color=EF6E61]◉ High Risk[/color]'
    if manager.ctx.data_out_of_date:legend_text+='\n[color=FFAA66]Map or mod data is out of date. Run /download_data to update.[/color]'
    legend=getattr(manager,'slay_fixed_legend',None)
    if legend is None:
        strip=BoxLayout(size_hint_y=None,height=dp(76),padding=[dp(28),dp(6)])
        panel(strip,color=(.018,.048,.075,.96),border=False)
        legend=label(legend_text,font_size=dp(15),halign='left',valign='middle')
        legend.bind(size=lambda widget,value:setattr(widget,'text_size',value))
        strip.add_widget(legend)
        controls=BoxLayout(size_hint_x=None,width=dp(390),spacing=dp(8))
        def change_zoom(factor=None,fit=False):
            manager.slay_zoom_fit=fit
            if not fit:manager.slay_zoom=max(.05,min(1.5,(getattr(manager,'slay_chart_scatter',None).scale if factor else 1)* (factor or 1)))
            resize=getattr(manager,'slay_chart_resize',None)
            if resize:resize()
        manager.slay_set_zoom=change_zoom
        slider=Slider(min=.05,max=1.5,value=getattr(manager,'slay_zoom',1),size_hint_x=1)
        percent=label('100%',size_hint_x=None,width=dp(52),valign='middle')
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
        manager.slay_mission_tab.content.add_widget(strip,index=1)
        manager.slay_fixed_legend=legend
        panel(manager.slay_mission_shell,'ui_screens_zeratul_prologue_starfield_generic_diff.png',color=(.85,.90,1,1),border=False)
    legend.text=legend_text
    manager.campaign_panel.clear_widgets();manager.campaign_panel.cols=1
    scene=FloatLayout(size_hint=(None,None))
    scaled=Scatter(size_hint=(None,None),size=chart.size,do_translation=False,do_rotation=False,do_scale=False,auto_bring_to_front=False)
    scaled.add_widget(chart);scene.add_widget(scaled)
    manager.campaign_panel.add_widget(scene)
    manager.slay_chart_scene=scene;manager.slay_chart_scatter=scaled
    scroll=manager.campaign_scroll_panel
    # Remove the legacy table's side gutters and expose the full lower viewport.
    if scroll.parent:
        for sibling in list(scroll.parent.children):
            if sibling is not scroll:scroll.parent.remove_widget(sibling)
    scroll.size_hint_x=1
    scroll.do_scroll_x=True;scroll.do_scroll_y=True
    scroll.scroll_type=['content'];scroll.bar_width=0
    scroll.scroll_x=.5;scroll.scroll_y=0
    if not getattr(scroll,'slay_wheel_zoom_bound',False):
        def wheel_zoom(widget,touch):
            if widget.collide_point(*touch.pos) and getattr(touch,'is_mouse_scrolling',False):
                direction=getattr(touch,'button','')
                if direction in ('scrollup','scrolldown'):
                    manager.slay_set_zoom(1/1.12 if direction=='scrollup' else 1.12)
                return True
            return False
        scroll.bind(on_touch_down=wheel_zoom)
        scroll.slay_wheel_zoom_bound=True
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
        chart.width=max(manager.campaign_scroll_panel.width,dp((3 if False else max_width)*228+160))
        scale=min(manager.campaign_scroll_panel.width/chart.width,manager.campaign_scroll_panel.height/chart.height) if getattr(manager,'slay_zoom_fit',False) else getattr(manager,'slay_zoom',1)
        scene.size=(max(chart.width*scale,scroll.width),max(chart.height*scale,scroll.height))
        scaled.size=chart.size;scaled.scale=scale
        chart.pos=(0,0)
        # Scatter.pos is its transformed bounding-box origin (not the unscaled origin).
        scaled.pos=((scene.width-chart.width*scale)/2,(scene.height-chart.height*scale)/2)
        manager.campaign_panel.size=scene.size
        manager.slay_sync_zoom=True
        manager.slay_zoom_slider.min=min(.05,scroll.height/chart.height,scroll.width/chart.width)
        manager.slay_zoom_slider.value=scale
        manager.slay_zoom_percent.text=f'{scale:.0%}'
        manager.slay_sync_zoom=False
        scroll.scroll_x=.5
        positions=resolve_route_positions(graph_data,chart.width,preferred)
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
    header=getattr(manager,'slay_header',None)
    if header:
        for w in header.children:
            if isinstance(w,Button):button(w)



def resolve_route_positions(nodes,width,preferred=None):
    """Keep original branch positions; separate only colliding labels. Pure display math."""
    preferred=preferred or {};rows=defaultdict(list)
    for mid,data in nodes.items():rows[int(data.get('layer',0))].append(mid)
    lanes=[float(data.get('lane',0)) for data in nodes.values()];lo=min(lanes,default=0);span=max(1,max(lanes,default=1)-lo)
    out={};margin=dp(120);gap=dp(228)
    for index,layer in enumerate(sorted(rows)):
        targets={}
        for mid in rows[layer]:
            data=nodes[mid];fraction=preferred.get(mid,.12+.76*(float(data.get('lane',0))-lo)/span)
            # Stable small offsets give each branch its own shape on every reopen/resize.
            offset=((int(mid)*37+layer*19)%61-30)*dp(1)
            targets[mid]=max(margin,min(width-margin,float(fraction)*width+offset))
        ordered=sorted(rows[layer],key=lambda mid:(targets[mid],float(nodes[mid].get('lane',0)),mid))
        xs=[targets[mid] for mid in ordered]
        for i in range(1,len(xs)):xs[i]=max(xs[i],xs[i-1]+gap)
        if xs and xs[-1]>width-margin:
            xs[-1]=width-margin
            for i in range(len(xs)-2,-1,-1):xs[i]=min(xs[i],xs[i+1]-gap)
        if xs and xs[0]<margin:
            delta=margin-xs[0];xs=[x+delta for x in xs]
        for mid,x in zip(ordered,xs):
            vertical=((int(mid)*23+layer*11)%29-14)*dp(1)
            out[mid]=(x,dp(30+index*205)+vertical)
    return out

def draw_edges(manager,*_):
    from worlds.sc2 import slay_the_starcraft as slay
    chart=getattr(manager,'slay_chart',None)
    if chart is None or chart.parent is None:return
    old=getattr(manager,'slay_chart_lines',None)
    if old:chart.canvas.before.remove(old)
    group=InstructionGroup();by_id={int(b.mission_id):b for b in manager.mission_buttons};traversed=slay.traversed_edge_pairs(manager.ctx);count=0
    for src,dst in slay.edge_pairs(manager.ctx):
        a=by_id.get(src);b=by_id.get(dst)
        if not a or not b:continue
        sx,sy=a.center_x,a.y+dp(107+51);dx,dy=b.center_x,b.y-dp(6)
        bend=max(dp(15),(dy-sy)*.52)
        bezier=[sx,sy,sx,sy+bend,dx,dy-bend,dx,dy]
        selected=(src,dst) in traversed
        color=(.30,.90,.59) if selected else (.24,.58,.79)
        points=[]
        for i in range(33):
            t=i/32;u=1-t
            points.append((u*u*u*sx+3*u*u*t*sx+3*u*t*t*dx+t*t*t*dx,
                           u*u*u*sy+3*u*u*t*(sy+bend)+3*u*t*t*(dy-bend)+t*t*t*dy))
        group.add(Color(*color,.12));group.add(stroke_mesh(points,dp(6)))
        group.add(Color(*color,.95 if selected else .6));group.add(stroke_mesh(points,dp(2.5)))
        group.add(Line(points=[dx-3,dy-6,dx,dy,dx+3,dy-6],width=dp(1)))
        count+=1
    chart.canvas.before.add(group);manager.slay_chart_lines=group;manager.slay_chart_edge_count=count


def install(module):
    """Change presentation only; retain native callbacks, stock and reward handling."""
    cls = module.SC2Manager
    if getattr(cls, '_slay_command_ui_installed', False):
        return
    original_build = cls.build_mission_table
    def build_mission_table(manager, dt):
        original_build(manager, dt)
        from worlds.sc2 import slay_the_starcraft as slay
        if slay.enabled(manager.ctx) and not manager.launching:
            build_chart(manager)
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
