#!/usr/bin/env python3
"""Analisi locale NAC. Legge file e stampa JSON; nessun accesso a USB, CAN o rete.

Non installa firmware e non sblocca Android Auto. Richiede Python >= 3.9.
"""
import argparse
import configparser
import hashlib
import json
import re
import sys
import tarfile
from pathlib import Path

UI_SHA256 = '4ea4167a3a3155aa9db3ea89586e2dfc07d4a6f93b95b1a3584b368b489459a1'
AA_PATH = 'media/datastore/ui/HMIApplications/AAuto/qml/AAutoHMILib/INTERNET_0033SkinLogic.qml'
STATUS_PATH = 'media/datastore/ui/HMIApplications/UIFramework/UIFwkApplications/HMIInternalApplication/qml/StatusBar/'
SELECTED = {
    'BTEL_AAP_ON_OFF', 'AAP_PRIVACY_ACTIVATI_1',
    'VIDEO_CODING_1', 'VIDEO_CODING_2',
    'LVDS_1_BWS_CONFIG_1', 'LVDS_2_BWS_CONFIG_1',
    'CLIM_STATUSLINE', 'ATT_DG_CHX_CAL_ECRAN',
}
ROOTFS_SHA256 = '4e2aa99c8ab885cf719cfde3f48bf4b862d14cfbcda047c4a0b3096eedaef38a'
ROOT_FILES = {
    'usr/share/ovip/ScreenManager/ScreenAreas.ini': '921bcf5eb653b0c239ccefa9ca2998487bea262ecb106c15538fbfd9ba9247d1',
    'usr/lib/ovip/Android/libAndroidAutoAppLogic.so': '7d4cbfb944f2da83eaf44cff6035f9fa36bbbad1104d68fa08ee9d4159e152e8',
    'usr/lib/ovip/UIFramework/ScreenManager/libHmiScreenManager.so.1.0.0': 'c39051c79f12341fa387b40da2f516ffb798df21eea35303ee65bb6f5ca96d25',
}

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()

def ui_audit(path, manifest=None):
    actual = digest(path)
    if actual != UI_SHA256:
        raise ValueError('Il modulo decifrato non corrisponde all\'hash analizzato del firmware 44.07.33.32_NAC-r0')
    if manifest:
        cfg = configparser.ConfigParser(interpolation=None, strict=True)
        cfg.read(manifest, encoding='utf-8')
        candidates = [s for s in cfg.sections() if s.endswith('/Universes/ui-app-data-resource.tar.gz')]
        if len(candidates) != 1 or cfg[candidates[0]].get('Hash', '').strip().lower() != actual:
            raise ValueError('Hash del modulo assente, ambiguo o diverso nel manifesto')
    wanted = [AA_PATH, STATUS_PATH+'LWHDScreenUILogicZ5.qml', STATUS_PATH+'RWHDScreenUILogicZ5.qml']
    found = {}
    with tarfile.open(path, mode='r:gz') as archive:
        count = 0
        for member in archive:
            count += 1
            if count > 10000:
                raise ValueError('Archivio con troppi elementi')
            name = member.name.removeprefix('./')
            if name not in wanted:
                continue
            if name in found or not member.isfile() or member.size > 1024*1024:
                raise ValueError('Elemento atteso duplicato o non valido')
            raw = archive.extractfile(member).read()
            found[name] = (raw, raw.decode('utf-8'))
    if set(found) != set(wanted):
        raise ValueError('Componenti grafici attesi mancanti')
    aa = found[AA_PATH][1]
    observations = {
        'contenitore_FullscreenContentScreen': bool(re.search(r'\bFullscreenContentScreen\s*\{', aa)),
        'anchors_fill_parent': 'anchors.fill: parent' in aa,
        'layerMasks_usano_parent_width': 'parent.width : 0' in aa,
        'layerMasks_usano_parent_height': 'parent.height : 0' in aa,
    }
    status = {}
    for filename in wanted[1:]:
        text = found[filename][1]
        width = re.search(r'^\s*width:\s*(\d+)\s*$', text, re.M)
        x = re.search(r'^\s*x:\s*(\d+)\s*$', text, re.M)
        status[Path(filename).name] = {
            'width_letterale': int(width[1]) if width else None,
            'x_letterale': int(x[1]) if x else None,
            'gruppo_clima': bool(re.search('groupStatusLineWHDClimate(?:Left|Right)', text)),
        }
    return {
        'ambito': 'Analisi statica del solo componente UI indicato',
        'sha256_ui_decifrato': actual,
        'hash_confrontato_con_manifesto': bool(manifest),
        'autenticita_firma_o_compatibilita_installazione_verificate': False,
        'prova_su_veicolo': False,
        'misura_risoluzione_o_negoziazione_AA': False,
        'file_sha256': {k: hashlib.sha256(v[0]).hexdigest() for k,v in found.items()},
        'schermata_android_auto': observations,
        'pannelli_stato_WHD': status,
        'avvertenza': 'La presenza di FullscreenContentScreen non dimostra il fullscreen sul pannello fisico. Non viene prodotta alcuna patch.',
    }

def read_backup(path):
    if Path(path).stat().st_size > 1024*1024:
        raise ValueError('Backup troppo grande')
    result = {}
    for number,line in enumerate(Path(path).read_text(encoding='utf-8-sig').splitlines(), 1):
        if not line.strip() or line.lstrip().startswith(('#', ';')):
            continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]{4})\s*=\s*((?:[0-9a-fA-F]{2})+)\s*', line)
        if not match:
            raise ValueError(f'Formato backup non valido alla riga {number}')
        zone, raw = match[1].upper(), bytes.fromhex(match[2])
        if zone in result:
            raise ValueError(f'Zona duplicata alla riga {number}')
        result[zone] = raw
    return result

def rootfs_audit(directory, image=None):
    directory = Path(directory)
    if image and digest(image) != ROOTFS_SHA256:
        raise ValueError('Immagine rootfs diversa da quella analizzata')
    hashes = {name:digest(directory/name) for name in ROOT_FILES}
    if hashes != ROOT_FILES:
        raise ValueError('I componenti rootfs non corrispondono alla versione analizzata')
    areas = configparser.ConfigParser(interpolation=None)
    areas.read(directory/'usr/share/ovip/ScreenManager/ScreenAreas.ini')
    rectangles = {}
    for k,value in areas['WHD'].items():
        m = re.fullmatch(r'@Rect\((\d+) (\d+) (\d+) (\d+)\)',value)
        if not m:
            raise ValueError('Rettangolo WHD non riconosciuto')
        rectangles[k.upper()] = dict(zip(['x','y','width','height'],map(int,m.groups())))
    binary = (directory/'usr/lib/ovip/Android/libAndroidAutoAppLogic.so').read_bytes()
    tokens = ['/home/root/cfg','readFromFile','screenWidth','screenHeight','widthMargin','heigthMargin','videoDPI','videoResolution','CAAPReadConfig']
    return {
        'ambito': 'Analisi statica rootfs, nessuna esecuzione di binari NAC',
        'sha256_rootfs_noto':ROOTFS_SHA256,
        'immagine_rootfs_confrontata':bool(image),
        'file_sha256':hashes,
        'rettangoli_WHD':rectangles,
        'stringhe_presenti_in_libAndroidAutoAppLogic':{t:t.encode() in binary for t in tokens},
        'prova_runtime_o_su_veicolo':False,
        'avvertenza':'I simboli e le stringhe identificano una pista di ricerca. Non provano che modificare un solo file produca un fullscreen corretto. ScreenAreas.ini riguarda piu applicazioni.',
    }

def backup_audit(path, schema):
    backup = read_backup(path)
    zones = json.loads(Path(schema).read_text(encoding='utf-8-sig'))['NAC']['zones']
    result = []
    for zone, definition in zones.items():
        for param in definition.get('params', []):
            if param.get('extra_name') not in SELECTED:
                continue
            row = {'zona':zone,'nome':param['extra_name'],'descrizione_schema':param.get('detail',{}).get('en','')}
            data = backup.get(zone)
            # Convenzione dello schema verificata in ParamsForm.cs, pos - 4.
            offset = int(param['pos']) - 4
            mask = int(param['mask'],16)
            row.update(offset_dati=offset, maschera=f'{mask:02X}')
            if data is None or offset < 0 or offset >= len(data):
                row['stato'] = 'zona assente o troppo corta'
            elif param.get('zoneLength') and len(data) != int(param['zoneLength']):
                row['stato'] = 'variante lunghezza non applicabile'
            else:
                value = data[offset] & mask
                row.update(stato='letto',valore_mascherato=f'{value:02X}')
                choices = [p.get('text',{}).get('en','') for p in param.get('listbox',[]) if int(p['value'],16)==value]
                if choices:
                    row['valore_secondo_schema'] = choices[0]
            result.append(row)
    return {
        'ambito': 'Backup locale fornito, nessuna connessione al veicolo',
        'sha256_backup':digest(path),'sha256_schema':digest(schema),
        'numero_zone_backup':len(backup),'numero_zone_schema':len(zones),
        'parametri_selezionati':result,
        'avvertenza':'I campi LVDS e VIDEO_CODING non sono una procedura documentata per il fullscreen. Nessuna modifica o comando di scrittura viene generato.',
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    ui = sub.add_parser('ui', help='Ispeziona il modulo UI gia decifrato')
    ui.add_argument('file', type=Path)
    ui.add_argument('--manifesto', type=Path)
    backup = sub.add_parser('backup', help='Legge parametri selezionati da un backup .nac')
    backup.add_argument('file', type=Path)
    backup.add_argument('--schema', required=True, type=Path)
    root = sub.add_parser('rootfs', help='Ispeziona la rootfs gia estratta senza eseguire binari NAC')
    root.add_argument('directory', type=Path)
    root.add_argument('--immagine', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'ui':
            result = ui_audit(args.file,args.manifesto)
        elif args.action == 'backup':
            result = backup_audit(args.file,args.schema)
        else:
            result = rootfs_audit(args.directory,args.immagine)
    except (ValueError,KeyError,OSError,tarfile.TarError) as e:
        print(f'Analisi interrotta: {e}', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
