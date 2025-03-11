import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.config import Config

class MyWidget(BoxLayout):
    def changelb(self):
        """
        Método simples para incremento do valor mostrado no label
        """
        self.ids['lb'].text = str(int(self.ids.lb.text) + 1) 
