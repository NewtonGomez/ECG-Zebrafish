from numpy import arange

n = 33.5
muestra = 1250

step = 0.88889/((muestra)*n/muestra)
print(f'pasos: {step}')

x = [i for i in arange(0, n, step)]
print(len(x), len(x)==1250)