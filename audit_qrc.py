#!/usr/bin/env python3
"""Audit in sola lettura di due risorse Qt compresse del firmware esatto."""
import argparse
import hashlib
import io
import json
import struct
import zlib
from pathlib import Path, PurePosixPath
from elftools.elf.elffile import ELFFile

SPECS=[
    {'file':'usr/lib/qt5/qml/UiKit/libdeclarative_uikitplugin.so.1.0.0',
     'sha256':'28379dd9e5c5b9590dbeb41e39090ba53c76ab3c58ee791832a682b03874694d',
     'tree':0x59a08,'names':0x59ac0,'data':0x59c98,
     'resource':'UiKit/Screen.qml','resource_sha256':'bf341482ec0c220eaf2710b0f902dd3d3e17748bd664f4209be83fde4ee57b29'},
    {'file':'usr/lib/libuikit_universe_Pixel.so.1.0.0',
     'sha256':'639b22db69713d7a8e21fa82e74d25089766e3d530584797941821f6ef6ef2a2',
     'tree':0xb00,'names':0xfc4,'data':0x1d88,
     'resource':'UiKit/FullscreenContentScreen.qml','resource_sha256':'49d5ea1292292378f7e3745f6d9f1ba65b3e130cea3bbd12a9d3ba4ee3e84199'},
]

def resource(data,spec):
    if hashlib.sha256(data).hexdigest()!=spec['sha256']:raise ValueError('SHA256 plugin inatteso.')
    elf=ELFFile(io.BytesIO(data));segments=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    def read(a,n):
        if n<0 or n>8*1024*1024:raise ValueError('Lunghezza risorsa non ammessa.')
        for s in segments:
            if s['p_vaddr']<=a and a+n<=s['p_vaddr']+s['p_filesz']:
                off=s['p_offset']+a-s['p_vaddr'];return data[off:off+n]
        raise ValueError('Intervallo fuori ELF.')
    def u32(a):return int.from_bytes(read(a,4),'big')
    visited=set();found=[]
    def visit(index,path,depth):
        if depth>20 or index in visited or len(visited)>10000:raise ValueError('Albero QRC inatteso.')
        visited.add(index);a=spec['tree']+14*index
        nameoff,flags=struct.unpack('>IH',read(a,6));n=spec['names']+nameoff
        size=int.from_bytes(read(n,2),'big')
        name=read(n+6,2*size).decode('utf-16-be') if index else ''
        if name in ('.','..') or '/' in name:raise ValueError('Nome QRC inatteso.')
        path=path/name
        if flags&2:
            count,child=struct.unpack('>II',read(a+6,8))
            if count>10000:raise ValueError('Troppi figli QRC.')
            for i in range(child,child+count):visit(i,path,depth+1)
        elif str(path)==spec['resource']:
            at=spec['data']+u32(a+10);payload=read(at+4,u32(at))
            if flags&1:
                expected=int.from_bytes(payload[:4],'big')
                if expected>8*1024*1024:raise ValueError('Risorsa troppo grande.')
                decoder=zlib.decompressobj();plain=decoder.decompress(payload[4:],expected+1)
                if len(plain)!=expected or not decoder.eof or decoder.unused_data:
                    raise ValueError('Risorsa compressa non valida.')
                payload=plain
            if hashlib.sha256(payload).hexdigest()!=spec['resource_sha256']:raise ValueError('SHA256 risorsa inatteso.')
            found.append((payload,bool(flags&1)))
    visit(0,PurePosixPath(),0)
    if len(found)!=1:raise ValueError('Risorsa mancante o duplicata.')
    return found[0]

def audit(root):
    rows=[]
    for spec in SPECS:
        data=(root/spec['file']).read_bytes();payload,compressed=resource(data,spec)
        text=payload.decode('utf-8');row={
            'plugin':spec['file'],'sha256_plugin':spec['sha256'],
            'risorsa':spec['resource'],'sha256_risorsa':spec['resource_sha256'],
            'byte_risorsa':len(payload),'compressione_zlib':compressed,
        }
        if spec['resource'].endswith('/Screen.qml'):
            row['binding_WHD_x_320']='x: ScreenInfo.displayCategory === ScreenInfo.WHD ? 320 : 0' in text
            row['binding_WHD_larghezza_meno_640']='width: ScreenInfo.displayCategory === ScreenInfo.WHD ? ScreenInfo.width - 640 : ScreenInfo.width' in text
        else:
            row['contenuto_ancorato_al_padre']='anchors.fill: parent' in text
            row['clip_condizionale_WHD']='clip: ScreenInfo.displayCategory === ScreenInfo.WHD' in text
        rows.append(row)
    return {'firmware':'44.07.33.32_NAC-r0','tipo_analisi':'QRC statico in sola lettura',
            'patch_applicata':False,'componenti':rows}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rootfs',type=Path);a=p.parse_args()
    try:print(json.dumps(audit(a.rootfs),indent=2))
    except (OSError,ValueError) as exc:p.exit(2,str(exc)+'\n')

if __name__=='__main__':main()
