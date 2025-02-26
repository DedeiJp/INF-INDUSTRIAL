from kivy.app import App
from kivy.core.window import Window
from kivy.lang.builder import Builder
import interface_main as im

class App_main(App):
    """
    Aplicativo principal:
        Recebe App da kivy.
    """

    def build(self):
        """
        Método de construção da janela, com os parametros. 
        """
        self._widget = im.MyWidget()
        return self._widget
    
    def App_stop(self):
        self._widget.stopRefresh()
    
if __name__ == '__main__':
    #Window.fullscreen = True
    Builder.load_string(open("Codebase/interface_main.kv", encoding = "utf-8").read(), rulesonly = True)
    #Builder.load_string(open("interface_secudarias.kv", encoding = "utf-8").read(), rulesonly = True)
    App_main().run()   