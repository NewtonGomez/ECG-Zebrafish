from socket import gethostbyname, gethostname, getfqdn
from tqdm import tqdm
from time import time

def AnalizarRed(ip_local: str):
    ip_local = ip_local.split('.')
    ip_modified = str()
    host_list = list()
    
    for host in tqdm(range(1, 20)):
        for i in range(0, 3):
            ip_modified += str(ip_local[i]) + '.'
        
        ip_modified += str(host)
        host_list.append(getfqdn(ip_modified))
        ip_modified = ''
    return host_list

inicio = time()

ip_local = gethostbyname(gethostname())
print(AnalizarRed(ip_local))

final = time()
print(f'tiempo estimado de analisis: {(final-inicio)/60} s')