#!/usr/bin/env python3
"""Reassemble the custom ARM snippets and compare them to the pinned patch plan.

Requires keystone-engine 0.9.2. Does not need, create or modify firmware files.
"""
from pathlib import Path
import json
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM,KS_MODE_LITTLE_ENDIAN
from patch_fullscreen_lab import load_plan, load_projection_spec, load_automatic_profile_spec

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
    projection = load_projection_spec()
    dispatch, handler = projection['chunks']
    for chunk, src in ((dispatch, 'bne 0x7713c'), (handler, (folder / 'native_projection_whd.s').read_text())):
        encoded, _ = assembler.asm(src, addr=int(chunk['elf_address'], 16))
        if bytes(encoded).hex() != chunk['after_hex']:
            raise ValueError('Projection assembly differs from the pinned plan: ' + chunk['label'])
    results.append({'source': 'native_projection_whd.s and format dispatch', 'matches_pinned_plan': True,
                    'bytes_with_padding': dispatch['length'] + handler['length']})
    profile, = load_automatic_profile_spec()['chunks']
    source = 'native_automatic_profile.s'
    encoded, _ = assembler.asm((folder / source).read_text(), addr=int(profile['elf_address'], 16))
    if bytes(encoded).hex() != profile['after_hex']:
        raise ValueError('Automatic-profile assembly differs from the pinned plan.')
    results.append({'source': source, 'matches_pinned_plan': True, 'bytes_with_padding': len(encoded)})
    if len(results)!=5:raise ValueError('Incomplete assembly verification.')
    print(json.dumps({'scope':'Assembly reproducibility only, not a device test','results':results},indent=2))

if __name__=='__main__':main()
