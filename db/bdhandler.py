from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from threading import Lock
from datetime import datetime

# Base para os modelos do SQLAlchemy
Base = declarative_base()

class DataTable(Base):
    """
    Modelo da tabela de dados.
    As colunas são criadas dinamicamente no __init__ do BDHandler.
    """
    __tablename__ = 'dataTable'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime)

class BDHandler:
    """
    Classe para manipulação do banco de dados usando SQLAlchemy.
    """
    def __init__(self, dbpath, tags, tablename='dataTable'):
        """
        Construtor.
        """
        self._dbpath = dbpath
        self._tablename = tablename
        self._engine = create_engine(f'sqlite:///{self._dbpath}')
        self._Session = sessionmaker(bind=self._engine)
        self._session = self._Session()
        # Filtra as colunas que não devem ser armazenadas no banco de dados
        self._col_names = [key for key, value in tags.items() if not value.get("ctrl", False) and key not in["tipo_motor", "driver_partida", "status_mot"]]
        self._lock = Lock()

        # Adiciona colunas dinamicamente com base nas tags
        for col_name in self._col_names:
            setattr(DataTable, col_name, Column(Float))

        # Cria a tabela se não existir
        Base.metadata.create_all(self._engine)

    def __del__(self):
        """
        Fecha a sessão ao destruir o objeto.
        """
        self._session.close()

    def insertData(self, data):
        """
        Método para inserção dos dados no BD.
        """
        try:
            self._lock.acquire()
            print("Adquire o lock do insert data")

            # Prepara os dados para inserção
            timestamp_str = data['timestamp']
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            values = data['values']

            # Cria um novo registro
            new_entry = DataTable(timestamp=timestamp, **values)
            self._session.add(new_entry)
            self._session.commit()
            print("Dado inserido no db")
        except Exception as e:
            print("Erro: ", e.args)
            self._session.rollback()
        finally:
            print("Libera o lock do insert data")
            self._lock.release()

    def selectData(self, cols, init_t, final_t):
        """
        Método que realiza a busca no BD entre dois horários.
        init_t e final_t são objetos datetime.
        """
        try:
            self._lock.acquire()
            print("Adquire o lock do select data")

            # Realiza a consulta
            query = self._session.query(DataTable).filter(
                DataTable.timestamp.between(init_t, final_t)
            ).with_entities(*[getattr(DataTable, col) for col in cols])

            # Organiza os dados em um dicionário
            dados = dict((sensor, []) for sensor in cols)
            for linha in query.all():
                for i, col in enumerate(cols):
                    if col == 'timestamp':
                        # Converte o datetime para string, se necessário
                        dados[col].append(linha[i].strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        dados[col].append(linha[i])
            return dados
        except Exception as e:
            print("Erro: ", e.args)
            return None
        finally:
            print("Libera o lock do select data")
            self._lock.release()