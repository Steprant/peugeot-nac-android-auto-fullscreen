# Esperimenti successivi su banco

**Stato: procedura di ricerca proposta, non eseguita.** Nessuna fase qui descritta attesta compatibilità o recupero dell'unità dell'utente. L'incarico attuale autorizza il lavoro offline. Una futura scrittura o installazione richiede le condizioni e l'autorizzazione separata già richieste dall'utente.

## Dati necessari

Acquisire numero ricambio, revisione hardware, calibrazione e modello pannello; distinguere NAND/eMMC e collegamento video. Un tecnico deve individuare da documentazione o misure il livello elettrico della console e il riferimento di massa. Non sono stati identificati pin o tensione UART utilizzabili per questa scheda: non collegare un adattatore basandosi su pinout di altre generazioni.

Occorrono unità da banco corrispondente, display e cablaggio documentati, alimentazione regolata e limitata in corrente, strumenti di misura e un ricevitore seriale elettricamente compatibile. Per la prima acquisizione usare il solo ricevitore, dopo identificazione elettrica. Non collegare trasmissione, non indurre guasti, non interrompere aggiornamenti e non modificare fuse o bootloader.

## Acquisizione passiva di avvio

Su banco registrare un avvio originale e identificare versione bootloader, memoria, command line effettiva, console e log HAB. Un log assente non prova che una protezione sia disattivata. La funzione `HABInfo` nel firmware non attesta i fuse della specifica scheda.

Questa acquisizione deve risolvere se il percorso contiene una console interattiva o un protocollo di manutenzione documentato. Non viene fornita una sequenza di sblocco: nessuna è stata verificata. La verifica deve avvenire su unità di prova con un recupero già dimostrato prima di inviare comandi che alterino avvio o software.

## Ipotesi da confermare

| Pista | Evidenza offline | Esperimento minimo successivo | Criterio di arresto |
|---|---|---|---|
| Parametro init per singola sessione | L'initramfs originale lo legge e lo usa in switch_root | Documentare un metodo autorizzato di controllo degli argomenti in RAM, senza scrivere ambiente o memoria persistente | Nessun metodo dimostrato o stato secure boot non compreso |
| Console di manutenzione | Getty e target debug presenti, account selezionati chiusi | Identificare il percorso di autenticazione legittimo della stessa revisione | Login non disponibile; non presumere password vuota da file alternativi |
| Shell di recupero originale | Funzione ash su errore di mount | Solo dopo un meccanismo non distruttivo di ingresso e recupero, verificarne I/O su banco | Necessità di corrompere filesystem, togliere alimentazione, forzare errori o bloccare l'unità |
| Risorsa temporanea a sistema avviato | UnionFS compilato come modulo | Dopo accesso privilegiato verificato, provare una risorsa innocua in una sessione isolata | Scrittura della rootfs, modifica di init o impatto sulle funzioni richieste |
| Servizio SEM | Binario, servizio e comandi diagnostici presenti | Documentare interfaccia, autenticazione e privilegi effettivi prima di qualsiasi test attivo | Nessun percorso di caricamento legittimo o nessun input controllabile provato |

La possibilità di controllare `init=` in modo transitorio è un prerequisito non risolto. La presenza del parser non offre tale controllo. Non usare errori intenzionali di mount sul veicolo; su eMMC la partizione assente può mantenere l'avvio nel ciclo di attesa.

## Raccolta dopo accesso indipendente

Se si ottiene una shell autorizzata, acquisire in sola lettura identità software, stato dei mount, hash delle librerie, `/home/root/cfg` preesistente e `/opt/ui/UIFwkTelecoding/hmi-telecoding.ini`. Lo script allegato prepara parte di questa lettura e scrive soltanto su stdout. Copiarlo sulla centralina o eseguirlo sono azioni non effettuate; prima va revisionato per l'ambiente reale. Nessun servizio viene avviato o fermato dallo script.

Gli hash devono coincidere con il piano fullscreen e con `firmware_pins.json`. Scartare automaticamente offset di altre versioni. Acquisire anche il QML esatto dal percorso runtime e il suo hash. Il percorso QML e il filesystem che lo ospita vanno confermati; i dati nell'archivio non sono una misura dello stato installato.

## Caricamento temporaneo futuro

Prima del candidato fullscreen, progettare una prova innocua che dimostri il caricamento di una risorsa sostitutiva in memoria. Un bind mount isolato o una sessione separata del processo potrebbero essere adatti, ma non sono stati provati. Un processo già avviato può avere le librerie mappate e non rileggerle: un mount successivo non basta. Individuare caricamento QML, namespace dei mount, controlli d'integrità e dipendenze prima di fermare o riavviare componenti.

Non viene consegnato uno script di mount, riavvio o iniezione. Il loro bersaglio e gli effetti non sono ancora verificati. Lo script originale `enable_unionfs.sh` altera `/sbin/init` e non soddisfa questa prima prova temporanea.

## Recupero e accettazione

Il banco deve permettere il ritorno allo stato originale dopo un mancato avvio. Servono backup completo coerente con l'hardware, dati specifici dell'unità e una via di ripristino collaudata. Un backup diagnostico .nac non basta.

Una futura prova temporanea deve registrare i file o mount interessati e dimostrare la rimozione degli override e il riavvio originale. Il solo riavvio ripulisce un tmpfs se nessun parametro o file persistente è stato alterato; non recupera una modifica dell'avvio. La procedura effettiva va verificata prima dell'installazione, non dedotta dal concetto di overlay.

Dopo la prova innocua, per il fullscreen occorre dimostrare sul display reale negoziazione Android Auto, decoder 1080p, crop, composizione, touch ai bordi, transizioni di focus, USB, audio e microfono. L'accesso al clima e la priorità di retrocamera e sensori devono funzionare in ogni transizione provata. Non procedere sul veicolo se questi requisiti o il recupero restano irrisolti.
