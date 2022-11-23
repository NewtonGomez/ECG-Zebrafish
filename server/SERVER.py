from socket import socket, AF_INET, SOCK_STREAM, gethostname, gethostbyname
import network
from time import sleep
from struct import pack
from machine import Pin, ADC

def web_page():
  with open('index.html', 'r') as file:
    web_page = str()
    for line in file.readlines():
        web_page += line.split('\n')[0]

    file.close()
  return web_page

exist = bool()

try: 
  file = open('contraseñas.txt', 'r')  
  exist = True
  file.close()
except:
  exist = False

if exist:
  ssid = str()
  pswd = str()
  with open('contraseñas.txt', 'r') as file:
    for line in file.readlines():
      if line == 'ssid':
        ssid = line
      elif line == 'pswd':
        pswd = line   
    file.close()
  
  station = network.WLAN(network.STA_IF)

  station.active(True)
  station.connect(ssid, pswd)

  while station.isconnected() == False:
    pass

  print("Conexion establecida")
  ip = station.ifconfig()[0]
  print(ip)

  server = socket(AF_INET, SOCK_STREAM)
  server.bind((ip, 9999))
  server.listen(5)

  i = 0
  while True:
      client, addr = server.accept() # si un cliente se conecta
      print(f'conexion con: {addr}') # mostramos la direccion de la conexion
      
      sleep(5)
      print('listo')
      sleep(0.5)
      while True:
          # leemos la informacion
          readit = float(ADC(Pin(26)))
          
          # para enviar la informacion hay que convertirla a un conjunto de bytes
          # por lo que la se甯絘l filtrada, es empaquetada con el metodo pack
          packedinfo = pack('f', readit)

          # enviamos la informacion al cliente
          try:
              client.sendall(packedinfo)
          except:
              continue

else:
  ap = network.WLAN(network.AP_IF)
  ap.active(True)
  ap.config(essid='wifi ecgza', password='1234')

  ip = ap.ipfconfig()[0]
  print(ip)
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #creating socket object
  s.bind((ip, 80))
  s.listen(5)
  while True:
    conn, addr = s.accept()
    print('Got a connection from %s' % str(addr))
    request = conn.recv(1024)
    response = web_page()
    conn.send(response)
    conn.close()