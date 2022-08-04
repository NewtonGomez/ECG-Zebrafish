import matplotlib.pyplot as plt
from scipy import signal
import numpy as np

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

y = np.fromfile("C://Users/n3wto/Documents/Señales/ECG signals/1 NSR/100m (2).mat", dtype=np.float32)
isimplecount = y.shape[0]
iSampleRate = 2500
yfft = np.abs(np.fft.rfft(y)/isimplecount)
xfreqs = np.linspace(0, iSampleRate/2, int(isimplecount/2)+1)
t = [i for i in np.arange(0, 18.06, 0.01)]

plt.Figure(figsize=(200,200))

ax2 = plt.subplot(3,3,1)
ax2.set_title('Original')
ax2.set_xlabel('Tiempo "s"')
ax2.set_ylabel("Voltaje 'v'")
ax2.plot(t, y)

ax3 = plt.subplot(3,3,7)
ax3.set_title('Frecuencia')
ax3.set_xlabel('Frequencia "Hz"')
ax3.set_ylabel('Power')
ax3.plot(xfreqs, yfft)

ax0 = plt.subplot(3, 3, 2)
for k in [2, 3, 4]:
    b, a = butterBandPassFilter(3,70,samplerate=iSampleRate,order=k)
    w, h = signal.freqz(b, a, worN=2000)
    ax0.set_title('Filtro Pasa Bandas')
    ax0.set_xlabel('Frecuencia')
    ax0.plot((iSampleRate*0.5/np.pi)*w,np.abs(h),label="order = %d" % k)

ax1 = plt.subplot(3, 3, 8)
for k in [2, 3, 4]:
    b, a = butterBandStopFilter(48, 52, samplerate=iSampleRate, order=k)
    w, h = signal.freqz(b, a, worN=2000)
    ax1.set_title('Filtro Rechaza Bandas')
    ax1.set_xlabel('Frecuencia')
    ax1.plot((iSampleRate*0.5/np.pi)*w,np.abs(h),label="order = %d" % k)
# aplicamos los filtros

b, a = butterBandPassFilter(3,70,samplerate=iSampleRate,order=k)
x = signal.lfilter(b, a, y)

b, a = butterBandStopFilter(48, 52, samplerate=iSampleRate, order=4)
y2 = signal.lfilter(b, a, x)

ax4 = plt.subplot(3,3,3)
ax4.set_title('Señal Filtrada')
ax4.set_xlabel('Tiempo "s"')
ax4.set_ylabel("Voltaje 'v'")
ax4.plot(t, y2)

yfft2 = np.abs(np.fft.rfft(y2)/isimplecount)

ax5 = plt.subplot(3,3,9)
ax5.set_title('Frecuencia Filtrada')
ax5.set_xlabel('Frequencia "Hz"')
ax5.set_ylabel('Power')
ax5.plot(xfreqs, yfft2)

plt.show()