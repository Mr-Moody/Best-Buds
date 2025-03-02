from datetime import datetime
from kivy.clock import Clock        # for scheduling when to update time for greeting

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.camera import Camera  # for taking photos
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.screenmanager import ScreenManager, Screen    # for the diff screens
from kivy.graphics import Color, RoundedRectangle

from kivy.core.window import Window     # for fixed window
from kivy.properties import StringProperty, ObjectProperty, DictProperty  # for idek what man property -> for dynamic variables

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.textfield import MDTextField
from kivy.core.text import LabelBase    # for fonts
from kivy.graphics.texture import Texture   # for camera screen display?

import os
from PIL import Image as PILImage  # for image manipulation
import cv2      # for camera display

from database import DB
dir_path = os.path.dirname(os.path.realpath(__file__))
db = DB()

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
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation="vertical", padding=5, spacing=5)
            
        self.plant_viewer = PlantViewer(size_hint=(1, 0.2))  # Make it span across the screen
        layout.add_widget(self.plant_viewer)

class CalendarScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

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
        # Capture frame from OpenCV
        ret, frame = self.capture.read()
        if ret:
            # Get frame dimensions
            height, width, _ = frame.shape

            # Determine the smaller dimension to create a square crop
            min_dim = min(height, width)
            x_start = (width - min_dim) // 2  # Center crop horizontally
            y_start = (height - min_dim) // 2  # Center crop vertically
            cropped_frame = frame[y_start:y_start + min_dim, x_start:x_start + min_dim]

            # Resize to match widget size without distortion
            square_size = int(min(self.ids.camera_widget.size))
            frame_resized = cv2.resize(cropped_frame, (square_size, square_size), interpolation=cv2.INTER_AREA)

            # Convert frame to texture
            buf = cv2.flip(frame_resized, 0).tobytes()
            texture = Texture.create(size=(frame_resized.shape[1], frame_resized.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

            # Assign the texture to the camera widget
            self.ids.camera_widget.texture = texture


class SettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

class BestBuds(MDApp):
    current_screen = StringProperty("home") # tracks current screen and StringProperty is used to auto update UI
    buttons = ObjectProperty(None)          # stores button ids or something idk
    greeting_text = StringProperty("Hello, _____!")      # hello hotbar 
    colours = DictProperty(COLOURS)         # to access COLOUR[] in the .kv file
    username = StringProperty("user")
    
    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.load_kv_files()  # load external kv files
        # return btn = ButtonWidget()
        root = Builder.load_file("myapp.kv")
        self.root = root

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

        layout = BoxLayout(orientation="vertical", padding=5, spacing=5)
        self.plant_viewer = PlantViewer(size_hint=(1, 0.2))  # Make it span across the screen
        layout.add_widget(self.plant_viewer)

        home_screen = screen_manager.get_screen("home")
        home_screen.add_widget(layout)
        
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
            print("No photo captured :(")
            return
        
        # Get frame dimensions
        height, width, _ = frame.shape

        # Determine the smaller dimension for cropping to a square
        min_dim = min(height, width)
        x_start = (width - min_dim) // 2  # Center crop horizontally
        y_start = (height - min_dim) // 2  # Center crop vertically
        cropped_frame = frame[y_start:y_start + min_dim, x_start:x_start + min_dim]  # Crop square region

        # Resize (optional) - Keeps the image consistent in size
        final_size = 512  # Example size, adjust as needed
        final_image = cv2.resize(cropped_frame, (final_size, final_size), interpolation=cv2.INTER_AREA)

        # Convert OpenCV image to Kivy Texture
        buf = cv2.flip(final_image, 0).tobytes()
        texture = Texture.create(size=(final_image.shape[1], final_image.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

        # Show confirmation popup with the generated texture
        self.show_confirmation_popup(final_image, texture)

    def save_captured_image(self, image, popup):
        # check how many already exist in the folder to number then sequentially
        existing_images = [f for f in os.listdir("images") if f.endswith(".png")]
        next_number = len(existing_images) + 1

        filename = f"images/plant_{next_number}.png"
        cv2.imwrite(filename, image)  # save the cropped image
        
        if os.path.exists(filename):
            print(f"{filename} picture saved!")
        else:
            print(f"where'd my photo go")
            
        popup.dismiss()
        # wait for user confirmation
        # Convert OpenCV image to Kivy Texture
        # buf = cv2.flip(final_image, 0).tobytes()
        # texture = Texture.create(size=(final_image.shape[1], final_image.shape[0]), colorfmt='bgr')
        # texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

    def show_confirmation_popup(self, image, texture):
        """ Displays a popup asking the user to confirm or retake the picture. """
        
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Show the image
        img_widget = Image(texture=texture, size_hint=(1, 1))
        
        # Buttons layout
        buttons = BoxLayout(size_hint=(1, 0.3), spacing=10)

        # Confirm button
        confirm_btn = Button(text="Confirm", size_hint=(0.5, 1))
        confirm_btn.bind(on_release=lambda x: self.save_captured_image(image, popup))

        # Retake button
        retake_btn = Button(text="Retake", size_hint=(0.5, 1))
        retake_btn.bind(on_release=lambda x: popup.dismiss())

        buttons.add_widget(confirm_btn)
        buttons.add_widget(retake_btn)

        # Add elements to the layout
        layout.add_widget(img_widget)
        layout.add_widget(buttons)

        # Create popup
        popup = Popup(title="Confirm Photo", content=layout, size_hint=(0.8, 0.8), auto_dismiss=False)
        
        # Open popup
        popup.open()

class PlantViewer(ScrollView):  # Change from Widget to ScrollView
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.layout = BoxLayout(orientation="horizontal", padding=10, spacing=30, size_hint=(None, 1))
        self.layout.bind(minimum_width=self.layout.setter("width"))

        plants = db.get_user_plants()
        self.populate_plants(plants)
        create_plant_btn = NewPlant(size_hint=(None, 1), size=(100, 100))
        self.layout.add_widget(create_plant_btn)
        self.add_widget(self.layout)
    
    def populate_plants(self, plants:list) -> None:
        for i in range(len(plants)):
            btn = PlantWidget(size_hint=(None, 1), size=(100, 100))
            btn.set_image(plants[i].id)
            btn.set_name(plants[i].name)
            self.layout.add_widget(btn)


class PlantWidget(ButtonBehavior, BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = 0.25

        with self.canvas.before:
            Color(0.8, 0.8, 0.8, 1)  # Grey border
            self.border = RoundedRectangle(pos=self.pos, size=self.size, radius=[20, ])
            
            Color(1, 1, 1, 1)  # White background
            self.background = RoundedRectangle(pos=(self.x + 2, self.y + 2), size=(self.width - 4, self.height - 4), radius=[20, ])

        self.bind(pos=self.update_graphics, size=self.update_graphics)

        layout = BoxLayout(orientation="vertical", padding=5, spacing=5)
        self.image = Image(source=None, size_hint=(1, 0.7))  # Image on top
        self.label = Label(text="Name", size_hint=(1, 0.3), color=(20, 220, 40, 1))  # Label below the image
        
        layout.add_widget(self.image)
        layout.add_widget(self.label)
        self.add_widget(layout)
    
    def update_graphics(self, *args):
        self.border.pos = self.pos
        self.border.size = self.size
        self.background.pos = (self.x + 2, self.y + 2)
        self.background.size = (self.width - 4, self.height - 4)

    def set_image(self, plant_id):
        self.image.source = f"{dir_path}/images/{plant_id}.jpg"

    def set_name(self, name):
        self.label.text = name

    def on_press(self):
        print("Rounded button pressed!")


class NewPlant(ButtonBehavior, BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = 0.25

        with self.canvas.before:
            Color(0.8, 0.8, 0.8, 1)  # Grey border
            self.border = RoundedRectangle(pos=self.pos, size=self.size, radius=[20, ])
            
            Color(1, 1, 1, 1)  # White background
            self.background = RoundedRectangle(pos=(self.x + 2, self.y + 2), size=(self.width - 4, self.height - 4), radius=[20, ])

        self.bind(pos=self.update_graphics, size=self.update_graphics)

        layout = BoxLayout(orientation="vertical", padding=5, spacing=5)
        self.image = Image(source=f"{dir_path}/static/icons/plus.png", size_hint=(0.7, 0.7), pos_hint={"x":0.15,"y":1})
        
        layout.add_widget(self.image)
        self.add_widget(layout)
    
    def update_graphics(self, *args):
        self.border.pos = self.pos
        self.border.size = self.size
        self.background.pos = (self.x + 2, self.y + 2)
        self.background.size = (self.width - 4, self.height - 4)

    def set_image(self, plant_id):
        self.image.source = f"{dir_path}/images/plants/{plant_id}.jpg"

    def set_name(self, name):
        self.label.text = name

    def on_press(self):
        content = PlantForm(size_hint=(1,1))
        popup = CustomPopup(content=content, auto_dismiss=False, size_hint=(0.8,0.8), title="Add new plant")

        content.bind(on_press=popup.dismiss)

        popup.open()


class PlantForm(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(0.2, 0.6, 0.2, 1)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[20, ])

        self.bind(size=self.update_graphics, pos=self.update_graphics)

        self.orientation = "vertical"
        self.spacing = 10
        self.padding = 10
        self.size_hint = (1, 1)

        scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)

        #form fields
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter("height"))

        self.name_label = Label(text="Plant Name")
        self.name_input = MDTextField(hint_text="Enter plant name", size_hint_y=None, height=40)
        
        self.species_label = Label(text="Species")
        self.species_input = MDTextField(hint_text="Enter species", size_hint_y=None, height=40)
        
        self.birth_date_label = Label(text="Birth Date (YYYY-MM-DD)")
        self.birth_date_input = MDTextField(hint_text="Select birth date", size_hint_y=None, height=40)
        self.birth_date_input.bind(focus=self.show_date_picker)
        
        self.height_label = Label(text="Plant Height (cm)")
        self.height_input = MDTextField(input_filter="int", hint_text="Enter height", size_hint_y=None, height=40)

        self.water_label = Label(text="Water Frequency (days)")
        self.water_spinner = MDTextField(input_filter="int", hint_text="Enter how often you need to water your plant", size_hint_y=None, height=40)

        self.fert_label = Label(text="Do you need fertiliser?")
        self.fert_checkbox = CheckBox(active=self.toggle_fertiliser_fields, size_hint_y=None, height=40)

        self.fert_type_label = Label(text="Fertiliser Type")
        self.fert_type_input = MDTextField(hint_text="Enter fertiliser type", size_hint_y=None, height=40)

        self.fert_freq_label = Label(text="Fertiliser Frequency (days)")
        self.fert_freq_input = MDTextField(input_filter="int", hint_text="Enter fertiliser frequency", size_hint_y=None, height=40)

        self.submit_btn = Button(text="Submit", size_hint_y=None, height=50)
        self.submit_btn.bind(on_press=self.submit_form)

        #add widgets to layout
        self.layout.add_widget(self.name_label)
        self.layout.add_widget(self.name_input)
        self.layout.add_widget(self.species_label)
        self.layout.add_widget(self.species_input)
        self.layout.add_widget(self.birth_date_label)
        self.layout.add_widget(self.birth_date_input)
        self.layout.add_widget(self.height_label)
        self.layout.add_widget(self.height_input)
        self.layout.add_widget(self.water_label)
        self.layout.add_widget(self.water_spinner)
        self.layout.add_widget(self.fert_label)
        self.layout.add_widget(self.fert_checkbox)
        self.layout.add_widget(self.fert_type_label)
        self.layout.add_widget(self.fert_type_input)
        self.layout.add_widget(self.fert_freq_label)
        self.layout.add_widget(self.fert_freq_input)
        self.layout.add_widget(self.submit_btn)

        scroll_view.add_widget(self.layout)

        self.add_widget(scroll_view)

    def update_graphics(self, *args):
        #update background position and size when layout is resized
        self.rect.pos = self.pos
        self.rect.size = self.size

    def show_date_picker(self, instance, focus):
        if not focus:
            return

        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.confirm_date)
        date_dialog.open()


    def confirm_date(self, instance, value, date_range):
        self.birth_date = value

    def toggle_fertiliser_fields(self, instance, value):
        if value:
            self.fert_type_label.opacity = 1
            self.fert_type_input.opacity = 1
            self.fert_freq_label.opacity = 1
            self.fert_freq_input.opacity = 1
        else:
            self.fert_type_label.opacity = 0
            self.fert_type_input.opacity = 0
            self.fert_freq_label.opacity = 0
            self.fert_freq_input.opacity = 0

    def submit_form(self, instance):
        # Get the values from the form
        name = self.name_input.text
        species = self.species_input.text
        height = self.height_input.text
        water_frequency = self.water_spinner.text
        fertiliser_needed = self.fert_checkbox.active

        if fertiliser_needed:
            fertiliser_type = self.fert_type_input.text
            fertiliser_freq = self.fert_freq_input.text
        else:
            fertiliser_type = None
            fertiliser_freq = None

        # Show the collected data in a popup or process it
        print(f"Name: {name} Species: {species} Birth Date: {self.birth_date} Height: {height} Water Frequency: {water_frequency} days Fertiliser Needed: {fertiliser_needed} Fertiliser Type: {fertiliser_type} Fertiliser Frequency: {fertiliser_freq} days")
        #popup.open()

        # Clear form after submission
        self.name_input.text = ''
        self.species_input.text = ''
        self.birth_date_input.text = ''
        self.height_input.text = ''
        self.fert_checkbox.active = False
        self.fert_type_input.text = ''
        self.fert_freq_input.text = ''

class CustomPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set custom background color
        with self.canvas.before:
            Color(0.2, 0.6, 0.2, 1)  # Green background (RGBA)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[20, ])  # Rounded rectangle

        self.bind(size=self.update_graphics, pos=self.update_graphics)

    def update_graphics(self, *args):
        # Update the position and size of the background rectangle
        self.rect.pos = self.pos
        self.rect.size = self.size

if __name__ == "__main__":
    app = BestBuds()
    app.run()
