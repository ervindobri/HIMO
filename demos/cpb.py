from kivy.app import App
from kivy.uix.progressbar import ProgressBar
from kivy.core.text import Label as CoreLabel
from kivy.lang.builder import Builder
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, ScreenManager

Builder.load_string('''
<HomePage>:
    AnchorLayout:
        # canvas.before:
        #     Rectangle:
        #         # self here refers to the widget i.e BoxLayout
        #         pos: self.pos
        #         size: 200,200
        CircularProgressBar:
            id: cp
            size_hint:(1,1)
            # pos: [dp(self.pos[0]) - dp(16), dp(self.pos[1]) + dp(16)]
            height:400
            width:400
            max:80
    ''')


class HomePage(Screen):
    pass
class CircularProgressBar(ProgressBar):
    def __init__(self,**kwargs):
        super(CircularProgressBar,self).__init__(**kwargs)
        self.thickness = 40
        self.label = CoreLabel(text="0",font_size=self.thickness)
        self.texture_size= None
        self.refresh_text()
        self.draw()
    def draw(self):
        with self.canvas:
            self.canvas.clear()
            #No progress
            Color(0.26,0.26,0.26)
            Ellipse(pos=self.pos, size=self.size)
            #Progress Circle
            Color(1,0,0)
            Ellipse(pos=self.pos,size=self.size,angle_end=(self.value/100.0)*360)#will be replaced with necessary data
            #Inner Circle
            Color(0,0,0)
            Ellipse(pos=(self.pos[0] + self.thickness / 2, self.pos[1] + self.thickness / 2),size=(self.size[0] - self.thickness, self.size[1] - self.thickness))
            #Inner text
            Color(1, 1, 1, 1)
            Rectangle(texture=self.label.texture,size=self.texture_size,pos=(self.size[0]/2-self.texture_size[0]/2,self.size[1]/2 - self.texture_size[1]/2))
            self.label.text = str(int(self.value))
    def refresh_text(self):
        self.label.refresh()
        self.texture_size=list(self.label.texture.size)
    def set_value(self, value):
        self.value = value
        self.label.text = str(int(self.value))
        self.refresh_text()
        self.draw()

sm = ScreenManager()
sm.add_widget(HomePage(name="HomePage"))

class HealthTrackingSystem(App):
    def animate(self,dt):
        circProgressBar = self.root.get_screen('HomePage').ids.cp
        if circProgressBar.value<80:
            circProgressBar.set_value(circProgressBar.value+1)
        else:
            circProgressBar.set_value(0)

    def build(self):
        Clock.schedule_interval(self.animate, 0.001)
        return sm

if __name__ == '__main__':
    HealthTrackingSystem().run()