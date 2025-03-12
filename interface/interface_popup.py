from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.graph import LinePlot

class ModbusConfig(Popup):
    """""
    Popup da configuração de IP e Porta no MODBUS
    """
    lb_informacao = None

    def __init__(self, **kwargs):
        """"
        Construtor da classe ModbusConfig
        """
        super().__init__(**kwargs)
    
    def limpar_dados(self):
        if self.lb_informacao is not None:
            self.ids.md_modbus_config.remove_widget(self.lb_informacao)

class ModalTensao(Popup):
    """""
    Popup da configuração de IP e Porta no MODBUS
    """

    def __init__(self, **kwargs):
        """"
        Construtor da classe ModalTensao
        """
        super().__init__(**kwargs)
    

class ModalCorrente(Popup):
    """""
    Popup da configuração de IP e Porta no MODBUS
    """

    def __init__(self, **kwargs):
        """"
        Construtor da classe ModalCorrente
        """
        super().__init__(**kwargs)

