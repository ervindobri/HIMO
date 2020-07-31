import glob
import json
import os
import queue
import threading
import time
from datetime import datetime, timedelta
from math import floor
from multiprocessing import Queue

from kivy import Config
from kivy.animation import Animation
from kivy.cache import Cache

from kivy.uix.behaviors import TouchRippleBehavior

from kivy.uix.image import Image

from kivy.uix.recycleview import RecycleView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.material_resources import dp

from kivymd.uix.card import MDCard
from kivy.core.window import Window

import myo
import kivy

from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty, ListProperty, NumericProperty, BooleanProperty, \
    ReferenceListProperty

# Builder.load_file("himold.kv")
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import HoverBehavior, RectangularRippleBehavior, RectangularElevationBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDFloatingActionButton, MDRectangleFlatButton, MDRoundFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.dropdownitem import MDDropDownItem
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.imagelist import SmartTileWithStar, SmartTileWithLabel
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineAvatarIconListItem, IRightBodyTouch, IRightBody, OneLineAvatarListItem
from kivymd.uix.menu import MDDropdownMenu

import HIMO
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.snackbar import Snackbar

from kivymd.utils import asynckivy
from akivymd.uix.piechart import AKPieChart

import gc
from HIMO import *
from colors import *

from demos.circular_progress_bar import *
from PIL import Image as PILImage


kivy.require("1.11.1")
# print(kivy.version)
# myo.init('X:\\Sapientia EMTE\\Szakmai Gyakorlat\\v2\\HIMO\\myo64.dll')
MAX_SIZE = (1300, 800)


# Configure app.
Window.clearcolor = GREY
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'fullscreen', '0')
Window.size = MAX_SIZE
Config.set('modules', 'monitor', '') #Show fps and input debug bar

# register a new Cache
Cache.register('test', limit=10)


# This class from Myo-python SDK listens to EMG signals from armband and other events

class Listener(myo.DeviceListener):

    def __init__(self):
        self.synced = False
        self.connected = False
        self.battery_level = 0
        self.connected = False

    def on_connected(self, event):
        self.battery_level = event.device.request_battery_level()
        self.connected = True

    def on_arm_synced(self, event):
        self.synced = True
        # self.battery_level = event.battery_level
        self.battery_level = event.device.request_battery_level()
        # print("Arm synced!")

    def on_arm_unsynced(self, event):
        self.synced = False
        # print("Arm unsynced!")

    def on_battery_level(self, event):
        self.battery_level = event.battery_level
        print("Battery:" + str(self.battery_level))

    def on_warmup_completed(self, event):
        print("Warmup completed!")

    def on_disconnected(self, event):
        self.connected = False


class CustomSnackbar(Snackbar):
    icon = StringProperty()
    message = StringProperty()
    sb_color = StringProperty('000000')

    def __init__(self, **kwargs):
        super(CustomSnackbar, self).__init__(**kwargs)


# region HOME_PAGE
class Home(Screen):
    battery_label = ObjectProperty()
    synced_label = ObjectProperty()
    text_box = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Home, self).__init__(**kwargs)
        # print("HOME SCREEN")

        # TODO: DONE check if myo is connected and synced
        # TODO: DONE display battery life
        # self.myo = Image(source='/resources/myo.jpg')
        self.synced = False
        self.connected = False
        self.battery = 0
        try:
            if check_if_process_running('Myo Connect.exe'):
                self.hub = myo.Hub()
                self.listener = Listener()
                Clock.schedule_interval(self.update_status, 3.0)
                pass
            else:
                print("MYO NOT CONNECTED")
                Clock.schedule_interval(self.update_status, 10.0)
                pass
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)

    def show_snackbar(self, *args):
        himo_app.show_snackbar("MYO Connect restarted", INFO_ICON, YELLOW_HEX)

    def restart_myo(self, *args):
        try:
            t = threading.Thread(target=restart_process)
            t.start()
            print("RESTARTING MYO CONNECT!")
            del t
        except:
            print("Error.")

    def on_start(self, *args):
        self.ids.connect_label.text = CONNECT_LABEL + MARKUP_RED[0] + "DISCONNECTED" + MARKUP_RED[1]
        self.ids.synced_label.text = SYNC_LABEL + MARKUP_RED[0] + "UNSYNCED" + MARKUP_RED[1]
        self.ids.battery_label.text = "BATTERY LEVEL: NO INFORMATION"

    def update_status(self, *args):
        # restart_process()
        def check_myo_status():
            if check_if_process_running('Myo Connect.exe'):
                # print("Running")
                if not self.hub:
                    self.hub = myo.Hub()
                    self.listener = Listener()
                self.hub.run(self.listener.on_event, 10)
                # print(listener.battery_level)
                self.synced = self.listener.synced
                self.battery = self.listener.battery_level
                self.connected = self.listener.connected
            else:
                # MYO not connected
                # print("MYO ARMBAND IS NOT CONNECTED")
                self.connected = False
                self.synced = False
                self.battery = 0

        if himo_app.root.ids.screen_manager.current_screen != self:
            Clock.unschedule(self.update_status)

        t = threading.Thread(target=check_myo_status)
        t.start()
        t.join()
        # Display labels and progress bar
        if self.connected:
            # print("Connected")
            himo_app.myo_connected = True
            self.ids.connect_label.text = CONNECT_LABEL + MARKUP_GREEN[0] + "CONNECTED" + MARKUP_GREEN[1]
            if self.synced:
                # print("SYNCED")
                himo_app.myo_synced = True
                self.ids.synced_label.text = SYNC_LABEL + MARKUP_GREEN[0] + "SYNCED" + MARKUP_GREEN[1]
                self.ids.battery_label.text = BATTERY_LABEL + MARKUP_YELLOW[0] + str(self.battery) + "%" + \
                                              MARKUP_YELLOW[1]
            else:
                himo_app.myo_synced = False
                # print("NOT SYNCED")
                self.ids.synced_label.text = SYNC_LABEL + MARKUP_RED[0] + "UNSYNCED" + MARKUP_RED[1]
                self.ids.battery_label.text = BATTERY_LABEL + MARKUP_YELLOW[0] + str(self.battery) + "%" + \
                                              MARKUP_YELLOW[1]
        else:
            himo_app.myo_connected = False
            # print("Disconnected")
            # print("NOT SYNCED")
            self.ids.connect_label.text = CONNECT_LABEL + MARKUP_RED[0] + "DISCONNECTED" + MARKUP_RED[1]
            self.ids.synced_label.text = SYNC_LABEL + MARKUP_RED[0] + "UNSYNCED" + MARKUP_RED[1]
            self.ids.battery_label.text = BATTERY_LABEL + MARKUP_YELLOW[0] + "NO INFORMATION" + MARKUP_YELLOW[1]

        # Display last sync time:
        self.ids.last_update.text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# endregion

# region BROWSE_PAGE
global img_name
img_path = ""


class ImageList(BoxLayout):
    global img_path

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # global img_name
        # print("PATH:" + img_path)
        self.add_widget(Image(source=img_path))
        # Clock.schedule_once(self.on_start, 1)

    pass

    def on_start(self, *l):
        # print("PATH:" + img_path)
        self.add_widget(Image(source=img_path))
        # self.ids.img_dialog.source = img_path


class ImageTile(TouchRippleBehavior, SmartTileWithLabel):
    dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_name = ""

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # print(self.text)
            # I want to replicate a ripple behaviour here
            touch.grab(self)
            self.ripple_duration_in = 0.7
            self.ripple_color = [MYOBLUE[0], MYOBLUE[1], MYOBLUE[2], self.ripple_fade_from_alpha]
            self.ripple_scale = 1
            self.ripple_show(touch)

            self.image_name = self.text
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)

            self.ripple_duration_out = 0.4
            self.ripple_fade()
            self.ripple_fade()

            self.open_dialog()
            return True
        return False

    def open_dialog(self):
        global img_path
        # Open a dalog containing image zoomed in
        # print(self.image_name)
        if not self.dialog:
            path = "X:/Sapientia EMTE/Szakmai Gyakorlat/v2/HIMO/data/results/figures/" + self.image_name
            img_path = path
            self.dialog = MDDialog(
                title=self.image_name,
                type="custom",
                content_cls=ImageList(),
                buttons=[
                    # MDFlatButton(
                    #     text="CANCEL", text_color=self.theme_cls.primary_color
                    # ),
                ],
            )
            del img_path
            del path
            gc.collect()
        self.dialog.open()
        # self.dialog.buttons[0].bind(on_release=self.dialog.close())


# TODO: BRowse page - complete redesign


class ExerciseContent(MDBoxLayout):
    correct = StringProperty('0')
    missed = StringProperty('0')
    pass


class ResultContent(MDBoxLayout):
    result_data = {}
    percentage = 0
    efficiency_color = ObjectProperty([0, 0.7411, 0.87, 1])
    def __init__(self, **kwargs):
        super(ResultContent, self).__init__(**kwargs)
        Clock.schedule_once(self.on_start)

    def on_start(self, *args):
        self.tiptoe_done = self.result_data['Tiptoe'][0]['Correct']
        self.tiptoe_missed = self.result_data['Tiptoe'][0]['Missed']

        self.heel_done = self.result_data['Heel'][0]['Correct']
        self.heel_missed = self.result_data['Heel'][0]['Missed']

        self.tiptoe_total = self.tiptoe_done + self.tiptoe_missed

        self.heel_total = self.heel_done + self.heel_missed

        self.total_total = self.result_data['Total'][0]['Correct'] + \
                           self.result_data['Total'][0]['Missed']

        # Display data, charts, and training efficency
        self.results = {
            'Tiptoe': [{
                'Correct': self.tiptoe_done * 100 / self.tiptoe_total,
                'Missed': self.tiptoe_missed * 100 / self.tiptoe_total
            }],
            'Heel': [{
                'Correct': self.heel_done * 100 / self.heel_total,
                'Missed': self.heel_missed * 100 / self.heel_total
            }],
            'Total': [{
                'Correct': (self.tiptoe_done + self.heel_done) * 100 / self.total_total,
                'Missed': (self.tiptoe_missed + self.heel_missed) * 100 / self.total_total
            }]
        }

        tiptoe_results = self.results['Tiptoe']
        heel_results = self.results['Heel']
        total_results = self.results['Total']

        # region Tiptoe results
        tiptoe_chart = AKPieChart(
            items=tiptoe_results, pos_hint={'center_x': 0.5, 'center_y': .5},
            size_hint=[None, None],
            size=(dp(100), dp(100))
        )
        self.ids.tiptoe_results.add_widget(tiptoe_chart)
        self.ids.tiptoe_results.add_widget(
            MDLabel(text="TIPTOE",
                    halign="center")
        )

        tiptoe_content = ExerciseContent()
        tiptoe_content.correct = str(self.tiptoe_done)
        tiptoe_content.missed = str(self.tiptoe_missed)
        self.ids.tiptoe_results.add_widget(tiptoe_content)
        # endregion
        # region Heel results
        heel_chart = AKPieChart(
            items=heel_results, pos_hint={'center_x': 0.5, 'center_y': .5},
            size_hint=[None, None],
            size=(dp(100), dp(100))
        )
        self.ids.heel_results.add_widget(heel_chart)
        self.ids.heel_results.add_widget(
            MDLabel(text="HEEL",
                    halign="center")
        )

        heel_content = ExerciseContent()
        heel_content.correct = str(self.heel_done)
        heel_content.missed = str(self.heel_missed)
        self.ids.heel_results.add_widget(heel_content)
        # endregion
        # region Total results
        total_chart = AKPieChart(
            items=total_results, pos_hint={'center_x': 0.5, 'center_y': .5},
            size_hint=[None, None],
            size=(dp(100), dp(100))
        )
        self.ids.total_results.add_widget(total_chart)
        self.ids.total_results.add_widget(
            MDLabel(text="TOTAL",
                    halign="center")
        )

        total_content = ExerciseContent()
        total_content.correct = str(self.heel_done + self.tiptoe_done)
        total_content.missed = str(self.heel_missed + self.tiptoe_missed)
        self.ids.total_results.add_widget(total_content)
        # endregion

        # Display efficiency percentage in a progressbar
        self.efficiency_color = [0, 1, .25, 1]
        bar = self.ids.efficiency_container.children[0]
        bar.value = int(self.percentage)

        del bar
        del total_results
        del heel_results
        del tiptoe_results

class ResultCard(MDCard, ThemableBehavior, HoverBehavior):
    '''Custom item implementing hover behavior.'''
    efficiency = StringProperty('69%')
    normal_color = ListProperty([1,1,1,1])
    bg_color = ObjectProperty([1,1,1,1])
    result_data = {}
    dialog = None

    def __init__(self, **kwargs):
        super(ResultCard, self).__init__(**kwargs)
        self.hover_color = [1,1,1,1]
        Clock.schedule_once(self.init_colors)

    def init_colors(self, *l):
        self.normal_color = self.calculate_card_color()
        self.hover_color = [self.normal_color[0], self.normal_color[1] - 0.15, self.normal_color[2], 1]
        self.bg_color = self.normal_color

    def calculate_card_color(self):
        if int(self.efficiency.split('%')[0]) < 50:
            return EFF_GREY
        elif int(self.efficiency.split('%')[0]) < 70:
            return EFF_BLUE
        elif int(self.efficiency.split('%')[0]) < 90:
            return EFF_PURPLE
        else:
            return EFF_GOLD

    # Animation to simulate smooth hover
    def color_hover(self, *args):
        anim = Animation(bg_color=self.normal_color, duration=0.01) + \
               Animation(bg_color=self.hover_color, duration=0.2)
        anim.start(self)

    def hover_back(self, *args):
        anim = Animation(bg_color=self.hover_color, duration=0.01) + \
               Animation(bg_color=self.normal_color, duration=0.25)
        anim.start(self)

    def on_enter(self, *args):
        '''The method will be called when the mouse cursor
        is within the borders of the current widget.'''
        # print("hover")
        Clock.schedule_once(self.color_hover)

    def on_leave(self, *args):
        '''The method will be called when the mouse cursor goes beyond
        the borders of the current widget.'''
        Clock.schedule_once(self.hover_back)
        # self.dialog = None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            pass
            # print("GECI")
            # return True
        # return False
        super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.open_result_dialog(self.result_data)
            # return True
            pass
        # return False
        super().on_touch_up(touch)

    def open_result_dialog(self, result_data):
        if not self.dialog:
            self.content = ResultContent()
            self.content.result_data = result_data
            self.content.percentage = self.efficiency.split('%')[0]
            self.dialog = MDDialog(
                title="Session info",
                type="custom",
                content_cls=self.content,
                buttons=[
                    MDFlatButton(
                        text="CANCEL", text_color=MYOBLUE, on_release=self.close_dialog
                    )
                ],
            )
            self.dialog.open()

    def close_dialog(self, *l):
        self.dialog.dismiss()
        self.dialog = None



class Content(MDBoxLayout):
    '''Custom content.'''
    information = StringProperty('')
    pass

class Browse(Screen):
    menu = ObjectProperty(None)
    dropdown_menu = StringProperty()
    average_color = ObjectProperty([0, 0.7411, 0.87, 1])

    sname = StringProperty('John')
    sage = StringProperty('18')
    sgender = StringProperty('Male')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("ANALYSIS SCREEN")
        Clock.schedule_once(self.on_start)
        self.menu_items = []
        self.subject_name = ""

        self.figures = "X:/Sapientia EMTE/Szakmai Gyakorlat/v2/HIMO/data/results/figures"
        self.subjects = []
        self.results = []

        self.sum_of_efficiencies = 0
        self.average = 0
    def on_start(self, *l):
        ''' Set dropdown items '''
        with open(himo_app.subjects_file, 'r') as data_file:
            data = json.load(data_file)

        for element in data['Subjects']:
            self.subjects.append(element)
            self.menu_items.append(
                {
                    "viewclass": "HoverItem",
                    "text": element['Name'],
                    "theme_text_color": "Custom",
                    "text_color": [0, 0, 0, 1],
                }
            )
        self.menu = MDDropdownMenu(
            # id="dropdown_menu",
            caller=self.ids.drop_subjects,
            items=self.menu_items,
            position="auto",
            callback=self.set_item,
            selected_color=MYOBLUE,
            width_mult=3,
        )
        ''' Create image container layout '''
        nr_of_images = len(glob.glob1(self.figures, "*.png"))
        self.image_layout = MDGridLayout(
            # id = "imglayout",
            cols=4,
            rows=nr_of_images,
            adaptive_height=True,
            padding=["40dp", "40dp"],
            spacing="4dp"
        )
        counter = 0
        # Create image tiles and display in layout
        for filename in os.listdir(self.figures):
            if counter < nr_of_images:
                if filename.endswith(".png"):
                    fpath = self.figures + "/" + filename
                    image = ImageTile(
                        # allow_stretch = False,
                        size_hint_y=None,
                        height="120dp",
                        source=fpath,
                        text=filename,
                        tile_text_color=himo_app.theme_cls.primary_color
                    )
                    self.image_layout.add_widget(image)
                    counter += 1
            else:
                break
        self.ids.scroll_images.add_widget(self.image_layout)

        # Display all models
        self.set_available_cards("", True)

        del counter
        del data
        del fpath
        del image
        del nr_of_images
        gc.collect()

        # Display expansion panel

    def set_item(self, instance):
        bar = self.ids.average_container.children[0]
        bar.value = 0

        self.ids.drop_subjects.set_item(instance.text)

        self.subject_name = instance.text

        self.update_subject_info(instance.text)

        self.update_result_info(instance.text)

        self.update_average_bar()

        self.update_image_list(instance.text, True)
        self.menu.dismiss()
        del bar
        gc.collect()


    def update_average_bar(self):
        try:
            number_of_sessions = len(self.ids.scroll_results.children)
            self.average = self.sum_of_efficiencies / number_of_sessions
        except Exception as e:
            if hasattr(e,'message'):
                print( "Exception: " + str(e.message) )
            else:
                print( "Exception: " + str(e))

        Clock.schedule_interval(self.animate_average, 0.01)
    def animate_average(self, dt):
        bar = self.ids.average_container.children[0]
        if bar.value < bar.max:
            bar.value_normalized += 0.001
            if bar.value == floor(self.average):
                Clock.unschedule(self.animate_average)

    def update_subject_info(self, name):
        with open(himo_app.subjects_file, 'r') as data_file:
            data = json.load(data_file)

        for element in data['Subjects']:
            if element['Name'] == name:
                self.sname = element['Name']
                self.sage = str(element['Age'])
                self.sgender = element['Gender']

    def update_result_info(self, name):
        # Reset calculations
        self.ids.scroll_results.clear_widgets()
        gc.collect()
        self.sum_of_efficiencies = 0
        self.average = 0

        # Update data and calculate numbers
        with open(himo_app.results_file, 'r') as data_file:
            data = json.load(data_file)

        for element in data['Results']:
            if element.get(name):
                # print(element[name])
                percentage = element[name]['Total'][0]['Correct'] * 100 / (
                        element[name]['Total'][0]['Correct'] + element[name]['Total'][0]['Missed'])
                card = ResultCard()
                card.efficiency = str(int(percentage)) + ' %'
                card.normal_color = card.calculate_card_color()
                card.result_data = element[name]
                self.sum_of_efficiencies += int(percentage)
                self.ids.scroll_results.add_widget(card)
                del card
            else:
                pass
        gc.collect()

    def update_image_list(self, text="", search=False):
        # print(text)

        # Meaning we have an actual subject with that text/name
        def add_image(self, path, filename):
            image = ImageTile(
                # allow_stretch=False,
                size_hint_y=None,
                height="120dp",
                source=path,
                text=filename,
                tile_text_color=himo_app.theme_cls.primary_color
            )
            self.image_layout.add_widget(image)

        # Empty text - display all images
        if text == "":
            for filename in os.listdir(self.figures):
                if search:
                    if filename.endswith(".png"):
                        fpath = self.figures + "/" + filename
                        add_image(self, fpath, filename)

        if text != "" and self.subject_name:
            # Clear image list
            self.image_layout.clear_widgets()
            gc.collect()
            # Update image list
            for filename in os.listdir(self.figures):
                if search:
                    model = "=" + text + "="
                    if model in filename and filename.endswith(".png"):
                        fpath = self.figures + "/" + filename
                        add_image(self, fpath, filename)

        del model
        del fpath
        gc.collect()

    def set_available_cards(self, text="", search=False):
        '''Builds a list of icons for the screen MDIcons.'''
        self.menu_items.clear()

        def add_filename(self, filename):
            self.menu_items.append(
                {
                    "viewclass": "HoverItem",
                    "text": filename,
                    "theme_text_color": "Custom",
                    "text_color": [0, 0, 0, 1],
                }
            )

class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)


# endregion

# region DASHBOARD_PAGE
class Dashboard(Screen):
    pass


# endregion

# region EXERCISES_PAGE

# Animation widget for color changing
class Pulser(Widget):
    bg_color = ObjectProperty([0, 0.7411, 0.87, 1])

    def __init__(self, **kwargs):
        super(Pulser, self).__init__(**kwargs)

    #  RIGHT EXERCISE
    def right_pulsing(self, *args):
        anim = Animation(bg_color=[0, 1, .3, 1], duration=0.4) + \
               Animation(bg_color=[0, 0.7411, 0.87, 1], duration=0.2)
        anim.start(self)

    #     WRONG EXERCISE
    def wrong_pulsing(self, *args):
        anim = Animation(bg_color=[1, 0, .3, 1], duration=0.4) + \
               Animation(bg_color=[0, 0.7411, 0.87, 1], duration=0.2)
        anim.start(self)


class IncrediblyCrudeClock(Label):
    a = NumericProperty(5)  # seconds

    def start(self):
        Animation.cancel_all(self)  # stop any current animations
        self.anim = Animation(a=0, duration=self.a)

        def finish_callback(animation, incr_crude_clock):
            incr_crude_clock.text = "FINISHED"

        self.anim.bind(on_complete=finish_callback)
        self.anim.start(self)


class MyRoundFlatButton(MDRoundFlatButton, ThemableBehavior, HoverBehavior):
    '''Custom item implementing hover behavior.'''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self, *args):
        '''The method will be called when the mouse cursor
        is within the borders of the current widget.'''
        self.text_color = (1,1,1,1)
        self.md_bg_color = (0,1,.65,1)

    def on_leave(self, *args):
        '''The method will be called when the mouse cursor goes beyond
        the borders of the current widget.'''
        self.text_color = (1, 1, 1, 1)
        # self.md_bg_color = None
        self.md_bg_color = (0,1,.35,1)


class SubjectInfo(MDBoxLayout):
    pass


class SessionInfo(MDBoxLayout):
    pass


class Exercises(Screen):
    countdown = NumericProperty()
    tiptoe_timer = StringProperty('00:00')

    models_menu = ObjectProperty(None)
    session_menu = ObjectProperty(None)
    status_color = ObjectProperty([1, 1, 1, 1])
    sb_color = StringProperty('111111')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        gc.collect()
        print("PREDICT SCREEN")
        # self.counter = 10
        self.result = ""
        self.active_page = 0

        # Check Myo status
        # self.status_color = MYOBLUE
        Clock.schedule_interval(self.set_status_color, 1)

        self.session_started = False
        # Exercises set/session:
        # TODO: dropdown with selectable sessions
        self.tiptoe_done = 0
        self.tiptoe_required = 5

        self.heel_done = 0
        self.heel_required = 5

        # Select model/suject
        # TODO: dropdown with selectable models
        self.subject = ""
        self.subjects = []
        self.model = None
        self.selected_session = False
        self.sessions = []
        self.q = queue.Queue()

        # Timer variales - 5 second count down
        self.startcountdown = 5
        self.countdown = self.startcountdown
        self.exercise_timeout = 3

        Clock.schedule_once(self.on_start, 0)

        self.tiptoe_timer = '0:00'
        self.start = str(time.time())
        self.end = self.start
        self.menu_items = []
        # Results
        # ---------------------good-bad-total
        self.tiptoe_missed = 0
        self.heel_missed = 0

        self.tiptoe_total = 0
        self.heel_total = 0
        self.total_total = 0

        self.results = {}
        self.saved = False

    def set_status_color(self, *l):
        # print("SET COLOR")
        if himo_app.myo_connected:
            self.status_color = YELLOW
            self.sb_color = YELLOW_HEX
            if himo_app.myo_synced:
                self.status_color = GREEN
                self.sb_color = GREEN_HEX
                Clock.unschedule(self.set_status_color)
                Clock.schedule_interval(self.set_status_color, 10)
            else:
                # self.status_color = MYOBLUE
                pass
        else:
            self.sb_color = RED_HEX
            self.status_color = RED

    def on_pre_enter(self, *args):
        Window.size = MAX_SIZE[0] + 1, MAX_SIZE[1] + 1
        # print("Screen size SET")
        Window.size = MAX_SIZE
        # Clock.schedule_once(self.on_start, 0)
        # gc.collect()

    def on_start(self, *l):
        bar = self.ids.heel_circ_parent.children[0]
        bar.value_normalized = 0

        bar = self.ids.tiptoe_circ_parent.children[0]
        bar.value_normalized = 0

        # Fill up dropdown list
        ''' Set dropdown items '''
        with open(himo_app.subjects_file, 'r') as data_file:
            data = json.load(data_file)

        for element in data['Subjects']:
            self.subjects.append(element)
            self.menu_items.append(
                {
                    "viewclass": "HoverItem",
                    "text": element['Name'],
                    "theme_text_color": "Custom",
                    "text_color": [0, 0, 0, 1],
                }
            )
        self.models_menu = MDDropdownMenu(
            # id="dropdown_menu",
            caller=self.ids.drop_models,
            items=self.menu_items,
            position="auto",
            callback=self.set_subject,
            selected_color=MYOBLUE,
            width_mult=4,
        )
        self.menu_items.clear()
        for element in data['Sessions']:
            self.sessions.append(element)
            self.menu_items.append(
                {
                    "viewclass": "HoverItem",
                    "text": 'TIPTOE - ' + str(element['Tiptoe']) + ' / HEEL - ' + str(element['Heel']),
                    "theme_text_color": "Custom",
                    "text_color": [0, 0, 0, 1],
                }
            )
        self.session_menu = MDDropdownMenu(
            # id="dropdown_menu",
            caller=self.ids.drop_sessions,
            items=self.menu_items,
            position="auto",
            callback=self.set_session,
            selected_color=MYOBLUE,
            width_mult=6,
        )
        # DEBUG CPB
        del bar
        del data
        gc.collect()
        # self.active_page = 1
        # Clock.schedule_interval(self.animate, 0.01)

    def set_subject(self, instance):
        # self.ids.drop_models.set_item(instance.text.split('_')[0])
        self.ids.drop_models.set_item(instance.text)
        if len(self.ids.subject_panel.children) == 1:
            self.ids.subject_panel.add_widget(SubjectInfo())

        self.ids.subject_panel.children[0].ids.name_label.text = next((str(i['Name']) for i in self.subjects if
                                                                       i['Name'] == instance.text), None)
        self.ids.subject_panel.children[0].ids.age_label.text = next((str(i['Age']) for i in self.subjects if
                                                                      instance.text == i['Name']), None)
        self.ids.subject_panel.children[0].ids.gender_label.text = next((str(i['Gender']) for i in self.subjects if
                                                                         i['Name'] == instance.text), None)
        self.models_menu.dismiss()
        gc.collect()

        self.subject = instance.text

    def set_session(self, instance):
        # self.ids.drop_models.set_item(instance.text.split('_')[0])
        self.ids.drop_sessions.set_item(instance.text)
        if len(self.ids.session_panel.children) == 1:
            self.ids.session_panel.add_widget(SessionInfo())

        self.ids.session_panel.children[0].ids.tiptoe_label.text = next(
            (str(i['Tiptoe']) for i in self.sessions if
             'TIPTOE - ' + str(i['Tiptoe']) + ' / HEEL - ' + str(i['Heel']) == instance.text), None)
        self.ids.session_panel.children[0].ids.heel_label.text = next(
            (str(i['Heel']) for i in self.sessions if
             'TIPTOE - ' + str(i['Tiptoe']) + ' / HEEL - ' + str(i['Heel']) == instance.text), None)
        self.session_menu.dismiss()
        gc.collect()

        self.selected_session = True

    # TODO: display expansion panel with info about this page
    # TODO: DONE create timer function

    def check_for_switch_exercise(self, *args):
        # Switch to second exercise
        if self.tiptoe_required == self.tiptoe_done:
            Clock.schedule_once(self.set_next_page, .5)
            # Clock.unschedule(self.timer)
            Clock.unschedule(self.check_for_switch_exercise)


    def check_for_switch_results(self, *args):
        # Switch to results page
        if self.tiptoe_required <= self.tiptoe_done and self.heel_done >= self.heel_required:
            HIMO.session_finished = True
            Clock.unschedule(self.check_for_switch_results)
            Clock.unschedule(self.timer)
            Clock.unschedule(self.exercise_callback)
            Clock.unschedule(self.get_result)


            Clock.schedule_once(self.set_next_page, .5)
            self.create_charts()
            self.ids.start_button.text = "RESTART"

    def set_next_page(self, *l):
        self.active_page += 1
        self.ids.session_nav.switch_tab(str(self.active_page))

    def create_charts(self):
        self.tiptoe_total = (self.tiptoe_done + self.tiptoe_missed)
        self.heel_total = (self.heel_done + self.heel_missed)
        self.total_total = self.tiptoe_total + self.heel_total
        self.results = {
            'Tiptoe': [{
                'Correct': self.tiptoe_done * 100 / self.tiptoe_total,
                'Missed': self.tiptoe_missed * 100 / self.tiptoe_total
            }],
            'Heel': [{
                'Correct': self.heel_done * 100 / self.heel_total,
                'Missed': self.heel_missed * 100 / self.heel_total
            }],
            'Total': [{
                'Correct': (self.tiptoe_done + self.heel_done) * 100 / self.total_total,
                'Missed': (self.tiptoe_missed + self.heel_missed) * 100 / self.total_total
            }]
        }

        tiptoe_results = self.results['Tiptoe']
        heel_results = self.results['Heel']
        total_results = self.results['Total']

        tiptoe_chart = AKPieChart(
            items=tiptoe_results, pos_hint={'center_x': 0.5, 'center_y': .5},
            size_hint=[None, None],
            size=(dp(150), dp(150))
        )
        self.ids.tiptoe_chart_container.add_widget(tiptoe_chart)
        self.ids.tiptoe_result_container.add_widget(
            MDLabel(text="Correct: " + str(self.tiptoe_done),
                    theme_text_color="ContrastParentBackground",
                    halign="center")
        )
        self.ids.tiptoe_result_container.add_widget(
            MDLabel(text="Missed: " + str(self.tiptoe_missed),
                    theme_text_color="ContrastParentBackground",
                    halign="center")
        )
        self.ids.tiptoe_result_container.add_widget(
            MDLabel(text="Total: " + str(self.tiptoe_total),
                    theme_text_color="ContrastParentBackground",
                    halign="center")
        )
        # Heel results:
        self.ids.heel_chart_container.add_widget(
            AKPieChart(
                items=heel_results, pos_hint={'center_x': 0.5, 'center_y': .5},
                size_hint=[None, None],
                size=(dp(150), dp(150))
            )
        )

        self.ids.heel_result_container.add_widget(
            MDLabel(text="Correct: " + str(self.heel_done),
                    theme_text_color="ContrastParentBackground",
                    halign="center"
                    )
        )
        self.ids.heel_result_container.add_widget(
            MDLabel(text="Missed: " + str(self.heel_missed),
                    theme_text_color="ContrastParentBackground",
                    halign="center"
                    )
        )
        self.ids.heel_result_container.add_widget(
            MDLabel(text="Total: " + str(self.heel_total),
                    theme_text_color="ContrastParentBackground",
                    halign="center"
                    )
        )
        # Total results:
        self.ids.total_chart_container.add_widget(
            AKPieChart(
                items=total_results, pos_hint={'center_x': 0.5, 'center_y': .5},
                size_hint=[None, None],
                size=(dp(150), dp(150))
            )
        )

        self.ids.total_result_container.add_widget(
            MDLabel(text="Correct: " + str(self.heel_done + self.tiptoe_done),
                    theme_text_color="ContrastParentBackground",
                    halign="center"
                    )
        )
        self.ids.total_result_container.add_widget(
            MDLabel(text="Missed: " + str(self.heel_missed + self.tiptoe_missed),
                    theme_text_color="ContrastParentBackground",
                    halign="center"
                    )
        )
        self.ids.total_result_container.add_widget(
            MDLabel(text="Total: " + str(self.total_total),
                    theme_text_color="ContrastParentBackground",
                    halign="center"
                    )
        )

    def reset_progress(self, *l):
        bar = self.ids.tiptoe_circ_parent.children[0]
        bar.value = 0

        bar = self.ids.heel_circ_parent.children[0]
        bar.value = 0

        self.ids.tiptoe_chart_container.clear_widgets()
        self.ids.heel_chart_container.clear_widgets()
        self.ids.total_chart_container.clear_widgets()

        self.ids.tiptoe_result_container.clear_widgets()
        self.ids.heel_result_container.clear_widgets()
        self.ids.total_result_container.clear_widgets()
        gc.collect()

        print("PROGRESS RESET")

    def add_progress(self, *l):
        # Progress bar
        if self.active_page == 1:
            if self.result == "TIP TOE":
                event = Clock.schedule_interval(self.animate, 0.01)
                # Color change
                Clock.schedule_once(self.ids.tiptoe_pulser.right_pulsing, 0.01)
                # Label change
                Clock.schedule_once(self.inc_tiptoe, 0)
            else:
                self.tiptoe_missed += 1
                Clock.schedule_once(self.ids.tiptoe_pulser.wrong_pulsing, 0.01)

            # Switch to next set page
            Clock.schedule_once(self.check_for_switch_exercise)
        elif self.active_page == 2:
            if self.result == "TOE CRUNCH":
                event = Clock.schedule_interval(self.animate, 0.01)
                # Color change
                Clock.schedule_once(self.ids.heel_pulser.right_pulsing, 0.01)
                # Label change
                Clock.schedule_once(self.inc_heel, 0)
            else:
                self.heel_missed += 1
                Clock.schedule_once(self.ids.heel_pulser.wrong_pulsing, 0.01)

            # Switch to results page
            Clock.schedule_once(self.check_for_switch_results)
        else:
            # We're on the results page
            pass

    # TODO: RESET before starting again

    # Simple animation to show the circular progress bar in action
    def animate(self, dt):
        # # Showcase that setting the values using value_normalized property also works
        if self.active_page == 1:
            bar = self.ids.tiptoe_circ_parent.children[0]
            bar.max = self.tiptoe_required * 10
            required = self.tiptoe_required
        else:
            bar = self.ids.heel_circ_parent.children[0]
            bar.max = self.heel_required * 10
            required = self.heel_required
        if bar.value < bar.max:
            bar.value_normalized += 0.0001
            # print(bar.value)
            # if bar.value % floor((bar.max / int(required))) == 0:
            if bar.value % 10 == 0:
                # Means a tiptoe is done
                Clock.unschedule(self.animate)
                pass
        else:
            bar.value_normalized = 0

    def decr_countdown(self, *l):
        if self.countdown:
            self.countdown -= 1
            # print(self.countdown)

        else:
            # Set first page
            Clock.schedule_once(self.set_next_page, 0)

            # Start Timer.
            Clock.schedule_once(self.start_timer_thread, self.exercise_timeout)

            # START PREDICTING GESTURES
            # Clock.schedule_once(self.start_doing_exercise, self.exercise_timeout)
            Clock.schedule_once(self.get_model)

            Clock.schedule_once(self.get_result, self.exercise_timeout)

            Clock.unschedule(self.decr_countdown)

    def start_doing_exercise(self, *l):
        Clock.schedule_interval(self.get_result, 1)

    def start_timer_thread(self, *args):
        threading.Thread(target=self.start_timer).start()

    def start_timer(self, *l):
        # START tip toe timer
        self.start = time.time()
        Clock.schedule_interval(self.timer, 0.01)

    def timer(self, *l):
        self.tiptoe_timer = str((timedelta(seconds=time.time() - self.start)))

    def exercise_callback(self, *l):
        try:
            self.result = self.q.get_nowait()
            # self.result = self.q.get()
            print("RESULT: " + self.result)

            if self.result is not '':
                Clock.schedule_once(self.add_progress)

        except Exception as e:
            # print("EXCEPTION")
            pass

    # Subject name to load neural network model
    def inc_tiptoe(self, *l):
        self.tiptoe_done += 1
        self.ids.tiptoe.text = str(self.tiptoe_done) + '/' + str(self.tiptoe_required)
        # print(self.ids.tiptoe.text)

    def inc_heel(self, *l):
        self.heel_done += 1
        self.ids.heel.text = str(self.heel_done) + '/' + str(self.heel_required)
        # print(self.ids.heel.text)

    def start_exercises(self, *args):
        if himo_app.myo_synced:
            if self.subject is not "" or self.selected_session:
                HIMO.session_finished = False
                if not self.session_started:
                    print("STARTED")
                    # TODO: DONE start timer
                    # SET variables ( exercises required )
                    try:
                        self.tiptoe_required = int(self.ids.session_panel.children[0].ids.tiptoe_label.text)
                        self.heel_required = int(self.ids.session_panel.children[0].ids.heel_label.text)
                    except:
                        print("SELECT SUBJECT AND SESSION!")

                    # UPDATE labels
                    self.ids.tiptoe.text = str(self.tiptoe_done) + '/' + str(self.tiptoe_required)
                    self.ids.heel.text = str(self.heel_done) + '/' + str(self.heel_required)

                    # START COUNTDOWN
                    self.active_page = 0

                    Clock.schedule_interval(self.decr_countdown, 1)
                    self.session_started = True
                    self.ids.start_button.text = "STOP"
                else:
                    print("STOPPED")
                    Clock.unschedule(self.decr_countdown)
                    Clock.unschedule(self.get_result)
                    Clock.unschedule(self.start_timer)
                    Clock.unschedule(self.timer)
                    Clock.unschedule(self.exercise_callback)
                    HIMO.session_finished = False
                    Clock.schedule_once(self.reset_progress)
                    self.countdown = self.startcountdown
                    self.tiptoe_timer = '0:00'
                    self.start = time.time()
                    self.end = self.start

                    self.tiptoe_done = 0
                    self.heel_done = 0

                    # Set active page
                    self.active_page = -1
                    Clock.schedule_once(self.set_next_page, 0.1)

                    self.session_started = False
                    self.ids.start_button.text = "START"
            else:
                himo_app.show_snackbar("Select subject and session!", ERROR_ICON, RED_HEX)

        else:
            # Show snackbar
            # himo_app.root.screen_manager.current_screen..snackbar_show("MYO Armband is  not connected")
            himo_app.show_snackbar("Your MYO Armband is  not connected and synced!", ERROR_ICON, RED_HEX)

    def get_model(self, *l):
        self.model = load_model(result_path + self.subject + '_realistic_model.h5')

    def get_result(self, *l):
        try:
            self.q = Queue()
            # t = threading.Thread(target=PredictGestures, args=[self.subject, self.q])
            t = threading.Thread(target=PredictGesturesLoop, args=[self.model, self.q])
            t.start()
            # t.join()

            # Call evaluation almost instantly
            # Clock.schedule_interval(self.exercise_callback, .1)
            # self.result = self.q.get_nowait()
            # self.result = self.q.get()
            Clock.schedule_interval(self.exercise_callback, .1)

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)

    def write_json(self, data):
        with open(himo_app.results_file, 'w') as f:
            json.dump(data, f, indent=4)

    # SAVE exercise results
    def save_exercise_results(self, *args):
        if self.session_started:
            if not self.saved:
                try:
                    # Convert from percentages
                    self.results = {
                        'Tiptoe': [{
                            'Correct': self.tiptoe_done,
                            'Missed': self.tiptoe_missed
                        }],
                        'Heel': [{
                            'Correct': self.heel_done,
                            'Missed': self.heel_missed
                        }],
                        'Total': [{
                            'Correct': (self.tiptoe_done + self.heel_done),
                            'Missed': (self.tiptoe_missed + self.heel_missed)
                        }]
                    }
                    # Insert new data into json file, or create if doesnt exist
                    if not os.path.exists(himo_app.results_file):
                        data = {"Results": []}
                        self.write_json(data)

                    with open(himo_app.results_file) as f:
                        # json.dump(data, f, ensure_ascii=False, indent=4)
                        data = json.load(f)
                        temp = data['Results']

                        result_data = {self.subject: []}
                        self.results['Time'] = self.tiptoe_timer
                        self.results['Date'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        result_data[self.subject] = self.results

                        temp.append(result_data)

                    self.write_json(data)
                    self.saved = True
                    himo_app.show_snackbar("Results saved successfully!", CHECK_ICON, GREEN_HEX)
                except Exception as e:
                    if hasattr(e, 'message'):
                        print(e.message)
                        himo_app.show_snackbar("Couldn't save results: " + str(e.message), ERROR_ICON, RED_HEX)
                    else:
                        print(e)
                        himo_app.show_snackbar("Couldn't save results: " + str(e), ERROR_ICON, RED_HEX)
            else:
                himo_app.show_snackbar("Already saved!", INFO_ICON, YELLOW_HEX)
        else:
            himo_app.show_snackbar("Session is stopped!", INFO_ICON, YELLOW_HEX)


# endregion

# region UPLOAD_PAGE


class MyFloatingActionButtonVariant(MDFloatingActionButton, ThemableBehavior, HoverBehavior):
    '''Custom item implementing hover behavior.'''

    def on_enter(self, *args):
        '''The method will be called when the mouse cursor
        is within the borders of the current widget.'''
        self.md_bg_color = (0, 0.7411, 0.87, 1)
        self.text_color = (1, 1, 1, 1)

    def on_leave(self, *args):
        '''The method will be called when the mouse cursor goes beyond
        the borders of the current widget.'''
        self.md_bg_color = (1, 1, 1, 1)
        self.text_color = (0, 0.7411, 0.87, 1)


class MyFloatingActionButton(MDFloatingActionButton, ThemableBehavior, HoverBehavior):
    '''Custom item implementing hover behavior.'''

    def on_enter(self, *args):
        '''The method will be called when the mouse cursor
        is within the borders of the current widget.'''
        self.md_bg_color = (0, 0, 0, 1)
        self.text_color = (.75, .75, .75, 1)

    def on_leave(self, *args):
        '''The method will be called when the mouse cursor goes beyond
        the borders of the current widget.'''
        self.md_bg_color = (0, 0.7411, 0.87, 1)
        self.text_color = (1, 1, 1, 1)


class MyCard(MDCard, ThemableBehavior, HoverBehavior):
    '''Custom item implementing hover behavior.'''

    def on_enter(self, *args):
        '''The method will be called when the mouse cursor
        is within the borders of the current widget.'''
        # print("hover")
        self.md_bg_color = self.theme_cls.bg_light
        self.theme_text_color: "Custom"
        self.text_color = (0, 0, 1, 1)

    def on_leave(self, *args):
        '''The method will be called when the mouse cursor goes beyond
        the borders of the current widget.'''
        self.md_bg_color = (0, 0.7411, 0.87, 1)


class MySubjectCard(TouchRippleBehavior, MDCard, ThemableBehavior, HoverBehavior):
    '''Custom item implementing hover behavior.'''
    dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Name"
        self.age = "18"
        self.gender = "Male"
        self.snackbar = None
        self._interval = 0

    def on_enter(self, *args):
        '''The method will be called when the mouse cursor
        is within the borders of the current widget.'''
        if self.dialog is None:
            # print("hover")
            self.md_bg_color = self.theme_cls.bg_light
            self.theme_text_color: "Custom"
            self.text_color = (0, 0, 1, 1)
            self.width += 20
            self.height += 20

            self.ids.subject_data.add_widget(
                MDLabel(
                    text=self.age,
                    theme_text_color="Primary",
                    halign="center",
                    valign="center"
                )
            )
            self.ids.subject_data.add_widget(
                MDLabel(
                    text=self.gender,
                    theme_text_color="Primary",
                    halign="center",
                    valign="center"
                )
            )
            self.ids.modify_button.user_font_size = "26sp"
            self.ids.delete_button.user_font_size = "26sp"
            # gc.collect()
    def on_leave(self, *args):
        '''The method will be called when the mouse cursor goes beyond
        the borders of the current widget.'''
        self.md_bg_color = (0, 0.7411, 0.87, 1)
        self.width -= 20
        self.height -= 20
        # print(self.ids.modify_button.user_font_size)

        for child in self.ids.subject_data.children[:2]:
            self.ids.subject_data.remove_widget(child)

        self.ids.modify_button.user_font_size = "20sp"
        self.ids.delete_button.user_font_size = "20sp"
        # gc.collect()

    def open_edit_subject_dialog(self):
        content = ModifySubjectContent()
        content.ids.name_textfield.text = self.name
        content.ids.age_slider.value = self.age
        if self.gender == content.ids.male_check.gender:
            content.ids.male_check.active = True
        else:
            content.ids.female_check.active = True
            content.gender = self.gender

        # print(content.gender)
        def edit_subject(*args):
            try:
                with open(himo_app.subjects_file, 'r') as data_file:
                    data = json.load(data_file)

                for element in data['Subjects']:
                    if element['Name'] == self.name:
                        element.update((k, floor(content.age)) for k, v in element.items() if k == 'Age')
                        element.update((k, content.gender) for k, v in element.items() if k == 'Gender')
                    # print(element)

                with open(himo_app.subjects_file, 'w') as data_file:
                    data = json.dump(data, data_file, indent=4)

                self.close_dialog()
                himo_app.show_snackbar("Subject edited successfully!", CHECK_ICON, GREEN_HEX)
            except Exception as e:
                if hasattr(e, 'message'):
                    print(e.message)
                    himo_app.show_snackbar("Couldn't edit subject: " + e.message, ERROR_ICON, RED_HEX)
                else:
                    print(e)
                    himo_app.show_snackbar("Couldn't delete subject: " + e, ERROR_ICON, RED_HEX)
                pass

        if not self.dialog:
            self.dialog = MDDialog(
                title="Modify subject data",
                type="custom",
                content_cls=content,
                buttons=[
                    MDFlatButton(
                        text="CANCEL", text_color=MYOBLUE, on_release=self.close_dialog
                    ),
                    MDFlatButton(
                        text="CONFIRM", text_color=MYOBLUE, on_release=edit_subject
                    )
                ],
            )
        self.dialog.open()

    def open_delete_subject_dialog(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Delete Subject",
                buttons=[
                    MDFlatButton(
                        text="CANCEL", text_color=MYOBLUE, on_release=self.close_dialog
                    ),
                    MDFlatButton(
                        text="CONFIRM", text_color=MYOBLUE, on_release=self.delete_subject
                    )
                ],
            )
        self.dialog.open()

    def delete_subject(self, *l):
        try:
            with open(himo_app.subjects_file, 'r') as data_file:
                data = json.load(data_file)

            for element in data['Subjects']:
                if element['Name'] == self.name:
                    data['Subjects'].remove(element)
            with open(himo_app.subjects_file, 'w') as data_file:
                json.dump(data, data_file, indent=4)
            # print("subject deleted!")
            self.dialog.dismiss()
            gc.collect()

            del data
            himo_app.show_snackbar("Subject deleted successfully", ERROR_ICON, RED_HEX)

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
                himo_app.show_snackbar("Couldn't delete subject: " + e.message, RED_HEX)
            else:
                print(e)
                himo_app.show_snackbar("Couldn't delete subject: " + e.message, RED_HEX)
            # print("Exception:" e)

    def close_dialog(self, *l):
        self.dialog.dismiss()
        self.dialog = None
        self.parent.parent.parent.parent.parent.parent.parent.parent.set_tabs("Subjects")


# Upload page contents for each button


class AddSubjectContent(BoxLayout):
    name = StringProperty("")
    age = NumericProperty(1)
    gender = StringProperty("")

    male_check = ObjectProperty(True)
    female_check = ObjectProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ModifySubjectContent(AddSubjectContent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    pass


class Check(MDCheckbox):
    def on_checkbox_active(self, checkbox, value):
        self.parent.parent.parent.parent.gender = self.gender
        if value:
            print('The checkbox', checkbox, 'is active', 'and', checkbox.state, 'state')
        else:
            print('The checkbox', checkbox, 'is inactive', 'and', checkbox.state, 'state')
    # pass


class SubjectsContent(MDBoxLayout):
    dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.snackbar = None
        self._interval = 0
        self.x = 0
        self.y = 15
        self.content = None

        # Initialize creating cards
        Clock.schedule_once(self.on_start, 0)

    # open dialog with form
    def open_add_subject_dialog(self):
        self.content = AddSubjectContent()
        if not self.dialog:
            self.dialog = MDDialog(
                title="Add Subject",
                type="custom",
                content_cls=self.content,
                buttons=[
                    MDFlatButton(
                        text="CANCEL", text_color=MYOBLUE, on_release=self.close_dialog
                    ),
                    MDFlatButton(
                        text="CONFIRM", text_color=MYOBLUE, on_release=self.upload_subject
                    )
                ],
            )
        self.dialog.open()

    def close_dialog(self, *l):
        self.dialog.dismiss()
        # self.dialog = None
        gc.collect()


    def write_json(self, data):
        with open(himo_app.subjects_file, 'w') as f:
            json.dump(data, f, indent=4)

    def upload_subject(self, *l):
        # function to add to JSON
        # Build up dictionary
        try:
            self.subject = {
                # "Name": self.dialog.content_cls.ids.name_textfield.text,
                # "Age": floor(self.dialog.content_cls.ids.age_slider.value),
                # "Gender": self.dialog.content_cls.gender
                "Name": self.content.name,
                "Age": floor(self.content.age),
                "Gender": self.content.gender
            }
            # Insert new data into json file, or create if doesnt exist
            if os.path.exists(himo_app.subjects_file):
                with open(himo_app.subjects_file) as f:
                    # json.dump(data, f, ensure_ascii=False, indent=4)
                    data = json.load(f)
                    temp = data['Subjects']
                    temp.append(self.subject)

                self.write_json(data)

            self.close_dialog()
            himo_app.show_snackbar("Subject added successfully!", CHECK_ICON, GREEN_HEX)
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
                himo_app.show_snackbar("Couldn't add subject: " + str(e.message), RED_HEX)
            else:
                print(e)
                himo_app.show_snackbar("Couldn't add subject: " + str(e), RED_HEX)
            pass

    # Initialize stuff
    def on_start(self, *l):
        # Populate subject cards
        # Parent: subject_cards
        async def set_cards():
            try:
                if os.path.exists(himo_app.subjects_file):
                    with open(himo_app.subjects_file) as f:
                        # json.dump(data, f, ensure_ascii=False, indent=4)
                        data = json.load(f)
                        temp = data['Subjects']
                        # print(temp)
                        for card, index in zip(temp, range(0, len(temp))):
                            await asynckivy.sleep(0)
                            subject_card = MySubjectCard()
                            subject_card.ids.title.text = card['Name']
                            if int(card['Age']) <= 15:
                                subject_card.width = 150
                                subject_card.height = 200
                            elif int(card['Age']) >= 20:
                                subject_card.width = 200
                                subject_card.height = 250
                            else:
                                subject_card.width = card['Age'] * 10
                                subject_card.height = card['Age'] * 15
                            subject_card.name = card['Name']
                            subject_card.age = str(card['Age'])
                            subject_card.gender = card['Gender']
                            self.ids.subject_cards.add_widget(subject_card)
                        del temp
                        del data
                else:
                    print("No subject cards")
            except Exception as e:
                if hasattr(e, 'message'):
                    print(e.message)
                else:
                    print(e)
                pass

        asynckivy.start(set_cards())

    # def refresh_callback(self, *args):
    #     '''A method that updates the state of your application
    #     while the spinner remains on the screen.'''
    #
    #     def refresh_callback(interval):
    #         self.ids.subject_cards.clear_widgets()
    #         if self.x == 0:
    #             self.x, self.y = 15, 30
    #         else:
    #             self.x, self.y = 0, 15
    #         # Repopulate
    #         self.on_start()
    #         self.ids.refresh_layout.refresh_done()
    #         self.tick = 0
    #
    #     Clock.schedule_once(refresh_callback, 0.1)


class SessionListItem(OneLineAvatarIconListItem):
    '''Custom list item.'''
    text = StringProperty("")
    icon = StringProperty("")
    active = BooleanProperty(False)
    tiptoe = NumericProperty()
    heel = NumericProperty()

    def on_checkbox_active(self, checkbox, value):
        if value:
            print('The checkbox', checkbox, 'is active', 'and', checkbox.state, 'state')
            self.active = True
        else:
            self.active = False
            print('The checkbox', checkbox, 'is inactive', 'and', checkbox.state, 'state')

    def set_icon(self, name):
        self.icon = name


class RightLayout(IRightBody, MDBoxLayout):
    pass


class RightCheckbox(IRightBodyTouch, MDCheckbox):
    '''Custom right container.'''
    pass


class RightEditButton(IRightBodyTouch, MDFlatButton):
    '''Custom right container.'''
    pass


class AddSessionContent(MDBoxLayout):
    tiptoe = NumericProperty()
    heel = NumericProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class SessionContent(MDBoxLayout):
    dialog = None

    # TODO: add remove to list
    # TODO: edit session data
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.snackbar = None
        self._interval = 0
        self.content = None
        # Initialize creating cards
        self.session = {}
        self.sessions = []
        Clock.schedule_once(self.on_start, 0)

    pass

    # open dialog with form
    def open_add_session_dialog(self):
        self.content = AddSessionContent()
        if not self.dialog:
            self.dialog = MDDialog(
                title="Add Session",
                type="custom",
                content_cls=self.content,
                buttons=[
                    MDFlatButton(
                        text="CANCEL", text_color=MYOBLUE, on_release=self.close_dialog
                    ),
                    MDFlatButton(
                        text="CONFIRM", text_color=MYOBLUE, on_release=self.upload_session
                    )
                ],
            )
        self.dialog.open()
        gc.collect()

    def open_remove_session_dialog(self):
        self.content = AddSessionContent()
        if not self.dialog:
            self.dialog = MDDialog(
                title="Delete Session",
                type="custom",
                buttons=[
                    MDFlatButton(
                        text="CANCEL", text_color=MYOBLUE, on_release=self.close_dialog
                    ),
                    MDFlatButton(
                        text="CONFIRM", text_color=MYOBLUE, on_release=self.delete_session
                    )
                ],
            )
        self.dialog.open()
        gc.collect()

    def delete_session(self, *l):
        try:
            with open(himo_app.subjects_file, 'r') as data_file:
                data = json.load(data_file)

                # Search for the active checkboxes
                for item in self.ids.session_list.children:
                    if item.active:
                        # Search for element and delete from file/db
                        for element in data['Sessions']:
                            if element['Tiptoe'] == item.tiptoe and element['Heel'] == item.heel:
                                data['Sessions'].remove(element)
                                # self.ids.session_list.remove_widget(item)
                                break

            with open(himo_app.subjects_file, 'w') as data_file:
                data = json.dump(data, data_file, indent=4)
            # print("subject deleted!")
            self.dialog.dismiss()
            gc.collect()

            Clock.schedule_once(self.on_start, 0.1)
            himo_app.show_snackbar("Sessions removed!", CHECK_ICON, GREEN_HEX)

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
                himo_app.show_snackbar("ERROR! Couldn't remove sessions: " + e.message, ERROR_ICON, RED_HEX)

            else:
                print(e)
                himo_app.show_snackbar("ERROR! Couldn't remove sessions: " + e, ERROR_ICON, RED_HEX)

    def close_dialog(self, *l):
        self.dialog.dismiss()
        self.dialog = None
        gc.collect()


    def write_json(self, data):
        with open(himo_app.subjects_file, 'w') as f:
            json.dump(data, f, indent=4)

    def upload_session(self, *l):
        # function to add to JSON
        # Build up dictionary
        try:
            self.session = {
                "Tiptoe": floor(self.content.tiptoe),
                "Heel": floor(self.content.heel),
            }

            # Insert new data into json file, or create if doesnt exist
            if os.path.exists(himo_app.subjects_file):
                with open(himo_app.subjects_file) as f:
                    # json.dump(data, f, ensure_ascii=False, indent=4)
                    data = json.load(f)
                    temp = data['Sessions']
                    if {'Tiptoe': self.session['Tiptoe'], 'Heel': self.session['Heel']} not in temp:
                        temp.append(self.session)
                        self.write_json(data)
                        Clock.schedule_once(self.on_start, 0.1)
                        himo_app.show_snackbar("Session added successfully!", CHECK_ICON, GREEN_HEX)
                    else:
                        himo_app.show_snackbar("Sessions already in list!", INFO_ICON, YELLOW_HEX)

            self.close_dialog()
            gc.collect()

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
                himo_app.show_snackbar("ERROR! Couldn't add session: " + e.message, ERROR_ICON, RED_HEX)

            else:
                print(e)
                himo_app.show_snackbar("ERROR! Couldn't add session: " + e, ERROR_ICON, RED_HEX)

    # Initialize stuff
    def on_start(self, *l):
        # Populate datatable containing info about sessions
        try:
            self.ids.session_list.clear_widgets()
            gc.collect()
            if os.path.exists(himo_app.subjects_file):
                with open(himo_app.subjects_file) as f:
                    # json.dump(data, f, ensure_ascii=False, indent=4)
                    data = json.load(f)
                    temp = data['Sessions']
                    for element, index in zip(temp, range(0, len(temp))):
                        item = SessionListItem()
                        item.set_icon('numeric-' + str(index))
                        item.text = 'TIPTOE - ' + str(element['Tiptoe']) + ' / HEEL - ' + str(element['Heel'])
                        item.tiptoe = element['Tiptoe']
                        item.heel = element['Heel']
                        self.ids.session_list.add_widget(
                            item
                        )
                    del temp
                    del data
                    gc.collect()

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print("Exception:" + str(e))
            pass
        pass

class ExercisesContent(MDBoxLayout):
    models_menu = ObjectProperty(None)
    subjects_menu = ObjectProperty(None)
    retrain_value = NumericProperty(69)

    train_value = NumericProperty(69)
    trainable_datafile = StringProperty("filename.txt")
    # instructions = StringProperty('')
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.q = queue.Queue()
        self.menu_items = []
        self.selected_model = ""
        self.selected_subject = ""

        self.retrain_active = False
        self.train_active = False
        self.data = np.ndarray((0, 0))

        self.save_file = ""
        # Initialize stuff
        Clock.schedule_once(self.on_start, .1)
        Clock.unschedule(himo_app.check_myo_sync)

        gc.collect()

    def on_start(self, *l):
        self.load_models()

        self.instructions = HIMO.instructions


    def load_models(self):
        if Cache.get('test', 'models_menu') == None and \
                Cache.get('test', 'subjects_menu') == None:
            for filename in os.listdir(himo_app.result_path):
                if filename.endswith(".h5"):
                    self.menu_items.append(
                        {
                            "viewclass": "HoverItem",
                            "text": filename,
                            "theme_text_color": "Custom",
                            "text_color": [0, 0, 0, 1],
                        }
                    )
            self.models_menu = MDDropdownMenu(
                caller=self.ids.drop_models,
                items=self.menu_items,
                position="auto",
                callback=self.set_item,
                selected_color=MYOBLUE,
                width_mult=6,
            )

            with open(himo_app.subjects_file, 'r') as data_file:
                data = json.load(data_file)
            self.menu_items.clear()
            for element in data['Subjects']:
                self.menu_items.append(
                    {
                        "viewclass": "HoverItem",
                        "text": element['Name'],
                        "theme_text_color": "Custom",
                        "text_color": [0, 0, 0, 1],
                    }
                )
            self.subjects_menu = MDDropdownMenu(
                # id="dropdown_menu",
                caller=self.ids.drop_subjects,
                items=self.menu_items,
                position="auto",
                callback=self.set_subject,
                selected_color=MYOBLUE,
                width_mult=4,
            )
            Cache.append('test', 'models_menu', self.models_menu)

            Cache.append('test', 'subjects_menu', self.subjects_menu)


            print("SAVING TO CACHE")
        else:
            print("LOADING FROM CACHE")
            self.models_menu = Cache.get('test', 'models_menu')
            self.subjects_menu = Cache.get('test', 'subjects_menu')

        # Delete unused var
        # del data
        # gc.collect()


    def set_subject(self, instance):
        self.ids.drop_subjects.set_item(instance.text)
        self.selected_subject = instance.text
        self.subjects_menu.dismiss()


    def set_item(self, instance):
        self.ids.drop_models.set_item(instance.text)
        self.selected_model = instance.text
        self.models_menu.dismiss()


    def retrain_model(self, *args):
        # TODO: retrain selected network model
        if not self.retrain_active:
            try:
                data = np.loadtxt(himo_app.result_path + '/' + self.selected_model.split('_')[0] + '.txt')
                name = self.selected_model.split('_')[0]
                self.q = queue.Queue()
                t = threading.Thread(target=TrainEMG, args=[data, name, self.q])
                t.start()
                self.retrain_active = True

                del data
                del name
                gc.collect()
            except Exception as e:
                if hasattr(e, 'message'):
                    print(e.message)
                else:
                    print(e)
        else:
            himo_app.show_snackbar("RE-TRAINING ALREADY IN PROGRESS!", INFO_ICON, YELLOW_HEX)
        pass


    # Display re-training progress and button
    def display_image(self):
        img = PILImage.open(self.save_file)
        img.show()
        gc.collect()


    def open_image(self, *l):
        t = threading.Thread(target=self.display_image)
        t.start()

    def show_display_button(self, container):
        # Display button to view plot
        self.save_file = self.q.get()
        container.clear_widgets()
        gc.collect()
        container.add_widget(
            MDRectangleFlatButton(text="Display", on_release=self.open_image)
        )

    def retrain_progress_value(self, *l):
        gc.collect()
        try:
            self.retrain_value = floor(HIMO.epoch_counter / 3)
            # print("RE-TRAIN IN PROGRESS:" + str(self.retrain_value))
            if HIMO.epoch_counter == HIMO.max_epochs:
                Clock.unschedule(self.retrain_progress_value)

                # Display button
                self.show_display_button(self.ids.retrain_container)
                self.retrain_active = False

                himo_app.show_snackbar("RE-TRAINING MODEL SUCCESSFUL!", CHECK_ICON, GREEN_HEX)
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
                himo_app.show_snackbar("ERROR in re-training model: " + e.message, ERROR_ICON, RED_HEX)
            else:
                print(e)
                himo_app.show_snackbar("ERROR in re-training model: " + e, ERROR_ICON, RED_HEX)

    def train_progress_value(self, *l):
        try:
            self.train_value = floor(HIMO.epoch_counter / 3)
            # print("TRAIN IN PROGRESS:" + str(self.retrain_value))
            if HIMO.epoch_counter == HIMO.max_epochs:
                Clock.unschedule(self.train_progress_value)
                self.train_active = False

                # Display button
                self.show_display_button(self.ids.train_container)

                himo_app.show_snackbar("TRAINING NEW MODEL SUCCESSFUL!", CHECK_ICON, GREEN_HEX)
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
                himo_app.show_snackbar("ERROR in training model: " + e.message, ERROR_ICON, RED_HEX)
            else:
                print(e)
                himo_app.show_snackbar("ERROR in training model: " + e, ERROR_ICON, RED_HEX)

    def retrain_progress(self, *args):
        self.retrain_value = 0
        Clock.schedule_interval(self.retrain_progress_value, 0.1)

    def train_model(self, *args):
        if self.trainable_datafile is not "filename.txt":
            if not self.train_active:
                name = self.trainable_datafile.split('.')[0]
                self.data = self.q.get()
                # Reinit queue
                self.q = queue.Queue()
                t = threading.Thread(target=TrainEMG, args=[self.data, name, self.q])
                t.start()
                self.train_active = True
            else:
                himo_app.show_snackbar("TRAINING ALREADY IN PROGRESS!", INFO_ICON, YELLOW_HEX)
        else:
            himo_app.show_snackbar("Please prepare a subject to continue!", ERROR_ICON, RED_HEX)
    def train_progress(self, *args):
        self.train_value = 0
        Clock.schedule_interval(self.train_progress_value, 0.1)

    def update_instructions(self, *args):
        self.ids.instructions.text = HIMO.instructions
        # self.instructions = HIMO.instructions

    def prepare_model(self):
        try:
            Clock.schedule_interval(self.update_instructions, 0.2)
            name = self.selected_subject
            self.trainable_datafile = name + '.txt'
            t = threading.Thread(target=PrepareTrainingData, args=[name, self.q])
            t.start()

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
        pass


class Upload(Screen):
    dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("UPLOAD SCREEN")
        Clock.schedule_once(self.on_start, 1)
        Clock.unschedule(himo_app.check_myo_sync)


    # Initialize tabs according to clicked button
    def set_tabs(self, text=""):
        if text is not self.ids.page_toolbar.title:
            # print(text)
            self.ids.page_toolbar.title = text
            # Remove content but not toolbar
            if len(self.ids.tabs_layout.children) > 1:
                for child in self.ids.tabs_layout.children:
                    # print(child)
                    self.ids.tabs_layout.remove_widget(child)
                    break
            options = {"Subjects": SubjectsContent(),
                       "Session": SessionContent(),
                       "Exercises": ExercisesContent()
                       }
            self.widget = options[text]
            self.ids.tabs_layout.add_widget(self.widget)
            del options



    def write_json(self, data):
        with open(himo_app.subjects_file, 'w') as f:
            json.dump(data, f, indent=4)

    def on_start(self, *l):
        self.ids.page_toolbar.title = "Subjects"

        if not os.path.exists(himo_app.subjects_file):
            self.data = {"Subjects": [], "Sessions": []}
            self.write_json(self.data)
        pass
        gc.collect()
        # pass

    def on_pre_enter(self, *args):
        Window.size = MAX_SIZE[0] + 1, MAX_SIZE[1] + 1
        # print("Screen size SET")
        Window.size = MAX_SIZE
        # Clock.schedule_once(self.on_start, 0)
        gc.collect()


# endregion


# region MENU

class MenuListItems(OneLineAvatarListItem, ThemableBehavior, HoverBehavior):
    '''Custom item implementing hover behavior.'''
    efficiency = StringProperty('69%')
    bg_color = ObjectProperty([.11, .11, .11, 1])
    anim = None

    # Animation to simulate smooth hover
    def hover_color(self, *args):
        anim = Animation(bg_color=[.11, .11, .11, 1], duration=0.01) + \
               Animation(bg_color=[.07, .07, .07, 1], duration=0.2)
        anim.start(self)

    def hover_back(self, *args):
        anim = Animation(bg_color=[.07, .07, .07, 1], duration=0.01) + \
               Animation(bg_color=[.11, .11, .11, 1], duration=0.25)
        anim.start(self)

    def on_enter(self, *args):
        '''The method will be called when the mouse cursor
        is within the borders of the current widget.'''
        # print("hover")
        Clock.schedule_once(self.hover_color)

    def on_leave(self, *args):
        '''The method will be called when the mouse cursor goes beyond
        the borders of the current widget.'''
        # self.md_bg_color = (0, 0.7411, 0.87, 1)
        Clock.schedule_once(self.hover_back)


class ContentNavigationDrawer(BoxLayout):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()


# endregion
class HIMOApp(MDApp):
    screen_manager = ObjectProperty()
    subjects_file = "X:/Sapientia EMTE/Szakmai Gyakorlat/v2/HIMO/data/subjects/subjects.json"
    MYOCOLOR = MYOBLUE
    result_path = "X:/Sapientia EMTE/Szakmai Gyakorlat/v2/HIMO/data/results"
    results_file = "X:/Sapientia EMTE/Szakmai Gyakorlat/v2/HIMO/data/results/results.json"
    myo_connected = False
    myo_synced = False
    snackbar = None

    @staticmethod
    def check_resize(instance, x, y):
        # resize X
        if x > MAX_SIZE[0]:
            Window.size = (MAX_SIZE[0], Window.size[1])
        # resize Y
        if y > MAX_SIZE[1]:
            Window.size = (Window.size[0], MAX_SIZE[1])

    def check_myo_sync(self, *args):
        try:
            if check_if_process_running('Myo Connect.exe'):
                self.hub = myo.Hub()
                self.listener = Listener()

                self.hub.run(self.listener.on_event, 10)
                self.myo_synced = self.listener.synced
                self.myo_connected = self.listener.connected
        except:
            self.myo_synced = False

    def build(self):
        Window.size = MAX_SIZE
        self.theme_cls.primary_palette = "Cyan"
        self.theme_cls.theme_style = "Dark"

        return Builder.load_file("himoka.kv")

    def show_snackbar(self, message, cicon, color='000000'):
        self.snackbar = CustomSnackbar(
            text=message,
            icon=cicon,
            padding="50dp",
            button_text="HIDE",
            button_color=(1, 1, 1, 1),

            button_callback=self.hide_snackbar
        )
        self.snackbar.sb_color = color
        self.snackbar.show()

    def hide_snackbar(self, *args):
        self.snackbar = None


if __name__ == '__main__':
    himo_app = HIMOApp()
    himo_app.run()
