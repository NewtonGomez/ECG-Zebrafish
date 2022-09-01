from collections import deque
from tkinter import *
from tkinter import Tk
from tkinter.font import BOLD
from tkinter.ttk import Progressbar, Style, Scale, Treeview
from tkinter.filedialog import askopenfile, asksaveasfile
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import webbrowser
import json
import matplotlib.animation as animation
from struct import unpack, calcsize, pack
from socket import gethostbyname, gethostname, socket, AF_INET, SOCK_STREAM, getfqdn
import math
import numpy as np
import os
from scipy import signal

class Toolbar(NavigationToolbar2Tk):

    def set_message(self, s):
        pass

def butterBandPassFilter(lowcut, hihgcut, samplerate, order):
    semiSamplerate = samplerate*0.5
    low = lowcut / semiSamplerate
    high = hihgcut / semiSamplerate
    b, a = signal.butter(order, [low, high], btype='bandpass')
    return b, a

def butterBandStopFilter(lowcut, highcut, samplerate, order):
    "Generar filtro de parada de banda de Butterworth"
    semiSampleRate = samplerate*0.5
    low = lowcut / semiSampleRate
    high = highcut / semiSampleRate
    b,a = signal.butter(order,[low,high],btype='bandstop')
    return b,a

def ecg_analyzer(dataset) -> dict:
    sampleRate = 1000
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
        elif (datapoint > rollingmean):
            print(datapoint) #If signal comes above local mean, mark ROI
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

def getbpm(dataset) -> list:
    dataset = pd.DataFrame([i for i in dataset if i != 9.5])
    dataset.columns = ['hart']
    sampleRate = 1000
    hrw = 0.25 
    fs = sampleRate

    mov_avg = dataset['hart'].rolling(int(hrw*fs)).mean() 
   
    avg_hr = (np.mean(dataset.hart[:sampleRate]))
    mov_avg = [avg_hr if math.isnan(x) else x for x in mov_avg]
    mov_avg = [x*1.2 for x in mov_avg] 
    dataset['hart_rollingmean'] = mov_avg 
    
    window = []
    peaklist = []
    listpos = 0 

    for datapoint in dataset.hart:
        rollingmean = dataset.hart_rollingmean[listpos] 
        if (datapoint < rollingmean) and (len(window) < 1):
            listpos += 1
        elif (datapoint > rollingmean): 
            window.append(datapoint)
            listpos += 1
        else: 
            beatposition = listpos - len(window) + (window.index(max(window))) 
            peaklist.append(beatposition) 
            window = [] 
            listpos += 1

    RR_list = []
    cnt = 0

    while (cnt < (len(peaklist)-1)):
        RR_interval = (peaklist[cnt+1] - peaklist[cnt]) 
        ms_dist = ((RR_interval / fs) * float(sampleRate)) 
        RR_list.append(ms_dist)
        cnt += 1
    
    bpm = round(30000 / np.mean(RR_list))
    return int(bpm), list(dataset.hart_rollingmean)

class FilterDesign(Menu):
    def __init__(self, ws) -> None:
        self.ws= ws
        self.ws.protocol('WM_DELETE_WINDOW',self.AskQuit)
        Menu.__init__(self, ws)
        self.bg_color = '#D3D3D3'

        file = Menu(self, tearoff=False)
        file.add_command(label="Nuevo", command=self.newFilter)  
        file.add_command(label="Abrir", command=self.openFilter)  
        file.add_command(label="Guardar", command=self.saveFilter)  
        file.add_separator()
        file.add_command(label="Salir", underline=1, command=self.AskQuit)
        self.add_cascade(label="Archivo",underline=0, menu=file)
        
        self.edit = Menu(self, tearoff=0)  
        self.edit.add_command(label="Deshacer")  
        self.edit.add_command(label="Rehacer")  
        self.edit.add_separator()
        self.add_cascade(label="Editar", menu=self.edit) 

        self.framePrincipal = Frame(self.master, bg=self.bg_color)
        self.framePrincipal.pack(fill='both', expand=5)

        self.widgets()
    
    def widgets(self):
        def graphWdiget(title):
            fig, self.ax = plt.subplots(facecolor=self.bg_color, dpi = 100, figsize =(4,3))
            plt.title(title, color = '#000000', size = 12, family = 'Arial')
            plt.xlabel('Frecuencia (Hz)')
            plt.ylabel('Power')
            self.ax.tick_params(direction='out', length=5, width = 2, colors='#000000', grid_color='r', grid_alpha=0.5)
            
            self.ax.set_facecolor('#ffffff')
            self.ax.spines['bottom'].set_color('blue')
            self.ax.spines['left'].set_color('blue')
            self.ax.spines['top'].set_color('blue')
            self.ax.spines['right'].set_color('blue')

            self.canvas = FigureCanvasTkAgg(fig, master = self.frame_derecho_superior)
            toolbar = Toolbar(self.canvas, self.frame_derecho_inferior)
            toolbar.config(background = self.bg_color)
            self.canvas.get_tk_widget().pack(padx=10, pady=5, expand=True, fill='both')


        self.frame_izquierdo = Frame(self.framePrincipal, bg=self.bg_color, bd=2)
        self.frame_izquierdo.grid(row=1, column=1)
        
        self.frame_izquierdo_inferior = Frame(self.framePrincipal, bg=self.bg_color)
        self.frame_izquierdo_inferior.grid(row=2, column=1)

        self.generateFrames()

        Label(self.frame_izquierdo, text='Parametros del Filtro:', bg=self.bg_color, font=('Arial', 15, BOLD)).grid(row=1, column=1)
        Label(self.frame_izquierdo, text='   ', bg=self.bg_color, font=('Arial', 12, BOLD)).grid(row=2, column=1)
        Label(self.frame_izquierdo, text='Tipo de filtro:', bg=self.bg_color, font=('Arial', 12)).grid(row=3, column=1)
        
        Label(self.frame_izquierdo, text='   ', bg=self.bg_color, font=('Arial', 12, BOLD)).grid(row=5, column=1)

        self.kindFilter= IntVar()
        Checkbutton(self.frame_izquierdo, text='PasaBandas', variable=self.kindFilter, onvalue=1, offvalue=0, bg=self.bg_color, font=('Arial', 12)).grid(row=5, column=1)
        Checkbutton(self.frame_izquierdo, text='RechazaBandas', variable=self.kindFilter, onvalue=2, offvalue=0, bg=self.bg_color, font=('Arial', 12)).grid(row=5, column=2)

        Label(self.frame_izquierdo, text='   ', bg=self.bg_color, font=('Arial', 12, BOLD)).grid(row=6, column=1)
        
        Label(self.frame_izquierdo, text='Nombre:', bg=self.bg_color, font=('Arial', 12)).grid(row=7, column=1)
        self.nombre = Entry(self.frame_izquierdo, font=('Arial', 12))
        self.nombre.grid(row=7, column=2)
        
        Label(self.frame_izquierdo, text='   ', bg=self.bg_color, font=('Arial', 12, BOLD)).grid(row=8, column=1)

        Label(self.frame_izquierdo, text='Frecuencia Corte Bajo:', bg=self.bg_color, font=('Arial', 12)).grid(row=9, column=1)
        self.lowcut = Entry(self.frame_izquierdo, font=('Arial', 12))
        self.lowcut.grid(row=9, column=2)

        Label(self.frame_izquierdo, text='   ', bg=self.bg_color, font=('Arial', 12, BOLD)).grid(row=10, column=1)
        
        Label(self.frame_izquierdo, text='Frecuencia Corte Alto:', bg=self.bg_color, font=('Arial', 12)).grid(row=11, column=1)
        self.highcut= Entry(self.frame_izquierdo, font=('Arial', 12))
        self.highcut.grid(row=11, column=2)
        
        Label(self.frame_izquierdo, text='   ', bg=self.bg_color, font=('Arial', 12, BOLD)).grid(row=12, column=1)
        
        Label(self.frame_izquierdo, text='Orden del Filtro:', bg=self.bg_color, font=('Arial', 12)).grid(row=13, column=1)
        self.order= Entry(self.frame_izquierdo, font=('Arial', 12))
        self.order.grid(row=13, column=2)
        
        generar = Button(self.frame_izquierdo_inferior, text='Generar Filtro', bd=1, font=('Arial', 12), command=self.generateFilter)
        generar.pack(expand=True)

        graphWdiget('Frecuencia de corte')
    
    def graphWdiget(self, title):
            fig, self.ax = plt.subplots(facecolor=self.bg_color, dpi = 100, figsize =(4,3))
            plt.title(title, color = '#000000', size = 12, family = 'Arial')
            plt.xlabel('Frecuencia (Hz)')
            plt.ylabel('Power')
            self.ax.tick_params(direction='out', length=5, width = 2, colors='#000000', grid_color='r', grid_alpha=0.5)
            
            self.ax.set_facecolor('#ffffff')
            self.ax.spines['bottom'].set_color('blue')
            self.ax.spines['left'].set_color('blue')
            self.ax.spines['top'].set_color('blue')
            self.ax.spines['right'].set_color('blue')

            self.canvas = FigureCanvasTkAgg(fig, master = self.frame_derecho_superior)
            toolbar = Toolbar(self.canvas, self.frame_derecho_inferior)
            toolbar.config(background = self.bg_color)
            self.canvas.get_tk_widget().pack(padx=10, pady=5, expand=True, fill='both')

    def widgetsOpen(self):        
        filepath = 'config/filtros.json'
        with open(filepath) as feedsjson:
            feeds = json.load(feedsjson)
            feedsjson.close()

        data = list()
        for key, value in feeds.items():
            if key == self.openData[0]:
                data.append(key)
                for kew, dat in value.items():
                    data.append([kew, dat])
                break

        self.frame_izquierdo = Frame(self.framePrincipal, bg=self.bg_color, bd=2)
        self.frame_izquierdo.grid(row=1, column=1)
        
        self.frame_izquierdo_inferior = Frame(self.framePrincipal, bg=self.bg_color)
        self.frame_izquierdo_inferior.grid(row=2, column=1)

        self.generateFrames()
            

        Label(self.frame_izquierdo, text=f'Parametros del Filtro: {data[0]}', bg=self.bg_color, font=('Arial', 13, BOLD)).grid(row=1, column=1)
        Label(self.frame_izquierdo, text='   ', bg=self.bg_color, font=('Arial', 12, BOLD)).grid(row=2, column=1)
        Label(self.frame_izquierdo, text='Tipo de filtro:', bg=self.bg_color, font=('Arial', 12)).grid(row=3, column=1)
        
        Label(self.frame_izquierdo, text='   ', bg=self.bg_color, font=('Arial', 12, BOLD)).grid(row=5, column=1)

        self.kindFilter= IntVar()
        if data[1][1] == 'pasabandas':
            self.kindFilter.set(1)
        elif data[1][1] == 'rechazabandas':
            self.kindFilter.set(2)

        Checkbutton(self.frame_izquierdo, text='PasaBandas', variable=self.kindFilter, onvalue=1, offvalue=0, bg=self.bg_color, font=('Arial', 12)).grid(row=5, column=1)
        Checkbutton(self.frame_izquierdo, text='RechazaBandas', variable=self.kindFilter, onvalue=2, offvalue=0, bg=self.bg_color, font=('Arial', 12)).grid(row=5, column=2)

        Label(self.frame_izquierdo, text='   ', bg=self.bg_color, font=('Arial', 12, BOLD)).grid(row=6, column=1)
        
        Label(self.frame_izquierdo, text='Nombre:', bg=self.bg_color, font=('Arial', 12)).grid(row=7, column=1)
        self.nombre = Entry(self.frame_izquierdo, font=('Arial', 12))
        self.nombre.insert(END, data[0])
        self.nombre.grid(row=7, column=2)
        
        Label(self.frame_izquierdo, text='   ', bg=self.bg_color, font=('Arial', 12, BOLD)).grid(row=8, column=1)

        Label(self.frame_izquierdo, text='Frecuencia Corte Bajo:', bg=self.bg_color, font=('Arial', 12)).grid(row=9, column=1)
        self.lowcut = Entry(self.frame_izquierdo, font=('Arial', 12))
        self.lowcut.insert(END, data[2][1])
        self.lowcut.grid(row=9, column=2)

        Label(self.frame_izquierdo, text='   ', bg=self.bg_color, font=('Arial', 12, BOLD)).grid(row=10, column=1)
        
        Label(self.frame_izquierdo, text='Frecuencia Corte Alto:', bg=self.bg_color, font=('Arial', 12)).grid(row=11, column=1)
        self.highcut= Entry(self.frame_izquierdo, font=('Arial', 12))
        self.highcut.insert(END, data[3][1])
        self.highcut.grid(row=11, column=2)
        
        Label(self.frame_izquierdo, text='   ', bg=self.bg_color, font=('Arial', 12, BOLD)).grid(row=12, column=1)
        
        Label(self.frame_izquierdo, text='Orden del Filtro:', bg=self.bg_color, font=('Arial', 12)).grid(row=13, column=1)
        self.order= Entry(self.frame_izquierdo, font=('Arial', 12))
        self.order.insert(END, data[4][1])
        self.order.grid(row=13, column=2)
        
        generar = Button(self.frame_izquierdo_inferior, text='Generar Filtro', bd=1, font=('Arial', 12), command=self.generateFilter)
        generar.pack(expand=True)


        self.graphWdiget('Frecuencia de corte')
        self.generateFilter()
    
    def generateFrames(self):
        self.frame_derecho_superior = Frame(self.framePrincipal, bg=self.bg_color)
        self.frame_derecho_superior.grid(row=1, column=2, columnspan=5, pady=10)
        
        self.frame_derecho_inferior = Frame(self.framePrincipal, bg=self.bg_color)
        self.frame_derecho_inferior.grid(row=2, column=2, columnspan=5, pady=5)

    def generateFilter(self):
        if self.kindFilter.get() == 0:
            messagebox.showerror('Error', 'Por favor selecciona el tipo de filtro')

        self.frame_derecho_superior.forget()
        self.frame_derecho_inferior.forget()

        self.generateFrames()
        self.graphWdiget('Frecuencia de corte')
        
        if self.nombre.get() == '' or self.lowcut.get() == None or self.highcut.get() == '' or self.order.get() == '':
                messagebox.showerror('Entrada Vacia', 'Una de tus entradas esta vacia')
        else:
            lowcut = int(self.lowcut.get())
            highcut = int(self.highcut.get())
            k = int(self.order.get())
        
            if self.kindFilter.get() == 1:
                # filtro pasabandas        
                b, a = butterBandPassFilter(lowcut, highcut, samplerate=2000, order=k)
                w, h = signal.freqz(b, a, worN=2000)

                self.ax.plot((2000*0.5/np.pi)*w,np.abs(h),label="order = %d" % k)
                self.canvas.draw()

            elif self.kindFilter.get() == 2:
                # filtro rechazabandas
                b, a = butterBandStopFilter(lowcut, highcut, samplerate=2000, order=k)
                w, h = signal.freqz(b, a, worN=2000)

                self.ax.plot((2000*0.5/np.pi)*w,np.abs(h),label="order = %d" % k)
                self.canvas.draw()

    def saveFilter(self):
        if self.nombre.get() == '' or self.lowcut.get() == None or self.highcut.get() == '' or self.order.get() == '':
                messagebox.showerror('Entrada Vacia', 'Una de tus entradas esta vacia')
        else:
            kindFilter = str()
            if self.kindFilter.get() == 1:
                kindFilter = 'pasabandas'
            if self.kindFilter.get() == 2:
                kindFilter = 'rechazabandas'

            filterData = {
                self.nombre.get(): {
                    'type': kindFilter,
                    'lowcut': int(self.lowcut.get()),
                    'highcut': int(self.highcut.get()),
                    'order': int(self.order.get())
                }
            }

            filepath = 'config/filtros.json'
            json_object = json.dumps(filterData, indent=4)
            
            if not os.path.isfile(filepath):
                with open(filepath, "w") as outfile:
                    outfile.write(json_object)
                    outfile.close()
                    messagebox.showinfo('Listo', 'Filtro agregado con éxito')
            else:
                with open(filepath) as feedsjson:
                    feeds = json.load(feedsjson)
                    feedsjson.close()
                if self.nombre.get() in feeds:
                    messagebox.showerror('Repetido', 'este nombre ya se usado con aterioridad')
                else:
                    feeds.update(filterData)
                    with open(filepath, mode='w') as file:
                        file.write(json.dumps(feeds, indent=2))
                        file.close()

                    messagebox.showinfo('Listo', 'Filtro agregado con éxito')

    def openFilter(self):

        def item_selected(event):
            for selected_item in tree.selection():
                item = tree.item(selected_item)
                self.openData = item['values']
                self.framePrincipal.forget()
                
                self.framePrincipal = Frame(self.master, bg=self.bg_color)
                self.framePrincipal.pack(fill='both', expand=5)

                self.widgetsOpen()

        newwindow = Toplevel(self.ws)
        width = self.ws.winfo_screenwidth()
        height = self.ws.winfo_screenheight()
        newwindow.geometry("%dx%d" % (width/3, height/3))

        frame = Frame(newwindow, bg=self.bg_color)
        frame.pack(fill='both', expand=True)

        columnas = ('Nombre', 'Tipo')
        tree = Treeview(frame, columns=columnas, show='headings')
        tree.pack(fill='both', expand=True)
        tree.heading('Nombre', text='Nombre', anchor=CENTER)
        tree.heading('Tipo', text='Tipo', anchor=CENTER)
        tree.bind('<<TreeviewSelect>>', item_selected)

        filepath = 'config/filtros.json'

        if not os.path.isfile(filepath):
            with open(filepath, "w") as outfile:
                messagebox.showerror('Sin filtros', 'Vaya esto parece estar un poco vacio')
                outfile.close()
                newwindow.quit()
                newwindow.destroy()
        else:
            with open(filepath) as feedsjson:
                feeds = json.load(feedsjson)
                feedsjson.close()
                
                filters = list()
                for key, values in feeds.items():
                    for kind, value in values.items():
                        if kind == 'type':
                            filters.append((key, value))

                for datafilter in filters:
                    tree.insert('', END, values=datafilter)
    
    def newFilter(self):
        self.framePrincipal.forget()
        
        self.framePrincipal = Frame(self.master, bg=self.bg_color)
        self.framePrincipal.pack(fill='both', expand=5)

        self.widgets()

    def AskQuit(self):
        self.ws.quit()
        self.ws.destroy()

class MenuBar(Menu):
    def __init__(self, ws):
        self.ws = ws
        self.temporizador = 0
        self.tiempo = 0
        self.ws.protocol('WM_DELETE_WINDOW',self.AskQuit)
        Menu.__init__(self, ws)
        self.muestra = 1000
        self.offset = StringVar()
        self.bg_color = '#D3D3D3'
        self.conectado = False
        self.frame_scanner = True
        
        filepath = 'config/filtros.json'
        if not os.path.isfile(filepath):
            os.mkdir('config')
            open(filepath, 'w').close()
        else:    
            with open(filepath) as feedsjson:
                    feeds = json.load(feedsjson)
                    feedsjson.close()
        
        file = Menu(self, tearoff=False)
        file.add_command(label="Abrir", command=self.abrir_archivo)  
        file.add_command(label="Nuevo", command=self.nuevo_escaner)  
        file.add_command(label="Guardar")  
        file.add_command(label="Guardar como", command=self.guardar)    
        file.add_separator()
        file.add_command(label="Salir", underline=1, command=self.AskQuit)
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

        chec = StringVar()
        self.filtros = Menu(self.edit, tearoff=0)

        for feed in feeds:
            self.filtros.add_checkbutton(label=feed.upper(), variable=chec, onvalue=feed, offvalue='0', command=lambda: self.AplicarFiltros(chec))

        self.filtros.add_separator()
        self.filtros.add_command(label="Crear Filtro", command= self.DiseñarFiltro)
        self.edit.add_cascade(label='Filtros', menu=self.filtros)
    
        if self.frame_scanner:
            self.edit.entryconfig('Filtros', state='disabled')

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

        self.bpm = StringVar()
        self.bpm.set('BPM: 0')
        self.label_bpm = Label(frame_izquierda, textvariable=self.bpm, font=('Arial', 40), bg=self.bg_color)
        self.label_bpm.pack(fill='both')

        self.fig, ax = plt.subplots(facecolor=self.bg_color, dpi = 100, figsize =(4,5))
        plt.title('ELECTROCARDIOGRAMA', color = '#000000', size = 12, family = 'Arial')
        plt.xlabel('Muestras por segundo "Muestras/s"')
        plt.ylabel('Voltaje "V"')
        ax.tick_params(direction='out', length=5, width = 2, colors='#000000', grid_color='r', grid_alpha=0.5)

        self.line, = ax.plot([],[],color='g', marker='o', linewidth=2, markersize=0, markeredgecolor='g')
        self.line2, = ax.plot([],[],color='y', marker='o', linewidth=2, markersize=0, markeredgecolor='g')
        
        plt.xlim([0, self.muestra])
        plt.ylim([8.5,13])
        
        ax.set_facecolor('#ffffff')
        ax.spines['bottom'].set_color('blue')
        ax.spines['left'].set_color('blue')
        ax.spines['top'].set_color('blue')
        ax.spines['right'].set_color('blue')

        self.datos_señal_uno = deque([9.5]*self.muestra, maxlen = self.muestra)
        self.datos_rolling_mean = deque([11.2]*self.muestra, maxlen = self.muestra)
        
        self.line.set_data(range(self.muestra), self.datos_señal_uno)
        self.line2.set_data(range(self.muestra), self.datos_rolling_mean)

        self.frame_principal.columnconfigure(0, weight=1)
        self.frame_principal.columnconfigure(0, weight=1)
        self.frame_principal.columnconfigure(1, weight=1)
        self.frame_principal.rowconfigure(0, weight=5)
        self.frame_principal.rowconfigure(1, weight=1) 
        
        self.variable_estado = StringVar()
        self.variable_estado.set('Desconectado')
        self.estado_conexion = Label(frame, textvariable=self.variable_estado, font=('Arial', 7), bg=self.bg_color, fg='red')
        self.estado_conexion.pack()

        self.canvas = FigureCanvasTkAgg(self.fig, master = frame)
        self.canvas.get_tk_widget().pack(padx=0, pady=0, expand = True, fill='both')

        # botones
        self.bt_graficar = Button(frame_izquierda, text='Graficar', font=('Arial', 12, 'bold'), bg='#29b9bb', fg = '#000000', command = self.iniciar, bd=1, state='disabled')
        self.bt_graficar.pack(fill='both', expand=5)
        self.bt_pausar = Button(frame_izquierda, state='disabled', text = 'Pausar', font=('Arial', 12, 'bold'), bg = '#29b9bb', fg = '#000000', command = self.pausar, bd=1)
        self.bt_pausar.pack(fill='both', expand=5)
        self.bt_reanudar = Button(frame_izquierda, state = 'disabled', text = 'Reanudar', font =('Arial',12, 'bold'), bg = '#29b9bb', fg='#000000', command= self.reanudar, bd=1)
        self.bt_reanudar.pack(fill='both', expand=5)
        
        Label(frame_sliders, text = 'Offset', font =('Arial', 25), bg = self.bg_color, fg = '#000000').pack(expand=1)
        style = Style()
        style.configure("Horizontal.TScale", background =self.bg_color)
        self.slider_uno = Scale(frame_sliders, command=self.dato_slider_uno, to=4, from_=-4, orient='horizontal', length=280, style='TScale', value=0)
        self.slider_uno.pack(fill='both',expand = 5, padx=15)

        self.offset_number = StringVar()
        self.offset_number.set('0.000 v')
        self.label_offset = Label(frame_sliders, textvariable=self.offset_number, font=('Arial', 25), bg=self.bg_color, fg='#000000')
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
        bpm = 0
        self.datos = self.getData()
        if self.offset.get() == "":
            self.datos_señal_uno.append(self.datos)
        else:
            self.datos_señal_uno.append(self.datos + float(self.offset.get()))

        self.temporizador += 0.018
        if self.temporizador < 1.01 and self.temporizador > 0.9 :
            self.tiempo += 1
            self.temporizador = 0
            
        if self.tiempo > 10:
            bpm, rolling_mean = getbpm(list(self.datos_señal_uno))
            self.bpm.set(f'BPM: {bpm}')
            self.datos_rolling_mean.extend(rolling_mean)

        self.line.set_data(range(self.muestra), self.datos_señal_uno)
        self.line2.set_data(range(self.muestra), self.datos_rolling_mean)

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
        with open('config/conexiones.txt', 'r') as file:
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
                host = ('192.168.0.25', 9999)
                self.client.connect(host)
                
                messagebox.showinfo('Conectado', 'Listo para gráficar el electrocardiograma.')
                self.conectado = True
                self.bt_graficar.config(state='normal')
                self.variable_estado.set('Conectado')
                self.estado_conexion.config(fg='green', textvariable=self.variable_estado)
                self.estado_conexion.update()
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

    def AskQuit(self):
        self.ws.quit()
        self.ws.destroy()

    def guardar(self):
        filepath = asksaveasfile(
            filetypes=(
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
        self.filepath = askopenfile(
            filetypes=(
                ('CSV (Delimitado por comas)', '*.csv'), 
                ("Text files", "*.txt"),
            ),
            defaultextension='.csv',
        )
        
        self.dataset = pd.read_csv(self.filepath)

        self.frame_scanner = False
        self.frame_principal.forget()
        
        self.frame_analisis = Frame(self.master, background=self.bg_color)
        self.frame_analisis.pack(fill='both', expand=5)
        
        self.edit.entryconfig('Filtros', state='normal')
       
        self.widgetsedicion(str(self.filepath.name), self.dataset)

    def widgetsedicion(self, filepath, dataset):
        filepath = filepath.split('/')
        filepath = filepath[len(filepath)-1]

        
        self.frame_analisis.columnconfigure(0, weight=1)
        self.frame_analisis.rowconfigure(0, weight=5)

        graphic_frame = Frame(self.frame_analisis, bd=0)
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
        ws=MenuFilters()
        width = ws.winfo_screenwidth()
        height = ws.winfo_screenheight()
        ws.geometry("%dx%d" % (width/2, height/2))
        ws.title('Electrocardiografo perronsote')
        ws.mainloop()

    def AplicarFiltros(self, filtro):
        self.frame_analisis.forget()
        
        self.frame_analisis = Frame(self.master, background=self.bg_color)
        self.frame_analisis.pack(fill='both', expand=5)

        with open('config/filtros.json') as feedsjson:
            feeds = json.load(feedsjson)
            feedsjson.close()

        data = list()
        for key, values in feeds.items():
            if key == filtro.get():
                data.append(key)
                for kew, value in values.items():
                    data.append([kew, value])
        nombre = data[0]
        if data[1][1] == 'pasabandas':
            b, a = butterBandPassFilter(data[2][1], data[3][1], 2000, data[4][1])
        elif data[1][1] == 'rechazabandas':
            b, a = butterBandStopFilter(data[2][1], data[3][1], 2000, data[4][1])
        
        aux = list()
        for x in self.dataset.hart:
            aux.append(x)
        filteredData = signal.lfilter(b, a, aux)
        del aux
        
        filteredData = filteredData.tolist()
        tiempo = 0
        with open('config/aux.csv', 'a') as file:
            file.write('t,hart\n')
            for data in filteredData:
                file.write(f'{round(tiempo, 3)},{round(data, 2)}\n')
                tiempo  += 60/2000
            file.close()
        
        filteredData = pd.read_csv('config/aux.csv')
        self.widgetsedicion(str(self.filepath.name), filteredData)
        messagebox.showinfo('Listo', f'Se ha aplicado el filtro: {nombre}')

class MenuDemo(Tk):
    def __init__(self):
        Tk.__init__(self)
        menubar = MenuBar(self)
        self.config(menu=menubar)

class MenuFilters(Tk):
    def __init__(self):
        Tk.__init__(self)
        menubar = FilterDesign(self)
        self.config(menu=menubar)

if __name__ == "__main__":
    ws=MenuDemo()
    width = ws.winfo_screenwidth()
    height = ws.winfo_screenheight()
    ws.geometry("%dx%d" % (width, height))
    ws.title('Electrocardiografo perronsote')
    ws.mainloop()