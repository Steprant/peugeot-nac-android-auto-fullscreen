<!-- Text snapshot of the revision 4 Italian report, 30 October 2026. -->
<!-- The original report diagram is described in the technical findings and its table. -->

# Peugeot 2008 Android Auto a schermo intero

Rapporto tecnico sul firmware 44.07.33.32_NAC-r0Revisione 4 del 30 ottobre 2026

Il prototipo fullscreen resta validato solo offline. La revisione 4 aggiunge l’analisi dei controlli di firma e dell’avvio, con 25 nuovi test superati. Non è stata individuata una procedura di installazione dimostrata sul NAC.

Il candidato estende il contenitore a 1920 × 720 e condiziona le fasce al focus Android Auto. I 53 test precedenti restano documentati. La nuova pista riguarda i parametri dell’avvio originale; il loro controllo sulla scheda reale, l’accesso privilegiato e il recupero restano da dimostrare [D3, D4].

### Sistema identificato

| Elemento | Identificazione e grado di verifica |
| --- | --- |
| Veicolo e telefono | 2008 GT del 2020, display da 10 pollici, Xiaomi 14 con Android 16 e USB. Dati forniti dall’utente. |
| Famiglia software | UpdateInfo.xml del pacchetto riporta NAC_EUR_WAVE4 e NAC_EUR_WAVE4_B0. Confermata la famiglia dell’archivio, non il codice hardware dell’unità installata [D1]. |
| Sistema operativo | Linux ARM a 32 bit, Qt Quick e Wayland. Verificati file di sistema, formato ELF e servizi nel firmware [D1]. |
| Hardware esatto | Numero ricambio, revisione, supporto NAND o eMMC e modello del pannello non acquisiti. Il pacchetto contiene varianti hardware diverse. La sola versione non identifica la scheda installata [D1]. |

### Architettura rilevante

Lo smartphone genera il contenuto di Android Auto. Sul NAC, AndroidAutoApp e la libreria di logica configurano il servizio di proiezione conn_AndroidAutoProjection.out. Il gestore delle schermate, l’interfaccia Qt e il sistema Wayland assegnano superfici, posizione e input. I pannelli di stato e clima sono componenti distinti dell’interfaccia Peugeot [D1].

La famiglia i.MX6 è riportata in una ricognizione hardware della comunità. La conclusione sul fullscreen deriva invece dai file del firmware analizzato e non richiede di assumere un particolare modello di processore [14, D1].

## Il vincolo nel sistema grafico

Il file /usr/share/ovip/ScreenManager/ScreenAreas.ini contiene una sezione WHD. Tutti e tre gli stati MINISTATUSBAR, STATUSBAR e FULLSCREEN assegnano un rettangolo con origine x=320, y=0, larghezza 1280 e altezza 720. Il nome FULLSCREEN indica quindi l’intera area centrale consentita dal gestore, non l’intero pannello panoramico [D1].

| Stato WHD | x | y | Larghezza | Altezza |
| --- | --- | --- | --- | --- |
| MINISTATUSBAR | 320 | 0 | 1280 | 720 |
| STATUSBAR | 320 | 0 | 1280 | 720 |
| FULLSCREEN | 320 | 0 | 1280 | 720 |

Schema ricostruito dai rettangoli e dai pannelli QML del firmware. Non è una cattura del veicolo né una simulazione del suo funzionamento [D1].

Nelle risorse QML, LWHDScreenUILogicZ5.qml e RWHDScreenUILogicZ5.qml hanno larghezza 320. Il pannello destro parte da x=1600. Entrambi caricano gruppi del climatizzatore. La loro posizione coincide con la divisione WHD da 1920 × 720 documentata da Stellantis [1, D1].

### La schermata Android Auto usa già il proprio contenitore

INTERNET_0033SkinLogic.qml usa FullscreenContentScreen. Il genitore Screen.qml impone x=320 e width=ScreenInfo.width−640 in WHD. Il candidato corregge questi binding soltanto nella schermata Android Auto e nel formato 1920 × 720. Nascondere le fasce, da solo, lascerebbe il contenuto centrale a 1280 pixel [D1, D3].

### Tre dimensioni da non confondere

Il pannello WHD è documentato come 1920 × 720. Il rettangolo FULLSCREEN trovato nel gestore è 1280 × 720. La documentazione WebPortal assegna alle proprie applicazioni 1280 × 620, con ulteriori aree di sistema. Quest’ultimo valore riguarda WebPortal e non costituisce una misura del flusso Android Auto negoziato dall’auto [1, D1].

## La configurazione interna di Android Auto

La libreria /usr/lib/ovip/Android/libAndroidAutoAppLogic.so contiene CAAPReadConfig. La disassemblazione ARM mostra che il costruttore di CAAPVideoScreenSize richiama readFile. Questa funzione costruisce un QFile sul percorso /home/root/cfg, legge righe separate dal carattere uguale e gestisce il flag readFromFile con il valore true [D1].

| Funzione nel binario analizzato | Indirizzo statico |
| --- | --- |
| CAAPReadConfig::readFile | 0x37ec0e60 |
| CAAPReadConfig::isFileConfigurationSupported | 0x37ebf38c |
| CAAPVideoScreenSize::CAAPVideoScreenSize | 0x37ebdf9c |
| CAAPVideoScreenSize::setHMIVisibleArea | 0x37ebd1b0 |

Gli indirizzi della tabella sono statici nel file ELF, non letture della memoria dell’unità. Indirizzi, offset e hash del candidato coordinato sono nel piano e nell’appendice di sviluppo [D1, D3].

Le funzioni e le stringhe associate riguardano screenWidth, screenHeight, widthMargin, heigthMargin, videoDPI e videoResolution. La grafia heigthMargin è quella presente nel binario. Sono presenti le denominazioni 480p, 720p e 1080p. È una pista concreta di configurazione interna, distinta dalla telecodifica UDS [D1].

### Cosa prova questa scoperta

L’esecuzione parziale conferma l’override dei valori quando il flag è attivo. La revisione 3 esercita anche crop e conversione touch nei percorsi nativi. Non dimostra avvio completo, decoder 1080p o invio degli eventi al telefono. conn_AndroidAuto.conf contiene soltanto l’opzione delle statistiche Cinemo [D1, D3].

### Il protocollo può descrivere un formato panoramico

Google documenta risoluzioni video e margini dichiarati dall’unità ricevente. Il telefono riceve i parametri della proiezione, non necessariamente le dimensioni fisiche del pannello. Il candidato usa un fotogramma 1920 × 1080 con margine verticale totale 360, lasciando contenuto 1920 × 720. Il decoder NAC e la negoziazione reale non sono collaudati [2, D3].

Il prototipo coordina configurazione, contenitore, fasce e crop in prove separate. Le conversioni native del touch non richiedono una patch nel caso esaminato. Il passaggio da questi percorsi al sistema completo deve essere verificato su banco, con calibrazione e priorità effettive [D3].

## Telecodifica e progetti pubblici

Sono stati esaminati il trasporto diagnostico arduino-psa-diag, le configurazioni e calibrazioni NAC, lo schema pubblico nac.json e il sorgente del configuratore di dragouf. Lo schema principale comprende 52 zone. Nessuno dei campi selezionati costituisce una procedura documentata di fullscreen per il firmware indicato [3–5, 10].

| Zona | Parametro o famiglia | Significato nello schema |
| --- | --- | --- |
| 2131 | BTEL_AAP_ON_OFF | Abilita Android Auto. Non definisce l’area del video. |
| 2133 | AAP_PRIVACY_ACTIVATI_1 | Modalità privata Android Auto. Non è un comando di espansione. |
| 2133 | LVDS_1_BWS_CONFIG_1 e LVDS_2_BWS_CONFIG_1 | Configurazione del collegamento video. Valori GMSL e larghezza di banda. |
| 2129 | VIDEO_CODING_1 e VIDEO_CODING_2 | Flag descritti come risoluzione video. Lo schema non fornisce una mappa verificata per espandere Android Auto. |
| 212C | CLIM_STATUSLINE | Menu del clima. Disattivarlo non dimostra il recupero delle fasce laterali. |
| 210F | ATT_DG_CHX_CAL_ECRAN | Tipo touchscreen, indicato come impostazione fittizia nello schema. Non usarlo per dedurre il pannello fisico. |

I campi VIDEO_CODING e LVDS riguardano anche la compatibilità del display. Non vanno modificati per tentativi. Il fatto che una voce contenga la parola risoluzione non dimostra che controlli il rettangolo riservato ad Android Auto [5, D1].

### Riscontri della comunità

VLud, autore degli strumenti, rispose nel 2021 a un proprietario di 2008 GT che il fullscreen era legato al firmware e non alla configurazione. È una testimonianza tecnica pertinente, precedente alla versione qui esaminata. L’analisi diretta dei file offre un riscontro specifico per la versione 44.07.33.32 [6, D1].

Un tentativo pubblicato nel 2024 riferisce di aver individuato una configurazione delle dimensioni ma di non riuscire a reinstallare l’applicazione modificata. Non fornisce una patch riproducibile né una prova sul veicolo. Le ricerche su GitHub, GitLab e nei forum non hanno prodotto un rilascio verificabile che soddisfi tutti i requisiti di questo caso [7].

## Fattibilità delle sei strade

| Intervento | Esito per questa ricerca |
| --- | --- |
| Telecodifica | Nessuno sblocco documentato individuato. I campi esaminati non sostituiscono il vincolo HMI. |
| Risoluzione Android Auto | Profilo 1920×1080 con margine verticale 360 esercitato nei percorsi nativi. Decoder e negoziazione sul NAC non collaudati. |
| Patch software NAC | Prototipo coordinato con guardie di geometria e hash. Prove ARM e Qt offline superate; installazione e collaudo fisico irrisolti. |
| Interfaccia Peugeot | Override del solo QML Android Auto e consenso alle fasce legato al focus. Nessuna modifica dei rettangoli o QML condivisi. |
| Protocollo di proiezione | Supporta margini e diversi rapporti. Un intermediario sul solo USB non governa il compositore Peugeot. |
| Alternativa con sistema originale | Un inseritore video può aggirare il ritaglio a valle del NAC, ma non è stata dimostrata un’integrazione completa e sicura per questa vettura. |

Il candidato coordinato è una fattibilità di ricerca verificata offline. Non è una procedura di installazione approvata per l’unità dell’utente, né una prova di conservazione delle funzioni del veicolo [D1, D3].

### Adattatori USB e modifiche del telefono

AAWireless dichiara esplicitamente che il proprio dispositivo non può abilitare il fullscreen se l’unità dell’auto non lo supporta. Il DPI può cambiare il layout all’interno dell’area disponibile. Non elimina il vincolo centrale rilevato nel NAC. Non emerge quindi una ragione tecnica per acquistarlo con questo obiettivo [8, D1].

La risoluzione dello schermo dello Xiaomi e il rettangolo del video sul NAC appartengono a livelli diversi. Una modifica lato telefono non costituisce una patch del gestore delle schermate Peugeot [2, D1, inferenza tecnica].

### Inserimento video sul display originale

Il manuale NavLinkz HDV-NAC12/HDA-NAC12 elenca 2008 II dal novembre 2019 con monitor panoramico. Il modello HDV aggiunge un ingresso HDMI. Lo stesso produttore segnala limiti di compatibilità CAN, audio separato e possibili assenze della grafica dei sensori. È un riscontro di una possibile architettura alternativa, non una soluzione Android Auto pronta e conforme a tutti i requisiti [9, pp. 6–7].

Per considerarla servirebbe una dimostrazione sullo stesso display e sistema: occupazione effettiva della larghezza, touch corretto, audio, accesso immediato al clima e priorità invariata a telecamera e sensori. In assenza di questi riscontri non viene raccomandato un kit da acquistare o installare [D1, criterio di accettazione].

## Verifiche eseguite e loro limiti

È stato letto via richieste HTTP Range l’indice del TAR pubblico da 6.312.212.480 byte. Sono stati identificati 192 elementi senza scaricare tutte le risorse dell’archivio. UpdateInfo.xml dichiara versione 44.07.33.32_NAC-r0, fornitore CONTINENTAL e UpdateID 001315031692686757 [11, D1].

| Componente decifrato | Byte | Esito SHA256 |
| --- | --- | --- |
| Rootfs NAND ricomposta | 381.181.952 | Coincide con HashList.ini |
| Sistema TSW NAND | 40.378.368 | Coincide con HashList.ini |
| Risorse UI | 7.266.668 | Coincide con HashList.ini |
| Risorse EFS | 8.423 | Coincide con HashList.ini |
| Dati della partizione scrivibile | 620.487 | Coincide con HashList.ini |

Gli hash completi sono in integrita_moduli.json. Si riferiscono ai moduli decifrati. I contenitori S/MIME cifrati hanno hash differenti. L’estrazione UBIFS è stata eseguita su file locali con UBI Reader 0.8.16, senza montare o scrivere dispositivi della vettura [5, 13, D1].

La verifica locale standard di MediaVersion.ini con OpenSSL ha restituito digest failure. Non è quindi attestata l’autenticità crittografica dell’intera distribuzione né la sua accettazione da parte del NAC. La corrispondenza degli hash dei moduli con il manifesto è un controllo distinto. Non viene consigliato di installare il pacchetto utilizzato per l’analisi [D1].

La chiave pubblicata per decifrare i componenti è diversa dalla chiave pubblica del certificato di firma Continental incluso. Il pacchetto collega inoltre MediaVersion.ini a HashList.ini, che elenca anche FirmwareList.ini. Poter leggere o ricostruire i file non fornisce quindi una firma ufficiale per un aggiornamento modificato [D1].

### Codice sviluppato

audit_statico.py esegue l’audit iniziale. patch_fullscreen_lab.py genera nuove copie delle due librerie e del QML, un cfg candidato e un profilo DHU. Controlla hash e istruzioni, rifiuta ingressi incompatibili e destinazioni esistenti. Non contiene accesso USB, CAN, rete o installazione [D2–D3].

Sono passati 53 test senza test saltati: audit, parser, patch e ripristino, percorsi ARM nativi e layout Qt desktop. Le tre sorgenti ARM pubblicate riassemblano esattamente il piano. Il backup diagnostico e2008 con 48 zone è un campione pubblico, distinto dalla configurazione dell’auto dell’utente [D2–D3].

Non eseguiti: avvio completo del NAC, sessione DHU con lo Xiaomi, acquisizione USB, decoder, banco o veicolo, installazione e recupero della centralina. Qt, monitor delle zone e parti dell’I/O sono simulati; il touch si arresta prima dell’invio a Cinemo. Nessuna funzionalità del veicolo è dichiarata collaudata [D3].

## Procedura successiva e ripristino

### Identificare e salvare prima di intervenire

Acquisire in lettura numero ricambio e revisione del NAC, codice calibrazione, modello del display e configurazione dell’unità. Un PC con diagnosi appropriata può servire per l’identificazione. Arduino e interfaccia CAN compatibile sono un’opzione prevista dai progetti pubblici, ma non sono necessari per usare gli strumenti offline allegati [3–5].

Un backup .nac salva parametri. Non è un’immagine completa della memoria e non garantisce il recupero dopo un firmware non avviabile. Prima di un esperimento serve un metodo di ripristino verificato sul medesimo hardware, con immagini e dati originali dell’unità [3–5, D1].

### Sviluppare su banco

Occorrono NAC della stessa revisione, display, cablaggio documentato, alimentazione da banco e accesso reversibile al filesystem. Il candidato modifica il solo QML Android Auto e due librerie; ScreenAreas.ini e i QML condivisi restano originali. Le regole runtime del gestore delle superfici vanno lette prima del collaudo [D3].

La prova deve verificare rapporto d’aspetto, coordinate touch ai bordi, connessione e riconnessione USB, audio e microfono, ritorno ai menu del clima, telecamera e sensori, sospensione e riavvio. Per iniziare sul veicolo occorrono prima compatibilità e ripristino dimostrati, oltre all’autorizzazione espressa prevista dal mandato [D1, requisiti di collaudo].

| Rischio concreto | Condizione per procedere |
| --- | --- |
| Modifica delle altre schermate | Limitare il cambiamento al contesto Android Auto e verificare le transizioni. |
| Clima o parcheggio non accessibili | Dimostrare accesso ai comandi e priorità di telecamera e sensori in tutte le transizioni. |
| Avvio fallito o aggiornamento respinto | Disporre di accesso di recupero e immagini originali già collaudati. |
| Aggiornamento ufficiale successivo | Riesaminare hash, percorsi, firma e comportamento. Non riutilizzare offset alla cieca. |

### Ostacoli ancora da superare

Restano irrisolti identità hardware, calibrazione effettiva, accesso reversibile, recupero e distribuzione accettata dal NAC. Le regole di SurfaceManager possono cambiare la geometria finale. Mancano negoziazione, decoder e priorità reali. Il candidato è riproducibile offline, non una soluzione già installabile [D3].

## Fonti e riproducibilità

Le fonti sono state consultate il 30 ottobre 2026. I riferimenti GitHub puntano ai commit esaminati. Le testimonianze nei forum sono attribuite ai rispettivi autori e non equivalgono a un collaudo.

[1] Stellantis. [WebPortal v1 Infotainment System e schema WHD](https://developer.groupe-psa.io/webportal/v1/overview/infotainment-system/)

[2] Google. [Desktop Head Unit sezione Video configuration](https://developer.android.com/training/cars/testing/dhu#video-configuration)

[3] Ludwig V. [arduino psa diag codice e protocollo UDS](https://github.com/ludwig-v/arduino-psa-diag/tree/c1409e60798f66bb63149505826170b5eb3c163f)

[4] Ludwig V. [Configurazioni e calibrazioni NAC RCC CIROCCO](https://github.com/ludwig-v/arduino-psa-nac_rcc_cirocco/tree/d21cc90b425f1464941f6343ec4a8e74b96ec5cd)

[5] Ludwig V. [Reverse engineering firmware schema nac json e chiavi](https://github.com/ludwig-v/psa-nac-firmware-reverse-engineering/tree/4ce14d0ff528cf4127dcf141463c3a946d6c8997)

[6] VLud. [Risposta del 24 ottobre 2021 post 2765 sul fullscreen della 2008 GT](https://www.forum-peugeot.com/Forum/threads/tuto-t%C3%A9l%C3%A9codage-et-calibration-dun-nac-rcc-cirocco-cmb_num-sans-diagbox-via-arduino.121767/page-93)

[7] Thomas03. [Esperimento personale e208 del 25 e 26 dicembre 2024](https://forums.automobile-propre.com/topic/mise-%C3%A0-jour-personnalis%C3%A9e-e208-64864/)

[8] AAWireless. [FAQ ufficiale sul supporto alla proiezione fullscreen](https://www.aawireless.io/en/support/topics-faq-aawireless/product-info)

[9] NavLinkz. [HDV NAC12 e HDA NAC12 manuale 8 ottobre 2026 pagine 6 e 7](https://www.navlinkz.de/artikel/HDA-NAC12/ins_eng_HDA-NAC12.pdf)

[10] dragouf. [Sorgente del configuratore ParamsForm cs e MainForm cs](https://github.com/dragouf/PSA-Arduino-NAC-RCC/tree/fbca1d80d3b7d764dec9d965a99b538202c2a3c5)

[11] Continental e PSA. [Pacchetto firmware pubblico analizzato fonte D1](https://ds4emloty3shq.cloudfront.net/CONTINENTAL/NAC_EU/ovip-int-firmware-version/PSA_ovip-int-firmware-version_44-07-33-32_NAC-r0_NAC_EUR_WAVE4.tar)

[12] Peugeot. [Pagina ufficiale dei componenti a sorgente aperto dei sistemi infotainment](https://www.peugeot.com/en/oss-source-codes.html)

[13] ONEKEY. [UBI Reader strumento di estrazione utilizzato versione 0 8 16](https://github.com/onekey-sec/ubi_reader)

[14] Marcheur45. [Ricognizione hardware NAC Wave 3 e Wave 4 del 2025](https://www.forum-peugeot.com/Forum/threads/diff%C3%A9rences-nac-wave-3-vs-wave-4.140505/)

### Evidenze prodotte in questa analisi

[D1] Analisi statica del pacchetto [11]. integrita_moduli.json conserva dimensioni e hash dei moduli; esito_rootfs_reale.json ed esito_ui_reale.json identificano i vincoli. reverse_engineering.json e sviluppo_integrato_v3.json distinguono riscontri, prove e limiti. Il confronto NAND/eMMC comprende nove componenti.

[D2] audit_statico.py e test_audit_statico.py; esito_backup_pubblico_e2008.json documenta il campione [4]. README.md e PROCEDURA_LABORATORIO.md spiegano la riproduzione. Il pacchetto allegato contiene codice e metadati: non include firmware completi, librerie, QML proprietari, certificati o chiavi.

## Il prototipo coordinato offline

La revisione 3 supera il precedente candidato di un solo byte: coordina area HMI, contenitore QML, fasce e ritaglio. Tutti gli interventi sono generati su nuovi file nel PC. Nessun NAC è stato acceso o modificato [D3].

| Componente | Intervento verificato offline |
| --- | --- |
| AAuto HMI | Rettangolo centrale 320,0,1280,720 esteso a 0,0,1920,720; rimosso il secondo limite di larghezza della stessa applicazione. |
| Schermata QML AA | Origine x=0 e larghezza 1920 solo con WHD 1920×720. Contenuto e maschera seguono il nuovo contenitore. |
| Gestore delle fasce | Nega il consenso alle fasce solo per Android Auto focalizzato. Le funzioni originali chiedono hide/show di entrambe le fasce. |
| Crop video | Per il solo profilo previsto, offset y=-180. L’aritmetica originale isolata nel test produce -178; gli altri casi mantengono il proprio valore. |

### Guardie e transizioni

La guardia nativa del rettangolo riconosce solo le coordinate inclusive QRect 320,0,1599,719. Il crop richiede area 0,0,1920,720, fotogramma 1920×1080, margine orizzontale nullo e verticale 360. Il QML non modifica i componenti condivisi Screen.qml o FullscreenContentScreen.qml, né ScreenAreas.ini [D3].

Il gestore delle fasce usa topMost(enum 0), isFocused e un nome esatto tra INTERNET_0033, INTERNET_0033Skin e INTERNET_0033SkinLogic. L’enum 0 deriva dalla registrazione nativa di AA. Nei casi provati, uscita dal focus o passaggio al clima ripristinano le richieste per entrambe le fasce. Nomi sconosciuti e monitor assente conservano la decisione originale [D3].

### Compatibilità e modifica dei binari

Il generatore accetta soltanto SHA256, dimensioni e istruzioni originali del piano. Nella libreria AA cambiano 273 byte; nel gestore HMIInternal, 239. Parte del logging testuale viene sostituita. Prologhi, epiloghi, canary e sezioni ARM di unwinding restano originali; ciò non equivale a collaudare eccezioni e sistema completo [D3].

Il QML amplia anche il placeholder AA. Con primo utilizzo o rendering inattivo la maschera resta a zero nei casi desktop; la transizione reale richiede banco. La corrispondenza dei file del pacchetto non identifica l’hardware installato nell’auto [D3].

## Video, touch e prove riprodotte

Il profilo candidato usa screenWidth=1920, screenHeight=1080, widthMargin=0, heigthMargin=360, videoDPI=240 e videoResolution=1080p, con readFromFile=true. La grafia heigthMargin è quella del firmware. screenHeight indica qui l’altezza del fotogramma codificato, non i 720 pixel visibili [D3].

I margini totali sono divisi in 180 pixel sopra e sotto. Con la superficie a y=-180, il pannello espone 1920×720. Il DPI 240 corrisponde al valore DPI_HD nel firmware. La leggibilità fisica e il supporto effettivo del decoder restano da verificare [2, D3].

| Prova | Esito e limite |
| --- | --- |
| Layout QML | WHD 1920×720: contenitore, contenuto e maschera passano da 1280 a 1920. HD, SD e formati WHD diversi provati mantengono il layout originale. |
| Area nativa e fasce | Funzione getVisibleArea eseguita con getter Qt simulato. Il percorso nativo delle fasce emette richieste hide/show per due schermate simulate. |
| Touch nativo | Setter del formato input, callback Wayland down/motion e conversioni originali: angoli, frazioni e due identificativi. Arresto prima dell’invio a Cinemo. |
| Superficie predefinita | applySizeDefault e setter SurfaceData producono 0,-180,1920,1080. Non viene eseguito l’intero compositore Wayland. |
| Integrità e ripristino | 53 test superati, nessuno saltato. Tre sorgenti ARM riassemblate uguali al piano; librerie e QML ripristinati byte per byte. |
| NAND ed eMMC | Nove componenti del pacchetto sono identici. I percorsi ARM del prototipo danno lo stesso esito sui componenti di entrambe le immagini. |

### Quanto viene simulato

Unicorn esegue codice ARM estratto dai file con ingressi Qt e monitor delle zone controllati. Il crop è provato per frammenti, senza l’intero percorso marca/carline. Nel setter input viene saltato l’invio intermedio dei metadati alla piattaforma. Le coordinate Wayland locali alla superficie vengono convertite sottraendo metà del margine: y=180…899 diventa y=0…719 [D3, 15, 17].

Il controllo QML usa Qt desktop 5.15.19 e PyQt5 5.15.11, non Qt 5.5 del NAC. BaseScreen, ScreenInfo, stile, API e LayerWidget sono simulati. Tre binding Separator del footer nascosto sono rimossi solo dalla fixture desktop, non dal candidato. Nessun fotogramma del telefono è stato visualizzato [D3, 16].

Ostacolo specifico: SurfaceManager può applicare regole da /opt/ui/UIFwkTelecoding/hmi-telecoding.ini. Il file runtime dell’unità non è acquisito; i suoi offset potrebbero alterare la geometria. Il percorso predefinito provato non certifica questa calibrazione [D3].

## Applicazione locale e passaggio al banco

### Generazione su copie nel PC

Servono Python 3.10 o successivo per le prove, le due librerie originali ai percorsi del piano e il QML AA originale. Il generatore usa la libreria standard. I test aggiungono pyelftools, Unicorn e PyQt5 nelle versioni fissate dai file requirements. Procedura completa, controlli e tutti i comandi di ripristino sono in PROCEDURA_LABORATORIO.md [D3].

python patch_fullscreen_lab.py prepare \

  --rootfs rootfs_estratta \

  --ui-file INTERNET_0033SkinLogic.qml --output candidato_offline

La nuova cartella contiene due copie .offline.so, AAutoScreen.candidate.qml, cfg.candidate, DHU_1920x720.ini e il manifesto. I nomi non sono quelli di sistema. Nessun ingresso viene sovrascritto. Il manifesto dichiara installable=false e vehicle_tested=false [D3].

### Ripristino dei file locali

restore-copy richiede l’hash esatto del candidato e genera un nuovo file .restored.so o .restored.qml. I componenti sono aauto_geometry_and_crop, sidebars_with_native_focus e aa_qml. L’originale viene ricostruito byte per byte. Questo non recupera una centralina e non ripristina un cfg runtime preesistente mai acquisito [D3].

### Requisiti prima di una scrittura fisica

Acquisire numero ricambio e revisione del NAC, modello del pannello e calibrazione effettiva; leggere eventuale /home/root/cfg e hmi-telecoding.ini. Preparare un banco con unità corrispondente, display, cablaggio, alimentazione stabile e un metodo di recupero già collaudato. Accesso reversibile e distribuzione modificata accettata dal NAC restano irrisolti [D3].

Il collaudo deve misurare negoziazione con Xiaomi 14/Android 16, decoder 1080p, composizione, touch ai bordi, focus e riconnessione. Deve dimostrare accesso al clima e priorità di telecamera e sensori, oltre ad audio, microfono, sospensione e ripristino. Il codice non è stato installato: non è possibile certificare queste funzioni dalle prove offline [D3].

Un aggiornamento ufficiale richiede una nuova analisi degli hash e dei percorsi. Il generatore rifiuta file diversi. Non viene prodotto un pacchetto SWL o USB; la chiave di decifratura pubblica non abilita la firma di un aggiornamento modificato. La fase fisica richiede compatibilità preventiva e autorizzazione espressa [D1, D3].

### Evidenze e fonti aggiuntive

[D3] sviluppo_integrato_v3.json, patch_fullscreen_plan.json, sorgenti .s, generatori, prove native/QML, esiti JSON e test_esiti.txt. I file esplicitamente v2 conservano lo studio precedente. Nessun esito offline costituisce una prova sul veicolo.

[15] Unicorn Engine. Tutorial ufficiale dell’API. [Apri la fonte](https://www.unicorn-engine.org/docs/tutorial.html)

[16] Qt Project. Qt Base v5.5.0, QRC e contenitori. [Apri la fonte](https://github.com/qt/qtbase/tree/v5.5.0/src/corelib)

[17] Wayland Project. Specifica primaria wl_touch. [Apri la fonte](https://wayland.freedesktop.org/docs/html/apa.html#protocol-spec-wl_touch)

## Installazione senza chiave OEM

La ricerca aggiuntiva non ha prodotto un installer o un accesso amministratore dimostrato. Ha individuato un percorso da verificare su banco: l’initramfs originale accetta un parametro init= e contiene una shell di recupero. Per usarli occorre prima dimostrare il controllo transitorio degli argomenti di avvio o un ingresso di manutenzione sulla stessa scheda [D4].

La mancanza della chiave privata OEM impedisce di firmare normalmente un aggiornamento modificato. Un intervento temporaneo dopo l’avvio potrebbe evitare di ricostruire quel pacchetto, ma richiede un accesso privilegiato e la prova che il sistema carichi la risorsa sostitutiva. Questi prerequisiti restano aperti [D4].

### Controlli distinti

| Livello | Riscontro sul pacchetto esatto | Dato ancora mancante |
| --- | --- | --- |
| Aggiornamento SWL | Controllo nativo della firma dei metadati; hash dei moduli nel manifesto. | Accettazione effettiva del pacchetto sul NAC. |
| Avvio del processore | HABInfo e bootloader HW2019_HD contengono il supporto HAB. | Stato dei fuse e revisione della scheda. |
| Kernel Linux | Firma obbligatoria dei moduli non configurata; UnionFS disponibile come modulo. | Accesso con privilegi di caricamento. |
| Applicazioni e risorse | Non dimostrata una verifica globale di ogni libreria o QML. | Regole runtime e prova di caricamento temporaneo. |

### Copertura della nuova analisi

Sono stati riletti l’indice del TAR ufficiale e i moduli selezionati. Sono stati decifrati i sei contenitori kernel, la rootfs NAND, TSW, risorse e pacchetti di installazione. Il bootloader esaminato è HW2019_HD: non identifica quello montato nella vettura. Gli hash dei sei contenitori kernel coincidono con HashList.ini [11, D4].

Le fonti pubbliche consultate non offrono una procedura riproducibile di installazione per questo candidato. Il risultato riguarda i materiali e i percorsi esaminati; non attesta l’assenza di ogni vulnerabilità possibile. La pagina OSS Peugeot elenca pacchetti Wave 4 della serie 42, senza il sorgente esatto 44.07.33.32 tra quelli individuati [5, 7, 12, D4].

## Controlli nativi della firma

In /usr/lib/libswlprodext.so, SwlProdValidateMedia richiama il recupero del certificato di firma e della CA, quindi secVerifySignature. La guardia richiede il valore di ritorno 1. Un errore di inizializzazione o una verifica diversa da 1 porta al percorso di uscita nel frammento esaminato [D4].

| Punto del codice | Indirizzo statico o valore |
| --- | --- |
| SwlProdValidateMedia | 0x11a9c |
| Chiamata secVerifySignature | 0x124b8 |
| Uscita per verifica fallita | 0x124ec |
| Prosecuzione alla fase successiva | 0x12934 |
| Chiamata CMS_verify in libsecuUtils.so | 0x3776f874 |
| Flag effettivi del percorso esaminato | 0x2040 = CMS_NOCRL \| CMS_DETACHED |

Il chiamante fornisce 0x2000; il wrapper conserva il valore e il worker aggiunge 0x40. Non vengono impostati CMS_NO_CONTENT_VERIFY, CMS_NO_ATTR_VERIFY o CMS_NO_SIGNER_CERT_VERIFY. CMS_NOCRL non elimina la verifica del contenuto o della firma. Le definizioni sono state confrontate con l’header OpenSSL 1.0.2k, versione riportata dalla libcrypto nell’immagine [18, D4].

### Limite della prova ARM

Unicorn ha eseguito tre frammenti originali: guardia dell’aggiornamento, trasferimento degli argomenti e costruzione dei flag. Le chiamate crittografiche sono stub dichiarati. La prova conferma rami e argomenti; non verifica una firma reale e non dimostra una modifica accettata dal NAC [D4].

### Il digest dei metadati resta irrisolto

OpenSSL 3.0.13 sul PC restituisce ancora un errore nella verifica completa di MediaVersion.ini. Il digest del corpo estratto non coincide con messageDigest; le varianti comuni di fine riga e terminazione provate non lo correggono. Saltare esplicitamente il controllo del contenuto consente solo la verifica degli attributi firmati e non autentica i metadati [D4].

Questo limite non dimostra che il NAC rifiuti il pacchetto ufficiale. Impedisce di attestare localmente l’autenticità completa della distribuzione. La verifica degli hash dei moduli e la ricostruzione del flusso nativo rimangono risultati distinti. Non è stato trovato un flag di produzione che renda installabile il candidato [D4].

## Avvio e accessi presenti nel firmware

### Kernel identificato dai contenitori originali

I kernel principale, SWL e TSW nelle varianti NAND/eMMC producono lo stesso corpo Linux di 4.715.264 byte. Il banner riporta 3.10.53 con suffisso del produttore e build del 21 agosto 2023. I checksum LZOp e il CRC gzip della configurazione sono validi. Gli hash completi sono in firmware_pins.json [D4].

IKCONFIG contiene CONFIG_MODULES=y, CONFIG_UNION_FS=m e “# CONFIG_MODULE_SIG is not set”. Anche SECCOMP e SECURITY non sono configurati. Questi dati descrivono il kernel dell’archivio; non concedono accesso root, non provano l’assenza di controlli utente e non bastano per attribuire vulnerabilità a una build con possibili backport [D4].

### Initramfs e parametri di avvio

Il file /sbin/init dell’initramfs principale legge init= da /proc/cmdline e passa il risultato a switch_root. Contiene inoltre rescue_shell, che esegue ash dopo un errore di mount della rootfs. Non compare un’autenticazione nella funzione esaminata. Mancano però prova di raggiungibilità, input della console, controllo degli argomenti e comportamento del watchdog [D4].

La variante eMMC attende che la partizione esista prima del mount. Una partizione assente può lasciare il sistema in attesa. Non viene proposto di corrompere file, interrompere alimentazione o indurre errori di mount. La pista prioritaria è verificare, su banco, se esista un controllo autorizzato degli argomenti per una sola sessione, senza scrivere l’ambiente di avvio [D4].

### HAB e autenticazione della console

HABInfo legge riferimenti allo stato di secure boot dal device tree e a registri OTP. La loro presenza, e le stringhe analoghe nel bootloader HW2019_HD, non rivelano il valore dei fuse della scheda dell’utente. Non è stato dimostrato un bootloader U Boot o un comando interattivo utilizzabile [D4].

Il target debug cita SSH e serial getty. Nei percorsi dell’immagine esaminati mancano demone e servizio SSH. Il getty usa il login ordinario. Il link /etc/passwd seleziona la variante inactive closed: root e gli account rilevanti hanno password bloccata e shell /bin/false. stdOVIPuser ha UID 0 in questa variante. I file alternativi più aperti non dimostrano credenziali valide sul sistema installato [D4].

## Caricamento temporaneo e prova su banco

### UnionFS richiede un accesso già disponibile

La rootfs contiene il modulo unionfs.ko e gli script di predisposizione. init_unionfs.sh combina una parte scrivibile in tmpfs con la root originale e usa pivot_root. Ma enable_unionfs.sh sostituisce il collegamento /sbin/init: abilitarlo modifica persistentemente l’avvio. Non è una procedura pronta per il primo esperimento reversibile [D4].

Un bind mount temporaneo di una risorsa potrebbe essere preferibile per una prova futura, dopo accesso e recupero verificati. Servono namespace e percorso effettivi del processo, eventuali controlli d’integrità e prova di ricaricamento. Un processo con librerie già mappate non usa automaticamente la copia sostitutiva dopo il mount. Nessun mount o riavvio di servizio è stato effettuato [D4].

### Servizi diagnostici e altri controlli

sem_dm_server è presente con comandi di diagnostica, logging e cattura schermo. L’unica chiamata diretta a system individuata nella scansione ARM usa una stringa costante per weston screenshooter; non dimostra esecuzione di un comando arbitrario. Interfaccia, autenticazione e raggiungibilità runtime non sono state verificate [D4].

efsValidator contiene controlli relativi ad archivio cifrato EFS, certificati e coerenza delle chiavi. L’analisi non lo identifica come validatore globale di ogni libreria o QML. Le funzioni di firma presenti nelle librerie non mettono a disposizione la chiave privata di firma OEM [D4].

### Prima verifica fisica utile

Occorre identificare la revisione hardware e acquisire passivamente un avvio originale su un banco corrispondente. Vanno documentati console, livelli elettrici, bootloader, command line e log HAB. Non sono stati verificati pin UART o tensioni per la specifica scheda. La registrazione deve precedere ogni tentativo di trasmissione [D4].

PROVA_BANCO_DA_ESEGUIRE.md specifica prerequisiti, esperimenti minimi e arresti. Se esiste un accesso autorizzato indipendente, raccogliere prima hash, mount, cfg preesistente e calibrazione HMI. Solo dopo recupero dimostrato si può progettare una risorsa di prova innocua e temporanea. Restano necessari i collaudi di clima, telecamera, sensori, audio e priorità richiesti dall’utente [D3, D4].

## Riproduzione della revisione 4

La cartella installazione_v4 dello ZIP contiene l’audit e le prove dei controlli originali. Richiede Python 3.10 o successivo, pyelftools 0.33, Unicorn 2.1.4 e lzallright 0.2.6 sul PC. Non occorre installare Python nel NAC [D4].

### Ingressi e verifica locale

Servono la rootfs NAND estratta e i sei contenitori kernel decifrati nella struttura AUTO. firmware_pins.json fissa dimensioni e SHA256. Gli strumenti rifiutano ingressi diversi. audit_accesso.py risolve i link assoluti dentro la root estratta, valida i contenitori e analizza CPIO senza creare file o link [D4].

python audit_accesso.py --rootfs ROOT --decrypted MODULI

python prove_firma_arm.py --rootfs ROOT

python test_installazione.py --rootfs ROOT --decrypted MODULI

I 25 nuovi test sono passati senza esclusioni. Provano corruzione e troncamento, limiti di decompressione, link e attraversamento dei percorsi, hash incompatibili, sei kernel e frammenti ARM. I 53 test della revisione 3 restano l’esecuzione precedente e non sono stati rieseguiti in questa fase [D4].

### Materiali e azioni non eseguite

raccolta_lettura.sh prepara letture da stdout dopo un accesso già ottenuto e autorizzato. Non concede una shell e non è stato eseguito sul NAC. Non legge OTP o chiavi, non controlla servizi e non modifica file o mount. Non sono stati prodotti installer SWL, firmware firmati o script di iniezione [D4].

L’esito resta un percorso teorico sostenuto da evidenze, con un prerequisito preciso: dimostrare un ingresso privilegiato reversibile o il controllo transitorio degli argomenti del bootloader della stessa revisione. Le prove disponibili non consentono ancora installazione, rimozione delle fasce sul veicolo o attestazione delle funzioni originali [D4].

### Evidenze e fonti aggiuntive

[D4] installazione_v4 contiene firmware_pins.json, esito_audit_accesso.json, esito_firma_arm.json, hashlist_kernels.json, evidenze_installazione_v4.json, i sorgenti e test_esiti_v4.txt. fonti_v4.json conserva riferimenti e limiti della ricerca.

[[18] OpenSSL 1 0 2k header CMS e definizioni dei flag](https://github.com/openssl/openssl/blob/OpenSSL_1_0_2k/crypto/cms/cms.h)

[[19] Linux v3 10 decompressione LZOp formato del contenitore](https://github.com/torvalds/linux/blob/v3.10/lib/decompress_unlzo.c)
