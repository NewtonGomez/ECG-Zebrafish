# ECG TRANSMITIDO VIA WI-FI
<h2 id='introduccion'>Introducción</h2>
El uso de animales como modelos biológicos en el campo de la medicina en el campo de la 
toxicidad de los medicamentos a través del sistema cardiovascular, es indispensable, ya que así 
se pueden reevaluar y analizar diferentes fármacos para el beneficio del ser humano. Uno de los 
modelos biológicos que han despegado en los últimos años en esta área es el pez cebra, ya que 
tiene una onda electrocardiográfica demasiado similar al de los seres humanos; y es capaz de 
ser reproducido y almacenado en espacios reducidos y con bajos insumos vitales para su 
supervivencia. 
Se diseño este programa para poder enviar esa señal digitalizada desde un sistema embedido basado en arduino, y recogida
en el programa de computadora para su posterior analisis y modificacion.

2. [Graficación y animación](#animacion)
    * [Creación del canvas](#canvas) 
    * [Animación](#animaciones) 
3. [Prótocolo de recepción WIFI](#protocolo)
4. [Acondicionamiento de la señal](#acondicionamiento)
5. [Análisis de la señal ECG](#analisis)


<br>

<h2 id='animacion'>Animación</h2>
La animación de la gráfica se divide en dos secciones, la primera es la creación del canvas, y la animación

<br>

<h3 id='canvas'>Creación del Canvas</h3>

``` python
self.fig, ax = plt.subplots(
    facecolor=self.bg_color, 
    dpi = 100, 
    figsize=(4,5)
)
ax.tick_params(
    direction='out', 
    length=5, 
    width = 2, 
    colors='#000000', 
    grid_color='r', 
    grid_alpha=0.5
)
self.line, = ax.plot(
    [],[],
    color='m', 
    marker='o', 
    linewidth=2, 
    markersize=0, 
    markeredgecolor='g'
)

plt.xlim([0, self.muestra])
plt.ylim([5,15])

ax.set_facecolor('#ffffff')
ax.spines['bottom'].set_color('blue')
ax.spines['left'].set_color('blue')
ax.spines['top'].set_color('blue')
ax.spines['right'].set_color('blue')

self.datos_señal_uno = deque(
    [0]*self.muestra, 
    maxlen = self.muestra
)

self.canvas = FigureCanvasTkAgg(self.fig, master = frame)
self.canvas.get_tk_widget().pack()
```
Donde con la función [**subplots**]() se define una figura donde se colocará la gráfica. Con [**tick_params**]() se le dan las caracteristicas que se necesitan para la linea de la gráfica. Con las funciones [**xlim**]() y [**ylim**]() se le dice el tamaño que se requiere.

La parte que contiene la información de la gráfica es *datos señal uno*, el cual usa la función [**deque**](https://www.geeksforgeeks.org/deque-in-python/) el cual almacena una lista de tamaño *n* (siendo *n* la cantidad de muestras que se sobreponen a la gráfica). Esta variable se va actualizando con la función **get_Data**, que recibe información via WIFI

<br>

<h3 id='animaciones'>Animación</h3>

``` python
self.datos = self.getData()
if self.offset.get() == "":
    self.datos_señal_uno.append(self.datos)
else:
    self.datos_señal_uno.append(self.datos + float(self.offset.get()))
self.line.set_data(range(self.muestra), self.datos_señal_uno)

```

Lo que se hace es que al obtener información a traves de la red, se agrega este valor flotante en la variable lista *datos_señal_uno*, y esta lista completa se actualiza a la variable *line* con su método [**set_data**]().

<br>

<h2 id='protocolo'>Prótocolo de recepción WI-FI</h2>

```Python
data = b''
payloadsize = calcsize('f')

while len(data) < payloadsize:
    packet = self.client.recv(4)
    if not packet:
        break
    data += packet

packedmsg = data[:payloadsize]
data = data[payloadsize:]

unpackedmsg = unpack('i', packedmsg)
return float(unpackedmsg[0])/100
```

Lo que se hace en esta función es establecer una variable con el tamaño del paquete que se va a recibir (recibiendo como parametro lo que sabemos que es el tipo de variable que se va a recibir, en este caso un flotante) llamada payloadsize. 

Se hace un ciclo while con la condición de que la variable data sea menor que payloadsize, con la funcion [**recv**](https://docs.python.org/es/3/library/socket.html), el valor devuelto es un objeto bytes que representa los datos recibidos.

La información retornada en la variable packet se suma en bytes a data. De ahí se desempaqueta, y se regresa en una division entre 100 para reducir el valor de información.

<h2 id='acondicionamiento'>Acondicionamiento de la señal</h2>
<h2 id='analisis'>Analisís de la señal</h2>
