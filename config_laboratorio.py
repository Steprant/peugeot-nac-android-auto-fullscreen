#!/usr/bin/env python3
"""Controlla o genera testo per il lettore cfg del laboratorio. Non accede a /home/root/cfg."""
import argparse
import json
import re
from pathlib import Path

KEYS=('readFromFile','screenWidth','screenHeight','widthMargin','heigthMargin','videoDPI','videoResolution')

def validate_cfg(text):
    if not text.isascii() or len(text)>4096:
        raise ValueError('Sono ammessi soltanto ASCII e al massimo 4096 caratteri.')
    result={}
    for line in text.splitlines():
        if line.count('=')!=1:
            raise ValueError('Ogni riga deve avere esattamente un uguale; niente commenti o righe vuote.')
        key,value=line.split('=')
        if key not in KEYS or key in result:
            raise ValueError('Chiave sconosciuta o ripetuta: '+key)
        if key=='readFromFile':
            if value!='true':raise ValueError('readFromFile deve essere esattamente true.')
        elif key=='videoResolution':
            if value not in ('480p','720p','1080p'):raise ValueError('Risoluzione testuale sconosciuta.')
        else:
            if not re.fullmatch(r'0|[1-9][0-9]*',value):raise ValueError('Intero decimale canonico richiesto: '+key)
            number=int(value)
            if number>2147483647 or (key in ('screenWidth','screenHeight','videoDPI') and number==0):
                raise ValueError('Intero non rappresentabile o nullo: '+key)
        result[key]=value
    if set(result)!=set(KEYS):raise ValueError('Sono obbligatorie tutte le sette chiavi, incluso heigthMargin con questa grafia.')
    return result

def render_cfg(mapping):
    if set(mapping)!=set(KEYS):raise ValueError('Chiavi JSON diverse dalle sette chiavi previste.')
    text=''.join(k+'='+str(mapping[k])+'\n' for k in KEYS)
    validate_cfg(text)
    return text

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('azione',choices=('check','render'))
    p.add_argument('file',type=Path)
    a=p.parse_args()
    try:
        if a.azione=='render':print(render_cfg(json.loads(a.file.read_text())),end='')
        else:
            result=validate_cfg(a.file.read_text())
            print(json.dumps({'sintassi_coerente':True,'parametri':result,
                              'compatibilita_decoder_o_hardware_verificata':False},indent=2))
    except (ValueError,OSError) as exc:p.exit(2,str(exc)+'\n')

if __name__=='__main__':main()
