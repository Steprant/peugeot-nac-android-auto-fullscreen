# Riferimento completo dei profili e verifica del candidato

Prova del 25 novembre 2026 per la Peugeot 2008 GT europea del 2020, display da 10″ di serie, NAC Wave 4 `44.07.33.32_NAC-r0`. L'esecuzione è avvenuta su PC. Non è disponibile un telefono o un NAC fisico collegato nel banco di esecuzione; non è stato effettuato alcun aggiornamento o intervento sulla vettura.

## Ritaglio, visualizzazione e touch di riferimento

Google documenta i modi 800 × 480, 1280 × 720 e 1920 × 1080 e i margini simmetrici da rimuovere. Il profilo mancante, [wide-480p.ini](dhu/wide-480p.ini), usa 180 pixel di margine verticale totale. Per tutti i modi panoramici si ottiene la proporzione 8:3 del pannello WHD di riferimento, senza deformazione. [Documentazione DHU](https://developer.android.com/training/cars/testing/dhu#video-configuration)

| Profilo | Area utile | Scala uniforme | Fotogramma logico sulla tela | Origine del fotogramma |
| --- | --- | --- | --- | --- |
| 1080p | 1920 × 720 | 1 | 1920 × 1080 | (0, −180) |
| 720p | 1280 × 480 | 1,5 | 1920 × 1080 | (0, −180) |
| 480p | 800 × 300 | 2,4 | 1920 × 1152 | (0, −216) |
| Centrale 720p | 1280 × 720 | 1 | 1280 × 720 | (320, 0) |

Il [modulo indipendente](../../tools/projection_reference.py) calcola la geometria con rapporti esatti e trasforma i pixel della superficie visibile in coordinate del fotogramma o dell'area ritagliata. Le coordinate fuori dal contenuto non vengono forzate sul bordo. La perdita del focus e il cambio di risoluzione rilasciano tutti i puntatori attivi nel modello. Non implementa né presume il protocollo touch effettivo di Android Auto.

La [prova video](../../tools/prove_reference_video.py) genera quattro flussi H.264 sintetici di 30 fotogrammi, li decodifica, misura i ritagli e applica scala e composizione alla tela 1920 × 720. In tutti i **120 fotogrammi** sono visibili i quattro marcatori agli angoli dell'area utile. Il quadrato di controllo da 40 × 40 pixel resta quadrato: 40 × 40 per 1080p, 60 × 60 per 720p e 96 × 96 per 480p. Le fasce del controllo centrale rimangono nere. Per ciascun profilo sono verificate tutte le posizioni sui due assi del modello touch; l'errore massimo di ritorno è un pixel del pannello per le modalità ridimensionate, zero per le altre. Tutti i quattro puntatori della prova vengono rilasciati quando l'app perde il focus.

Questa è una verifica del **riferimento software PC**, non l'esecuzione del renderer, del decoder o dell'instradamento touch del NAC reale. [Risultati integrali](pc-reference-results.json)

## Regressioni della revisione 7

L'[audit aggiuntivo](../../tools/audit_profile_lists.py) eseguito sugli stessi input ARM del progetto interroga anche la lista completa delle configurazioni, anziché verificare soltanto i parametri della prima modalità. Il candidato della revisione 7 supera **4 casi su 11**. Il firmware originale completa la restituzione di tutte le 11 liste con gli stessi sostituti Qt e di configurazione usati nel test.

- I tre controlli con risoluzione primaria 720p e il controllo con registro limitato a 480p/720p restituiscono un errore di lettura in memoria nell'emulatore per il candidato, dopo l'osservazione delle chiamate di append. Non è dimostrato un arresto della centralina fisica.
- Con la geometria adiacente di 1840 × 720, la correzione del margine viene applicata anche al di fuori del profilo richiesto.
- Nei due casi WHD esatti, il record 720p ha margine 240 ma la geometria HMI osservata non riporta il corrispondente margine logico 360. Il record 480p usa ancora 240, anziché 180, con ulteriori differenze nella geometria HMI. La sua area 800 × 240, anche scalata uniformemente, arriva soltanto a 1920 × 576 sulla tela.

Il candidato nativo è pertanto **respinto dal controllo di regressione**. I risultati della revisione 7 restano disponibili come risultati sperimentali, non come build pronta per l'hardware. [Registro dei confronti](profile-list-audit-v7.json)

## Installazione e prove indipendenti

Al 25 novembre i canali pubblici consultati non documentano la funzione desiderata per il NAC esatto:

| Canale | Esito della verifica |
| --- | --- |
| MyPeugeot / Peugeot Update | Peugeot prevede aggiornamenti del sistema multimediale con supporto USB e verifica dell'idoneità mediante VIN. Non è stato trovato un aggiornamento approvato con proiezione a tutta larghezza per il NAC in esame. [Istruzioni ufficiali](https://www.peugeot.co.uk/content/dam/peugeot/master/media/manual/1/en/map-software-nac-en.632380.pdf) · [Verifica Peugeot Italia](https://www.peugeot.it/servizi-peugeot/mobilita-e-connettivita/gps-update.html) |
| WebPortal v1 | Il portale richiede validazione e distribuzione da Stellantis; le applicazioni sono web app nell'area destinata alle app. Per WHD l'area documentata è 1280 × 620, non l'intero pannello. Il catalogo delle API non espone una configurazione della superficie Android Auto. [Area disponibile](https://developer.groupe-psa.io/webportal/v1/overview/infotainment-system/) · [App Validation](https://developer.groupe-psa.io/webportal/v1/overview/app-validation/) · [API](https://developer.groupe-psa.io/webportal/v1/api-reference/list/) |
| Configurazione ordinaria | Il manuale 2008 dell'edizione 2020 documenta informazioni permanenti nelle fasce e le opzioni di configurazione dello schermo, senza una modalità Android Auto panoramica. [Manuale, pp. 25–26 e 218](https://public.servicebox.peugeot.com/APddb/modeles/2008.p2/eGuide_p24_ed01-20/pdfs/9999_9999_402_en-GB.pdf) |

Il recente confronto dei manifesti della versione 44.06.44.22-r1 rimane invariato come evidenza di contenuto, non di installazione: [confronto del 24 novembre](release-metadata.md). Il restyling 2023 usa un sistema i-Connect diverso ([fonte Peugeot](https://www.media.stellantis.com/it-it/peugeot/press/nuovo-peugeot-2008)); non dimostra un aggiornamento installabile sul NAC del 2020. I resoconti trovati sulla 2008 da 10″ del 2021 e su altri modelli non contengono prova completa di versione, proiezione USB, installazione e touch sulla 2008 GT 2020. [Discussione con un proprietario di 2008 GT 2021](https://www.reddit.com/r/peugeot/comments/1ehi2jw/upgrade_nac_to_ivi_peugeot_508_r8/)

## Condizione di completamento

Per qualificare una soluzione servono una configurazione o versione accettata tramite un canale documentato, e il relativo collaudo su un banco NAC autorizzato, con l'hardware di serie identificato e il telefono reale collegato via USB. Registrare versione iniziale e finale, display, area attiva misurata, risposta ai tocchi su entrambi i lati, tre riconnessioni USB riuscite e disponibilità di clima, retrocamera, sensori, audio e microfono. Verificare anche che l'interfaccia originale abbia la precedenza quando necessario e che la proiezione riprenda al termine.

Non sono state acquistate componenti o servizi e non sono stati contattati terzi. Non è stato effettuato alcun accesso alla vettura. Nessuna delle prove pubblicate dimostra ancora l'installabilità o il funzionamento sulla centralina.

## Riproduzione

Dalla radice del repository, con FFmpeg locale dotato di libx264:

```sh
python -m unittest test_projection_reference
python -m tools.prove_reference_video
python tools/render_dhu_preview.py ../confronto-android-auto.html
```

Per ripetere il controllo di regressione della revisione 7, con le dipendenze emulative preesistenti e gli stessi input locali già utilizzati dal progetto:

```sh
python -m tools.audit_profile_lists --rootfs /percorso/rootfs
```

L'uscita 1 dell'audit è l'esito atteso per il candidato respinto. L'audit non prepara un pacchetto di installazione. I 50 test pubblici senza firmware e l'esecuzione video di riferimento del 25 novembre sono terminati senza errori; ciò non annulla l'esito negativo dei confronti ARM aggiuntivi.
