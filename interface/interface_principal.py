import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config
from interface.interface_popup import IpConfigModbus

class MyWidget(BoxLayout):
    
    def __init__(self, **kwargs):
        """
        Construtor da interface pricipal
        """
        super().__init__()


        #Popups
        self._ipConfig = IpConfigModbus()
