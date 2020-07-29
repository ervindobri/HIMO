from kivy.lang import Builder
from kivymd.app import MDApp
import kivy.core.text.markup

KV = '''
#:import Markup kivy.core.text.markup

<MyTile@SmartTileWithStar>
    size_hint_y: None
    height: "240dp"


ScrollView:

    MDGridLayout:
        cols: 3
        adaptive_height: True
        padding: dp(4), dp(4)
        spacing: dp(4)

        MyTile:
            source: "cat-1.jpg"
            text: "[size=26]Cat 1[/size]\n[size=14]cat-1.jpg[/size]"

        MyTile:
            source: "cat-2.jpg"
            text: "[size=26]Cat 2[/size]\n[size=14]cat-2.jpg[/size]"
            tile_text_color: app.theme_cls.accent_color

        MyTile:
            source: "cat-3.jpg"
            text: "[size=26][color=#ffffff]Cat 3[/color][/size]\n[size=14]cat-3.jpg[/size]"
            tile_text_color: app.theme_cls.accent_color
'''


class MyApp(MDApp):
    def build(self):
        return Builder.load_string(KV)


MyApp().run()