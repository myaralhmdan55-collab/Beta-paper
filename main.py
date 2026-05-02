from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.dropdown import DropDown
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.uix.popup import Popup

# ملف الحفظ الدائم
store = JsonStore('shadda_final_v3.json')

class ArchiveScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        layout.add_widget(Label(text="Teams Archive", font_size=25))
        self.t_name = TextInput(hint_text="Enter Team Name", multiline=False, size_hint_y=None, height=50)
        btn_save = Button(text="Save Team", background_color=(0, 1, 0, 1), size_hint_y=None, height=50)
        btn_save.bind(on_press=self.save_team)
        layout.add_widget(self.t_name)
        layout.add_widget(btn_save)
        
        btn_show = Button(text="Show All Stats", size_hint_y=None, height=50)
        btn_show.bind(on_press=self.show_stats)
        layout.add_widget(btn_show)
        
        btn_go = Button(text="Setup Match >>", background_color=(0.2, 0.6, 1, 1), size_hint_y=None, height=60)
        btn_go.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        layout.add_widget(btn_go)
        self.add_widget(layout)

    def save_team(self, instance):
        name = self.t_name.text.strip()
        if name and not store.exists(name):
            store.put(name, wins=0, total=0, rate=50.0)
            self.t_name.text = ""

    def show_stats(self, instance):
        output = "Stats:\n"
        for team in store.keys():
            d = store.get(team)
            output += f"{team}: {d['rate']}% (Wins: {d['wins']})\n"
        Popup(title="Database", content=Label(text=output), size_hint=(0.8, 0.6)).open()

class SetupScreen(Screen):
    def on_enter(self):
        self.refresh_menus()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.btn_a = Button(text="Select Team A", size_hint_y=None, height=50)
        self.btn_b = Button(text="Select Team B", size_hint_y=None, height=50)
        self.layout.add_widget(self.btn_a)
        self.layout.add_widget(self.btn_b)
        
        self.p_inps = [TextInput(hint_text=f"Player {i+1}", multiline=False) for i in range(4)]
        for p in self.p_inps: self.layout.add_widget(p)
        
        btn_start = Button(text="Start Game", background_color=(0, 1, 0, 1), size_hint_y=None, height=60)
        btn_start.bind(on_press=self.start_match)
        self.layout.add_widget(btn_start)
        
        btn_back = Button(text="<< Back to Archive", size_hint_y=None, height=40)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'db'))
        self.layout.add_widget(btn_back)
        self.add_widget(self.layout)

    def refresh_menus(self):
        # وظيفة لإنشاء القائمة المنسدلة لكل زر بشكل منفصل
        def make_dd(button):
            dd = DropDown()
            for name in store.keys():
                b = Button(text=name, size_hint_y=None, height=44)
                b.bind(on_release=lambda btn_obj: dd.select(btn_obj.text))
                dd.add_widget(b)
            button.bind(on_release=dd.open)
            dd.bind(on_select=lambda inst, x: setattr(button, 'text', x))

        make_dd(self.btn_a)
        make_dd(self.btn_b)

    def start_match(self, instance):
        app = App.get_running_app()
        app.active_t = [self.btn_a.text, self.btn_b.text]
        app.active_p = [p.text or f"P{i+1}" for i, p in enumerate(self.p_inps)]
        self.manager.current = 'game'

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.cur_p = 0
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.header = Label(text="", font_size=16, size_hint_y=None, height=40, color=(0,1,1,1))
        self.layout.add_widget(self.header)
        
        self.p_btns = []
        for i in range(4):
            btn = Button(text="", font_size=18, background_color=(0.2, 0.2, 0.2, 1))
            btn.bind(on_press=lambda inst, x=i: self.edit_manual(x))
            self.p_btns.append(btn); self.layout.add_widget(btn)
            
        self.info = Label(text="", font_size=20, color=(1, 1, 0, 1))
        self.layout.add_widget(self.info)
        
        self.inp = TextInput(hint_text="Request", input_filter='int', multiline=False, font_size=40, halign='center', size_hint_y=None, height=70)
        self.inp.bind(on_text_validate=lambda x: self.process('win'))
        self.layout.add_widget(self.inp)
        
        btns = BoxLayout(spacing=20, size_hint_y=None, height=70)
        b_w = Button(text="WIN (+)", background_color=(0, .7, 0, 1))
        b_w.bind(on_press=lambda x: self.process('win'))
        b_l = Button(text="LOSS (-)", background_color=(.7, 0, 0, 1))
        b_l.bind(on_press=lambda x: self.process('loss'))
        btns.add_widget(b_w); btns.add_widget(b_l)
        self.layout.add_widget(btns)
        
        btn_back = Button(text="Back / Reset Names", size_hint_y=None, height=45, background_color=(0.5,0.5,0.5,1))
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        self.layout.add_widget(btn_back)
        self.add_widget(self.layout)

    def on_enter(self): 
        self.update_ui()

    def edit_manual(self, idx):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        new_val = TextInput(text=str(self.app.global_scores[idx]), input_filter='int', multiline=False, font_size=30)
        content.add_widget(new_val)
        btn = Button(text="Save", background_color=(0,1,0,1))
        content.add_widget(btn)
        pop = Popup(title=f"Edit {self.app.active_p[idx]}", content=content, size_hint=(0.8, 0.4))
        def save(x): self.app.global_scores[idx] = int(new_val.text or 0); self.update_ui(); pop.dismiss()
        btn.bind(on_press=save); pop.open()

    def process(self, status):
        if not self.inp.text: return
        val = abs(int(self.inp.text))
        curr = self.app.global_scores[self.cur_p]
        
        # قوانين الإجبار
        min_r = 2
        for t, m in [(30,3),(40,4),(50,5),(60,6),(70,7),(80,8),(90,9),(100,10)]:
            if curr >= t: min_r = m
        if val < min_r or val > 13: self.inp.text = ""; return
        
        # قانون الضعف
        db = [7,8,9,10,11,12,13]
        if curr < 30: db.append(5)
        
        pts = val * 2 if val in db else val
        self.app.global_scores[self.cur_p] += pts if status == 'win' else -pts
        
        # فحص الفوز
        partners = {0:2, 2:0, 1:3, 3:1}
        for i in range(4):
            if self.app.global_scores[i] >= 42 and self.app.global_scores[partners[i]] > 0:
                self.handle_win(i, partners[i]); return
        
        self.cur_p = (self.cur_p + 1) % 4
        self.update_ui()

    def handle_win(self, p1, p2):
        win_t = self.app.active_t[0] if p1 in [0,2] else self.app.active_t[1]
        lose_t = self.app.active_t[1] if win_t == self.app.active_t[0] else self.app.active_t[0]
        
        for t in [win_t, lose_t]:
            if store.exists(t):
                d = store.get(t)
                nt = d['total'] + 1
                nw = d['wins'] + 1 if t == win_t else d['wins']
                store.put(t, wins=nw, total=nt, rate=round((nw/nt)*100, 1))
        
        self.info.text = "WINNER DECLARED!"
        Popup(title="Result", content=Label(text=f"{win_t} Wins!"), size_hint=(0.6,0.3)).open()

    def update_ui(self):
        r1 = store.get(self.app.active_t[0])['rate'] if store.exists(self.app.active_t[0]) else 50
        r2 = store.get(self.app.active_t[1])['rate'] if store.exists(self.app.active_t[1]) else 50
        self.header.text = f"{self.app.active_t[0]} ({r1}%) VS {self.app.active_t[1]} ({r2}%)"
        
        for i in range(4):
            t = self.app.active_t[0] if i in [0,2] else self.app.active_t[1]
            self.p_btns[i].text = f"{self.app.active_p[i]} ({t}): {self.app.global_scores[i]}"
        
        self.info.text = f"Next Turn: {self.app.active_p[self.cur_p]}"
        self.inp.text = ""; Clock.schedule_once(lambda dt: setattr(self.inp, 'focus', True), 0.2)

class ShaddaApp(App):
    def build(self):
        self.active_t = ["Team A", "Team B"]
        self.active_p = ["P1", "P2", "P3", "P4"]
        self.global_scores = [0, 0, 0, 0] # مصفوفة السكور العام
        sm = ScreenManager()
        sm.add_widget(ArchiveScreen(name='db'))
        sm.add_widget(SetupScreen(name='settings'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == "__main__":
    ShaddaApp().run()