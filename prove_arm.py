#!/usr/bin/env python3
"""Esegue blocchi ARM del firmware esatto in Unicorn, con Qt e file di configurazione simulati.

Non emula NAC, GPU, Wayland, CAN, USB, decoder, Android Auto o telefono.
Nessun firmware e incluso. I file forniti vengono soltanto letti.
"""
import argparse
import collections
import hashlib
import io
import json
import re
import struct
from pathlib import Path

from elftools.elf.elffile import ELFFile
import elftools
import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R7, UC_ARM_REG_R8,
    UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_SP, UC_ARM_REG_LR,
    UC_ARM_REG_PC,
)
from patch_laboratorio import HMI_SHA256, candidate

APP_SHA256 = "7d4cbfb944f2da83eaf44cff6035f9fa36bbbad1104d68fa08ee9d4159e152e8"
REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)
HEAP = 0x10000000
STACK = 0x70000000
RETURN = 0x20000000
READ_FILE = 0x37EC0E60
PARSER_END = 0x37EC19D8
NO_FILE = 0x37EC0FCC
OVERRIDE_START = 0x37EBD5E8
OVERRIDE_END = 0x37EBD688
OVERRIDE_DISABLED = 0x37EBD948
FIELDS = {
    "screenWidth": 0x37EBF3D4,
    "screenHeight": 0x37EBFA04,
    "widthMargin": 0x37EBFD1C,
    "heigthMargin": 0x37EBF6EC,
    "videoDPI": 0x37EC0034,
    "videoResolution": 0x37EC034C,
}

class Arm:
    """Maps supplied ELF load segments. All execution stays inside Unicorn memory."""
    def __init__(self, data, expected):
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("ELF non corrispondente al firmware analizzato.")
        elf = ELFFile(io.BytesIO(data))
        if elf['e_machine'] != 'EM_ARM' or elf.elfclass != 32 or not elf.little_endian:
            raise ValueError("Formato ELF ARM inatteso.")
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        pages = set()
        for s in elf.iter_segments():
            if s['p_type'] != 'PT_LOAD':
                continue
            first=s['p_vaddr']&~0xfff; end=(s['p_vaddr']+s['p_memsz']+4095)&~4095
            for p in range(first,end,4096):
                if p not in pages:
                    self.uc.mem_map(p,4096); pages.add(p)
            self.uc.mem_write(s['p_vaddr'],s.data())
        self.uc.mem_map(HEAP, 0x800000)
        self.uc.mem_map(STACK, 0x20000)
        self.uc.mem_map(RETURN, 4096)
        self.next = HEAP
        self.plt = {}
        dyn = elf.get_section_by_name('.dynsym')
        self.symbols = {s.name:s['st_value'] for s in dyn.iter_symbols() if s['st_value']}
        rel = elf.get_section_by_name('.rel.plt')
        plt = elf.get_section_by_name('.plt')
        if rel is not None:
            for n,r in enumerate(rel.iter_relocations()):
                self.plt[plt['sh_addr']+20+12*n] = dyn.get_symbol(r['r_info_sym']).name
        self.import_data = {}
        rel = elf.get_section_by_name('.rel.dyn')
        if rel is not None:
            for r in rel.iter_relocations():
                if not r['r_info_sym']:
                    continue
                s=dyn.get_symbol(r['r_info_sym'])
                if s['st_shndx']=='SHN_UNDEF' and s['st_info']['type'] != 'STT_FUNC':
                    ptr=self.import_data.setdefault(s.name,self.alloc(128))
                    self.put32(r['r_offset'],ptr)
        self.stops=set()
        self.last_stop=None
        self.calls=collections.Counter()
        self.uc.hook_add(UC_HOOK_CODE,self.hook)

    def alloc(self,n=64):
        p=self.next; self.next=(p+n+15)&~15
        if self.next>HEAP+0x800000:
            raise ValueError("Limite memoria laboratorio.")
        return p

    def get32(self,p):return int.from_bytes(self.uc.mem_read(p,4),'little')
    def put32(self,p,v):self.uc.mem_write(p,(v&0xffffffff).to_bytes(4,'little'))
    def r(self,n):return self.uc.reg_read(REGS[n])
    def cstr(self,p,n=None):
        if n is not None:
            return bytes(self.uc.mem_read(p,n)).decode('latin1')
        out=bytearray()
        for i in range(4096):
            b=self.uc.mem_read(p+i,1)[0]
            if b==0:return out.decode('latin1')
            out.append(b)
        raise ValueError("Stringa non terminata.")

    def hook(self,uc,address,size,user):
        if address in self.stops:
            self.last_stop=address;uc.emu_stop();return
        if address in self.plt:
            name=self.plt[address];self.calls[name]+=1
            if name in self.symbols and 'CAAPReadConfig' in name:
                uc.reg_write(UC_ARM_REG_PC,self.symbols[name]);return
            value=self.stub(name)
            if value is not None:
                uc.reg_write(UC_ARM_REG_R0,value&0xffffffff)
            uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))

    def stub(self,name):
        raise RuntimeError("Chiamata esterna non prevista: "+name)

    def run(self,start,args=(),stops=()):
        self.stops=set(stops)|{RETURN};self.last_stop=None
        self.uc.reg_write(UC_ARM_REG_SP,STACK+0x18000)
        self.uc.reg_write(UC_ARM_REG_LR,RETURN)
        for reg,val in zip(REGS,args):self.uc.reg_write(reg,val)
        self.uc.emu_start(start,RETURN+4,count=250000)
        if self.last_stop is None:
            raise RuntimeError("Esecuzione non terminata nel punto atteso.")
        return self.uc.reg_read(UC_ARM_REG_R0)

class ConfigLab(Arm):
    """Minimal Qt substitutes, explicitly not a Qt runtime or a Linux process."""
    def __init__(self,data,text):
        super().__init__(data,APP_SHA256)
        self.lines=[] if text is None else text.splitlines()
        self.present=text is not None;self.line_no=0;self.filename=None
        self.empty=self.qdata('')
        shared_map=self.import_data['_ZN12QMapDataBase11shared_nullE']
        self.put32(shared_map,0xffffffff)
        self.put32(self.import_data['_ZN10QArrayData11shared_nullE'],0xffffffff)
        # QString shared_null is QArrayData[2] in Qt 5.5; offset/size are supplied here.
        p=self.import_data['_ZN10QArrayData11shared_nullE']
        self.put32(p+4,0);self.put32(p+12,16)
        self.obj=self.alloc(64);self.put32(self.obj+4,shared_map)

    def qdata(self,text):
        b=text.encode('utf-16-le');p=self.alloc(16+len(b)+2)
        self.put32(p,0xffffffff);self.put32(p+4,len(b)//2);self.put32(p+12,16)
        self.uc.mem_write(p+16,b+b'\0\0');return p

    def qs(self,ptr):
        p=self.get32(ptr);n=self.get32(p+4);off=self.get32(p+12)
        if n>4096:raise ValueError("Dimensione QString inattesa.")
        return bytes(self.uc.mem_read(p+off,n*2)).decode('utf-16-le')

    def map_items(self):
        root=self.get32(self.get32(self.obj+4)+12);items={};seen=set()
        def visit(p):
            if not p:return
            if p in seen:raise ValueError("Ciclo nella mappa Qt simulata.")
            seen.add(p);visit(self.get32(p+4));items[self.qs(p+12)]=self.qs(p+16);visit(self.get32(p+8))
        visit(root);return items

    def stub(self,name):
        a,b,c,d=[self.r(i) for i in range(4)]
        if name=='_ZN7QString16fromAscii_helperEPKci':return self.qdata(self.cstr(a,b))
        if name=='_ZN5QFileC1ERK7QString':self.filename=self.qs(b);return a
        if name=='_ZNK5QFile6existsEv':return int(self.present)
        if name=='_ZN5QFile4openE6QFlagsIN9QIODevice12OpenModeFlagEE':return int(self.present)
        if name=='_ZN11QTextStreamC1EP9QIODevice':return a
        if name=='_ZNK11QTextStream5atEndEv':return int(self.line_no>=len(self.lines))
        if name=='_ZN11QTextStream8readLineEx':
            text=self.lines[self.line_no];self.line_no+=1;self.put32(a,self.qdata(text));return a
        if name=='_ZNK7QString5splitERKS_NS_13SplitBehaviorEN2Qt15CaseSensitivityE':
            parts=self.qs(b).split(self.qs(c));p=self.alloc(16+4*len(parts))
            self.put32(p,1);self.put32(p+4,len(parts));self.put32(p+8,0);self.put32(p+12,len(parts))
            for i,part in enumerate(parts):self.put32(p+16+4*i,self.qdata(part))
            self.put32(a,p);return a
        if name=='_ZN12QMapDataBase10createDataEv':
            p=self.alloc(32);self.put32(p,1);return p
        if name=='_ZN4QMapI7QStringS0_E13detach_helperEv':
            old=self.get32(a)
            if self.get32(old+12):raise RuntimeError("Clone di mappa non implementato nel modello Qt.")
            p=self.alloc(32);self.put32(p,1);self.put32(a,p);return None
        if name=='_ZN12QMapDataBase10createNodeEiiP12QMapNodeBaseb':
            node=self.alloc(b);left=self.get32(self.uc.reg_read(UC_ARM_REG_SP))
            self.put32(node,d)
            if d==a+8:self.put32(a+12,node)
            else:self.put32(d+(4 if left else 8),node)
            self.put32(a+4,self.get32(a+4)+1);return node
        if name=='_ZltRK7QStringS1_':return int(self.qs(a)<self.qs(b))
        if name=='_ZNK7QString7compareERKS_N2Qt15CaseSensitivityE':
            lhs,rhs=self.qs(a),self.qs(b)
            if c==0:lhs,rhs=lhs.casefold(),rhs.casefold()
            return (lhs>rhs)-(lhs<rhs)
        if name=='_ZN7QStringaSERKS_':self.put32(a,self.get32(b));return a
        if name=='_ZN7QString14compare_helperEPK5QChariPKciN2Qt15CaseSensitivityE':
            lhs=bytes(self.uc.mem_read(a,b*2)).decode('utf-16-le')
            rhs=self.cstr(c,None if d==0xffffffff else d)
            return (lhs>rhs)-(lhs<rhs)
        if name=='_ZNK7QString5toIntEPbi':
            value=self.qs(a).strip();ok=bool(re.fullmatch(r'[+-]?[0-9]+',value))
            value=int(value) if ok else 0;ok=ok and -(2**31)<=value<2**31
            if b:self.uc.mem_write(b,bytes([ok]))
            return value if ok else 0
        if name in {
            '_ZN6QListI7QStringED1Ev','_ZN5QListI7QStringED1Ev','_ZN5QListI7QStringED2Ev','_ZN11QTextStreamD1Ev',
            '_ZN7QStringD1Ev','_ZN10QArrayData10deallocateEPS_jj',
            '_ZN12QMapDataBase8freeDataEPS_',
        }:return None
        return super().stub(name)

    def parse(self):
        self.run(READ_FILE,(self.obj,),stops=(PARSER_END,NO_FILE))
        if self.filename!='/home/root/cfg':raise RuntimeError("Percorso firmware inatteso.")
        return {"flag":bool(self.uc.mem_read(self.obj,1)[0]),"mappa":self.map_items(),"righe_lette":self.line_no}

    def getter(self,key):
        out=self.alloc(4);self.put32(out,0xa5a5a5a5)
        ret=self.run(FIELDS[key],(self.obj,out))
        return {"return":ret,"value":self.get32(out)}

    def override(self):
        # Execute the real branch of setHMIVisibleArea, not its logging/mapValue prefix.
        obj=self.alloc(0x80);self.put32(obj+0x44,self.obj)
        self.put32(obj+8,2);self.put32(obj+12,1)
        self.uc.reg_write(UC_ARM_REG_R4,obj)
        self.run(OVERRIDE_START,stops=(OVERRIDE_END,OVERRIDE_DISABLED))
        return {"ramo_file":self.last_stop==OVERRIDE_END,
                "campi_oggetto_18_40":[self.get32(obj+i) for i in range(0x18,0x44,4)]}

def geometry(data,rect,patched=False):
    """Execute original getVisibleArea tail from CMP through QRect construction."""
    if patched:data=candidate(data)
    expected=hashlib.sha256(data).hexdigest() if patched else HMI_SHA256
    arm=Arm(data,expected);obj=arm.alloc(128);out=arm.alloc(16);guard=arm.alloc(4)
    x,y,w,h=rect
    for reg,v in ((UC_ARM_REG_R8,x),(UC_ARM_REG_R5,y),(UC_ARM_REG_R4,w),
                  (UC_ARM_REG_R7,h),(UC_ARM_REG_R9,obj)):
        arm.uc.reg_write(reg,v)
    # Stack offsets correspond to the original function after its prologue.
    # run() restores SP at this same value; no native call is made in the tested block.
    sp=STACK+0x18000
    arm.put32(sp+0x3c,guard);arm.put32(sp+0x14,out)
    arm.put32(sp+0x204,0);arm.put32(guard,0)
    arm.run(0x37D8C648,stops=(0x37D8C6B0,))
    left,top,right,bottom=struct.unpack('<4i',arm.uc.mem_read(out,16))
    return {"x":left,"y":top,"width":right-left+1,"height":bottom-top+1}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--rootfs',required=True,type=Path)
    a=ap.parse_args()
    app=(a.rootfs/'usr/lib/ovip/Android/libAndroidAutoAppLogic.so').read_bytes()
    hmi=(a.rootfs/'usr/lib/ovip/AAuto/libAAutoHMILib.so.1.0.0').read_bytes()
    text='readFromFile=true\nscreenWidth=1920\nscreenHeight=720\nwidthMargin=0\nheigthMargin=360\nvideoDPI=240\nvideoResolution=1080p\n'
    lab=ConfigLab(app,text);parsed=lab.parse()
    result={
        'ambito':'Blocchi ARM originali in Unicorn; Qt/I-O simulati; nessun veicolo o protocollo AA.',
        'versioni':{'unicorn':unicorn.__version__,'pyelftools':elftools.__version__},
        'parser':parsed,'getter':{k:lab.getter(k) for k in FIELDS},
        'override':lab.override(),
        'geometrie':[{'input':list(rect),'originale':geometry(hmi,rect),
                      'candidato':geometry(hmi,rect,True)}
                     for rect in [(320,0,1280,720),(0,0,1920,720),(0,0,800,480)]],
        'parametri_esempio':'Scelti per osservare il codice; non sono una configurazione omologata o provata sul decoder.',
        'fullscreen_su_veicolo_dimostrato':False,
    }
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
