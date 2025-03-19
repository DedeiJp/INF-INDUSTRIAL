from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.uix.layout import Layout
import interface.interface_principal as ui_p

class App_main(MDApp):
    """
    Aplicativo principal:
        Herda classe App da kivy.
    """
    def build(self):
        """
        Método de construção da janela com os parametros. 
        """
        db_path = "teste1.db"
        self._widget = ui_p.MyWidget(db_path=db_path)
        return self._widget
    
    def on_stop(self):
        """
        Método de fechamento do aplicativo.
        """
        self._widget.shutdown()
    
if __name__ == '__main__':
    # Window.fullscreen = True
    Window.size = (1280, 720)
    Builder.load_string(open("interface/interface_principal.kv", encoding = "utf-8").read())
    Builder.load_string(open("interface/interface_popup.kv", encoding = "utf-8").read(), rulesonly = True)
    App_main().run()
