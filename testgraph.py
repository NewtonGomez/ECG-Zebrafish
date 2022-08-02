from turtle import color
import matplotlib.pyplot as plt
from tqdm import tqdm

def valores_mas_alto(lista: list):
    posiciones = []
    valor = 12
    for i in range(0, len(lista)):
        if lista[i] > valor:
            posiciones.append(i)
    return posiciones

x = []
y = []
with open("C://Users/n3wto/Documents/Señales/pruebas/test.csv", 'r') as file:
    for line in tqdm(file.readlines()):
        y.append(line.split(',')[1])
        x.append(line.split(',')[0])
    file.close()
for i in range(0, len(x)):
    x[i] = float(x[i])
    y[i] = float(y[i])
posiciones = valores_mas_alto(y)
plt.plot(x, y)
for i in range(0, len(posiciones)):
    plt.axvspan(x[posiciones[i]]-1, x[posiciones[i]]+1, color='red', alpha=0.3)
plt.show()