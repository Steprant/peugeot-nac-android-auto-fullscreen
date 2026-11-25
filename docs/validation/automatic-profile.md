# Revisione 6 · configurazione video automatica

> Aggiornamento: la revisione 7 riportata in questa pagina è stata respinta dai controlli aggiuntivi della lista video (4/11 superati). Non usare le copie sperimentali su hardware. Vedere il [nuovo audit e il riferimento indipendente](reference-and-readiness.md).

Il firmware NAC Wave 4 `44.07.33.32_NAC-r0` contiene quattro configurazioni grafiche di fabbrica. Il file originale `ScreenAreas.ini`, verificato mediante lo SHA-256 del progetto, assegna questi rettangoli allo stato FULLSCREEN:

| Profilo | Origine | Dimensioni |
| --- | --- | --- |
| SD | 0, 0 | 800 × 480 |
| HD | 0, 0 | 1280 × 768 |
| HD9 | 0, 0 | 1280 × 720 |
| WHD | 320, 0 | 1280 × 720 |

Il profilo WHD della 2008 da 10″ usa dunque una finestra centrale. Fra i quattro profili del firmware esaminato manca una modalità FULLSCREEN con area utile 1920 × 720. Il solo passaggio a HD9 manterrebbe una geometria di 1280 × 720. La compatibilità di eventuali configurazioni d'officina con il display specifico resta da dimostrare.

## Generazione automatica dei parametri

Nel codice originale di `libAndroidAutoAppLogic.so` sono state eseguite la registrazione delle risoluzioni, l'associazione delle altezze agli enum 480p, 720p e 1080p, e la scelta del fotogramma in funzione della superficie richiesta.

Per una superficie di 1920 × 720, il codice originale seleziona già **1920 × 1080**. La sua configurazione senza file aggiuntivo calcola 360 pixel di margine verticale totale, ma impone 80 pixel di margine orizzontale per gli enum schermo 4 e 5.

La revisione 6 usa il calcolo nativo del margine orizzontale anche per questi due enum, esclusivamente quando la superficie richiesta è esattamente 1920 × 720 e il fotogramma selezionato è 1920 × 1080. Il risultato è un margine orizzontale nullo e un margine verticale di 180 pixel per lato. Il calcolo del DPI video restituisce 240, come nel profilo precedente. Rimangono attivi il percorso originale di selezione della risoluzione e il calcolo della densità reale. Quest'ultimo è verificato attraverso gli argomenti della chiamata e una risposta simulata. Il percorso di configurazione esplicita tramite file mantiene il comportamento precedente.

## Collaudo della catena in emulazione

Sono stati eseguiti 84 confronti tra il codice ARM originale e il candidato. Gli ingressi comprendono i quattro rettangoli di fabbrica, il profilo WHD espanso, dimensioni adiacenti e sette valori dell'enum schermo. Soltanto i due casi previsti modificano il margine orizzontale, da 80 a 0. Un controllo con una tabella di risoluzioni limitata a 480p e 720p conserva i parametri originali. La correzione utilizza una sola lettura dell'enum schermo per la selezione del margine anziché le due possibili letture originarie, con la relativa differenza nel tracciamento diagnostico. I campi grafici e gli argomenti della successiva chiamata DPI sono stati confrontati.

L'emulazione collega quindi il rettangolo restituito dal candidato HMI della revisione 3 alla configurazione automatica della revisione 6. La lista generata dal codice originale di selezione dei modi contiene questi tre profili:

| Fotogramma | Margine orizzontale | Margine verticale totale | Area utile calcolata |
| --- | ---: | ---: | --- |
| 1920 × 1080 | 0 | 360 | **1920 × 720** |
| 1280 × 720 | 0 | 360 | 1280 × 360 |
| 800 × 480 | 0 | 360 | 800 × 120 |

La conversione nativa del primo profilo in dimensioni HMI restituisce 1920 × 1080 con margini 0 e 360. Il frammento di ritaglio HMI produce l'origine verticale −180. I parametri del profilo sono stati forniti al componente di proiezione della revisione 5. Il ricevitore grafico simulato ha ricevuto un rettangolo di sorgente e destinazione pari a (0, 180, 1920, 900), con area utile di 1920 × 720. I medesimi parametri e l'origine verticale HMI hanno inizializzato il percorso touch, che ha inoltrato correttamente i sei eventi di due dita ai quattro angoli al ricevitore simulato.

La lista nativa mostra ancora che i modi secondari ereditano il margine verticale del modo 1080p. Inoltre la conversione HMI nativa restituisce per il 720p un fotogramma scalato a 1920 × 1080 senza margini, e per il 480p un fotogramma scalato a 1800 × 1080 con margine orizzontale 120. Entrambi richiedono un ulteriore adattamento coordinato della geometria e del touch. La proiezione a tutta larghezza è verificata nel modello per il primo profilo. La selezione effettiva da parte del telefono, il decoder, il compositor, la priorità dei controlli originali e il touch fisico rimangono da verificare.

## Revisione 7 · fallback 720p

Il costruttore originale copiava il margine verticale 360 del profilo 1080p nei due record secondari. Il nuovo frammento ARM riconosce il solo ramo con risoluzione primaria 1080p e margine 360 e applica al 720p la proporzione `360 × 720 / 1080 = 240`. La lista prodotta dal codice nativo passa così da aree utili 1920×720, 1280×360 e 800×120 a **1920×720, 1280×480 e 800×240**. Il 480p non è ancora corretto: per conservare l'aspetto 8:3 richiede 180 pixel di margine totale.

Il record 720p corretto è stato inoltrato al processo di proiezione della revisione 5. Il ricevitore grafico simulato ha ricevuto sorgente e destinazione `(0,120)–(1280,600)`, cioè 1280×480 pixel utili. Il controllo negativo con un profilo 1920×1080 senza margine verticale restituisce la stessa lista del firmware originale. L'assembly ricostruito occupa esattamente i 236 byte fissati dal piano e il ripristino parte sempre dall'hash originale noto.

Questa resta un'esecuzione ARM su PC con sostituti Qt e grafici. Il calcolo HMI originale continua a restituire 1920×1080 senza margini per il record 720p; touch, telefono, decoder/compositor, centralina fisica e canale d'installazione non sono quindi dimostrati.

L'audit successivo ha inoltre rilevato regressioni nel percorso con modo primario 720p e modifiche non previste alla geometria adiacente. La revisione è [respinta dal controllo di regressione](reference-and-readiness.md#regressioni-della-revisione-7).

[Risultati completi dell'esecuzione](automatic-profile-results.json)

## Riproduzione e pacchetto di sviluppo

Il generatore della revisione 7 produce il candidato senza il precedente file `cfg.candidate`. Verifica gli hash dei componenti originali, applica le modifiche alle copie locali e controlla il ripristino byte per byte. Include le modifiche video e touch della revisione 5.

```sh
python prove_automatic_profile.py --rootfs /percorso/rootfs
python patch_fullscreen_lab.py prepare --automatic-video-profile \
  --rootfs /percorso/rootfs \
  --ui-file /percorso/INTERNET_0033SkinLogic.qml \
  --output candidato_whd_v7
python patch_fullscreen_lab.py restore-copy --component automatic_video_profile \
  candidato_whd_v7/automatic_video_profile.offline.so app.restored.so
```

I risultati derivano da esecuzioni ARM su PC, con sostituti Qt, dati di configurazione da banco e ricevitori grafici e touch simulati. In ambiente di lavoro non era disponibile un dispositivo NAC fisico collegato. L'installabilità tramite i canali previsti da Peugeot e il funzionamento sul modello richiesto restano aperti.
