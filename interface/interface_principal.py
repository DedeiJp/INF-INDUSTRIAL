import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.config import Config
from interface.interface_popup import ModbusConfig, ModalTensao, ModalCorrente, ModalTemperatura, ModalPotencia, ModalAcionamento, ModalPID
from os import path
from time import sleep
from threading import Thread, Lock
import sys
from kivy.garden import bar

from kivymd.icon_definitions import md_icons
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from kivymd.uix.list import MDListItem

from kivy.clock import mainthread

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
    __modbusDataTable: dict[dict[str, str|int]]

    _lock: Lock = Lock()

    _motor_actuator_register_write_thread: Thread = None
    _motor_driver_type_register_write_thread: Thread = None

    _PID_parameters_write_thread: Thread = None

    _modbus_connection_establishment_thread: Thread = None

    _data_ui_update_thread: Thread = None
    _enable_ui_update: bool = False
    _shutdown_initiated: bool = False

    _tipo_partida: int = 0
    
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
        self._acionamentoModal = ModalAcionamento()
        self._pidModal = ModalPID()

        self.__modbusDataTable: dict[dict[str, str|int]] = {
            "tipo_motor": { "addr": 708, "float": False, "multiplicador": 1, "valor": None, "unidade": "", "widget": self},
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
            "driver_partida": { "addr": 1216, "float": False, "multiplicador": 1, "valor": 0, "unidade": "", "widget": self._acionamentoModal}, # TODO: Mudar pra self._comandoModal
            "ctrl_partida_inv": { "addr": 1312, "float": False, "multiplicador": 1, "valor": None, "ctrl": True}, # TODO: Definir valor inicial das variáveis de controle
            "freq_partida_inv": { "addr": 1313, "float": False, "multiplicador": 10, "valor": None, "ctrl": True},
            "tempo_rampa_partida_inv": { "addr": 1314, "float": False, "multiplicador": 10, "valor": None, "ctrl": True},
            "tempo_rampa_desacc_inv": { "addr": 1315, "float": False, "multiplicador": 10, "valor": None, "ctrl": True},
            "ctrl_partida_soft": { "addr": 1316, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "tempo_rampa_partida_soft": { "addr": 1317, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "tempo_rampa_desacc_soft": { "addr": 1318, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "ctrl_partida_dir": { "addr": 1319, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "ctrl_driver_partida": { "addr": 1324, "float": False, "multiplicador": 1, "valor": None, "ctrl": True},
            "ctrl_tipo_pid": { "addr": 1332, "float": False, "multiplicador": 1, "valor": None, "ctrl": True}, # Se é automático ou manual
            "ctrl_sp_pid": { "addr": 1302, "float": True, "multiplicador": 1, "valor": None, "ctrl": True},
            "ctrl_P_pid": { "addr": 1304, "float": True, "multiplicador": 1, "valor": None, "ctrl": True},
            "ctrl_I_pid": { "addr": 1306, "float": True, "multiplicador": 1, "valor": None, "ctrl": True},
            "ctrl_D_pid": { "addr": 1308, "float": True, "multiplicador": 1, "valor": None, "ctrl": True},
            "ctrl_mv_pid": { "addr": 1310, "float": True, "multiplicador": 1, "valor": None, "ctrl": True},
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
        with self._lock:
            print("Definindo intervalo de atualização de dados modbus e UI")
            self._modbusConnParams["scan_time"] = scan_time / 1000

    def set_modbus_conn_params(self, host: str, port: int):
        """
        Define os parâmetros de conexão ao servidor modbus
        """
        if type(host) is str and type(port) is int:
            with self._lock:
                self._modbusConnParams['host'] = host
                self._modbusConnParams['port'] = port
        else:
            print("Erro: parâmetros de conexão com formato inválido")
            return

    def _create_modbus_connection(self, host: str, port: int, scantime: int = 1000):
        """
        Cria a conexão do cliente com o servidor modbus
        """
        if type(host) is str and type(port) is int:
            self.set_modbus_conn_params(host, port)
            self.set_modbus_scan_time(scantime)
        else:
            print("Erro: parâmetros de conexão com formato inválido")
            return

        with self._lock:
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
                self._enable_buttons()
                # Mudança de Status
                self.__handle_client_connected()

                print("Conexão estabelecida com sucesso")
                self._enable_ui_update = True
                self.__start_update_thread()

    
    def create_modbus_connection(self, host: str, port: int, scantime: int = 1000):
        """
        Inicia uma Thread secundária responsável por iniciar a conexão do cliente com o servidor modbus
        """
        if self._modbus_connection_establishment_thread and self._modbus_connection_establishment_thread.is_alive():
            return

        self._modbus_connection_establishment_thread = Thread(target=self._create_modbus_connection, args=(host, port, scantime))
        self._modbus_connection_establishment_thread.start()

    def _close_modbus_connection(self):
        """
        Encerra a conexão do cliente com o servidor modbus
        """
        with self._lock:
            print("Fechando conexão com servidor modbus")
            if not self._modbusClient: return

            self._modbusClient.close()
            self._enable_ui_update = False

            # Desabilitação dos botões
            self._disable_buttons()
            # Mudança de Status
            self.__handle_client_disconnected()

    def close_modbus_connection(self):
        """
        Inicia uma Thread secundária responsável por encerrar a conexão do cliente com o servidor modbus
        """
        if self._modbus_connection_establishment_thread and self._modbus_connection_establishment_thread.is_alive():
            return
        
        self._modbus_connection_establishment_thread = Thread(target=self._close_modbus_connection)
        self._modbus_connection_establishment_thread.start()

    def __start_update_thread(self):
        """
        Inicializa a thread de leitura de dados e atualização de interface
        """
        print("Inicializando thread de atualização de dados e UI...")
        if not self._data_ui_update_thread or not self._data_ui_update_thread.is_alive():
            self._data_ui_update_thread = Thread(target=self._update_data_and_ui)
            self._data_ui_update_thread.start()
            
        self._enable_ui_update = True

    def _update_data_and_ui(self):
        """
        Realiza leitura dos dados do servidor modbus e atualiza a interface com os dados atualizados
        """
        while not self._shutdown_initiated:
            try:
                while self._enable_ui_update and self._modbusClient.is_connected():
                    print("Atualizando dados...")
                    self._update_data()
                    self._update_ui()
                    sleep(self._modbusConnParams["scan_time"])
                break # Encerra o loop da thread para que ela morra caso ocorra exceção
            except Exception as e:
                if not self._shutdown_initiated:
                    self.close_modbus_connection()
                    print("Erro ao atualizar dados e interface: ", e.args)

                    # Desabilitação dos Botões
                    self._disable_buttons()
                    # Mudança de Status com Erro
                    self.__handle_client_lost_connection()

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
                        tipo_motor = "MOTOR DE ALTA EFICIENCIA" if int(info_dado["valor"]) == 1 else "MOTOR DE BAIXA EFICIENCIA" if int(info_dado["valor"]) == 2 else "MOTOR DE BAIXA EFICIENCIA"
                        info_dado["widget"].ids[f"lb_{nome_dado}"].text = tipo_motor
                        continue
                    case "driver_partida":
                        driver_partida = "DIRETA" if int(info_dado["valor"]) == 0 else "SOFT-START" if int(info_dado["valor"]) == 1 else "INVERSOR" if int(info_dado["valor"]) == 2 else None
                        info_dado["widget"].ids[f"lb_{nome_dado}"].text = driver_partida
                        continue
                    case "vel_est":
                        velocidade_esteira = float(self.__modbusDataTable["vel_est"]["valor"])
                        self.ids.bar_velocidade.value = (velocidade_esteira / 100) * 100
                        continue
                    case "rot_motor":
                        rpm = float(self.__modbusDataTable["rot_motor"]["valor"])
                        self.ids.bar_rpm.value = (rpm / 2000) * 100
                        continue
                    case "torque_mot":
                        torque = float(self.__modbusDataTable["torque_mot"]["valor"])
                        self.ids.bar_torque.value = (torque / 1) * 100
                        continue
                    case _:
                        info_dado["widget"].ids[f"lb_{nome_dado}"].text = str(info_dado["valor"]) + " " + info_dado["unidade"]
                
            except KeyError as ke:
                print("Label inexistente: ", ke.args)

    def _set_tipo_partida(self, tipo_partida: int):
        """
        Escreve nos registradores modbus adequados para que seja definido o tipo de partida do motor
        """
        if tipo_partida >= 0 and tipo_partida <= 2:
            with self._lock:
                self.__modbusDataTable["ctrl_driver_partida"]["valor"] = tipo_partida

            self._modbusClient.escreveDado(\
                addr.HOLDING_REGISTER,\
                self.__modbusDataTable["ctrl_driver_partida"]["addr"],\
                str(tipo_partida)\
            )


    def set_tipo_partida(self, tipo_partida: int):
        """
        Inicia uma Thread secundário responsável por escrever nos registradores modbus adequados para que seja definido o tipo de partida do motor
        """
        if (self._motor_driver_type_register_write_thread and self._motor_driver_type_register_write_thread.is_alive()):
            return

        self._motor_driver_type_register_write_thread = Thread(target=self._set_tipo_partida, args=(tipo_partida,))

        self._motor_driver_type_register_write_thread.start()

    def _start_motor(self, acc: int, desacc: int, freq: int):
        """
        Escreve nos registradores modbus adequados para que seja realizada a partida do motor
        """
        with self._lock:
            driver_partida = self.__modbusDataTable["driver_partida"]["valor"]

        match driver_partida:
            case 0:
                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["ctrl_partida_dir"]["addr"],\
                    '1'\
                )
            case 1:
                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["tempo_rampa_partida_soft"]["addr"],\
                    str(acc)\
                )

                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["tempo_rampa_desacc_soft"]["addr"],\
                    str(desacc)\
                )

                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["ctrl_partida_soft"]["addr"],\
                    '1'\
                )
            case 2:
                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["freq_partida_inv"]["addr"],\
                    str(freq)\
                )

                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["tempo_rampa_partida_inv"]["addr"],\
                    str(acc)\
                )

                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["tempo_rampa_desacc_inv"]["addr"],\
                    str(desacc)\
                )

                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["ctrl_partida_inv"]["addr"],\
                    '1'\
                )

    def start_motor(self, acc: int, desacc: int, freq: int):
        """
        Inicia uma Thread secundário responsável por escrever nos registradores modbus adequados para que seja realizado a partida do motor
        """
        if (self._motor_actuator_register_write_thread and self._motor_actuator_register_write_thread.is_alive()):
            return
        
        try:
            acc = int(acc)
            desacc = int(desacc)
            freq = int(freq)
        except ValueError as ve:
            print("É preciso definir os valores de aceleração e desaceleração para realizar a partida do motor")
            return
        

        if acc < 10 or desacc < 10 or freq < 0:
            acc = 10
            desacc = 10
            freq = 0
        elif acc > 60 or desacc > 60 or freq > 60:
            acc = 60
            desacc = 60
            freq = 60

        self._motor_actuator_register_write_thread = Thread(target=self._start_motor, args=(acc, desacc, freq,))

        self._motor_actuator_register_write_thread.start()

    def _stop_motor(self):
        """
        Escreve nos registradores modbus adequados para que seja realizada a parada do motor
        """
        with self._lock:
            driver_partida = self.__modbusDataTable["driver_partida"]["valor"]

        match driver_partida:
            case 0:
                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["ctrl_partida_dir"]["addr"],\
                    '0'\
                )
            case 1:
                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["ctrl_partida_soft"]["addr"],\
                    '0'\
                )
            case 2:
                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["ctrl_partida_inv"]["addr"],\
                    '0'\
                )
                      
    def stop_motor(self):
        """
        Inicia uma Thread secundária responsável por escrever nos registradores modbus adequados para que seja realizada a parada do motor
        """
        if (self._motor_actuator_register_write_thread and self._motor_actuator_register_write_thread.is_alive()):
            return

        self._motor_actuator_register_write_thread = Thread(target=self._stop_motor)
        
        self._motor_actuator_register_write_thread.start()

    def _reset_motor(self):
        """
        Escreve nos registradores modbus adequados para que seja realizado o reset do motor
        """
        with self._lock:
            driver_partida = self.__modbusDataTable["driver_partida"]["valor"]

        match driver_partida:
            case 0:
                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["ctrl_partida_dir"]["addr"],\
                    '2'\
                )
            case 1:
                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["ctrl_partida_soft"]["addr"],\
                    '2'\
                )
            case 2:
                self._modbusClient.escreveDado(\
                    addr.HOLDING_REGISTER,\
                    self.__modbusDataTable["ctrl_partida_inv"]["addr"],\
                    '2'\
                )

    def reset_motor(self):
        """
        Inicia um Thread secundária responsável por escrever nos registradores modbus adequados para que seja realizado o reset do motor
        """
        if (self._motor_actuator_register_write_thread and self._motor_actuator_register_write_thread.is_alive()):
            return
        
        self._motor_actuator_register_write_thread = Thread(target=self._reset_motor)

        self._motor_actuator_register_write_thread.start()

    def _set_pid_parameters(self, auto: bool, sp: float, mv: float, P: float, I: float, D: float):
        """
        Escreve nos registradores modbus adequados para atualizar os valores de parâmetros PID da carga
        """
        with self._lock:
            self.__modbusDataTable["ctrl_tipo_pid"]["valor"] = 1 if auto else 0
            self.__modbusDataTable["ctrl_sp_pid"]["valor"] = sp
            self.__modbusDataTable["ctrl_mv_pid"]["valor"] = mv
            self.__modbusDataTable["ctrl_P_pid"]["valor"] = P
            self.__modbusDataTable["ctrl_I_pid"]["valor"] = I
            self.__modbusDataTable["ctrl_D_pid"]["valor"] = D

        self._modbusClient.escreveDado(\
            addr.HOLDING_REGISTER,\
            self.__modbusDataTable["ctrl_tipo_pid"]["addr"],\
            str(1 if auto else 0)\
        )

        self._modbusClient.escreveDado(\
            addr.HOLDING_REGISTER,\
            self.__modbusDataTable["ctrl_sp_pid"]["addr"],\
            str(sp)\
        )

        self._modbusClient.escreveDado(\
            addr.HOLDING_REGISTER,\
            self.__modbusDataTable["ctrl_mv_pid"]["addr"],\
            str(mv)\
        )

        self._modbusClient.escreveDado(\
            addr.HOLDING_REGISTER,\
            self.__modbusDataTable["ctrl_P_pid"]["addr"],\
            str(P)\
        )

        self._modbusClient.escreveDado(\
            addr.HOLDING_REGISTER,\
            self.__modbusDataTable["ctrl_I_pid"]["addr"],\
            str(I)\
        )

        self._modbusClient.escreveDado(\
            addr.HOLDING_REGISTER,\
            self.__modbusDataTable["ctrl_D_pid"]["addr"],\
            str(D)\
        )

    def set_pid_parameters(self, auto: bool, sp: float, mv: float, P: float, I: float, D: float):
        """
        Inicia uma Thread secundária responsável por escrever nos registradores modbus adequados para atualizar os valores de parâmetros PID da carga
        """
        if self._PID_parameters_write_thread and self._PID_parameters_write_thread.is_alive():
            return

        self._PID_parameters_write_thread = Thread(target=self._set_pid_parameters, args=(auto, sp, mv, P, I, D))

        self._PID_parameters_write_thread.start()
    
    @mainthread
    def _enable_buttons(self):
        self.ids.bt_temperatura.disabled = False
        self.ids.bt_potencia.disabled = False
        self.ids.bt_tensao.disabled = False
        self.ids.bt_corrente.disabled = False
        self.ids.bt_torque.disabled = False
        self.ids.bt_rpm.disabled = False
        self.ids.bt_velocidade.disabled = False
        self.ids.bt_pid.disabled = False
        self.ids.bt_acionamento.disabled = False

    @mainthread
    def _disable_buttons(self):
        self.ids.bt_temperatura.disabled = True
        self.ids.bt_potencia.disabled = True
        self.ids.bt_tensao.disabled = True
        self.ids.bt_corrente.disabled = True
        self.ids.bt_torque.disabled = True
        self.ids.bt_rpm.disabled = True
        self.ids.bt_velocidade.disabled = True
        self.ids.bt_pid.disabled = True
        self.ids.bt_acionamento.disabled = True

    @mainthread
    def __handle_client_connected(self):
        self.ids.lb_status_conected_text.text = "Cliente Conectado"
        self.ids.lb_status_conected_icon.icon = "lan-connect"
        self.ids.img_warnnig_conn.opacity = 0
    
    @mainthread
    def __handle_client_disconnected(self):
        self.ids.lb_status_conected_text.text = "Cliente Desconectado"
        self.ids.lb_status_conected_icon.icon = "lan-disconnect"
        self.ids.img_warnnig_conn.opacity = 0
    
    @mainthread
    def __handle_client_lost_connection(self):
        self.ids.lb_status_conected_text.text = "Conexão Perdida"
        self.ids.lb_status_conected_icon.icon = "lan-disconnect"
        self.ids.img_warnnig_conn.opacity = 100
