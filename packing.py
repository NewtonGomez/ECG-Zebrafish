# SERVIDOR
from struct import pack
from random import randint
#from machine import Pin
#import network
from socket import socket, AF_INET, SOCK_STREAM, gethostname, gethostbyname

#ap = network.WLAN(network.AP_IF)
#ap.active(True)
#ap.config(essid="ecg_zebra", password="1234")

#led = Pin(2, Pin.OUT)
#led.value(not led.value())
server = socket(AF_INET, SOCK_STREAM) # creacion del socket

#ip = ap.ifconfig()[0] # obtenemos el nombre del servidor
ip = gethostbyname(gethostname())
port = 9999 # puerto al que accederemos
direccion = (ip, port) # tupla con la direccion completa ip:port

print(f'DIRECCION -> {direccion}') # impresion de la direccion
server.bind(direccion) # abre un enlace en la direccion del servidor
server.listen(5) # cantidad de conexiones permitidas

while True:
    client, addr = server.accept() # si un cliente se conecta
    print(f'conexion con: {addr}') # mostramos la direccion de la conexion
    
    while True:
        #led.value(not led.value())
        # creamos un numero aleatorio para enviarlo
        adc_read = float(f'{randint(-4, 4)}.{randint(0, 9)}') 
        
        # para enviar la informacion hay que convertirla a un conjunto de bytes
        # por lo que la se甯絘l filtrada, es empaquetada con el metodo pack
        packedinfo = pack('f',adc_read)

        # enviamos la informacion al cliente
        client.sendall(packedinfo)

