from clientemodbus import ClienteMODBUS

"""
Módulo main para testes
"""

# c = ClienteMODBUS('10.15.20.24', 502)
c = ClienteMODBUS('localhost', 502)
c.atendimento()
