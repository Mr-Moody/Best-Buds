from datetime import datetime
from kivy.clock import Clock        # for scheduling when to update time for greeting

from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.camera import Camera  # for taking photos
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window     # for fixed window
from kivy.properties import StringProperty, ObjectProperty, DictProperty  # for idek what man property -> for dynamic variables
from kivy.uix.screenmanager import ScreenManager, Screen    # for the diff screens

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton
from kivy.core.text import LabelBase    # for fonts
from kivy.graphics.texture import Texture   # for camera screen display?

import os
from PIL import Image   # for image manipulation
import cv2      # for camera display

LabelBase.register(name="MainFont", fn_regular="static/fonts/EB_Garamond_static/EBGaramond-SemiBold.ttf")
LabelBase.register(name="SecondaryFont", fn_regular="static/fonts/Comfortaa_static/Comfortaa-Light.ttf")

if not os.path.exists("images"):
    os.makedirs("images")
    
KV_FILES = ["home.kv", "calendar.kv", "camera.kv", "settings.kv"]   # load in the diff screens

COLOURS = {
    "active": (0.576, 0.749, 0.51, 1),        # dark green
    "inactive": (0.659, 0.859, 0.576, 1),         # light green
    "accent": (1, 0.78, 0.88, 1)            # light pink accent
}

Window.size = (720/2, 1280/2)
Window.resizable = False


class CustomImageButton(RelativeLayout):
    image_source = StringProperty("")
    screen_name = StringProperty("")
    bg_colour = ObjectProperty(COLOURS["inactive"])
    
# for all the screens
class HomeScreen(Screen):
    pass

class CalendarScreen(Screen):
    pass

class CameraScreen(Screen):
    def on_enter(self):
        # start the opencv camera feed when entering the screen
        self.capture = cv2.VideoCapture(0)
        Clock.schedule_interval(self.update_camera, 1.0/30.0)      # updates every 30FPS
        
    def on_leave(self):
        # stop camera when leaving
        self.capture.release()
        Clock.unschedule(self.update_camera)
    
    def update_camera(self, dt):
        # capture frame and display
        ret, frame = self.capture.read()
        if ret:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)    # rotate cam
            
            square_size = int(min(self.ids.camera_widget.size))
            frame_resized = cv2.resize(frame, (square_size, square_size), interpolation=cv2.INTER_AREA)
            buf = cv2.flip(frame_resized, 0).tobytes()
            texture = Texture.create(size=(frame_resized.shape[1], frame_resized.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf,colorfmt='bgr', bufferfmt='ubyte')
            self.ids.camera_widget.texture = texture

class SettingsScreen(Screen):
    pass

class MyApp(MDApp):
    current_screen = StringProperty("home") # tracks current screen and StringProperty is used to auto update UI
    buttons = ObjectProperty(None)          # stores button ids or something idk
    greeting_text = StringProperty("Hello, _____!")      # hello hotbar 
    colours = DictProperty(COLOURS)         # to access COLOUR[] in the .kv file
    username = StringProperty("user")
    
    def build(self):
        self.load_kv_files()  # load external kv files
        # return btn = ButtonWidget()
        root = Builder.load_file("myapp.kv")
        
        screen_manager = root.ids.screen_manager
        screen_manager.clear_widgets()
    
        screen_manager.add_widget(HomeScreen(name="home"))
        screen_manager.add_widget(CalendarScreen(name="calendar"))
        screen_manager.add_widget(CameraScreen(name="camera"))
        screen_manager.add_widget(SettingsScreen(name="settings"))
        
        self.buttons = {
            "home": root.ids.home_button,
            "calendar": root.ids.calendar_button,
            "camera": root.ids.camera_button,
            "settings": root.ids.settings_button,
        }
        # for key, btn in self.buttons.items():         # debugging
        #     print(f"{key}: {btn}\n")
            
        self.update_greeting()
        Clock.schedule_once(self.update_greeting, 0.5)  # makes sure it updates after the UI loads
        self.change_user_name("Tara")
        return root
    
    def load_kv_files(self):
        # load the kv files
        for kv_file in KV_FILES:
            path = os.path.join("screens", kv_file)
            if os.path.exists(path):
                Builder.load_file(path)
                print(f"loaded {kv_file}")
            else:
                print(f"NOOOOOOOO: this {kv_file} not found!")
                
    def change_screen(self, screen_name, button):
        
        if screen_name in self.root.ids.screen_manager.screen_names:
            self.current_screen = screen_name           # updates current screen
            self.root.ids.screen_manager.current = screen_name      # updates current screen
            self.update_button_colour()
            print(f"screen change!")
        else:
            print(f"NO screen {screen_name} found!!!")

    def update_greeting(self, dt=None):
        # will change based on time of day
        hour = datetime.now().hour
        if 5 <= hour < 12:
            self.greeting_text = f"Good Morning {self.username}!"
        elif 12 <= hour < 17:
            self.greeting_text = f"Good Afternoon {self.username}!"
        elif 17 <= hour < 20:
            self.greeting_text = f"Good Evening {self.username}!"
        else:
            self.greeting_text = f"Good Night {self.username}! 🌙"
        
        self.root.ids.greeting_label.text = self.greeting_text
        
    def update_button_colour(self):
        pass
        # for name, btn in self.buttons.items():
        #     if name == self.current_screen:
        #         btn.bg_colour = self.colours["active"]
        #     else:
        #         btn.bg_colour = self.colours["inactive"]
                
    def change_user_name(self, new_name):
        self.username = new_name  
        self.update_greeting()
        
    def capture_picture(self):
        # take piccy
        camera_screen = self.root.ids.screen_manager.get_screen("camera")
        
        #get piccy from opencv
        ret, frame = camera_screen.capture.read()
        if not ret:
            print("no piccy taken :(")
            return
        
        # check how many already exist in the folder to number then sequentially
        existing_images = [f for f in os.listdir("images") if f.endswith(".png")]
        next_number = len(existing_images) + 1
        
        filename = f"images/plant_{next_number}.png"
        cv2.imwrite(filename, frame)     # save image to folder
        
        if os.path.exists(filename):
            print(f"{filename} picture saved!")
        else:
            print(f"where'd my photo go")

app = MyApp()
app.run()
