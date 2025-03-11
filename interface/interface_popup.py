from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.graph import LinePlot

class IpConfigModbus(Popup):
    """""
    Popup da configuração de IP e Porta no MODBUS
    """
    def __init__(self, **kwargs):
        """"
        Construtor da classe ModbusPopup
        """
        super().__init__(**kwargs)

