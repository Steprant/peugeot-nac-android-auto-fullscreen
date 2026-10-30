# Accesso al NAC e firma degli aggiornamenti

Revisione 4 del 30 ottobre 2026. Questa estensione esegue il nuovo incarico di ricerca sull'installazione senza chiave OEM. Il prototipo fullscreen della revisione 3 resta invariato.

**Esito: percorso alternativo condizionato, ancora da verificare. Nessuna installazione dimostrata.** L'assenza della chiave OEM blocca la ricostruzione ordinaria di un aggiornamento firmato. Non dimostra che ogni modifica temporanea a sistema avviato sia impossibile. Manca un accesso privilegiato verificato sulla specifica unità e manca il recupero su banco.

## Risultati nuovi

- Sono stati decifrati e analizzati i sei contenitori kernel del pacchetto esatto: principale, SWL e TSW, ciascuno NAND/eMMC. I loro hash coincidono con HashList.ini. Le immagini del kernel decompresse sono identiche e contengono Linux 3.10.53 con suffisso del produttore, build del 21 agosto 2023. I dodici stream LZOp superano i checksum; la configurazione IKCONFIG supera anche il CRC gzip.
- La configurazione contiene `# CONFIG_MODULE_SIG is not set` e `CONFIG_UNION_FS=m`. Ciò non concede il privilegio di caricare moduli. Non dimostra l'assenza di ogni controllo a livello utente.
- L'initramfs principale legge `init=` dalla command line e passa il risultato a `switch_root`. Contiene anche una funzione di shell di recupero invocata in caso di errore di mount. Non è provato che il bootloader consenta argomenti controllati, che UART accetti input o che il recupero sia utilizzabile senza danneggiare il sistema. Su eMMC un ciclo attende prima che la partizione esista: una partizione assente non porta automaticamente alla shell.
- La configurazione `/etc/passwd` selezionata nell'immagine chiude gli account rilevanti con password bloccata e `/bin/false`. `stdOVIPuser` ha UID 0 in questa variante; il nome non equivale a un utente non privilegiato. Le varianti alternative del file non sono la configurazione selezionata.
- Un target debug cita SSH, ma né il demone né il relativo servizio sono presenti nei percorsi esaminati. Il server SEM esiste; il comando `system()` diretto individuato usa una stringa costante per la cattura dello schermo. Non è stata individuata una shell arbitraria attraverso questo percorso. Porte, raggiungibilità e autenticazione runtime non sono attestate.
- Lo script `enable_unionfs.sh` sostituisce il collegamento `/sbin/init`: è una modifica persistente dell'avvio. Non viene proposto come primo esperimento reversibile. Un bind mount temporaneo richiederebbe già privilegi e una prova separata del caricamento della risorsa.
- `HABInfo` e il bootloader HW2019_HD contengono riferimenti al secure boot HAB. Il valore dei fuse della scheda reale resta sconosciuto. La presenza del codice non dimostra uno stato secure boot chiuso oppure aperto.
- Il percorso nativo di aggiornamento richiede esito 1 da `secVerifySignature`. I flag arrivano a `CMS_verify` come `0x2040`: non sono impostati i flag che saltano verifica del contenuto, attributi firmati o certificato del firmatario.

## Riprodurre sul PC

Usare Python 3.10 o successivo e un ambiente virtuale, come richiesto da pyelftools 0.33. Le prove sono state eseguite con Python 3.12.14. Installare `requirements.txt` di questa cartella. `prove_firma_arm.py` riusa il caricatore ELF in `../prove_arm.py`, perciò conservare la struttura dello ZIP. Non serve PyQt5 per i 25 nuovi test.

Servono una rootfs NAND originale estratta e la directory dei moduli **decifrati** contenente `AUTO/1010101`, `AUTO/1010102` e `AUTO/101010a`. I file originali non sono inclusi. I percorsi, dimensioni e SHA256 obbligatori sono in `firmware_pins.json`. Gli strumenti rifiutano file diversi.

```bash
python -m pip install -r requirements.txt
python audit_accesso.py --rootfs ROOT_ESTRATTA --decrypted MODULI_DECIFRATI > audit.json
python prove_firma_arm.py --rootfs ROOT_ESTRATTA > firma.json
python test_installazione.py --rootfs ROOT_ESTRATTA --decrypted MODULI_DECIFRATI
```

L'audit risolve i link assoluti nel contesto della root estratta. Non legge `/etc/passwd` del computer ospite per interpretare il link della centralina. Analizza CPIO senza creare link o estrarre file; valida limiti e checksum LZOp prima di leggere IKCONFIG. La cartella estratta deve rimanere stabile durante la lettura; il risolutore non difende da un processo che la modifica contemporaneamente.

## Prove eseguite

Sono passati **25 nuovi test, nessuno saltato**, come riportato in `test_esiti_v4.txt`. Comprendono corruzione e troncamento dei contenitori, limiti di decompressione, attraversamento dei percorsi, link, integrità degli ingressi, i sei kernel e frammenti ARM originali.

Unicorn esegue la guardia di aggiornamento, il prologo che trasferisce gli argomenti e il frammento che costruisce i flag CMS. `secInit`, `secVerifySignature`, il logger e `CMS_verify` sono sostituiti da stub espliciti. Gli esiti provano rami e argomenti, non la validità di una firma, una vulnerabilità, l'avvio Linux o l'accettazione del pacchetto sul NAC.

I 53 test della revisione 3 restano documentati come esecuzione precedente. Non sono stati rieseguiti in questa fase e non vengono sommati per suggerire una validazione integrata del sistema.

## Verifica MediaVersion

Sul PC, OpenSSL 3.0.13 restituisce ancora `content verify error` o `digest failure` nella verifica completa del MediaVersion.ini originale scaricato. Sono state provate le modalità CMS/SMIME, con e senza opzione binary. Gli attributi firmati risultano verificabili solo escludendo esplicitamente la verifica del contenuto. Questo controllo parziale **non autentica MediaVersion.ini** e non costituisce una soluzione.

Il digest del corpo estratto non coincide con l'attributo messageDigest; varianti comuni di fine riga, terminazione, spazi e BOM non hanno risolto la differenza. La causa resta aperta: non è dimostrato che il NAC rifiuti il pacchetto ufficiale. L'analisi dei flag della libreria target, che riporta OpenSSL 1.0.2k, è distinta dalle prove con OpenSSL 3 sul PC.

## Prova fisica successiva

Leggere `PROVA_BANCO_DA_ESEGUIRE.md`. `raccolta_lettura.sh` è soltanto una raccolta di stato **preparata e mai eseguita su un NAC**. Presuppone una shell ottenuta e autorizzata in modo indipendente; non ne fornisce una. Non legge OTP/fuse né chiavi e non modifica mount, servizi o file. Non è un'autorun USB e non va rinominato per renderlo tale.

Non sono inclusi installer SWL, pacchetti firmati, nuovi firmware, chiavi o binari proprietari. L'aggiramento del controllo di aggiornamento non è stato ottenuto.
