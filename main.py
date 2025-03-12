from kivy.app import App
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.uix.layout import Layout
import interface.interface_principal as ui_p

class App_main(App):
    """
    Aplicativo principal:
        Herda classe App da kivy.
    """
    def build(self):
        """
        Método de construção da janela com os parametros. 
        """
        self._widget = ui_p.MyWidget()
        return self._widget
    
    def app_stop(self):
        # TODO: Avaliar para que serve essa função
        self._widget.stopRefresh()
    
if __name__ == '__main__':
    # Window.fullscreen = True
    Window.size = (1280, 720)
    Builder.load_string(open("interface/interface_principal.kv", encoding = "utf-8").read())
    Builder.load_string(open("interface/interface_popup.kv", encoding = "utf-8").read(), rulesonly = True)
    App_main().run()
