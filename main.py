from collections import deque
from tkinter import *
from tkinter.ttk import Progressbar, Style, Scale
from tkinter.filedialog import askopenfile, asksaveasfile
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import webbrowser
import matplotlib.animation as animation
from struct import unpack, calcsize, pack
from socket import gethostbyname, gethostname, socket, AF_INET, SOCK_STREAM, getfqdn
import math
import numpy as np

def ecg_analyzer(dataset) -> dict:
    sampleRate = 2000
    hrw = 0.25 #One-sided window size, as proportion of the sampling frequency
    fs = sampleRate #The example dataset was recorded at 100Hz

    mov_avg = dataset['hart'].rolling(int(hrw*fs)).mean() #Calculate moving average
    #Impute where moving average function returns NaN, which is the beginning of the signal where x hrw
    avg_hr = (np.mean(dataset.hart[:sampleRate]))
    mov_avg = [avg_hr if math.isnan(x) else x for x in mov_avg]
    mov_avg = [x*1.2 for x in mov_avg] 
    dataset['hart_rollingmean'] = mov_avg #Append the moving average to the dataframe

    #Mark regions of interest
    window = []
    peaklist = []
    listpos = 0 #We use a counter to move over the different data columns

    for datapoint in dataset.hart:
        rollingmean = dataset.hart_rollingmean[listpos] #Get local mean
        if (datapoint < rollingmean) and (len(window) < 1): #If no detectable R-complex activity -> do nothing
            listpos += 1
        elif (datapoint > rollingmean): #If signal comes above local mean, mark ROI
            window.append(datapoint)
            listpos += 1
        else: #If signal drops below local mean -> determine highest point
            beatposition = listpos - len(window) + (window.index(max(window))) #Notate the position of the point on the X-axis
            peaklist.append(beatposition) #Add detected peak to list
            window = [] #Clear marked ROI
            listpos += 1

    ybeat = [dataset.hart[x] for x in peaklist] #Get the y-value of all peaks for plotting purposes

    RR_list = []
    cnt = 0

    while (cnt < (len(peaklist)-1)):
        RR_interval = (peaklist[cnt+1] - peaklist[cnt]) #Calculate distance between beats in # of samples
        ms_dist = ((RR_interval / fs) * float(sampleRate)) #Convert sample distances to ms distances
        RR_list.append(ms_dist) #Append to list
        cnt += 1

    bpm = round(60000 / np.mean(RR_list))
    return {'x':peaklist, 'y':ybeat, 'bpm':bpm}

class MenuBar(Menu):
    def __init__(self, ws):
        Menu.__init__(self, ws)
        self.muestra = 2700
        self.offset = StringVar()
        self.bg_color = '#D3D3D3'
        self.conectado = False
        self.frame_scanner = True
        # grafica
        
        file = Menu(self, tearoff=False)
        file.add_command(label="Abrir", command=self.abrir_archivo)  
        file.add_command(label="Nuevo", command=self.nuevo_escaner)  
        file.add_command(label="Guardar")  
        file.add_command(label="Guardar como", command=self.guardar)    
        file.add_separator()
        file.add_command(label="Salir", underline=1, command=self.quit)
        self.add_cascade(label="Archivo",underline=0, menu=file)
        
        self.conectar = Menu(self, tearoff=0)
        self.conectar.add_command(label='Conectar', command=self.conectar_serial)
        self.conectar.add_separator()
        self.conectar.add_command(label='Desconectar', command=self.desconectar_serial)
        self.conectar.add_separator()
        self.conectar.add_command(label='Buscar Dispostivo', command=self.establecerConexion)
        self.add_cascade(label='Conectar', underline=0, menu=self.conectar)

        self.edit = Menu(self, tearoff=0)  
        self.edit.add_command(label="Deshacer")  
        self.edit.add_command(label="Rehacer")  
        self.edit.add_separator()
        self.add_cascade(label="Editar", menu=self.edit) 

        self.filtros = Menu(self.edit, tearoff=0)
        self.filtros.add_command(label="Crear Filtro", command= self.DiseñarFiltro)
        self.filtros.add_command(label="Aplicar Filtro", command=self.AplicarFiltros)
        self.edit.add_cascade(label='Filtros', menu=self.filtros)

        help = Menu(self, tearoff=0)  
        help.add_command(label="Manual", command=lambda: webbrowser.open('https://qastack.mx/programming/4302027/how-to-open-a-url-in-python'))  
        help.add_command(label="Acerca De", command=lambda: webbrowser.open('https://qastack.mx/programming/4302027/how-to-open-a-url-in-python'))  
        self.add_cascade(label="Ayuda", menu=help)  
        
        self.Widgets()

    def nuevo_escaner(self):
        if not self.frame_scanner:
            self.frame_analisis.forget()
            self.Widgets()
        else:
            messagebox.showinfo('Listos para el registro', 'Estamos preparados para un nuevo registro.')

    def Widgets(self):
        self.frame_principal = Frame(self.master)
        self.frame_principal.pack(fill='both', expand=5)

        frame = Frame(self.frame_principal, bg=self.bg_color, bd=2)
        frame.grid(column= 0, columnspan = 5, row = 0, sticky = 'nsew')
        # botones de conexion
        frame_izquierda = Frame(self.frame_principal, bg = self.bg_color)
        frame_izquierda.grid(column = 0, row= 1, sticky = 'nsew')

        frame_sliders = Frame(self.frame_principal, bg = self.bg_color)
        frame_sliders.grid(column=1, row=1, sticky = 'nsew')

        self.fig, ax = plt.subplots(facecolor=self.bg_color, dpi = 100, figsize =(4,5))
        plt.title('ELECTROCARDIOGRAMA', color = '#000000', size = 12, family = 'Arial')
        plt.xlabel('Muestras por segundo "Muestras/s"')
        plt.ylabel('Voltaje "V"')
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

        self.frame_principal.columnconfigure(0, weight=1)
        self.frame_principal.columnconfigure(1, weight=1)
        self.frame_principal.rowconfigure(0, weight=5)
        self.frame_principal.rowconfigure(1, weight=1) 

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
        line = str()
        with open('data/conexiones.txt', 'r') as file:
            for line in file.readlines():
                if '192.168.0.25' in line:
                    hostip = line
                    break
            file.close()

        if self.conectado:
            messagebox.showerror('Error de conexion', 'Usted ya tiene una conexión con un dispositivo analizador.')
        else:
            try:
                self.client = socket(AF_INET, SOCK_STREAM)
                host = (hostip, 9999)
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

    def guardar(self):
        filepath = asksaveasfile(
            filetypes=(
                ("Text files", "*.txt"),
                ('CSV (Delimitado por comas)', '*.csv')
            ),
            defaultextension='.txt',
        )
        
        periodo = 60/2000
        tiempo = 0
        with open(filepath.name, 'a') as file:
            for data in self.datos_señal_uno:
                file.write(f'{round(tiempo, 3)},{data}\n')
                tiempo  += periodo
            file.close()
        messagebox.showinfo("Listo", f"El registro se ha guardado con éxito\nGuardado en {filepath.name}")
    
    def abrir_archivo(self):
        filepath = askopenfile(
            filetypes=(
                ("Text files", "*.txt"),
                ('CSV (Delimitado por comas)', '*.csv')
            ),
            defaultextension='.csv',
        )
        
        dataset = pd.read_csv(filepath)

        self.frame_scanner = False
        self.widgetsedicion(str(filepath.name), dataset)

    def widgetsedicion(self, filepath, dataset):
        filepath = filepath.split('/')
        filepath = filepath[len(filepath)-1]

        self.frame_principal.forget()
        self.frame_analisis = Frame(self.master, background=self.bg_color)
        self.frame_analisis.pack(fill='both', expand=5)

        self.frame_analisis.columnconfigure(0, weight=1)
        self.frame_analisis.rowconfigure(0, weight=5)

        graphic_frame = Frame(self.frame_analisis, bd=2)
        graphic_frame.grid(column=0, row=0, columnspan=5, sticky='nsew')

        fig, ax = plt.subplots(facecolor=self.bg_color, dpi = 100, figsize =(0,5))
        plt.title(filepath, color = '#000000', size = 12, family = 'Arial')
        
        ecg = ecg_analyzer(dataset=dataset)
        peaklist = ecg['x']
        ybeat = ecg['y']
        bpm = ecg['bpm']
        x = [t for t in range(0, 2000)]
        y = dataset['hart']

        ax.plot(x, y)
        ax.scatter(peaklist, ybeat, color='red', label=f"BPM: {bpm}")
        ax.legend(loc=4, framealpha=0.8)

        ax.set_facecolor('#ffffff')
        ax.spines['bottom'].set_color('blue')
        ax.spines['left'].set_color('blue')
        ax.spines['top'].set_color('blue')
        ax.spines['right'].set_color('blue')

        canvas = FigureCanvasTkAgg(fig, master = graphic_frame)
        NavigationToolbar2Tk(canvas, graphic_frame)
        canvas.get_tk_widget().pack(padx=0, pady=0, expand=True, fill='both')
        
    def analizarRed(self):
        ip_local = gethostbyname(gethostname())
        ip_local = ip_local.split('.')
        ip_modified = str()
        host_list = list()
        
        for host in range(1, 5):
            for i in range(0, 3):
                ip_modified += str(ip_local[i]) + '.'
            
            ip_modified += str(host)
            self.porcentaje.set(str(round(host/4*100))+' %')
            self.progreso.update()
            host_list.append(getfqdn(ip_modified))
            self.progressbar['value'] += host/4*100
            ip_modified = ''
        
        return host_list

    def establecerConexion(self):
        self.porcentaje = StringVar()
        self.porcentaje.set('0 %')

        newWindow = Toplevel(self.master)
        newWindow.title('Analizando Red')
        
        Label(newWindow, text='Buscando dispositivos', font=('Arial', 30)).pack(fill='both', padx=20, pady=30)
        
        self.progreso = Label(newWindow, textvariable=self.porcentaje, font=('Arial', 15))
        self.progreso.pack(fill='both')
        
        self.progressbar = Progressbar(newWindow, orient=HORIZONTAL, length=100, mode='determinate')
        self.progressbar.pack(fill='both', pady=30, padx=20)
        host_list = self.analizarRed()
        newWindow.destroy()

        with open('data/conexiones.txt', 'a') as file:
            for host in host_list:
                if 'micro' == host: #! CAMBIAR STR DE BUSQUEDA AL NOMBRE DEL MICRO
                    file.write(str(host)+'\n')
                    break
            file.close()

        self.conectar_serial()

    def DiseñarFiltro(self):
        pass

    def AplicarFiltros(self):
        pass

class MenuDemo(Tk):
    def __init__(self):
        Tk.__init__(self)
        menubar = MenuBar(self)
        self.config(menu=menubar)

if __name__ == "__main__":
    ws=MenuDemo()
    width = ws.winfo_screenwidth()
    height = ws.winfo_screenheight()
    ws.geometry("%dx%d" % (width, height))
    ws.title('Electrocardiografo perronsote')
    ws.mainloop()