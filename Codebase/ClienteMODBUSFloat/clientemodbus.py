from pyModbusTCP.client import ModbusClient
from pymodbus.client import ModbusTcpClient
from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.constants import Endian
from time import sleep

class ClienteMODBUS():
    """
    Classe Cliente MODBUS
    """
    def __init__(self, server_ip,porta,scan_time=1):
        """
        Construtor
        """
        self._cliente = ModbusTcpClient(host=server_ip,port = porta)
        self._scan_time = scan_time

    def atendimento(self):
        """
        Método para atendimento do usuário
        """
        self._cliente.connect()
        try:
            atendimento = True
            while atendimento:
                sel = input("Deseja realizar uma leitura, escrita ou configuração? (1- Leitura | 2- Escrita | 3- Configuração | 4- Sair):\n")
                
                if sel == '1':
                    tipo = input("""Qual tipo de endereço deseja ler? (1- Holding Register | 2- Coil | 3- Input Register | 4- Discrete Input) :\n""")
                    if tipo in ['1', '3']:
                        bool_float = input("""Qual o tipo de dado armazenado? (1 - int | 2 - float32) :\n""")
                    else: bool_float = '1'
                    multiplicador = int(input("Digite o multiplicador do dado:\n"))
                    addr = input(f"Digite o endereço da tabela MODBUS:\n")
                    nvezes = input("Digite o número de vezes que deseja ler:\n")
                    for i in range(0,int(nvezes)):
                        print(f"Leitura {i+1}: {self.lerDado(int(tipo), int(addr), int if bool_float == '1' else float if bool_float == '2' else None, multiplicador)}")
                        sleep(self._scan_time)
                elif sel =='2':
                    tipo = input("""Qual tipo de dado deseja escrever? (1- Holding Register | 2- Coil) :""")
                    addr = input(f"Digite o endereço da tabela MODBUS: ")
                    valor = input(f"Digite o valor que deseja escrever: ")
                    self.escreveDado(int(tipo),int(addr),valor)

                elif sel=='3':
                    scant = input("Digite o tempo de varredura desejado [s]: ")
                    self._scan_time = float(scant)

                elif sel =='4':
                    self._cliente.close()
                    atendimento = False
                else:
                    print("Seleção inválida")
        except Exception as e:
            print('Erro no atendimento: ',e.args)

    def __identificarTipoDeDado(self, valor):
        """
        Método estático para identificar se o tipo de dado é str, int, ou float
        """
        tipo_valor = str

        if valor.isdigit():
            valor = int(valor)
            tipo_valor = int
        else:
            try:
                valor = float(valor)
                tipo_valor = float
            except ValueError:
                pass

        return tipo_valor

    def lerDado(self, tipo_endereco, addr, tipo_dado=int, multiplicador:int=1):
        """
        Método para leitura de um dado da Tabela MODBUS
        """
        is_int = tipo_dado is int
        is_float = tipo_dado is float

        if tipo_endereco == 1:
            resp = self._cliente.read_holding_registers(address=addr, count=1 if is_int else 4 if is_float else 1)
            
            if is_float:
                return self._cliente.convert_from_registers(\
                    registers=resp.registers,\
                    data_type=ModbusClientMixin.DATATYPE.FLOAT32,\
                    word_order='little'\
                )[0]/multiplicador
            else:
                return resp.registers[0]/multiplicador

        if tipo_endereco == 2:
            return self._cliente.read_coils(addr,1)[0]

        if tipo_endereco == 3:
            resp = self._cliente.read_input_registers(address=addr, count=1 if is_int else 4 if is_float else 1)
            
            if is_float:
                return self._cliente.convert_from_registers(\
                    registers=resp.registers,\
                    data_type=ModbusClientMixin.DATATYPE.FLOAT32,\
                    word_order='little'\
                )[0]/multiplicador
            else:
                return resp.registers[0]/multiplicador

        if tipo_endereco == 4:
            return self._cliente.read_discrete_inputs(addr,1)[0]

    def escreveDado(self, tipo_addr, addr, valor:str):
        """
        Método para a escrita de dados na Tabela MODBUS
        """
        tipo_valor = self.__identificarTipoDeDado(valor)
        if tipo_valor is str: raise TypeError("Valor escrito não pode ser uma string")

        if tipo_addr == 1:
            if tipo_valor is int:
                return self._cliente.write_register(addr,tipo_valor(valor))
            elif tipo_valor is float:
                binaryBuilder = BinaryPayloadBuilder(byteorder=Endian.BIG)
                binaryBuilder.add_32bit_float(float(valor))
                payload = binaryBuilder.to_registers()
                
                decodedFloat32 = ModbusClientMixin.convert_from_registers(payload, data_type=ModbusClientMixin.DATATYPE.FLOAT32, word_order='big')
                print(f"Valor float escrito:\r\n {decodedFloat32}")

                return self._cliente.write_registers(addr, payload)
        if tipo_addr == 2:
            return self._cliente.write_coil(addr,valor) if tipo_valor is int else None