import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.config import Config
from interface.interface_popup import IpConfigModbus
from cliente_modbus import ClienteMODBUS, TipoEndereco as addr

class MyWidget(BoxLayout):
    _ipConfigModal: Popup
    _modbusClient: ClienteMODBUS = None
    _modbusConnParams: dict = {
        "host": None,
        "port": None,
        'scan_time': 1
    }
    __modbusDataTable: dict[dict[str, str|int]] = {
        "tipo_motor": { "addr": 708, "tipo_addr": addr.HOLDING_REGISTER, "float": True, "multiplicador": 1},
        "temp_r": { "addr": 700, "tipo_addr": addr.HOLDING_REGISTER, "float": True, "multiplicador": 10},
        "temp_s": { "addr": 702, "tipo_addr": addr.HOLDING_REGISTER, "float": True, "multiplicador": 10},
        "temp_t": { "addr": 704, "tipo_addr": addr.HOLDING_REGISTER, "float": True, "multiplicador": 10},
        "temp_carc": { "addr": 706, "tipo_addr": addr.HOLDING_REGISTER, "float": True, "multiplicador": 10},
        "carga_est": { "addr": 710, "tipo_addr": addr.HOLDING_REGISTER, "float": True, "multiplicador": 1},
        "vel_est": { "addr": 724, "tipo_addr": addr.HOLDING_REGISTER, "float": True, "multiplicador": 1},
        "curr_r": { "addr": 840, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 100},
        "curr_s": { "addr": 841, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 100},
        "curr_t": { "addr": 842, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 100},
        "curr_N": { "addr": 843, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 100},
        "curr_med": { "addr": 845, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 100},
        "tens_rs": { "addr": 847, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 10},
        "tens_st": { "addr": 848, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 10},
        "tens_tr": { "addr": 849, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 10},
        "pot_ativ_r": { "addr": 852, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "pot_ativ_s": { "addr": 853, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "pot_ativ_t": { "addr": 854, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "pot_ativ_total": { "addr": 855, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "pot_reativ_r": { "addr": 856, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "pot_reativ_s": { "addr": 857, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "pot_reativ_t": { "addr": 858, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "pot_reativ_total": { "addr": 859, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "pot_apar_r": { "addr": 860, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "pot_apar_s": { "addr": 861, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "pot_apar_t": { "addr": 862, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "pot_apar_total": { "addr": 863, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "rot_motor": { "addr": 884, "tipo_addr": addr.HOLDING_REGISTER, "float": True, "multiplicador": 1},
        "driver_partida": { "addr": 1216, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "ctrl_partida_inv": { "addr": 1312, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "freq_partida_inv": { "addr": 1313, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 10},
        "tempo_rampa_partida_inv": { "addr": 1314, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 10},
        "tempo_rampa_desacc_inv": { "addr": 1315, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 10},
        "ctrl_partida_soft": { "addr": 1316, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "tempo_rampa_partida_soft": { "addr": 1317, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "tempo_rampa_desacc_soft": { "addr": 1318, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "ctrl_partida_dir": { "addr": 1319, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "ctrl_driver_partida": { "addr": 1324, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "ctrl_tipo_pid": { "addr": 1332, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "energ_ativ": { "addr": 1210, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "energ_reativ": { "addr": 1212, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "energ_apar": { "addr": 1214, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1},
        "status_mot": { "addr": 1330, "tipo_addr": addr.HOLDING_REGISTER, "float": False, "multiplicador": 1, "bit": 0},
        "torque_mot": { "addr": 1420, "tipo_addr": addr.HOLDING_REGISTER, "float": True, "multiplicador": 100}
    }
    
    def __init__(self, **kwargs):
        """
        Construtor da interface pricipal
        """
        super().__init__()

        # Popups
        self._ipConfigModal = IpConfigModbus()

    
    def __setModbusConnParams(self, host: str, port: int, scan_time: int = 1):
        """
        Define os parâmetros de conexão ao servidor modbus
        """
        if type(host) is str and type(port) is int and type(scan_time) is int:
            self._modbusConnParams['host'] = host
            self._modbusConnParams['port'] = port
            self._modbusConnParams['scan_time'] = scan_time

    def __createModbusConnection(self):
        """
        Cria a conexão do cliente com o servidor modbus
        """
        if not self.__setModbusConnParams['host'] or not self.__setModbusConnParams['port']:
            # TODO: Tratar
            return

        if not self._modbusClient:
            self._modbusClient = ClienteMODBUS(\
                self.__setModbusConnParams['host'],\
                self.__setModbusConnParams['port'],\
                self.__setModbusConnParams['scan_time']
            )
        
        self._modbusClient.connect()

    def __closeModbusConnection(self):
        self._modbusClient.close()
