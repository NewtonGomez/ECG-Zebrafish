from concurrent.futures import thread
from tkinter import Tk, Frame, Button, Label, ttk, PhotoImage, StringVar
from tkinter.ttk import Combobox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import collections 
from struct import unpack, calcsize, pack
from socket import socket, AF_INET, SOCK_STREAM
import time
from threading import Thread

class Grafica(Frame): 
    def __init__(self,master, *args):
        super().__init__( master, *args, bg='#54123B')
        self.__force_Stop__ = True
        self.muestra = 100
        self.datos = 0.0
        self.offset = StringVar()

        self.fig, ax = plt.subplots(facecolor='#54123B', dpi = 100, figsize =(4,1))
        plt.title('ELECTROCARDIOGRAMA', color = 'white', size = 12, family = 'Arial')
        ax.tick_params(direction='out', length=5, width = 2, colors='white', grid_color='r', grid_alpha=0.5)

        self.line, = ax.plot([],[],color='m', marker='o', linewidth=2, markersize=1, markeredgecolor='g')

        plt.xlim([0, self.muestra])
        plt.ylim([-10,10])

        ax.set_facecolor('#000000')
        ax.spines['bottom'].set_color('blue')
        ax.spines['left'].set_color('blue')
        ax.spines['top'].set_color('blue')
        ax.spines['right'].set_color('blue')

        self.datos_señal_uno = collections.deque([0]*self.muestra, maxlen = self.muestra)

        self.widgets()
    
    def getData(self):
        data = b''
        payloadsize = calcsize('f')

        while len(data) < payloadsize:
            packet = self.client.recv(4)
            if not packet:
               break
            data += packet
        
        packedmsg = data[:payloadsize]
        data = data[payloadsize:]

        unpackedmsg = unpack('f', packedmsg)
        return float(unpackedmsg[0])

    def animate(self,i):
        self.datos = self.getData()
        print('------')
        print(type(self.offset.get()))
        print(f'offset {self.offset.get()}')
        if self.offset.get() == "":
            self.datos_señal_uno.append(self.datos)
        else:
            self.datos_señal_uno.append(self.datos + float(self.offset.get()))
        self.line.set_data(range(self.muestra), self.datos_señal_uno)

    def iniciar(self,): 
        self.ani = animation.FuncAnimation(self.fig, self.animate,
            interval = 0, blit = False)
        self.bt_graficar.config(state='disabled')
        self.bt_pausar.config(state='normal')
        self.canvas.draw()

    def pausar(self): 
        self.ani.event_source.stop()
        self.bt_reanudar.config(state='normal')

    def reanudar(self):
        self.ani.event_source.start()
        self.bt_reanudar.config(state='disabled')

    def widgets(self):
        # grafica
        frame = Frame(self.master, bg='#54123B', bd=2)
        frame.grid(column= 0, columnspan = 5, row = 0, sticky = 'nsew')
        
        # botones de conexion
        frame_izquierda = Frame(self.master, bg = '#54123B')
        frame_izquierda.grid(column = 0, row= 1, sticky = 'nsew')
        
        frame_derecha = Frame(self.master, bg = '#54123B')
        frame_derecha.grid(column=2, row= 1, sticky='nsew')
        
        frame_sliders = Frame(self.master, bg = '#54123B')
        frame_sliders.grid(column=1, row=1, sticky = 'nsew')

        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.columnconfigure(2, weight=1)
        self.master.rowconfigure(0, weight=5)
        self.master.rowconfigure(1, weight=1)

        self.canvas = FigureCanvasTkAgg(self.fig, master = frame)
        self.canvas.get_tk_widget().pack(padx=0, pady=0, expand = True, fill='both')

        self.bt_graficar = Button(frame_izquierda, text='Graficar ECG', font=('Arial', 12, 'bold'), bg='#84142D', fg = 'white', command = self.iniciar, bd=0)
        self.bt_graficar.pack(fill='both', expand=5)
        
        self.bt_pausar = Button(frame_izquierda, state='disabled', text = 'Pausar', font=('Arial', 12, 'bold'), bg = '#C02739', fg = 'white', command = self.pausar, bd=0)
        self.bt_pausar.pack(fill='both', expand=5)
        
        self.bt_reanudar = Button(frame_izquierda, state = 'disabled', text = 'Reanudar', font =('Arial',12, 'bold'), bg = '#84142D', fg='white', command= self.reanudar, bd=0)
        self.bt_reanudar.pack(fill='both', expand=5)

        Label(frame_sliders, text = 'Offset', font =('Arial', 15), bg = '#54123B', fg = 'white').pack(expand=1)
        style = ttk.Style()
        style.configure("Horizontal.TScale", background ='#54123B')

        self.slider_uno = ttk.Scale(frame_sliders, command = self.dato_slider_uno, to = 4, from_ =-4, orient='horizontal', length = 280, style ='TScale', value=0)
        self.slider_uno.pack(fill='both',expand = 5, padx=15)
        
        self.bt_grabar = Button(frame_derecha, text='Conectar', font =('Arial', 12, 'bold'), bg = '#29C7AC', fg='white',command = self.conectar_serial, bd=1) 
        self.bt_grabar.pack(fill='both', expand=5)

        self.thread_widgets_grabar = Thread(target=self.widgets_grabacion)
        self.thread_widgets_grabar.start()

    def widgets_grabacion(self):
        self.led_variable = StringVar()
        self.led_variable.set('rsc/led_red_off.png')

        self.frame_saving = Frame(self.master, bg= '#54123B', pady=20, padx=10)
        self.frame_saving.grid(column=5, row=0, sticky='nsew')

        self.frame_extra = Frame(self.master, bg= '#54123B')
        self.frame_extra.grid(column=5, row=1, sticky='nsew')

        self.led = PhotoImage(file=self.led_variable.get())
        self.led = self.led.subsample(2)
        self.label_led = Label(self.frame_saving, bd=0, image=self.led, bg='#54123B')
        self.label_led.pack(fill='both')

        self.tiempo = StringVar()
        self.tiempo.set('00:00 s')
        self. label_contador = Label(self.frame_saving, bd=0, bg='#54123B', textvariable=self.tiempo, font=('Arial', 50, 'bold'), fg='white')
        self.label_contador.pack(fill='both')

        timer_variable = StringVar()
        
        self.temporizador = Combobox(self.frame_saving, textvariable=timer_variable, font=('Arial', 15))
        self.temporizador.pack(fill='both')
        self.temporizador['values'] = ('5s', '10s', '30s', '60s', '90s', '120s', '180s')
        self.temporizador.current(5)
        self.temporizador.update()

        self.bt_grabar = Button(self.frame_saving, text='Grabar', font =('Arial', 12, 'bold'), bg = '#29C7AC', fg='white',command = lambda: self.accion_grabar(self.temporizador.get()), bd=1) 
        self.bt_grabar.pack(fill='both')

        self.bt_detener = Button(self.frame_saving, text='Detener', font =('Arial', 12, 'bold'), bg = '#29C7AC', fg='white', bd=1, state='disabled', command=self.stop_counting) 
        self.bt_detener.pack(fill='both')

    def accion_grabar(self, contador):
        print(f'conteo: {contador}')
        conteo = int(contador.replace('s', ''))
        
        self.led_variable.set('rsc/led_red_on.png')
        self.led = PhotoImage(file=self.led_variable.get())
        self.led = self.led.subsample(2)
        self.label_led.config(image=self.led)

        self.bt_grabar.config(state='disabled')
        self.bt_detener.config(state='normal')
        
        self.__force_Stop__ = True

        while self.__force_Stop__ and conteo:
            m, s = divmod(conteo, 60)
            intTiempo = '{:02d}:{:02d} s'.format(m, s)
            
            self.tiempo.set(intTiempo)
            self.label_contador.update()
            
            time.sleep(1)
            conteo -= 1

        self.tiempo.set('00:00 s')
        self.led_variable.set('rsc/led_red_off.png')
        self.led = PhotoImage(file=self.led_variable.get())
        self.led = self.led.subsample(2)
        self.label_led.config(image=self.led)

    def stop_counting(self):
        self.__force_Stop__ = False
        self.bt_grabar.config(state='normal')
        self.bt_detener.config(state='disabled')

    def sendinfo(self):
        self.client.sendall(pack('s', 'hola mundo'))

    def conectar_serial(self): 
        self.client = socket(AF_INET, SOCK_STREAM)

        host = ('192.168.100.148', 9999)
        self.client.connect(host)
        print('CONECTADO AL SERVIDOR')

    def dato_slider_uno(self, *args): 
        self.offset.set(self.slider_uno.get())

if __name__=="__main__":
    ventana = Tk()
    ventana.geometry('1500x800')
    ventana.config(bg= 'gray30', bd=4)
    ventana.wm_title('Electrocardiografo')
    ventana.minsize(width=700,height=400)
    app = Grafica(ventana)
    app.mainloop()