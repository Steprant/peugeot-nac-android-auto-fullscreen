# Procedura del prototipo coordinato

Revisione 3 del 30 ottobre 2026. I comandi lavorano esclusivamente su copie nel PC, salvo la futura prova DHU, indicata come non eseguita. Non è una procedura di installazione o flash sulla vettura.

## Ingressi

Servono Python 3.9 o successivo e i file originali del pacchetto 44.07.33.32_NAC-r0, UpdateID 001315031692686757. Le prove sono state eseguite con Python 3.12.14 su Linux x86_64.

Mantenere i percorsi originali dentro rootfs_estratta. Il generatore richiede:

    usr/lib/ovip/AAuto/libAAutoHMILib.so.1.0.0
    usr/lib/ovip/HMIInternal/HMIInternalApplication/libHMIInternalApplication.so.1.0.0

Il QML originale è INTERNET_0033SkinLogic.qml, estratto da media/datastore/ui/HMIApplications/AAuto/qml/AAutoHMILib/ nelle risorse UI. Le prove richiedono anche i componenti indicati in confronto_NAND_eMMC.json.

Preparazione e decifratura delle copie sono descritte nella procedura v2 e nelle fonti. Non utilizzare montaggi MTD o dispositivi della vettura. Il generatore controlla gli SHA256 esatti delle librerie, del QML e del piano.

## Generare le copie

Usare una nuova destinazione locale:

    python patch_fullscreen_lab.py prepare \
      --rootfs rootfs_estratta \
      --ui-file INTERNET_0033SkinLogic.qml \
      --output candidato_offline

Tutti gli ingressi sono verificati prima di creare la cartella. Nessun originale viene modificato.

| File prodotto | Intervento |
|---|---|
| aauto_geometry_and_crop.offline.so | Rettangolo Android Auto, limite di larghezza e ritaglio |
| sidebars_with_native_focus.offline.so | Consenso alle fasce condizionato al focus Android Auto |
| AAutoScreen.candidate.qml | Origine e larghezza della sola schermata Android Auto |
| cfg.candidate | Profilo video di laboratorio |
| DHU_1920x720.ini | Futuro test desktop con telefono |
| bundle_manifest.json | Hash, ripristino locale e verifiche mancanti |

I nomi non coincidono con i file di sistema. Non viene generata una struttura SWL o una chiavetta di aggiornamento. installable e vehicle_tested restano falsi nel manifesto.

## Profilo video

Il cfg candidato contiene esattamente:

    readFromFile=true
    screenWidth=1920
    screenHeight=1080
    widthMargin=0
    heigthMargin=360
    videoDPI=240
    videoResolution=1080p

/home/root/cfg è il percorso letto dal firmware, non un percorso USB. Questa informazione identifica il lettore studiato e non autorizza una scrittura sul NAC.

Il fotogramma è 1920×1080, con 180 pixel di margine sopra e sotto. La superficie si trova a y=-180 e il contenitore visibile misura 1920×720. Il DPI 240 corrisponde al DPI_HD nel firmware; la leggibilità fisica resta da verificare.
screenHeight è qui l'altezza del fotogramma, 1080. Il valore 720 nei precedenti esempi era uno stimolo del parser.

La chiave heigthMargin conserva il refuso del firmware. Non aggiungere commenti o righe vuote al cfg. Il controllo sintattico non certifica il decoder.

## Modifiche native

L'adattatore Android Auto espande il rettangolo WHD originale x=320, y=0, w=1280, h=720. Il QML amplia la propria geometria soltanto nel caso WHD 1920×720. ScreenAreas.ini e i componenti QML condivisi non cambiano.

Il gestore delle fasce usa topMost e isFocused del monitor nativo. L'enum 0 deriva dalla registrazione di INTERNET_0033, non dal numero contenuto nel nome di una zona. Sono riconosciuti soltanto INTERNET_0033, INTERNET_0033Skin e INTERNET_0033SkinLogic. Un nome sconosciuto, un contesto senza focus o un monitor assente conserva il risultato di fabbrica. Le chiamate originali del sistema mostrano o nascondono entrambe le fasce.

Il ritaglio viene corretto soltanto con area 0,0,1920,720, fotogramma 1920×1080, margine orizzontale nullo e verticale 360. L'offset -178 prodotto dall'aritmetica originale nel caso di prova diventa -180.

I blocchi sostituiti saltano parte della diagnostica testuale. Prologhi, epiloghi, canary e sezioni di unwinding restano invariati. Le eccezioni dell'applicazione completa non sono collaudate.

## Riprodurre le prove

Creare e attivare un ambiente virtuale dedicato, poi:

    python -m pip install -r requirements-laboratorio.txt
    python -m pip install -r requirements-qt-laboratorio.txt

Esempio POSIX per le 53 prove:

    NAC_LAB_ROOTFS=rootfs_estratta \
    NAC_LAB_UI_FILE=INTERNET_0033SkinLogic.qml \
    python -m unittest discover -s . -v

Con ingressi o PyQt5 mancanti alcuni test vengono saltati. Un esito con test saltati non riproduce il risultato completo.

Esecuzioni separate:

    python prove_native_fullscreen.py --rootfs rootfs_estratta
    python prove_qml_fullscreen.py \
      --rootfs rootfs_estratta --ui-file INTERNET_0033SkinLogic.qml

Il primo esegue percorsi ARM con alcuni ingressi Qt e delle zone simulati. La configurazione dell'input esegue i rami nativi del setter video, saltando l'invio intermedio dei metadati. I callback touch vengono arrestati prima della consegna finale a Cinemo. SurfaceManager è verificato nel percorso geometrico predefinito, non nel compositore completo.

Il secondo usa Qt desktop 5.15.19, non Qt 5.5 NAC. Verifica gli hash dei genitori QRC originali, simula i tipi nativi mancanti e rimuove tre binding Separator del footer nascosto soltanto dalla fixture desktop. Non cambia tali risorse nel candidato. Non verifica il rendering video o il touch fisico.

Riassemblaggio facoltativo delle sorgenti pubblicate:

    python -m pip install -r requirements-asm-laboratorio.txt
    python verifica_asm.py

## Ripristino locale

Creare nuovi file per ciascun componente:

    python patch_fullscreen_lab.py restore-copy \
      --component aauto_geometry_and_crop \
      candidato_offline/aauto_geometry_and_crop.offline.so \
      aauto_originale.restored.so

    python patch_fullscreen_lab.py restore-copy \
      --component sidebars_with_native_focus \
      candidato_offline/sidebars_with_native_focus.offline.so \
      interfaccia_originale.restored.so

    python patch_fullscreen_lab.py restore-copy \
      --component aa_qml \
      candidato_offline/AAutoScreen.candidate.qml \
      AAutoScreen_originale.restored.qml

La ricostruzione deve riprodurre gli hash originali, verificati byte per byte nei test. Nessun file esistente viene sovrascritto.

Questo ripristina file nel PC, non recupera una centralina. Non ripristina un cfg runtime che non è stato acquisito: il file potrebbe già esistere nella specifica auto.

## Prova DHU futura non eseguita

Il profilo DHU permette una verifica separata con il telefono collegato al PC, il server di unità principale Android Auto abilitato sul telefono e il DHU installato secondo Google:

    adb forward tcp:5277 tcp:5277
    desktop-head-unit -c candidato_offline/DHU_1920x720.ini

Questa prova non è stata effettuata. Un suo eventuale successo non dimostrerebbe il funzionamento del decoder e del compositore NAC.

## Condizioni per una prova fisica

Occorrono numero ricambio e revisione hardware del NAC, pannello e calibrazione effettivi. Vanno acquisiti in lettura l'eventuale cfg preesistente e le regole di /opt/ui/UIFwkTelecoding/hmi-telecoding.ini, che SurfaceManager può applicare alle superfici.

Servono accesso reversibile al filesystem, copie complete originali dell'unità e un recupero già provato sul medesimo hardware. Non è dimostrato un modo di produrre un aggiornamento modificato accettato dal NAC.

Su banco vanno verificati negoziazione dello Xiaomi, decoder 1080p, composizione, tocchi ai bordi, focus e transizioni, clima, telecamera, sensori, audio, sospensione e riconnessione. Il contesto esteso deve cedere alle schermate prioritarie. Queste funzioni non sono state collaudate dalla ricerca offline.

Finché mancano tali verifiche, il candidato non soddisfa la compatibilità preventiva richiesta dall'utente. Nessuna installazione sulla vettura è stata eseguita. La fase fisica richiede la relativa autorizzazione espressa.
