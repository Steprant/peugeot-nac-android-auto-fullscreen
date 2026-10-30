# Peugeot 2008 e NAC analisi offline

Questo archivio accompagna il rapporto tecnico del 30 ottobre 2026.
La revisione 2 contiene una patch PARZIALE per copie locali, un laboratorio di emulazione ARM e gli strumenti di analisi iniziali.
Non e uno sblocco fullscreen completo e non e un pacchetto da copiare su una chiavetta per aggiornare l'auto.
Gli strumenti non interagiscono con USB, CAN, UDS, servizi del veicolo o rete. Solo patch_laboratorio.py crea un nuovo file locale su richiesta esplicita; non sovrascrive file esistenti.

## Risultato della ricerca

Nel pacchetto 44.07.33.32_NAC-r0 sono stati identificati:

- Il limite centrale in `usr/share/ovip/ScreenManager/ScreenAreas.ini`.
- Una superficie WHD con x=320, y=0, larghezza 1280 e altezza 720 anche nello stato FULLSCREEN.
- I pannelli laterali QML da 320 pixel e la schermata Android Auto che occupa il proprio contenitore.
- Nella libreria `usr/lib/ovip/Android/libAndroidAutoAppLogic.so`, un lettore di configurazione del percorso locale `/home/root/cfg` e parametri di geometria video.

Nell'approfondimento sono stati inoltre identificati:

- Un limite esplicito a 1280 pixel in AAutoHMIUIFwkAdaptor::getVisibleArea(), nella libreria della sola applicazione Android Auto.
- Un binding WHD x=320 e larghezza=ScreenInfo.width-640 nella risorsa Qt UiKit/Screen.qml.
- Il clipping WHD del contenitore FullscreenContentScreen.

E stata sviluppata una modifica di un solo byte che salta il limite esplicito nella libreria Android Auto. Nell'emulazione del blocco originale, un ingresso di prova (0,0,1920,720) resta (0,0,1920,720); l'originale restituisce (320,0,1280,720).
Con l'ingresso centrale originale (320,0,1280,720), anche il candidato restituisce ancora il rettangolo centrale. Questa prova negativa dimostra perche la patch DA SOLA non basta.
Non e dimostrato che creare il file cfg o cambiare un rettangolo sia sufficiente a ottenere un fullscreen funzionante.
Il file ScreenAreas.ini e i pannelli di stato riguardano piu contesti del sistema. Non viene proposta una modifica globale sul veicolo.
Mancano accesso reversibile al filesystem dell'unita, installazione verificata, coordinamento di superficie e input e test delle funzioni originali.

## File inclusi

`audit_statico.py`: strumento Python senza dipendenze esterne.

`test_audit_statico.py`, `test_laboratorio.py` e `test_esiti.txt`: trenta test passati, di cui dieci iniziali e venti aggiunti. Comprendono prove sui blocchi ARM originali e sulle protezioni del generatore. Non testano il NAC completo.

`patch_laboratorio.py`: ispezione, generazione di una nuova copia candidata e ripristino di una copia. Richiede gli hash esatti del firmware studiato. Il ripristino locale ha riprodotto tutti i byte originali.

`prove_arm.py` e `esito_emulazione_ARM.json`: esecuzione limitata del parser, dei getter, del ramo di override e della coda geometrica in Unicorn. Qt e file di configurazione sono simulati; il sistema operativo e il protocollo Android Auto non vengono eseguiti.

`config_laboratorio.py`: controlla la sintassi o stampa una configurazione di laboratorio; richiede sette chiavi esatte. Non scrive nel filesystem del NAC e non certifica i valori scelti.

`audit_qrc.py` e `esito_qrc_reale.json`: lettura delle risorse Qt incorporate nei due plugin esatti, senza modifiche o estrazione di sorgenti nell'archivio allegato.

`manifesto_patch.json`: hash, posizione dell'istruzione, differenza di un byte, ambito e limiti del candidato.

`confronto_NAND_eMMC.json`: confronto di sette componenti dalle due immagini del pacchetto. Sono identici, compresi librerie Android Auto, UiKit, ScreenManager, configurazione delle aree e servizio di proiezione. L'hardware dell'auto resta da identificare.

`PROCEDURA_LABORATORIO.md`, `requirements-laboratorio.txt` e `sviluppo_patch_offline.json`: procedura completa, dipendenze e nuovi riscontri verificabili.

`esito_ui_reale.json` e `esito_rootfs_reale.json`: esecuzioni sui componenti reali decifrati del pacchetto analizzato.

`integrita_moduli.json`: SHA256 e dimensioni di cinque componenti decifrati, confrontati con il manifesto del pacchetto.

`esito_backup_pubblico_e2008.json`: prova del decoder su un esempio pubblico. NON e un backup dell'auto di Stefano e non deve essere ripristinato sulla sua unita.

`reverse_engineering.json`: simboli, indirizzi statici, origine del pacchetto e limiti delle conclusioni.

`fonti.json`: riferimenti esterni e commit esaminati.

Non sono inclusi firmware, binari originali o modificati Continental, sorgenti QML, certificati o chiavi. Il candidato viene ricostruito soltanto da una copia originale fornita localmente.

## Uso degli strumenti

Serve Python 3.9 o successivo; le nuove prove sono state eseguite con Python 3.12.14. Aprire il terminale nella cartella dell'archivio estratto.
Per patch, emulazione e risorse Qt leggere prima PROCEDURA_LABORATORIO.md. Gli esempi successivi riguardano l'audit iniziale.

UI gia decifrata:

```bash
python audit_statico.py ui ui-app.dec.tar.gz --manifesto HashList.ini
```

Rootfs gia estratta:

```bash
python audit_statico.py rootfs rootfs-extracted --immagine rootfs.dec.fsn
```

L'immagine e opzionale. Se fornita, il suo hash viene verificato. Gli hash dei tre componenti esaminati vengono comunque verificati.
Hash diversi interrompono l'analisi: non sono una prova di guasto, possono indicare una versione diversa.

Backup di configurazione locale:

```bash
python audit_statico.py backup backup_originale.nac --schema nac.json
```

Usare lo schema `Configuration/nac.json` del repository Ludwig V al commit indicato in fonti.json.
Il decoder applica la convenzione `pos - 4` verificata nel sorgente pubblico ParamsForm.cs.
Legge otto parametri selezionati e non attribuisce ai flag VIDEO_CODING dimensioni che lo schema non documenta.

Test:

```bash
python -m unittest discover -s . -v
```

Per includere le prove sugli ELF reali occorrono le dipendenze e NAC_LAB_ROOTFS, come descritto nella procedura di laboratorio. Senza questa variabile quelle prove vengono saltate.

I risultati dell’audit vengono scritti soltanto sullo standard output. Per conservarli, si puo reindirizzare l'output a un nuovo file JSON.
Gli input non vengono modificati.

## Preparazione dei file per la riproduzione tecnica

La ricerca ha usato l'archivio pubblico indicato nella fonte 11, identificato da UpdateInfo.xml come 44.07.33.32_NAC-r0, UpdateID 001315031692686757.
Per riprodurre l'analisi occorrono copie locali dei relativi componenti, estratte in una cartella di lavoro.

Il progetto della fonte 5 descrive la decifratura OpenSSL e pubblica la chiave denominata `Firmware_Keys/WAVE4/44.07.33-32-r0.key`.
Non e una chiave di firma per produrre aggiornamenti accettati dal veicolo.
Decifrare sempre su copie locali, in file di destinazione nuovi. Il nome `.tar.gz` del componente cifrato non significa che sia gia un archivio gzip leggibile.

Per la rootfs NAND sono stati decifrati separatamente i file `rootfs.fsn`, `rootfs.fsn01`, `rootfs.fsn02` e `rootfs.fsn03`.
I risultati sono stati concatenati in quest'ordine. La dimensione risultante e 381181952 byte.
L'hash atteso e registrato in integrita_moduli.json.

L'immagine UBIFS e stata estratta con UBI Reader 0.8.16, con output in una cartella locale. Non e stato utilizzato un montaggio di dispositivi MTD.
Lo script `mount_ubifs_nac.sh` del progetto originale contiene operazioni su dispositivi MTD: non e necessario per questi strumenti.

La corrispondenza degli hash dei moduli con HashList.ini non certifica la firma del pacchetto o la sua installabilita.
La verifica standard locale di MediaVersion.ini ha restituito un errore di digest. La ricerca non attesta l'autenticita crittografica globale della distribuzione.

## Cosa non e stato testato

Nessuna connessione al NAC reale, nessuna sessione Android Auto con lo Xiaomi, nessun avvio dell'applicazione completa o del sistema NAC, nessuna scrittura sulla vettura e nessuna prova di recupero di una centralina.
Sono state eseguite istruzioni ARM originali in un ambiente parziale con chiamate Qt simulate, ed e stata verificata la ricostruzione byte per byte della copia locale. Queste prove non dimostrano il fullscreen sul veicolo.
Restano da acquisire hardware e parametri negoziati dalla specifica auto, e da verificare superficie, input e priorita delle funzioni originali.

La procedura di sviluppo e i vincoli di ripristino sono descritti nel rapporto. Nessuna istruzione di scrittura sulla centralina viene fornita da questo archivio.
