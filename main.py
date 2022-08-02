from collections import deque
from tkinter import *
from tkinter.ttk import Style, Scale
from tkinter.filedialog import asksaveasfile
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from struct import unpack, calcsize, pack
from socket import socket, AF_INET, SOCK_STREAM


class MenuBar(Menu):
    def __init__(self, ws):
        Menu.__init__(self, ws)
        self.muestra = 1500
        self.offset = StringVar()
        self.bg_color = '#D3D3D3'
        self.conectado = False
        # grafica
        
        file = Menu(self, tearoff=False, font=('Arial',13))
        file.add_command(label="Abrir")  
        file.add_command(label="Guardar")  
        file.add_command(label="Guardar como", command=self.guardar)    
        file.add_separator()
        file.add_command(label="Salir", underline=1, command=self.quit)
        self.add_cascade(label="Archivo",underline=0, menu=file)
        
        self.conectar = Menu(self, tearoff=0, font=('Arial', 13))
        self.conectar.add_command(label='Conectar', command=self.conectar_serial)
        self.conectar.add_separator()
        self.conectar.add_command(label='Desconectar', command=self.desconectar_serial)
        self.add_cascade(label='Conectar', underline=0, menu=self.conectar)

        edit = Menu(self, tearoff=0, font=('Arial', 13))  
        edit.add_command(label="Deshacer")  
        edit.add_separator()     
        self.add_cascade(label="Editar", menu=edit) 

        help = Menu(self, tearoff=0, font=("Arial",13))  
        help.add_command(label="About", command=self.about)  
        self.add_cascade(label="Ayuda", menu=help, font=('Arial', 15))  
        
        self.Widgets()

    def Widgets(self):
        frame = Frame(self.master, bg=self.bg_color, bd=2)
        frame.grid(column= 0, columnspan = 5, row = 0, sticky = 'nsew')
        # botones de conexion
        frame_izquierda = Frame(self.master, bg = self.bg_color)
        frame_izquierda.grid(column = 0, row= 1, sticky = 'nsew')

        frame_sliders = Frame(self.master, bg = self.bg_color)
        frame_sliders.grid(column=1, row=1, sticky = 'nsew')

        self.fig, ax = plt.subplots(facecolor=self.bg_color, dpi = 100, figsize =(4,1))
        plt.title('ELECTROCARDIOGRAMA', color = '#000000', size = 12, family = 'Arial')
        ax.tick_params(direction='out', length=5, width = 2, colors='#000000', grid_color='r', grid_alpha=0.5)
        self.line, = ax.plot([],[],color='m', marker='o', linewidth=2, markersize=0, markeredgecolor='g')
        
        plt.xlim([0, self.muestra])
        plt.ylim([5,15])
        
        ax.set_facecolor('#ffffff')
        ax.spines['bottom'].set_color('blue')
        ax.spines['left'].set_color('blue')
        ax.spines['top'].set_color('blue')
        ax.spines['right'].set_color('blue')

        self.datos_señal_uno = deque([0]*self.muestra, maxlen = self.muestra)

        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.rowconfigure(0, weight=5)
        self.master.rowconfigure(1, weight=1) 

        self.canvas = FigureCanvasTkAgg(self.fig, master = frame)
        self.canvas.get_tk_widget().pack(padx=0, pady=0, expand = True, fill='both')

        # botones
        self.bt_graficar = Button(frame_izquierda, text='Graficar', font=('Arial', 12, 'bold'), bg='#29b9bb', fg = '#000000', command = self.iniciar, bd=1, state='disabled')
        self.bt_graficar.pack(fill='both', expand=5)
        self.bt_pausar = Button(frame_izquierda, state='disabled', text = 'Pausar', font=('Arial', 12, 'bold'), bg = '#29b9bb', fg = '#000000', command = self.pausar, bd=1)
        self.bt_pausar.pack(fill='both', expand=5)
        self.bt_reanudar = Button(frame_izquierda, state = 'disabled', text = 'Reanudar', font =('Arial',12, 'bold'), bg = '#29b9bb', fg='#000000', command= self.reanudar, bd=1)
        self.bt_reanudar.pack(fill='both', expand=5)
        
        Label(frame_sliders, text = 'Offset', font =('Arial', 15), bg = self.bg_color, fg = '#000000').pack(expand=1)
        style = Style()
        style.configure("Horizontal.TScale", background =self.bg_color)
        self.slider_uno = Scale(frame_sliders, command=self.dato_slider_uno, to=4, from_=-4, orient='horizontal', length=280, style='TScale', value=0)
        self.slider_uno.pack(fill='both',expand = 5, padx=15)

        self.offset_number = StringVar()
        self.offset_number.set('0.000 v')
        self.label_offset = Label(frame_sliders, textvariable=self.offset_number, font=('Arial', 43, 'bold'), bg=self.bg_color, fg='#000000')
        self.label_offset.pack(fill='both')
    
    def getData(self):
        try:
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
        except:
            messagebox.showwarning('Error de Conexion', 'Se ha interrumpido la conexión con el dispositivo analizador.')
            self.conectado = False
            self.pausar()

    def animate(self,i):
        self.datos = self.getData()
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
        self.bt_graficar.config(state='disabled')
        self.bt_pausar.config(state='disabled')

    def reanudar(self):
        self.ani.event_source.start()
        self.bt_reanudar.config(state='disabled')
        self.bt_graficar.config(state='disabled')
        self.bt_pausar.config(state='normal')

    def sendinfo(self):
        self.client.sendall(pack('s', 'hola mundo'))

    def conectar_serial(self): 
        if self.conectado:
            messagebox.showerror('Error de conexion', 'Usted ya tiene una conexión con un dispositivo analizador.')
        else:
            try:
                self.client = socket(AF_INET, SOCK_STREAM)
                host = ('192.168.100.148', 9999)
                self.client.connect(host)
                
                messagebox.showinfo('Conectado', 'Listo para gráficar el electrocardiograma.')
                self.conectado = True
                self.bt_graficar.config(state='normal')
            except:
                messagebox.showerror('Error de conexión', 'No se ha podido conectar con el dispositivo.\nRevise si este se encuentra encendido.')

    def desconectar_serial(self):
        if self.conectado:
            self.client.close()
            messagebox.showinfo('Desconectado', 'Se ha desconectado del dispositivo analizador.')
        else:
            messagebox.showerror('Error de desconexion', 'Usted no ha iniciado una conexión con un dispositivo analizador.')

    def dato_slider_uno(self, *args): 
        self.offset.set(self.slider_uno.get())
        self.offset_number.set(str(round(float(self.slider_uno.get()), 3)) + ' v')
        self.label_offset.update()

    def exit(self):
        self.exit

    def about(self):
            messagebox.showinfo('Electrocardiográfo perron', 'Python Guides aims at providing best practical tutorials')

    def guardar(self):
        filepath = asksaveasfile(
            filetypes=(
                ("Text files", "*.txt"),
                ('CSV (Delimitado por comas)', '*.csv')
            ),
            defaultextension='.txt',
        )
        
        periodo = 30/500
        tiempo = 0
        with open(filepath.name, 'a') as file:
            for data in self.datos_señal_uno:
                file.write(f'{tiempo},{data}\n')
                tiempo  += periodo
            file.close()
        messagebox.showinfo("Listo", f"El registro se ha guardado con éxito\nGuardado en {filepath.name}")

class MenuDemo(Tk):
    def __init__(self):
        Tk.__init__(self)
        menubar = MenuBar(self)
        self.config(menu=menubar)

if __name__ == "__main__":
    ws=MenuDemo()
    ws.title('Electrocardiografo perronsote')
    ws.geometry('1500x800')
    ws.mainloop()