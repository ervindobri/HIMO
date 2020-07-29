from kivy.lang import Builder
from kivymd.app import MDApp

KV = '''
MDBoxLayout:
    id: box_bottom
    adaptive_height: True
    padding: "10dp", 0, 0, 0
    ScrollView:
    
        MDList:
    
            OneLineAvatarListItem:
                id: synced_label
                text: "Single-line item with avatar"
                IconLeftWidget:
                    icon: "bluetooth-connect"
            OneLineAvatarListItem:
                id: battery_label
                text: "Single-line item with avatar"
                theme_text_color: "Custom"
                IconLeftWidget:
                    icon: "bluetooth-connect"
'''


class MainApp(MDApp):
    def build(self):
        return Builder.load_string(KV)


MainApp().run()