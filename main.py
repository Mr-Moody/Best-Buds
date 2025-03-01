from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget

class MyApp(App):
    def build(self):
        btn = ButtonWidget()
        return btn
    
class ButtonWidget(Widget):
    def __init__(self, **kwargs):
        super(ButtonWidget, self).__init__(**kwargs)
        btn1 = Button(text='Hello World 1')
        btn1.bind(on_press=self.callback)
        self.add_widget(btn1)

    def callback(self, instance):
        print('The button %s state is <%s>' % (instance, instance.state))

app = MyApp()
app.run()
