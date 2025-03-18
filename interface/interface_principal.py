import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.config import Config
from interface.interface_popup import ModbusConfig, ModalTensao, ModalCorrente, ModalTemperatura, ModalPotencia
from os import path
from time import sleep
from threading import Thread
import sys
from kivy.garden import bar

from kivymd.icon_definitions import md_icons
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from kivymd.uix.list import MDListItem

sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from cliente_modbus.clientemodbus import ClienteMODBUS, TipoEndereco as addr

class MyWidget(BoxLayout):
    # TODO: Implementar lógica de status motor
    # TODO: Implementar lógica de tipo de motor

    _ipConfigModal: Popup
    _modbusClient: ClienteMODBUS = None
    _modbusConnParams: dict = {
        "host": None,
        "port": None,
        'scan_time': 1
    }
    __modbusDataTable: dict[dict[str, str|int]]

    _data_ui_update_thread: Thread = None
    _enable_ui_update: bool = False
    _shutdown_initiated: bool = False
    
    def __init__(self, **kwargs):
        """
        Construtor da interface pricipal
        """
        super().__init__()

        # Popups
        self._ipConfigModal = ModbusConfig()
        self._tensaoModal = ModalTensao()
        self._correnteModal = ModalCorrente()
        self._potenciaModal = ModalPotencia()
        self._temperaturaModal = ModalTemperatura()

        self.__modbusDataTable: dict[dict[str, str|int]] = {
            "tipo_motor": { "addr": 708, "float": True, "multiplicador": 1, "valor": None, "unidade": "", "widget": self},
            "temp_r": { "addr": 700, "float": True, "multiplicador": 10, "valor": None, "unidade": "°C", "widget": self._temperaturaModal},
            "temp_s": { "addr": 702, "float": True, "multiplicador": 10, "valor": None, "unidade": "°C", "widget": self._temperaturaModal},
            "temp_t": { "addr": 704, "float": True, "multiplicador": 10, "valor": None, "unidade": "°C", "widget": self._temperaturaModal},
            "temp_carc": { "addr": 706, "float": True, "multiplicador": 10, "valor": None, "unidade": "°C", "widget": self._temperaturaModal},
            "carga_est": { "addr": 710, "float": True, "multiplicador": 1, "valor": None, "unidade": "Kgf/cm²", "widget": self},
            "vel_est": { "addr": 724, "float": True, "multiplicador": 1, "valor": None, "unidade": "m/min", "widget": self},
            "curr_r": { "addr": 840, "float": False, "multiplicador": 100, "valor": None, "unidade": "A", "widget": self._correnteModal},
            "curr_s": { "addr": 841, "float": False, "multiplicador": 100, "valor": None, "unidade": "A", "widget": self._correnteModal},
            "curr_t": { "addr": 842, "float": False, "multiplicador": 100, "valor": None, "unidade": "A", "widget": self._correnteModal},
            "curr_N": { "addr": 843, "float": False, "multiplicador": 100, "valor": None, "unidade": "A", "widget": self._correnteModal},
            "curr_med": { "addr": 845, "float": False, "multiplicador": 100, "valor": None, "unidade": "A", "widget": self._correnteModal},
            "tens_rs": { "addr": 847, "float": False, "multiplicador": 10, "valor": None, "unidade": "V", "widget": self._tensaoModal},
            "tens_st": { "addr": 848, "float": False, "multiplicador": 10, "valor": None, "unidade": "V", "widget": self._tensaoModal},
            "tens_tr": { "addr": 849, "float": False, "multiplicador": 10, "valor": None, "unidade": "V", "widget": self._tensaoModal},
            "pot_ativ_r": { "addr": 852, "float": False, "multiplicador": 1, "valor": None, "unidade": "W", "widget": self._potenciaModal},
            "pot_ativ_s": { "addr": 853, "float": False, "multiplicador": 1, "valor": None, "unidade": "W", "widget": self._potenciaModal},
            "pot_ativ_t": { "addr": 854, "float": False, "multiplicador": 1, "valor": None, "unidade": "W", "widget": self._potenciaModal},
            "pot_ativ_total": { "addr": 855, "float": False, "multiplicador": 1, "valor": None, "unidade": "W", "widget": self._potenciaModal},
            "pot_reativ_r": { "addr": 856, "float": False, "multiplicador": 1, "valor": None, "unidade": "VAr", "widget": self._potenciaModal},
            "pot_reativ_s": { "addr": 857, "float": False, "multiplicador": 1, "valor": None, "unidade": "VAr", "widget": self._potenciaModal},
            "pot_reativ_t": { "addr": 858, "float": False, "multiplicador": 1, "valor": None, "unidade": "VAr", "widget": self._potenciaModal},
            "pot_reativ_total": { "addr": 859, "float": False, "multiplicador": 1, "valor": None, "unidade": "VAr", "widget": self._potenciaModal},
            "pot_apar_r": { "addr": 860, "float": False, "multiplicador": 1, "valor": None, "unidade": "VA", "widget": self._potenciaModal},
            "pot_apar_s": { "addr": 861, "float": False, "multiplicador": 1, "valor": None, "unidade": "VA", "widget": self._potenciaModal},
            "pot_apar_t": { "addr": 862, "float": False, "multiplicador": 1, "valor": None, "unidade": "VA", "widget": self._potenciaModal},
            "pot_apar_total": { "addr": 863, "float": False, "multiplicador": 1, "valor": None, "unidade": "VA", "widget": self._potenciaModal},
            "rot_motor": { "addr": 884, "float": True, "multiplicador": 1, "valor": None, "unidade": "RPM", "widget": self},
            "driver_partida": { "addr": 1216, "float": False, "multiplicador": 1, "valor": None, "unidade": "", "widget": self}, # TODO: Mudar pra self._comandoModal
            "ctrl_partida_inv": { "addr": 1312, "float": False, "multiplicador": 1, "valor": None, "ctrl": True}, # TODO: Definir valor inicial das variáveis de controle
            "freq_partida_inv": { "addr": 1313, "float": False, "multiplicador": 10, "valor": None, "ctrl": True},
            "tempo_rampa_partida_inv": { "addr": 1314, "float": False, "multiplicador": 10, "valor": None, "ctrl": True},
            "tempo_rampa_desacc_inv": { "addr": 1315, "float": False, "multiplicador": 10, "valor": None, "ctrl": True},
            "ctrl_partida_soft": { "addr": 1316, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "tempo_rampa_partida_soft": { "addr": 1317, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "tempo_rampa_desacc_soft": { "addr": 1318, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "ctrl_partida_dir": { "addr": 1319, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "ctrl_driver_partida": { "addr": 1324, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "ctrl_tipo_pid": { "addr": 1332, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "energ_ativ": { "addr": 1210, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "energ_reativ": { "addr": 1212, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "energ_apar": { "addr": 1214, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "status_mot": { "addr": 1330, "float": False, "multiplicador": 1, "bit": 0, "valor": None, "unidade": "", "widget": self},
            "torque_mot": { "addr": 1420, "float": True, "multiplicador": 100, "valor": None, "unidade": "N*m", "widget": self}
        }

    def shutdown(self):
        self._shutdown_initiated = True
        if self._modbusClient:
            self.close_modbus_connection()
        self.clear_widgets()
    
    def set_modbus_scan_time(self, scan_time: int):
        print("Definindo intervalo de atualização de dados modbus e UI")
        self._modbusConnParams["scan_time"] = scan_time / 1000

    def set_modbus_conn_params(self, host: str, port: int, scan_time: int = 1):
        """
        Define os parâmetros de conexão ao servidor modbus
        """
        if type(host) is str and type(port) is int:
            self._modbusConnParams['host'] = host
            self._modbusConnParams['port'] = port

    def create_modbus_connection(self, host: str, port: int):
        """
        Cria a conexão do cliente com o servidor modbus
        """
        if type(host) is str and type(port) is int:
            self._modbusConnParams['host'] = host
            self._modbusConnParams['port'] = port
        else:
            print("Erro: parâmetros de conexão com formato inválido")
            return

        if self._modbusClient and self._modbusClient.is_connected():
            self.close_modbus_connection()
            # del self._modbusClient

        self._modbusClient = ClienteMODBUS(\
            self._modbusConnParams['host'],\
            self._modbusConnParams['port'],\
            self._modbusConnParams['scan_time']
        )

        print("Criando conexão com servidor modbus:", self._modbusConnParams)
        connected = self._modbusClient.connect()

        if connected:

            # Habilitação dos botões
            self.activate_buttons()
            # Mudança de Status
            self.interface_conectado()

            print("Conexão estabelecida com sucesso")
            self._enable_ui_update = True
            self.__start_update_thread()

    def close_modbus_connection(self):
        print("Fechando conexão com servidor modbus")
        self._modbusClient.close()
        self._enable_ui_update = False

        # Desabilitação dos botões
        self.disable_buttons()
        # Mudança de Status
        self.interface_desconectado()

    def __start_update_thread(self):
        """
        Inicializa a thread de leitura de dados e atualização de interface
        """
        print("Inicializando thread de atualização de dados e UI...")
        if not self._data_ui_update_thread:
            self._data_ui_update_thread = Thread(target=self._update_data_and_ui)
            self._data_ui_update_thread.start()
            
        self._enable_ui_update = True

    def _update_data_and_ui(self):
        """
        Realiza leitura dos dados do servidor modbus e atualiza a interface com os dados atualizados
        """
        while not self._shutdown_initiated:
            try:
                while self._enable_ui_update:
                    print("Atualizando dados...")
                    self._update_data()
                    self._update_ui()
                    sleep(self._modbusConnParams["scan_time"])
            except Exception as e:
                if not self._shutdown_initiated:
                    self.close_modbus_connection()
                    print("Erro ao atualizar dados e interface: ", e.args)

                    # Desabilitação dos Botões
                    self.disable_buttons()
                    # Mudança de Status com Erro
                    self.interface_conec_lost()

    def _update_data(self):
        """
        Realiza leitura e atualização em memória dos dados buscado no servidor modbus
        """
        for info_dado in self.__modbusDataTable.values():
            is_ctrl_var = info_dado.get("ctrl") is not None
            if is_ctrl_var:
                continue

            
            info_dado["valor"] = self._modbusClient.lerDado(\
                addr.HOLDING_REGISTER,\
                info_dado["addr"],\
                float if info_dado["float"] else int,\
                info_dado["multiplicador"]\
            )

    def _update_ui(self):
        """
        Atualiza a UI com os dados oriundos da tabela modbus
        """
        self.update_bars()

        for nome_dado, info_dado in self.__modbusDataTable.items():
            try:
                is_ctrl_var = info_dado.get("ctrl") is not None
                if is_ctrl_var:
                    continue

                match nome_dado:
                    case "status_mot":
                        bit_0 = int(info_dado["valor"]) & 1
                        info_dado["widget"].ids[f"lb_{nome_dado}"].text = "LIGADO" if bit_0 else "DESLIGADO"
                        continue
                    case "tipo_motor":
                        tipo_motor = "VERDE" if int(info_dado["valor"]) == 1 else "AZUL" if int(info_dado["valor"]) == 2 else None
                        info_dado["widget"].ids[f"lb_{nome_dado}"].text = tipo_motor
                        continue
                    case "driver_partida":
                        driver_partida = "DIRETA" if int(info_dado["valor"]) == 0 else "SOFT-START" if int(info_dado["valor"]) == 1 else "INVERSOR" if int(info_dado["valor"]) == 2 else None
                        info_dado["widget"].ids[f"lb_{nome_dado}"].text = driver_partida
                        continue
                    case _:
                        info_dado["widget"].ids[f"lb_{nome_dado}"].text = str(info_dado["valor"]) + " " + info_dado["unidade"]
                # if nome_dado == "status_mot":
                #     bit_0 = info_dado["valor"] & 1
                #     # TODO: Implementar lógica
                #     info_dado["widget"].ids[f"lb_{nome_dado}"].text = "LIGADO" if bit_0 else "DESLIGADO"
                #     continue

                # if nome_dado == "tipo_motor":
                #     tipo_motor = "VERDE" if info_dado["valor"] == 1 else "AZUL" if info_dado["valor"] == 2 else None
                #     info_dado["widget"].ids[f"lb_{nome_dado}"].text = tipo_motor
                #     continue

                # if nome_dado == "driver_partida":
                #     driver_partida = "DIRETA" if info_dado["valor"] == 0 else "SOFT-START" if info_dado["valor"] == 1 else "INVERSOR" if info_dado["valor"] == 2 else None
                #     info_dado["widget"].ids[f"lb_{nome_dado}"].text = driver_partida
                #     continue
                

                # info_dado["widget"].ids[f"lb_{nome_dado}"].text = str(info_dado["valor"]) + " " + info_dado["unidade"]
                
            except KeyError as ke:
                print("Label inexistente: ", ke.args)
    
    def activate_buttons(self):
        self.ids.bt_temperatura.disabled = False
        self.ids.bt_potencia.disabled = False
        self.ids.bt_tensao.disabled = False
        self.ids.bt_corrente.disabled = False
        self.ids.bt_torque.disabled = False
        self.ids.bt_rpm.disabled = False
        self.ids.bt_velocidade.disabled = False
        self.ids.bt_pid.disabled = False
        self.ids.bt_acionamento.disabled = False

    def disable_buttons(self):
        self.ids.bt_temperatura.disabled = True
        self.ids.bt_potencia.disabled = True
        self.ids.bt_tensao.disabled = True
        self.ids.bt_corrente.disabled = True
        self.ids.bt_torque.disabled = True
        self.ids.bt_rpm.disabled = True
        self.ids.bt_velocidade.disabled = True
        self.ids.bt_pid.disabled = True
        self.ids.bt_acionamento.disabled = True

    def interface_conectado(self):
        self.ids.lb_status_conected_text.text = "Cliente Conectado"
        self.ids.lb_status_conected_icon.icon = "lan-connect"
        self.ids.img_warnnig_conn.opacity = 0
    def interface_desconectado(self):
        self.ids.lb_status_conected_text.text = "Cliente Desconectado"
        self.ids.lb_status_conected_icon.icon = "lan-disconnect"
        self.ids.img_warnnig_conn.opacity = 0
    def interface_conec_lost(self):
        self.ids.lb_status_conected_text.text = "Conexão Perdida"
        self.ids.lb_status_conected_icon.icon = "lan-disconnect"
        self.ids.img_warnnig_conn.opacity = 100

    def update_bars(self):
        rpm = (self.__modbusDataTable["rot_motor"]["valor"])
        torque = (self.__modbusDataTable["torque_mot"]["valor"])
        velocidade = (self.__modbusDataTable["vel_est"]["valor"])

        self.ids.bar_torque.value = (torque / 1) * 100
        self.ids.bar_rpm.value = (rpm / 2000) * 100
        self.ids.bar_velocidade.value = (velocidade / 10) * 100