# Procedura per copie locali del firmware

Revisione 2 del 30 ottobre 2026. Questa procedura prepara e verifica una patch parziale su un PC. Non installa nulla sul NAC.
Il risultato conserva le dimensioni fornite al blocco geometrico Android Auto; non assegna le fasce laterali all'applicazione.

## Compatibilita verificata

Archivio 44.07.33.32_NAC-r0, UpdateID 001315031692686757. Per le immagini NAND ed eMMC dello stesso archivio sono identici i sette componenti elencati in confronto_NAND_eMMC.json.
L'immagine eMMC ext4 ricomposta misura 768282624 byte e ha SHA256 e8beccec9d51aac43e2e8130077456621c6410e15684f9980bf752960bab56ac, corrispondente a HashList.ini.
E stata letta con debugfs senza opzione di scrittura e senza montare filesystem.
Questo confronto non identifica il numero ricambio, la revisione o la calibrazione dell'auto dell'utente.

La libreria di ingresso deve essere esattamente usr/lib/ovip/AAuto/libAAutoHMILib.so.1.0.0, di 518940 byte, con SHA256:

```text
729c8f66ad835ce6fb62833311e635474a32213dfac0545257f925da29a98585
```

Il generatore rifiuta altri hash, anche se il nome della versione coincide. Non usare il candidato su altre versioni.

## Preparazione del PC

Per generare una copia della patch basta Python 3.9 o successivo, senza pacchetti aggiuntivi.
Per l'emulazione e l'audit QRC servono pyelftools e Unicorn. Le prove sono state eseguite con Python 3.12.14, pyelftools 0.33 e Unicorn 2.1.4.
Installare le dipendenze in un ambiente virtuale dedicato:

```bash
python -m venv .venv
```

Attivare l'ambiente secondo il proprio sistema operativo, poi:

```bash
python -m pip install -r requirements-laboratorio.txt
```

Usare una cartella di lavoro locale. Gli ELF non sono inclusi in questo ZIP: ricavarli da una copia del pacchetto indicato, secondo i riferimenti e la preparazione nel README. Non collegare l'auto per questi passaggi.

## Generazione e ripristino della copia

Copiare la libreria originale nella cartella di lavoro con nome originale.so. Conservare separatamente la copia originale.

```bash
python patch_laboratorio.py inspect originale.so
python patch_laboratorio.py prepare originale.so candidato.offline.so
python patch_laboratorio.py restore-copy candidato.offline.so originale.restored.so
```

La destinazione deve essere nuova; il programma rifiuta di sovrascrivere file. Il suffisso offline.so o restored.so evita di produrre direttamente il nome della libreria di sistema.
Le operazioni creano soltanto copie locali. Il file di ingresso non viene modificato.

La modifica sostituisce l'istruzione ARM BLS a indirizzo ELF 0x37d8c65c con B, con identica destinazione 0x37d8c678. L'offset nel file e 0x3c65c. I quattro byte passano da 05 00 00 9a a 05 00 00 ea: un solo byte cambia effettivamente, a offset 0x3c65f.
Il confronto che precede il salto resta nel file, ma il ramo che limita e ricentra la larghezza viene sempre saltato.

SHA256 atteso della copia candidata:

```text
c4f9f14e9789ec788983333cb6bd76104eefcc0ac9993e3f5dbe8229d2dd0a9f
```

restore-copy rifiuta altri hash e deve riprodurre esattamente l'hash originale. Il confronto di tutti i byte e passato nella ricerca. Questo e un ripristino di file sul PC, non una procedura di recupero di una centralina.

## Riproduzione delle prove ARM

Sia rootfs_estratta la cartella che conserva i percorsi usr/lib delle librerie elencate in confronto_NAND_eMMC.json. Per il laboratorio bastano i cinque plugin/librerie coinvolti; il servizio e ScreenAreas sono usati nel confronto statico.

```bash
python prove_arm.py --rootfs rootfs_estratta
python audit_qrc.py rootfs_estratta
```

Per eseguire tutti i trenta test, impostare la variabile NAC_LAB_ROOTFS sul percorso della cartella. In una shell POSIX:

```bash
NAC_LAB_ROOTFS=rootfs_estratta python -m unittest discover -s . -v
```

Senza quella variabile le prove che richiedono gli ELF vengono indicate come saltate: un esito con test saltati non riproduce il risultato completo allegato.

Il laboratorio esegue istruzioni del firmware reale con memoria simulata e sostituti Python limitati per QFile, QTextStream, QString e QMap. Non avvia Linux, Qt, Wayland o l'applicazione Android Auto completa. Non testa decoder H264, GPU, negoziazione USB, touchscreen o priorita tra schermate. L'allocazione e il rilascio Qt sono semplificati; le stringhe dei casi di prova sono ASCII. Una chiamata non prevista interrompe l'esecuzione.

## Configurazione interna

Il firmware legge /home/root/cfg al momento della costruzione di CAAPVideoScreenSize. Questa e una posizione nel filesystem del NAC, non sulla chiavetta USB.
L'emulazione del parser e del ramo in setHMIVisibleArea conferma il flag readFromFile=true e le chiavi screenWidth, screenHeight, widthMargin, heigthMargin, videoDPI e videoResolution. Gli enum osservati sono 480p=1, 720p=2, 1080p=3.
I valori numerici in esito_emulazione_ARM.json sono stimoli di laboratorio. Non costituiscono un profilo da installare o una prova di supporto del decoder.

config_laboratorio.py puo controllare un file di testo locale:

```bash
python config_laboratorio.py check esempio_locale.cfg
```

Per generare il testo da un JSON locale con esattamente le sette chiavi, usare render. Impostare readFromFile come stringa "true". Il programma scrive soltanto sullo standard output:

```bash
python config_laboratorio.py render parametri_di_prova.json
```

Il controllore rifiuta chiavi sconosciute o duplicate, spazi nei valori numerici, flag diversi da true, righe vuote e commenti. Nel blocco originale non si vede una validazione completa delle righe: il codice accede al secondo elemento dopo lo split. Una chiave errata puo produrre zero, e una risoluzione non riconosciuta resta sul valore iniziale 480p. Non affidarsi al lettore per rilevare errori.

## Cosa resta da sviluppare

La patch di un byte non modifica il rettangolo ScreenAreas.ini, il binding x/larghezza di Screen.qml, la maschera LayerWidget o le fasce laterali con il clima. Nel test con l'area centrale originale non amplia nulla.
Il candidato successivo deve coordinare questi elementi limitatamente al contesto INTERNET_0033 e alle sue transizioni di focus. La verifica deve comprendere i limiti reali di SurfaceManager, il sistema di input e l'uscita immediata verso le funzioni del veicolo.
Non viene distribuita una modifica globale di ScreenAreas.ini o del componente Screen.qml condiviso, ne una soppressione indiscriminata dei pannelli clima.

Un successivo esperimento fisico richiede un NAC della stessa revisione identificata, display compatibile, cablaggio e alimentazione da banco adeguati, backup originali dell'unita e un accesso di recupero gia provato. Una configurazione .nac non sostituisce l'immagine delle memorie.
Servono acquisizione delle dimensioni offerte al telefono, validazione del decoder e delle coordinate touch e prove di clima, telecamera, sensori, audio, riconnessione e riavvio. La distribuzione firmata e l'accesso reversibile al filesystem restano irrisolti.
Nessuna scrittura, flash o installazione sul veicolo e autorizzata da questa procedura. Per quella fase valgono la verifica preventiva di compatibilita e l'autorizzazione espressa richieste dall'utente.
