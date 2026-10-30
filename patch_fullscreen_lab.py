#!/usr/bin/env python3
"""Coordinated OFFLINE research candidate. No installation, device, CAN or network access."""
import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from config_laboratorio import render_cfg

PLAN_SHA256='75c52d25c5af91c941330c3c3f0e4ace92b02822cf9bcadb6081f80081c0fdb7'
QML_SHA256='5eeabbf143009cebeec61a583678219310b887cc2062509d6ecf5b482f184537'
QML_CANDIDATE_SHA256='c12b2629b19e9f50df04c3f19612fb86da61cf4d971b282775349d506e0f5584'
QML_DELTA='''
    // Offline research candidate for the exact WHD layout only.
    readonly property bool nacLabWHD: ScreenInfo.displayCategory === ScreenInfo.WHD
                                      && ScreenInfo.width === 1920 && ScreenInfo.height === 720
    x: nacLabWHD ? 0 : (ScreenInfo.displayCategory === ScreenInfo.WHD ? 320 : 0)
    width: nacLabWHD ? ScreenInfo.width
                    : (ScreenInfo.displayCategory === ScreenInfo.WHD ? ScreenInfo.width - 640 : ScreenInfo.width)
'''
PROFILE={'readFromFile':'true','screenWidth':1920,'screenHeight':1080,
         'widthMargin':0,'heigthMargin':360,'videoDPI':240,'videoResolution':'1080p'}
DHU='''# Desktop test profile only. Requires a real phone; not tested in this research.
[general]
inputmode = touch
resolution = 1920x1080
dpi = 240
realdpi = 240
framerate = 30
marginwidth = 0
marginheight = 360
cropmargins = true
'''

def sha(data):return hashlib.sha256(data).hexdigest()

def read_file(path):
    path=Path(path)
    if not stat.S_ISREG(path.lstat().st_mode):raise ValueError('Regular local file required; symlinks refused.')
    return path.read_bytes()

def load_plan(path=None):
    path=Path(path) if path else Path(__file__).with_name('patch_fullscreen_plan.json')
    data=read_file(path)
    if sha(data)!=PLAN_SHA256:raise ValueError('Patch plan hash is not the reviewed plan.')
    plan=json.loads(data)
    if plan['revision']!=3 or plan['firmware']!='44.07.33.32_NAC-r0':raise ValueError('Plan version mismatch.')
    return plan

def patch_bytes(data,spec,restore=False):
    expected=spec['candidate_sha256'] if restore else spec['original_sha256']
    if len(data)!=spec['size'] or sha(data)!=expected:raise ValueError('Source size/SHA256 mismatch.')
    output=bytearray(data);end=0
    for chunk in sorted(spec['chunks'],key=lambda c:c['file_offset']):
        off=chunk['file_offset'];old=bytes.fromhex(chunk['after_hex' if restore else 'before_hex'])
        new=bytes.fromhex(chunk['before_hex' if restore else 'after_hex'])
        if off<end or off<0 or len(old)!=len(new) or len(old)!=chunk['length'] or off+len(old)>len(data):
            raise ValueError('Patch interval invalid or overlapping.')
        if data[off:off+len(old)]!=old:raise ValueError('Instruction bytes differ.')
        output[off:off+len(old)]=new;end=off+len(old)
    if sha(output)!=(spec['original_sha256'] if restore else spec['candidate_sha256']):
        raise ValueError('Result hash mismatch.')
    return bytes(output)

def patch_qml(data):
    if sha(data)!=QML_SHA256:raise ValueError('AA QML SHA256 mismatch.')
    needle=b'    context: "INTERNET_0033"\n'
    if data.count(needle)!=1:raise ValueError('Exact AA context missing or repeated.')
    result=data.replace(needle,needle+QML_DELTA.encode(),1)
    if sha(result)!=QML_CANDIDATE_SHA256:raise ValueError('Candidate QML hash differs.')
    return result

def restore_qml(data):
    if sha(data)!=QML_CANDIDATE_SHA256 or data.count(QML_DELTA.encode())!=1:
        raise ValueError('Candidate QML hash differs.')
    result=data.replace(QML_DELTA.encode(),b'',1)
    if sha(result)!=QML_SHA256:raise ValueError('Restored QML hash differs.')
    return result

def write_new(path,data):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:f.write(data)

def prepare(root,qml,out):
    plan=load_plan();root=Path(root);qml=Path(qml);out=Path(out)
    products=[]
    for spec in plan['files']:
        source=read_file(root/spec['source_path']);result=patch_bytes(source,spec)
        restored=patch_bytes(result,spec,True)
        if restored!=source:raise ValueError('Byte-exact restoration failed.')
        products.append((spec['id']+'.offline.so',result,{'source':spec['source_path'],
            'original_sha256':sha(source),'candidate_sha256':sha(result),'local_restore_verified':True}))
    original_qml=read_file(qml);result_qml=patch_qml(original_qml)
    products.append(('AAutoScreen.candidate.qml',result_qml,{'source':str(qml),
        'original_sha256':sha(original_qml),'candidate_sha256':sha(result_qml)}))
    products.append(('cfg.candidate',render_cfg(PROFILE).encode(),{'runtime_location':'/home/root/cfg','runtime_original_unknown':True}))
    products.append(('DHU_1920x720.ini',DHU.encode(),{'executed_with_phone':False}))
    manifest={'revision':3,'firmware':plan['firmware'],'scope':'COPIES ON PC ONLY',
        'installable':False,'vehicle_tested':False,'original_input_files_modified':False,
        'runtime_original_cfg_acquired':False,'runtime_calibration_offsets_acquired':False,
        'unresolved':['Real hardware identity and calibration','Reversible filesystem access and accepted deployment',
                      'Decoder/Wayland/phone negotiation and all vehicle functions on a bench'],
        'files':[]}
    for name,data,extra in products:manifest['files'].append({'file':name,'bytes':len(data),'sha256':sha(data),**extra})
    # All validation completes before creating the new directory. No existing directory is used.
    out.mkdir(exist_ok=False)
    for name,data,_ in products:write_new(out/name,data)
    write_new(out/'bundle_manifest.json',(json.dumps(manifest,indent=2)+'\n').encode())
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    q=sub.add_parser('prepare');q.add_argument('--rootfs',required=True,type=Path);q.add_argument('--ui-file',required=True,type=Path);q.add_argument('--output',required=True,type=Path)
    q=sub.add_parser('restore-copy');q.add_argument('--component',required=True);q.add_argument('source',type=Path);q.add_argument('output',type=Path)
    a=p.parse_args()
    try:
        if a.action=='prepare':result=prepare(a.rootfs,a.ui_file,a.output)
        else:
            specs={s['id']:s for s in load_plan()['files']}
            if a.component=='aa_qml':
                if not a.output.name.endswith('.restored.qml'):raise ValueError('Use a new .restored.qml destination.')
                data=restore_qml(read_file(a.source))
            else:
                if a.component not in specs:raise ValueError('Unknown component.')
                if not a.output.name.endswith('.restored.so'):raise ValueError('Use a new .restored.so destination.')
                data=patch_bytes(read_file(a.source),specs[a.component],True)
            write_new(a.output,data)
            result={'restored_local_copy':str(a.output),'sha256':sha(data),'vehicle_recovery_tested':False}
        print(json.dumps(result,indent=2))
    except (ValueError,OSError) as exc:p.exit(2,str(exc)+'\n')

if __name__=='__main__':main()
