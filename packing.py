# SERVIDOR
from struct import pack, unpack, calcsize
from random import randint
from socket import socket, AF_INET, SOCK_STREAM, gethostname, gethostbyname

from numpy import empty

def Recibido(client):
    pass

def filtro60Hz(dato):
    # procesamiento matematico par aun filtro notch de 60Hz
    return dato

server = socket(AF_INET, SOCK_STREAM) # creacion del socket

hostname = gethostname() # obtenemos el nombre del servidor
ip = gethostbyname(hostname) # obtenemos la direccion ip
port = 9999 # puerto al que accederemos
direccion = (ip, port) # tupla con la direccion completa ip:port

print(f'DIRECCION -> {direccion}:{port}') # impresion de la direccion
server.bind(direccion) # abre un enlace en la direccion del servidor
server.listen(5) # cantidad de conexiones permitidas

while True:
    client, addr = server.accept() # si un cliente se conecta
    print(f'conexion con: {addr}') # mostramos la direccion de la conexion
    
    while True:
        # creamos un numero aleatorio para enviarlo
        adc_read = float(f'{randint(-4, 4)}.{randint(0, 9)}') 
        filtrado = filtro60Hz(adc_read) # filtramos la señal
        print(adc_read)
        
        # para enviar la informacion hay que convertirla a un conjunto de bytes
        # por lo que la señal filtrada, es empaquetada con el metodo pack
        packedinfo = pack('f', filtrado)

        # enviamos la informacion al cliente
        client.sendall(packedinfo)