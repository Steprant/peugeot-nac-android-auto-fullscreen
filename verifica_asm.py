#!/usr/bin/env python3
"""Reassemble the three custom ARM snippets and compare them to the pinned patch plan.

Requires keystone-engine 0.9.2. Does not need, create or modify firmware files.
"""
from pathlib import Path
import json
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM,KS_MODE_LITTLE_ENDIAN
from patch_fullscreen_lab import load_plan

def main():
    folder=Path(__file__).resolve().parent;plan=load_plan()
    sources={0x37da6a54:'native_geometry_guard.s',0x37d8ebfc:'native_crop_guard.s',0x378fdea0:'native_status_guard.s'}
    assembler=Ks(KS_ARCH_ARM,KS_MODE_ARM|KS_MODE_LITTLE_ENDIAN);results=[]
    for spec in plan['files']:
        for chunk in spec['chunks']:
            address=int(chunk['elf_address'],0)
            if address not in sources:continue
            encoded,count=assembler.asm((folder/sources[address]).read_text(),addr=address)
            encoded=bytes(encoded);encoded+=b'\0'*((-len(encoded))%4)
            encoded+=bytes.fromhex('00f020e3')*((chunk['length']-len(encoded))//4)
            if encoded.hex()!=chunk['after_hex']:raise ValueError('ASM differs from reviewed plan: '+sources[address])
            results.append({'source':sources[address],'matches_pinned_plan':True,'bytes_with_padding':len(encoded)})
    if len(results)!=3:raise ValueError('Incomplete assembly verification.')
    print(json.dumps({'scope':'Assembly reproducibility only, not a device test','results':results},indent=2))

if __name__=='__main__':main()
