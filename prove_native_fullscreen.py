#!/usr/bin/env python3
"""Limited ARM execution of the coordinated candidate, not a NAC emulator."""
import argparse
import hashlib
import io
import json
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn.arm_const import *
from prove_arm import Arm,ConfigLab,STACK,RETURN
from patch_fullscreen_lab import load_plan,patch_bytes,PROFILE
from config_laboratorio import render_cfg

INTERNAL='usr/lib/ovip/HMIInternal/HMIInternalApplication/libHMIInternalApplication.so.1.0.0'
HMI='usr/lib/ovip/AAuto/libAAutoHMILib.so.1.0.0'
APP='usr/lib/ovip/Android/libAndroidAutoAppLogic.so'
ZONE='usr/lib/ovip/UIFramework/ZoneManagement/libZoneManagement.so.1.0.0'
PROJECTION='usr/bin/conn_AndroidAutoProjection.out'
ZONE_SHA='2bea6fd54448608f5b1d7dc2ede7963a1c1d86abd931df6f7908637c5c58b350'
PROJECTION_SHA='a9d276efb4e23d63b680bebc998b1aa4aea84f41e57798b1c761599d457d873f'

class Native(Arm):
    def __init__(self,data,expected):
        super().__init__(data,expected)
        self.uc.reg_write(UC_ARM_REG_C1_C0_2,0x00f00000)
        self.uc.reg_write(UC_ARM_REG_FPEXC,0x40000000)
        self.trace=[];self.rectangle=(320,0,1280,720)
        self.zone=0;self.index=0;self.count=1;self.focused=True;self.name='INTERNET_0033Skin'
        self.sidebars_shown=True;self.main_shown=True

    def qdata(self,text):
        raw=text.encode('utf-16-le');p=self.alloc(16+len(raw)+2)
        self.put32(p,0xffffffff);self.put32(p+4,len(raw)//2);self.put32(p+12,16)
        self.uc.mem_write(p+16,raw+b'\0\0');return p

    def stub(self,name):
        a,b,c=[self.r(i) for i in range(3)];self.trace.append({'call':name,'r1':b})
        if name=='_ZN5uifwk7screens13ScreenManager14getVisibleAreaENS0_12ScreenStatusE':
            self.trace[-1]['screen_status']=c
            x,y,w,h=self.rectangle;self.uc.mem_write(a,struct.pack('<4i',x,y,x+w-1,y+h-1));return a
        if name=='_ZNK5uifwk5zones11ZoneMonitor7topMostENS0_4ZoneE':
            if b!=self.zone:raise ValueError('Zone differs from native AA registration.')
            return self.index
        if name=='_ZNK5uifwk5zones11ZoneMonitor5countEv':return self.count
        if name=='_ZNK5uifwk5zones11ZoneMonitor9isFocusedEj':return int(self.focused)
        if name=='_ZNK5uifwk5zones11ZoneMonitor6nameOfEj':
            self.put32(a,self.qdata(self.name));return a
        if name=='_ZNK5uifwk5zones11ZoneMonitor7isShownENS0_4ZoneE':return int(self.main_shown)
        if name=='_ZN5uifwk7screens13ScreenManager13isScreenShownEPNS0_8ScreenIDE':return int(self.sidebars_shown)
        if name=='_ZN5uifwk7screens13ScreenManager11requestHideEPNS0_8ScreenIDE':
            self.sidebars_shown=False;return None
        if name=='_ZN5uifwk7screens13ScreenManager11requestShowEPNS0_8ScreenIDE':
            self.sidebars_shown=True;return None
        if name in ('_ZN7QStringD1Ev','_ZN7QStringD2Ev'):return None
        return super().stub(name)

    def hook(self,uc,address,size,user):
        name=self.plt.get(address)
        if name and name in self.symbols and ('SurfaceData' in name or 'isStatusLineAllowed' in name):
            uc.reg_write(UC_ARM_REG_PC,self.symbols[name]);return
        super().hook(uc,address,size,user)

def prepared(root,component):
    spec=next(s for s in load_plan()['files'] if s['id']==component)
    return patch_bytes((Path(root)/spec['source_path']).read_bytes(),spec),spec

def visible_area(root,rect=(320,0,1280,720),climate=True,corrupt_canary=False):
    data,spec=prepared(root,'aauto_geometry_and_crop');lab=Native(data,spec['candidate_sha256'])
    lab.rectangle=rect;obj=lab.alloc(64);result=lab.alloc(16);lab.put32(obj+8,lab.alloc(64))
    if corrupt_canary:
        # Corrupt only the saved canary after the preserved ScreenManager call.
        from unicorn import UC_HOOK_CODE
        def corrupt(uc,at,size,user):
            if at==0x37da6a54:lab.put32(lab.uc.reg_read(UC_ARM_REG_SP)+0x1cc,1)
        lab.uc.hook_add(UC_HOOK_CODE,corrupt)
    ret=lab.run(0x37da69e8,(result,obj,int(climate)))
    a,b,c,d=struct.unpack('<4i',lab.uc.mem_read(result,16))
    return {'x':a,'y':b,'width':c-a+1,'height':d-b+1,'returned_pointer_correct':ret==result,
            'native_screen_status':lab.trace[0]['screen_status']}

def sidebar_allowed(root,whd=True,focused=True,name='INTERNET_0033Skin',index=0,count=1,
                    state=0,previous=True,climate_allowed=True,monitor_present=True):
    data,spec=prepared(root,'sidebars_with_native_focus');lab=Native(data,spec['candidate_sha256'])
    lab.focused=focused;lab.name=name;lab.index=index;lab.count=count
    obj=lab.alloc(192);lab.put32(obj+0x20,lab.alloc(64) if monitor_present else 0)
    lab.uc.mem_write(obj+0x60,bytes([bool(whd)]));lab.put32(obj+0x24,state)
    lab.uc.mem_write(obj+0x70,bytes([bool(previous)]));lab.uc.mem_write(obj+0x2c,bytes([bool(climate_allowed)]))
    allowed=lab.run(0x378fde50,(obj,))
    return {'allowed':bool(allowed),'stored':bool(lab.uc.mem_read(obj+0x70,1)[0]),'trace':lab.trace}

def crop_offset(root,rect=(0,0,1920,720),frame=(1920,1080),margin=360,xmargin=0):
    data,spec=prepared(root,'aauto_geometry_and_crop');lab=Native(data,spec['candidate_sha256'])
    obj=lab.alloc(128);x,y,w,h=rect
    for off,val in [(0x24,x),(0x28,y),(0x2c,w),(0x30,h),(0x34,xmargin),(0x3c,frame[0]),(0x40,frame[1])]:lab.put32(obj+off,val)
    lab.uc.reg_write(UC_ARM_REG_R9,obj)
    sp=STACK+0x18000;lab.put32(sp+0x3c,margin);lab.put32(sp+0x2c,frame[1])
    # Execute the original arithmetic, before the brand/carline path.
    lab.run(0x37d8eb64,stops=(0x37d8eb98,))
    before=struct.unpack('<i',lab.uc.mem_read(obj+0x38,4))[0]
    # Execute the new exact-profile guard before the original common epilogue.
    lab.run(0x37d8ebfc,stops=(0x37d8f240,))
    after=struct.unpack('<i',lab.uc.mem_read(obj+0x38,4))[0]
    return {'factory_arithmetic_y':before,'candidate_y':after,'frame':list(frame)}

def sidebar_transition(root):
    data,spec=prepared(root,'sidebars_with_native_focus');lab=Native(data,spec['candidate_sha256'])
    obj=lab.alloc(192);lab.put32(obj+8,lab.alloc(64));lab.put32(obj+0x20,lab.alloc(64))
    lab.put32(obj+0x14,111);lab.put32(obj+0x18,222);lab.uc.mem_write(obj+0x60,b'\1')
    lab.uc.mem_write(obj+0x70,b'\1');events=[]
    for name,focused in [('AUDIO_0001Skin',True),('INTERNET_0033Skin',True),
                         ('INTERNET_0033Skin',False),('INTERNET_0033Skin',True),('CLIMATE_0151SkinLogic',True)]:
        lab.name=name;lab.focused=focused;lab.trace=[]
        lab.run(0x378fe3b4,(obj,),stops=(0x378fe568,0x378fe6a0))
        requests=[{'action':'hide' if 'requestHide' in t['call'] else 'show','screen_id':t['r1']}
                  for t in lab.trace if 'requestHide' in t['call'] or 'requestShow' in t['call']]
        events.append({'context':name,'aa_focused':focused,'sidebars_shown_in_stub':lab.sidebars_shown,
                       'native_requests':requests})
    return events

def native_touch(root,x,y,action='down',finger=0):
    data=(Path(root)/PROJECTION).read_bytes();lab=Native(data,PROJECTION_SHA)
    user=lab.alloc(128);obj=lab.alloc(256);lab.put32(user+0x20,obj)
    sp=STACK+0x18000
    # Feed the video properties to the ORIGINAL input configuration setter.
    # Its enum-3 path writes 1920x1080; its later stores write the two margins.
    # The intervening platform metadata submission call is explicitly not run.
    properties=[3,PROFILE['widthMargin'],PROFILE['heigthMargin'],1,PROFILE['videoDPI'],0,0,0]
    for i,value in enumerate(properties[3:]):lab.put32(sp+4*i,value)
    lab.run(0x78ac8,(obj,*properties[:3]),stops=(0x78b40,))
    lab.stops={0x78b84};lab.last_stop=None
    lab.uc.emu_start(0x78b70,RETURN+4,count=100)
    if lab.last_stop!=0x78b84:raise RuntimeError('Native input setup did not reach its expected stop.')
    settings=[lab.get32(obj+offset) for offset in (0x84,0x88,0x8c,0x90)]
    if settings!=[1920,1080,0,360]:raise RuntimeError('Unexpected native input video settings.')
    if action=='down':
        start=0x7a5d8
        for off,val in [(0,0),(4,finger),(8,int(x*256)),(12,int(y*256))]:lab.put32(sp+off,val)
        args=(user,0,0,0)
    elif action=='motion':
        start=0x7a950;lab.put32(sp,int(x*256));lab.put32(sp+4,int(y*256));args=(user,0,0,finger)
    else:raise ValueError('Only the down/motion conversion path is exercised.')
    lab.run(start,args,stops=(0x790c0,))
    return {'x':lab.get32(obj+0x3c+finger*16),'y':lab.get32(obj+0x40+finger*16),
            'finger':finger,'action':action,'native_video_settings':settings,
            'platform_metadata_submission_executed':False,
            'scope':'Native input setter fragments and Wayland callback to coordinate conversion; stop before Cinemo event dispatch.'}

def surface_default(root,rect=(0,-180,1920,1080)):
    data=(Path(root)/ZONE).read_bytes();lab=Native(data,ZONE_SHA)
    r=lab.alloc(16);s=lab.alloc(128);dummy=lab.alloc(64);x,y,w,h=rect
    lab.uc.mem_write(r,struct.pack('<4i',x,y,x+w-1,y+h-1))
    lab.run(0x37653d00,(dummy,r,dummy,s))
    vals=[struct.unpack('<i',lab.uc.mem_read(s+o,4))[0] for o in (0x1c,0x20,0x24,0x28)]
    return dict(zip(('x','y','width','height'),vals))

def unchanged_unwind(root):
    result=[]
    for spec in load_plan()['files']:
        original=(Path(root)/spec['source_path']).read_bytes();new=patch_bytes(original,spec)
        elf=ELFFile(io.BytesIO(original))
        for name in ('.ARM.exidx','.ARM.extab','.gcc_except_table'):
            section=elf.get_section_by_name(name)
            if section:
                off=section['sh_offset'];n=section['sh_size']
                result.append({'file':spec['id'],'section':name,'unchanged':original[off:off+n]==new[off:off+n]})
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rootfs',required=True,type=Path);a=p.parse_args()
    cfg=ConfigLab((a.rootfs/APP).read_bytes(),render_cfg(PROFILE));parsed=cfg.parse()
    result={'revision':3,'scope':'Limited native ARM paths with mocked Qt/zone inputs; no vehicle, decoder or full compositor.',
      'configuration':{'parser':parsed,'override':cfg.override()},
      'visible_area':visible_area(a.rootfs),'crop':crop_offset(a.rootfs),
      'focus_transition':[{'focused':state,**sidebar_allowed(a.rootfs,focused=state)} for state in (False,True,False)],
      'native_sidebar_requests':sidebar_transition(a.rootfs),
      'touch_corners':[{'screen':[x,y],'native':native_touch(a.rootfs,x,y+180)} for x,y in ((0,0),(1919,0),(0,719),(1919,719))],
      'default_surface_path':surface_default(a.rootfs),'unwind_sections':unchanged_unwind(a.rootfs),
      'full_system_or_exception_unwind_tested':False,'vehicle_tested':False}
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
