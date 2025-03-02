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
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineListItem
from kivy.core.text import LabelBase    # for fonts
from kivy.graphics.texture import Texture   # for camera screen display?

import os
from PIL import Image as PILImage  # for image manipulation
import cv2      # for camera display

import openai
import base64

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set it into your environment w/ 'export OPENAI_API_KEY=""'")

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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation="vertical", spacing=10, padding=10)

        #title label for list of plants needing watering
        self.title_label = MDLabel(text="Your plants:", font_style="H5", size_hint_y=None, height=50)
        self.layout.add_widget(self.title_label)

        self.plant_viewer = PlantViewer()
        self.layout.add_widget(self.plant_viewer)

        self.add_widget(self.layout)

class CalendarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.plants_needing_water = []
        
        self.layout = MDBoxLayout(orientation="vertical", spacing=10, padding=10)
        
        #title label for list of plants needing watering
        self.title_label = MDLabel(text="Plants to Water Today:", font_style="H5", size_hint_y=None, height=50)
        self.layout.add_widget(self.title_label)

        self.scroll_view = ScrollView()
        self.plant_list = MDList()
        self.scroll_view.add_widget(self.plant_list)
        self.layout.add_widget(self.scroll_view)

        self.add_widget(self.layout)

        self.update_plant_list(datetime.today().strftime("%Y-%m-%d"))

    def update_plant_list(self, selected_date_str:str):
        #clear previous list
        self.plant_list.clear_widgets()

        #get the plants for the selected date
        user_plants = db.get_user_plants()

        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()

        for plant in user_plants:
            delta_days = (selected_date - plant.birth_date).days

            if delta_days >= 0 and delta_days % plant.water_frequency == 0:
                self.plants_needing_water.append(plant)

        if len(self.plants_needing_water) > 0:
            for plant in self.plants_needing_water:
                self.plant_list.add_widget(OneLineListItem(text=f"{plant.name} - Water every {plant.water_frequency} days"))
        else:
            self.plant_list.add_widget(OneLineListItem(text="No plants need watering."))


class CameraScreen(Screen):
    def on_enter(self):
        # start the opencv camera feed when entering the screen
        self.capture = cv2.VideoCapture(0)
        
        # check if cam opens properly
        if not self.capture.isOpened():
            print("Error: unable to access camera")
            return
        
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class BestBuds(MDApp):
    current_screen = StringProperty("home") # tracks current screen and StringProperty is used to auto update UI
    buttons = ObjectProperty(None)          # stores button ids or something idk
    greeting_text = StringProperty("Hello, _____!")      # hello hotbar 
    colours = DictProperty(COLOURS)         # to access COLOUR[] in the .kv file
    username = StringProperty("user")
    
    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.load_kv_files()  # load external kv files

        root = Builder.load_file("myapp.kv")
        self.root = root

        screen_manager = root.ids.screen_manager
        screen_manager.clear_widgets()
    
        screen_manager.add_widget(HomeScreen(name="home"))
        screen_manager.add_widget(CalendarScreen(name="calendar"))
        screen_manager.add_widget(CameraScreen(name="camera"))
        screen_manager.add_widget(SettingsScreen(name="settings"))

        self.buttons = {
            "home": self.root.ids.home_button,
            "calendar": self.root.ids.calendar_button,
            "camera": self.root.ids.camera_button,
            "settings": self.root.ids.settings_button,
        }
        

        home_screen = screen_manager.get_screen("home")
        
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
            # self.update_button_colour()
            # Reset all buttons to inactive
            
            # print(f"pressed button: {button.screen_name}")
            
            # for btn in self.buttons.values():
            #     btn.bg_colour = self.colours["inactive"]
            #     btn.canvas.ask_update()

            # # Activate the selected button
            # if isinstance(button, CustomImageButton):
            #     print(f"{button.screen_name} is a button")
            #     # button.bg_colour = self.colours["active"]
            #     btn.canvas.ask_update()
            
            print(f"screen change to {screen_name}!")
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
        # print(self.current_screen)
        # for name, btn in self.buttons.items():
        #     print(name)
        #     if name == self.current_screen:
        #         btn.bg_colour = self.colours["active"]
        #         print(f"{name} active")
        #     else:
        #         btn.bg_colour = self.colours["inactive"]
        #         print(f"{name} inactive")
                

    def change_user_name(self, new_name):
        self.username = new_name  
        self.update_greeting()    
        
        # if settings screen is open, update textinput value
        if self.root:
            settings_screen = self.root.ids.screen_manager.get_screen("settings")
            if settings_screen:
                settings_screen.ids.username_input.text = new_name
            
    def capture_picture(self, identify=True):
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
        self.show_confirmation_popup(final_image, texture, identify)

    def save_captured_image(self, image, popup, identify=True):
        # print(f"✅ save_captured_image() called. Identify = {identify}")
        
        #check if directory exists yet
        if not os.path.exists("images"):
            os.makedirs("images")
            
        save_dir = "images/plants" if identify else "images/health"
        
        # check how many already exist in the folder to number then sequentially number them
        existing_images = [f for f in os.listdir(save_dir) if f.endswith(".png")]
        next_number = len(existing_images) + 1
        
        # create the filename first - but don't save yet
        filename = f"{save_dir}/plant_{next_number}.png"
        cv2.imwrite(filename, image)  # save the cropped image
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        plant_name, health_status = None, None      # initialise to prevent unboundlocalerror

        if identify:
            # print("🟢 Calling identify_plant_with_openai()...")
            plant_name = self.identify_plant_with_openai(filename)
            print(f"🔍 Plant name received: {plant_name}")
            if plant_name: 
                message = f"Identified Plant: {plant_name}"
            else:
                message = "This does not appear to be a plant :("  
        else:
            health_status = self.check_plant_health(filename)        
            if health_status:
                message = f"Health status: {health_status}"
            else:
                message = "No issues detected - you have a healthy plant!"
                
        if identify and plant_name is None:
            popup.dismiss()
            msg = "This is not a plant, image will not be saved!"
            self.not_a_plant_popup(msg)
            return  # exit function without saving
        
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
        
        
        # print to terminal
        print(message)
        
        #show in a popup
        self.show_ai_result_popup(message)
    
    def identify_plant_with_openai(self, image_path):
        
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # openai.api_key = OPENAI_API_KEY   # deprecated..
        
        try:
            # read file in binary code
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                print(f"image size: {len(image_data)} bytes")
                if len(image_data) < 1000:
                    print("Image file is too small! Check if it's being saved correctly.")
                base64_image = base64.b64encode(image_data).decode()
                
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert botanist. Identify the plant in the given image.\n"
                                    "If the image contains leaves, stems, flowers, or any other plant part, describe the most likely plant.\n"
                                    "If the image contains no plant, say 'No plant detected'.\n"
                                    "If unsure, say 'Unclear, but this might be a plant"
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Is there a plant? If so, what plant is this?"},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=100
            )
            
            # print(f"🟢 OpenAI Raw Response: {response}")
            result = response.choices[0].message.content.strip()
            
            if "no plant" in result.lower() or "not a plant" in result.lower():
                return None
            if "unclear" in result.lower():
                return "Possible plant, but unclear"
            # else
            return result
        
        except Exception as e:
            print(f"Error identifying plant: {e}")
            return None

    def check_plant_health(self, image_path):
        
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # openai.api_key = OPENAI_API_KEY   # deprecated..
        
        try:
            # read file in binary code
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode()
                
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a plant health expert. Check for any disease, damage, or concerns in the plant image."
                                    "If the of the plant is healthy, say 'Nothing wrong here'"
                                    "If unsure, say 'Unclear"
                    },
                    {
                        "role": "user", "content": [
                            {"type": "text", "text": "Does this plant look healhty?"},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                max_tokens=50
            )
                
            result = response.choices[0].message.content.strip()
            
            if "nothing wrong" in result.lower():
                return None
            if "unclear" in result.lower():
                return "Possible damage, but unsure"
            # else
            return result
        
        except Exception as e:
            print(f"Error identifying health: {e}")
            return None

    def show_confirmation_popup(self, image, texture, identify=True):
        """ Displays a popup asking the user to confirm or retake the picture. """
        
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Show the image
        img_widget = Image(texture=texture, size_hint=(1, 1))
        
        # Buttons layout
        buttons = BoxLayout(size_hint=(1, 0.3), spacing=10)

        # Confirm button
        confirm_btn = Button(text="Confirm", size_hint=(0.5, 1), background_color=self.colours["accent"], background_normal="", font_name="SecondaryFont")
        confirm_btn.bind(on_release=lambda x: self.save_captured_image(image, popup, identify))

        # Retake button
        retake_btn = Button(text="Retake", size_hint=(0.5, 1), background_color=self.colours["active"], background_normal="",font_name="SecondaryFont")
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

    def show_ai_result_popup(self, message):
        # displays ai results in a popup
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        
        result_label = Label(text=message, color=(0,0,0,1), font_size=25,font_name="SecondaryFont", halign="center", valign="center", size_hint_y=0.8)
        result_label.bind(size=result_label.setter("text_size"))  # Ensures proper text wrapping
        
        close_btn = Button(text="OK", size_hint_y=0.2, background_color=self.colours["active"], background_normal="")
        close_btn.bind(on_release=lambda x: popup.dismiss())

        layout.add_widget(result_label)
        layout.add_widget(close_btn)

        popup = Popup(title="AI Analysis Result", content=layout, size_hint=(0.8, 0.5), auto_dismiss=True)
        popup.background = ""
        popup.title_size = 0
        popup.background_color = (1,1,1,1)
        popup.open()

    def not_a_plant_popup(self, msg):
        # popup for when no plant is detected
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        
        result_label = Label(text=msg, color=(0,0,0,1), font_size=40,font_name="SecondaryFont", halign="center", valign="center", size_hint_y=0.8)
        result_label.bind(size=result_label.setter("text_size"))  # Ensures proper text wrapping
        
        close_btn = Button(text="OK", size_hint_y=0.2, background_color=self.colours["active"], background_normal="")
        close_btn.bind(on_release=lambda x: popup.dismiss())

        layout.add_widget(result_label)
        layout.add_widget(close_btn)

        popup = Popup(title="No plant", content=layout, size_hint=(0.8, 0.5), auto_dismiss=False)
        popup.background = ""
        popup.title_size = 0
        popup.background_color = (1,1,1,1)
        popup.open()
        

class PlantViewer(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.layout = BoxLayout(orientation="horizontal", padding=10, spacing=30, size_hint=(None, 1))
        self.layout.bind(minimum_width=self.layout.setter("width"))

        plants = db.get_user_plants()
        self.populate_plants(plants)

        #add new plant button
        create_plant_btn = NewPlant(size_hint=(None, None), size=(200, 300))
        create_plant_btn.size_hint_y = 0.5
        self.layout.add_widget(create_plant_btn)
        self.add_widget(self.layout)
    
    def populate_plants(self, plants:list) -> None:
        for i in range(len(plants)):
            btn = PlantWidget(size_hint=(None, None), size=(200, 300))
            btn.set_image(plants[i].id)
            btn.set_name(plants[i].name, plants[i].species)
            self.layout.add_widget(btn)


class PlantWidget(ButtonBehavior, BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = 0.5

        with self.canvas.before:
            Color(0.8, 0.8, 0.8, 1)
            self.border = RoundedRectangle(pos=self.pos, size=self.size, radius=[10, ])
            
            Color(1, 1, 1, 1)
            self.background = RoundedRectangle(pos=(self.x + 2, self.y + 2), size=(self.width - 4, self.height - 4), radius=[10, ])

        self.bind(pos=self.update_graphics, size=self.update_graphics)

        layout = BoxLayout(orientation="vertical", padding=5, spacing=5)
        self.image = Image(source=None, size_hint=(1, 0.7))
        self.label = Label(text="Name", size_hint=(1, 0.3), color=(0, 0, 0, 1))
        
        layout.add_widget(self.image)
        layout.add_widget(self.label)
        self.add_widget(layout)
    
    def update_graphics(self, *args):
        self.border.pos = self.pos
        self.border.size = self.size
        self.background.pos = (self.x + 2, self.y + 2)
        self.background.size = (self.width - 4, self.height - 4)

    def set_image(self, plant_id):
        self.image.source = f"{dir_path}/images/plants/plant_{plant_id}.png"

    def set_name(self, name, species):
        self.label.text = f"{name} - {species}"

    def on_press(self):
        print("Rounded button pressed!")


class NewPlant(ButtonBehavior, BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = 0.25

        with self.canvas.before:
            Color(0.8, 0.8, 0.8, 1)  # Grey border
            self.border = RoundedRectangle(pos=self.pos, size=self.size, radius=[10, ])
            
            Color(1, 1, 1, 1)  # White background
            self.background = RoundedRectangle(pos=(self.x + 2, self.y + 2), size=(self.width - 4, self.height - 4), radius=[10, ])

        self.bind(pos=self.update_graphics, size=self.update_graphics)

        layout = BoxLayout(orientation="vertical", padding=5, spacing=5)
        self.image = Image(source=f"{dir_path}/static/icons/plus.png", size_hint=(0.3,0.3), pos_hint={"center_x": 0.5, "center_y": 0.5})
        
        layout.add_widget(self.image)
        self.add_widget(layout)
    
    def update_graphics(self, *args):
        self.border.pos = self.pos
        self.border.size = self.size
        self.background.pos = (self.x + 2, self.y + 2)
        self.background.size = (self.width - 4, self.height - 4)

    def set_image(self, plant_id):
        self.image.source = f"{dir_path}/images/plants/plant_{plant_id}.png"

    def set_name(self, name):
        self.label.text = name

    def on_press(self):
        content = PlantForm(size_hint=(1,1))
        popup = CustomPopup(content=content, auto_dismiss=True, size_hint=(0.8,0.8), title="Add new plant to your collection!", background="", background_color=(0,0,0,0), separator_color=(0,0,0,0))

        content.bind(on_press=popup.dismiss)

        popup.open()


class PlantForm(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(255, 255, 255, 1)
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

        self.image_label = Label(text="Plant Image")
        self.image_icon = Button(text="Take Plant Picture", background_normal="", background_color=COLOURS["inactive"], size_hint=(None, None), size=(200, 50))
        self.image_icon.bind(on_press=self.take_picture)

        self.name_label = Label(text="Plant Name")
        self.name_input = MDTextField(hint_text="Enter plant name", size_hint_y=None, height=40)
        
        self.species_label = Label(text="Species")
        self.species_input = MDTextField(hint_text="Enter species", size_hint_y=None, height=40, text_color_normal=(255, 255, 255, 1), text_color_focus=(0, 0, 0, 1))
        
        self.birth_date_label = Label(text="Birth Date (YYYY-MM-DD)")
        self.birth_date_input = MDTextField(hint_text="Select birth date", size_hint_y=None, height=40)
        self.birth_date_input.bind(focus=self.show_date_picker)
        
        self.height_label = Label(text="Plant Height (cm)")
        self.height_input = MDTextField(input_filter="float", hint_text="Enter height", size_hint_y=None, height=40)

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
        self.layout.add_widget(self.image_label)
        self.layout.add_widget(self.image_icon)
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

    def take_picture(self, instance):
        """ This function will trigger the camera to take a picture. """
        
        # Open the camera screen to capture an image
        camera_screen = self.parent.parent.ids.screen_manager.get_screen("camera")
        
        # Capture the image (camera capture code, modify according to your camera class)
        ret, frame = camera_screen.capture.read()
        if not ret:
            print("Failed to capture image.")
            return
        
        # Resize the image to be square and save it
        height, width, _ = frame.shape
        min_dim = min(height, width)
        x_start = (width - min_dim) // 2
        y_start = (height - min_dim) // 2
        cropped_frame = frame[y_start:y_start + min_dim, x_start:x_start + min_dim]
        
        final_size = 512
        final_image = cv2.resize(cropped_frame, (final_size, final_size), interpolation=cv2.INTER_AREA)

        # Convert the OpenCV image to a Kivy Texture for preview
        buf = cv2.flip(final_image, 0).tobytes()
        texture = Texture.create(size=(final_image.shape[1], final_image.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

        # Update the image preview with the captured picture
        self.image_preview.texture = texture

        # Save the image
        self.save_captured_image(final_image)
    
    def save_captured_image(self, image):
        """ Save the captured image to the local folder. """
        # Check how many images already exist and name this one accordingly
        existing_images = [f for f in os.listdir("images") if f.endswith(".png")]
        next_number = len(existing_images) + 1

        filename = f"images/plant_{next_number}.png"
        cv2.imwrite(filename, image)  # Save the image to the filesystem
        
        print(f"Picture saved as {filename}")

    def show_date_picker(self, instance, focus):
        if not focus:
            return

        date_dialog = MDDatePicker(size_hint=(0.8,0.4), pos_hint={"x":0.1, "y":0.2})
        date_dialog.bind(on_save=self.confirm_date)
        date_dialog.open()


    def confirm_date(self, instance, value, date_range):
        print(f"birth date value: {value}")
        self.birth_date = value
        self.birth_date_input.text = f"{value}"

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

        error = ""

        print(f"Height: {height}")
        #input validation
        if len(name) <= 0:
            error = "No name has been inputted."
        elif len(species) <= 0:
            error = "No species has been inputted."
        elif height == "":
            error = "No height has been inputted."
        elif float(height) <= 0:
            error = "Invalid height has been inputted."
        elif water_frequency == "":
            error = "No water frequency has been inputted."
        elif int(water_frequency) <= 0:
            error = "Invalid watering frequency has been inputted."

        if fertiliser_needed:
            if fertiliser_type == "":
                error = "No fertiliser type has been inputted."
            elif fertiliser_freq == "":
                error = "No fertiliser frequency has been inputted."
            elif int(fertiliser_freq) <= 0:
                error = "Invalid fertiliser frequency has been inputted."

        if len(error) <= 0:
            #no error detected in input fields
            db.new_plant_record(name=name, species=species, birth_date=self.birth_date, water_frequency=water_frequency, fertiliser_needed=fertiliser_needed, fertiliser_type=fertiliser_type, fertiliser_frequency=fertiliser_freq)

            #clear form after submission
            self.name_input.text = ''
            self.species_input.text = ''
            self.birth_date_input.text = ''
            self.height_input.text = ''
            self.fert_checkbox.active = False
            self.fert_type_input.text = ''
            self.fert_freq_input.text = ''

        else:
            popup = Popup(title="Error!", content=Label(text=error), size_hint=(0.7, 0.3))
            popup.open()

class CustomPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Set custom background color
        with self.canvas.before:
            Color(*COLOURS["accent"])
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[10, ])

        self.bind(size=self.update_graphics, pos=self.update_graphics)

    def update_graphics(self, *args):
        # Update the position and size of the background rectangle
        self.rect.pos = self.pos
        self.rect.size = self.size

if __name__ == "__main__":
    app = BestBuds()
    app.run()
