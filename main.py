"""Class Notice Board - Kivy app (Android-ready).
Add, edit, delete and browse classroom notices by date. Data is saved as JSON."""
import json
import os
import uuid
from datetime import date, datetime, timedelta

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

Window.softinput_mode = "below_target"

BG = (0.059, 0.090, 0.165, 1)
CARD = (0.118, 0.161, 0.231, 1)
FIELD = (0.2, 0.255, 0.333, 1)
ACCENT = (0.22, 0.74, 0.97, 1)
PRIORITY = {
    "High": (0.97, 0.44, 0.44, 1),
    "Normal": (0.22, 0.74, 0.97, 1),
    "Low": (0.20, 0.83, 0.60, 1),
}
PRI_ORDER = {"High": 0, "Normal": 1, "Low": 2}

KV = """
<RBtn>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    bold: True
    color: 1, 1, 1, 1
    canvas.before:
        Color:
            rgba: self.bg if self.state == 'normal' else self.bg[:3] + [0.7]
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

<DateHeader>:
    size_hint_y: None
    height: dp(34)
    text_size: self.width, None
    halign: 'left'
    valign: 'bottom'
    bold: True
    font_size: '14sp'
    color: 0.58, 0.64, 0.72, 1

<NoticeCard>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    padding: dp(16), dp(12), dp(12), dp(12)
    spacing: dp(6)
    canvas.before:
        Color:
            rgba: 0.118, 0.161, 0.231, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16)]
        Color:
            rgba: self.accent
        RoundedRectangle:
            pos: self.x, self.y + dp(10)
            size: dp(5), self.height - dp(20)
            radius: [dp(3)]
    BoxLayout:
        size_hint_y: None
        height: dp(20)
        Label:
            text: root.ndate_text
            font_size: '12sp'
            color: root.accent
            text_size: self.size
            halign: 'left'
            valign: 'middle'
        Label:
            text: root.priority.upper()
            font_size: '11sp'
            bold: True
            color: root.accent
            text_size: self.size
            halign: 'right'
            valign: 'middle'
    Label:
        text: root.title
        bold: True
        font_size: '18sp'
        color: 1, 1, 1, 1
        size_hint_y: None
        text_size: self.width, None
        height: self.texture_size[1]
        halign: 'left'
    Label:
        text: root.body
        font_size: '14sp'
        color: 0.8, 0.84, 0.9, 1
        size_hint_y: None
        text_size: self.width, None
        height: self.texture_size[1] if self.text else 0
        halign: 'left'
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(8)
        padding: 0, dp(6), 0, 0
        Widget:
        RBtn:
            text: 'Edit'
            bg: 0.2, 0.255, 0.333, 1
            size_hint_x: None
            width: dp(80)
            on_release: app.open_form(root.nid)
        RBtn:
            text: 'Delete'
            bg: 0.75, 0.3, 0.3, 1
            size_hint_x: None
            width: dp(80)
            on_release: app.confirm_delete(root.nid)

BoxLayout:
    orientation: 'vertical'
    padding: dp(14)
    spacing: dp(10)
    BoxLayout:
        size_hint_y: None
        height: dp(60)
        orientation: 'vertical'
        Label:
            text: 'Class Notice Board'
            bold: True
            font_size: '26sp'
            color: 1, 1, 1, 1
            text_size: self.size
            halign: 'left'
            valign: 'middle'
        Label:
            id: subtitle
            text: ''
            font_size: '13sp'
            color: 0.58, 0.64, 0.72, 1
            text_size: self.size
            halign: 'left'
            valign: 'top'
    BoxLayout:
        size_hint_y: None
        height: dp(46)
        spacing: dp(8)
        RBtn:
            text: '<'
            size_hint_x: None
            width: dp(46)
            bg: 0.118, 0.161, 0.231, 1
            on_release: app.shift_day(-1)
        Label:
            id: date_label
            text: ''
            bold: True
            font_size: '16sp'
            color: 0.22, 0.74, 0.97, 1
        RBtn:
            text: '>'
            size_hint_x: None
            width: dp(46)
            bg: 0.118, 0.161, 0.231, 1
            on_release: app.shift_day(1)
    BoxLayout:
        size_hint_y: None
        height: dp(42)
        spacing: dp(8)
        RBtn:
            text: 'Today'
            bg: 0.118, 0.161, 0.231, 1
            on_release: app.go_today()
        RBtn:
            id: all_btn
            text: 'Show all'
            bg: 0.118, 0.161, 0.231, 1
            on_release: app.toggle_all()
    ScrollView:
        bar_width: dp(3)
        GridLayout:
            id: list
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(10)
            padding: 0, 0, 0, dp(80)
    RBtn:
        text: '+  New notice'
        font_size: '17sp'
        size_hint_y: None
        height: dp(54)
        bg: 0.22, 0.74, 0.97, 1
        on_release: app.open_form()
"""


class RBtn(Button):
    bg = ListProperty([0.2, 0.255, 0.333, 1])


class DateHeader(Label):
    pass


class NoticeCard(BoxLayout):
    nid = StringProperty()
    title = StringProperty()
    body = StringProperty()
    priority = StringProperty("Normal")
    ndate_text = StringProperty()
    accent = ListProperty(ACCENT)


def field(**kw):
    return TextInput(
        background_normal="", background_active="", background_color=FIELD,
        foreground_color=(1, 1, 1, 1), hint_text_color=(0.6, 0.65, 0.72, 1),
        cursor_color=ACCENT, padding=(dp(12), dp(12)), **kw)


def themed_popup(title, content, size_hint=(0.92, 0.7)):
    return Popup(title=title, content=content, size_hint=size_hint,
                 background="", background_color=CARD,
                 separator_color=ACCENT, title_color=(1, 1, 1, 1))


class NoticeApp(App):
    def build(self):
        self.title = "Class Notice Board"
        Window.clearcolor = BG
        self.path = os.path.join(self.user_data_dir, "notices.json")
        self.notices = self.load()
        self.current = date.today()
        self.show_all = False
        return Builder.load_string(KV)

    def on_start(self):
        self.refresh()

    # ---------- storage ----------
    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            today = date.today()
            return [
                {"id": uuid.uuid4().hex, "title": "Welcome to your notice board",
                 "body": "Tap '+ New notice' to add one. Use Edit or Delete on any card.",
                 "date": today.isoformat(), "priority": "Normal"},
                {"id": uuid.uuid4().hex, "title": "Submit lab records",
                 "body": "Bring completed record books to the next lab session.",
                 "date": (today + timedelta(days=1)).isoformat(), "priority": "High"},
            ]

    def save(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.notices, f, indent=2)

    # ---------- navigation ----------
    def shift_day(self, n):
        self.show_all = False
        self.current += timedelta(days=n)
        self.refresh()

    def go_today(self):
        self.show_all = False
        self.current = date.today()
        self.refresh()

    def toggle_all(self):
        self.show_all = not self.show_all
        self.refresh()

    # ---------- display ----------
    def refresh(self):
        ids = self.root.ids
        box = ids.list
        box.clear_widgets()
        if self.show_all:
            items = sorted(self.notices, key=lambda n: (n["date"], PRI_ORDER[n["priority"]]))
            ids.date_label.text = "All notices"
        else:
            iso = self.current.isoformat()
            items = sorted((n for n in self.notices if n["date"] == iso),
                           key=lambda n: PRI_ORDER[n["priority"]])
            label = self.current.strftime("%a, %d %b %Y")
            if self.current == date.today():
                label += "  (Today)"
            ids.date_label.text = label
        ids.all_btn.text = "Show by date" if self.show_all else "Show all"
        ids.subtitle.text = f"{len(items)} notice(s) shown  |  {len(self.notices)} total"

        last = None
        for n in items:
            d = datetime.strptime(n["date"], "%Y-%m-%d").date()
            if self.show_all and n["date"] != last:
                box.add_widget(DateHeader(text=d.strftime("%A, %d %B %Y").upper()))
                last = n["date"]
            box.add_widget(NoticeCard(
                nid=n["id"], title=n["title"], body=n["body"],
                priority=n["priority"], ndate_text=d.strftime("%d %b %Y"),
                accent=PRIORITY[n["priority"]]))
        if not items:
            box.add_widget(Label(
                text="No notices for this day.\nTap '+ New notice' to add one.",
                halign="center", color=(0.58, 0.64, 0.72, 1),
                size_hint_y=None, height=dp(140)))

    # ---------- add / edit ----------
    def open_form(self, nid=None):
        existing = next((n for n in self.notices if n["id"] == nid), None)
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        title = field(hint_text="Title", multiline=False, size_hint_y=None, height=dp(46),
                      text=existing["title"] if existing else "")
        body = field(hint_text="Details (optional)", multiline=True,
                     text=existing["body"] if existing else "")
        d_default = existing["date"] if existing else (
            date.today() if self.show_all else self.current).isoformat()
        dt = field(hint_text="Date (YYYY-MM-DD)", multiline=False, size_hint_y=None,
                   height=dp(46), text=d_default)
        pri = Spinner(text=existing["priority"] if existing else "Normal",
                      values=list(PRIORITY), size_hint_y=None, height=dp(46),
                      background_normal="", background_color=FIELD, color=(1, 1, 1, 1))
        msg = Label(text="", color=PRIORITY["High"], size_hint_y=None, height=dp(20),
                    font_size="12sp")
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel = RBtn(text="Cancel", bg=list(FIELD))
        ok = RBtn(text="Save", bg=list(ACCENT))
        row.add_widget(cancel)
        row.add_widget(ok)
        for w in (title, body, dt, pri, msg, row):
            box.add_widget(w)
        pop = themed_popup("Edit notice" if existing else "New notice", box, (0.94, 0.8))

        def do_save(*_):
            t = title.text.strip()
            if not t:
                msg.text = "Please enter a title."
                return
            try:
                d = datetime.strptime(dt.text.strip(), "%Y-%m-%d").date()
            except ValueError:
                msg.text = "Date must look like 2026-10-18."
                return
            data = {"title": t, "body": body.text.strip(),
                    "date": d.isoformat(), "priority": pri.text}
            if existing:
                existing.update(data)
            else:
                self.notices.append({"id": uuid.uuid4().hex, **data})
            self.save()
            if not self.show_all:
                self.current = d
            pop.dismiss()
            self.refresh()

        ok.bind(on_release=do_save)
        cancel.bind(on_release=pop.dismiss)
        pop.open()

    # ---------- delete ----------
    def confirm_delete(self, nid):
        box = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(12))
        box.add_widget(Label(text="Delete this notice?\nThis cannot be undone.",
                             halign="center", color=(1, 1, 1, 1)))
        row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        no = RBtn(text="Keep", bg=list(FIELD))
        yes = RBtn(text="Delete", bg=[0.75, 0.3, 0.3, 1])
        row.add_widget(no)
        row.add_widget(yes)
        box.add_widget(row)
        pop = themed_popup("Confirm", box, (0.8, 0.3))

        def do_delete(*_):
            self.notices = [n for n in self.notices if n["id"] != nid]
            self.save()
            pop.dismiss()
            self.refresh()

        yes.bind(on_release=do_delete)
        no.bind(on_release=pop.dismiss)
        pop.open()


if __name__ == "__main__":
    NoticeApp().run()
