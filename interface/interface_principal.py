import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.config import Config
from interface.interface_popup import ModbusConfig, ModalTensao, ModalCorrente
from os import path
import sys

sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
from cliente_modbus.clientemodbus import ClienteMODBUS, TipoEndereco as addr

class MyWidget(BoxLayout):
    _ipConfigModal: Popup
    _modbusClient: ClienteMODBUS = None
    _modbusConnParams: dict = {
        "host": None,
        "port": None,
        'scan_time': 1
    }
    __modbusDataTable: dict[dict[str, str|int]] = {
        "tipo_motor": { "addr": 708, "float": True, "multiplicador": 1, "valor": None},
        "temp_r": { "addr": 700, "float": True, "multiplicador": 10, "valor": None},
        "temp_s": { "addr": 702, "float": True, "multiplicador": 10, "valor": None},
        "temp_t": { "addr": 704, "float": True, "multiplicador": 10, "valor": None},
        "temp_carc": { "addr": 706, "float": True, "multiplicador": 10, "valor": None},
        "carga_est": { "addr": 710, "float": True, "multiplicador": 1, "valor": None},
        "vel_est": { "addr": 724, "float": True, "multiplicador": 1, "valor": None},
        "curr_r": { "addr": 840, "float": False, "multiplicador": 100, "valor": None},
        "curr_s": { "addr": 841, "float": False, "multiplicador": 100, "valor": None},
        "curr_t": { "addr": 842, "float": False, "multiplicador": 100, "valor": None},
        "curr_N": { "addr": 843, "float": False, "multiplicador": 100, "valor": None},
        "curr_med": { "addr": 845, "float": False, "multiplicador": 100, "valor": None},
        "tens_rs": { "addr": 847, "float": False, "multiplicador": 10, "valor": None},
        "tens_st": { "addr": 848, "float": False, "multiplicador": 10, "valor": None},
        "tens_tr": { "addr": 849, "float": False, "multiplicador": 10, "valor": None},
        "pot_ativ_r": { "addr": 852, "float": False, "multiplicador": 1, "valor": None},
        "pot_ativ_s": { "addr": 853, "float": False, "multiplicador": 1, "valor": None},
        "pot_ativ_t": { "addr": 854, "float": False, "multiplicador": 1, "valor": None},
        "pot_ativ_total": { "addr": 855, "float": False, "multiplicador": 1, "valor": None},
        "pot_reativ_r": { "addr": 856, "float": False, "multiplicador": 1, "valor": None},
        "pot_reativ_s": { "addr": 857, "float": False, "multiplicador": 1, "valor": None},
        "pot_reativ_t": { "addr": 858, "float": False, "multiplicador": 1, "valor": None},
        "pot_reativ_total": { "addr": 859, "float": False, "multiplicador": 1, "valor": None},
        "pot_apar_r": { "addr": 860, "float": False, "multiplicador": 1, "valor": None},
        "pot_apar_s": { "addr": 861, "float": False, "multiplicador": 1, "valor": None},
        "pot_apar_t": { "addr": 862, "float": False, "multiplicador": 1, "valor": None},
        "pot_apar_total": { "addr": 863, "float": False, "multiplicador": 1, "valor": None},
        "rot_motor": { "addr": 884, "float": True, "multiplicador": 1, "valor": None},
        "driver_partida": { "addr": 1216, "float": False, "multiplicador": 1, "valor": None},
        "ctrl_partida_inv": { "addr": 1312, "float": False, "multiplicador": 1, "valor": None},
        "freq_partida_inv": { "addr": 1313, "float": False, "multiplicador": 10, "valor": None},
        "tempo_rampa_partida_inv": { "addr": 1314, "float": False, "multiplicador": 10, "valor": None},
        "tempo_rampa_desacc_inv": { "addr": 1315, "float": False, "multiplicador": 10, "valor": None},
        "ctrl_partida_soft": { "addr": 1316, "float": False, "multiplicador": 1, "valor": None},
        "tempo_rampa_partida_soft": { "addr": 1317, "float": False, "multiplicador": 1, "valor": None},
        "tempo_rampa_desacc_soft": { "addr": 1318, "float": False, "multiplicador": 1, "valor": None},
        "ctrl_partida_dir": { "addr": 1319, "float": False, "multiplicador": 1, "valor": None},
        "ctrl_driver_partida": { "addr": 1324, "float": False, "multiplicador": 1, "valor": None},
        "ctrl_tipo_pid": { "addr": 1332, "float": False, "multiplicador": 1, "valor": None},
        "energ_ativ": { "addr": 1210, "float": False, "multiplicador": 1, "valor": None},
        "energ_reativ": { "addr": 1212, "float": False, "multiplicador": 1, "valor": None},
        "energ_apar": { "addr": 1214, "float": False, "multiplicador": 1, "valor": None},
        "status_mot": { "addr": 1330, "float": False, "multiplicador": 1, "bit": 0, "valor": None},
        "torque_mot": { "addr": 1420, "float": True, "multiplicador": 100, "valor": None}
    }

    _data_ui_update_thread: Thread = None
    _enable_ui_update: bool = False
    
    def __init__(self, **kwargs):
        """
        Construtor da interface pricipal
        """
        super().__init__()

        # Popups
        self._ipConfigModal = ModbusConfig()
        self._tensaoModal = ModalTensao()
        self._correnteModal = ModalCorrente()
    
    def __set_modbus_conn_params(self, host: str, port: int, scan_time: int = 1):
        """
        Define os parâmetros de conexão ao servidor modbus
        """
        if type(host) is str and type(port) is int and type(scan_time) is int:
            self._modbusConnParams['host'] = host
            self._modbusConnParams['port'] = port
            self._modbusConnParams['scan_time'] = scan_time

    def __create_modbus_connection(self):
        """
        Cria a conexão do cliente com o servidor modbus
        """
        if not self.__set_modbus_conn_params['host'] or not self.__set_modbus_conn_params['port']:
            # TODO: Tratar
            return

        if not self._modbusClient:
            self._modbusClient = ClienteMODBUS(\
                self.__set_modbus_conn_params['host'],\
                self.__set_modbus_conn_params['port'],\
                self.__set_modbus_conn_params['scan_time']
            )
        
        connected = self._modbusClient.connect()

        if connected:
            self.__start_data_reading_thread()

    def __close_modbus_connection(self):
        self._modbusClient.close()
        self._enable_ui_update = False

    def __start_data_reading_thread(self):
        """
        Inicializa a thread de leitura de dados e atualização de interface
        """
        if not self._data_ui_update_thread:
            self._data_ui_update_thread = Thread(target=self._update_data_and_ui)
            self._data_ui_update_thread.start()

        self._update_ui = True

    def _update_data_and_ui(self):
        """
        Realiza leitura dos dados do servidor modbus e atualiza a interface com os dados atualizados
        """
        try:
            while self._enable_ui_update:
                self._read_and_update_modbus_data()
        except Exception as e:
            self.__close_modbus_connection()
            print("Erro: ", e.args)

    def _read_and_update_modbus_data(self):
        """
        Realiza leitura e atualização em memória dos dados buscado no servidor modbus
        """
        for nome_dado in self.__modbusDataTable.keys():
            self.__modbusDataTable[nome_dado]["valor"] = self._modbusClient.lerDado(\
                addr.HOLDING_REGISTER,\
                self.__modbusDataTable[nome_dado]["addr"],\
                float if self.__modbusDataTable[nome_dado]["float"] else int,\
                self.__modbusDataTable[nome_dado]["multiplicador"]\
            )
