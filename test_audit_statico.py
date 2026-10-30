import json
import tempfile
import unittest
from pathlib import Path
from audit_statico import read_backup, backup_audit, ui_audit, rootfs_audit, ROOT_FILES

class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def write(self,name,text):
        p=self.root/name;p.write_text(text,encoding='utf-8');return p

    def test_backup_esadecimale(self):
        p=self.write('backup.nac','\ufeff2131=80\n2129=C030\n')
        self.assertEqual(read_backup(p)['2129'],b'\xc0\x30')

    def test_rifiuta_duplicati(self):
        p=self.write('backup.nac','2131=80\n2131=00')
        with self.assertRaises(ValueError):read_backup(p)

    def test_rifiuta_byte_incompleto(self):
        with self.assertRaises(ValueError):read_backup(self.write('backup.nac','2131=8'))

    def test_rifiuta_contenuto_non_backup(self):
        with self.assertRaises(ValueError):read_backup(self.write('backup.nac','222131'))

    def test_maschera_e_posizione_con_risultato_noto(self):
        schema={'NAC':{'zones':{'2131':{'params':[{'extra_name':'BTEL_AAP_ON_OFF','pos':'04','mask':'80'}]}}}}
        p=self.write('schema.json',json.dumps(schema))
        b=self.write('backup.nac','2131=81')
        row=backup_audit(b,p)['parametri_selezionati'][0]
        self.assertEqual(row['valore_mascherato'],'80')
        self.assertEqual(row['offset_dati'],0)

    def test_zona_troppo_corta(self):
        schema={'NAC':{'zones':{'2129':{'params':[{'extra_name':'VIDEO_CODING_1','pos':'05','mask':'20'}]}}}}
        p=self.write('schema.json',json.dumps(schema))
        row=backup_audit(self.write('backup.nac','2129=C0'),p)['parametri_selezionati'][0]
        self.assertEqual(row['stato'],'zona assente o troppo corta')

    def test_variante_lunghezza_non_applicabile(self):
        schema={'NAC':{'zones':{'2131':{'params':[{'extra_name':'BTEL_AAP_ON_OFF','pos':'04','mask':'80','zoneLength':2}]}}}}
        p=self.write('schema.json',json.dumps(schema))
        row=backup_audit(self.write('backup.nac','2131=80'),p)['parametri_selezionati'][0]
        self.assertEqual(row['stato'],'variante lunghezza non applicabile')

    def test_blocca_ui_di_firmware_diverso(self):
        with self.assertRaises(ValueError):ui_audit(self.write('fake.tar.gz','non un firmware'))

    def test_blocca_immagine_rootfs_diversa(self):
        with self.assertRaises(ValueError):rootfs_audit(self.root,self.write('fake.fsn','non una rootfs'))

    def test_blocca_componenti_rootfs_alterati(self):
        for name in ROOT_FILES:
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'alterato')
        with self.assertRaises(ValueError):rootfs_audit(self.root)

if __name__=='__main__':unittest.main()
