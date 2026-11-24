# Verifica indipendente delle opzioni fullscreen

Aggiornamento del 24 novembre 2026. Veicolo di riferimento: Peugeot 2008 GT 2020, display originale da 10″, NAC Wave 4 con firmware `44.07.33.32_NAC-r0`, Android Auto via USB.

## Riscontri sullo schermo europeo

L’Argus ha provato la 2008 PureTech 130 GT Line del 2020 e documenta una cartografia di circa 7″ di diagonale tra le fasce del clima. L’articolo comprende anche una fotografia di Google Maps in Android Auto. AlVolante stima che le fasce occupino un terzo del display da 10″, mentre Numerama quantifica a vista la larghezza persa in circa 7 cm. [L’Argus, 28 novembre 2019](https://www.largus.fr/actualite-automobile/essai-peugeot-2008-12-puretech-2020-notre-avis-sur-le-suv-peugeot-10152399_p_3.html) · [AlVolante](https://www.alvolante.it/prova/peugeot-e-2008?page=1) · [Numerama](https://www.numerama.com/vroom/579648-peugeot-e-2008-nos-premieres-impressions-sur-le-suv-urbain-dope-a-lelectrique.html)

Questi riscontri sono coerenti con la [geometria WHD del progetto](dhu/README.md). Assumendo una diagonale nominale di 10″ e una tela di 1920 × 720, si ottengono le dimensioni teoriche seguenti. La formula è diagonale × dimensione in pixel ÷ diagonale in pixel.

| Area | Larghezza × altezza | Diagonale |
| --- | ---: | ---: |
| Pannello intero di riferimento | 23,78 × 8,92 cm | 10″ |
| Finestra centrale 1280 × 720 | 15,86 × 8,92 cm | 7,16″ |
| Display indipendente 9″, 1280 × 720 | 19,92 × 11,21 cm | 9″ |

La larghezza totale delle fasce nel modello è 7,93 cm. I dati pubblici confermano l’ordine di grandezza. La geometria effettiva dell’unità con firmware 44.07.33.32 resta da misurare.

## Che cosa può mostrare il NAC originale

La guida italiana della 2008 descrive i riquadri laterali permanenti del display HD da 10″. Ospitano temperatura, notifiche, impostazioni e comandi del clima. Nella sezione Connect Nav la procedura per Android Auto via USB termina all’avvio dell’applicazione. Fra i comandi descritti manca un selettore per allargare la proiezione. Una foto scattata durante la prova della 2008 GT Line mostra Google Maps con Android Auto al centro e i comandi Peugeot sui due lati. [Guida Peugeot, p. 27](https://public.servicebox.peugeot.com/APddb/modeles/2008.p2/eGuide_p24_ed01-19/pdfs/9999_9999_288_it-IT.pdf#page=29) · [Android Auto, p. 227](https://public.servicebox.peugeot.com/APddb/modeles/2008.p2/eGuide_p24_ed01-19/pdfs/9999_9999_288_it-IT.pdf#page=229) · [Foto della prova](https://www.largus.fr/actualite-automobile/essai-peugeot-2008-12-puretech-2020-notre-avis-sur-le-suv-peugeot-10152399_p_3.html)

Stellantis descrive una funzione del NAC che occupa tutto lo schermo, la tastiera virtuale di sistema. Per le app integrate di WebPortal lo schema WHD assegna invece 1280 × 620 pixel su 1920 × 720. Il catalogo pubblico delle API WebPortal non documenta un comando per estendere Android Auto. Il dato da verificare per la proiezione USB resta la dimensione dell’immagine effettivamente visualizzata sulla 2008. [Schema WHD e tastiera](https://developer.groupe-psa.io/webportal/v1/overview/infotainment-system/) · [API pubbliche](https://developer.groupe-psa.io/webportal/v1/api-reference/list/)

Due demolitori riportano il codice display **9824619980** su vetture donatrici del 2020, una 2008 GT e una GT Line. EuroFrance associa allo stesso codice la sigla **DGT10C CEM00**. Sono identificativi con cui cercare prove di compatibilità dei moduli video. Le schede consultate non dimostrano quale revisione sia montata sulla singola vettura, né documentano un modulo che su quel pannello proietti Android Auto via USB fino ai bordi con touch funzionante. [2008 GT, Delfincar](https://delfincar.com/73643-pantalla-multifuncion-9824619980-gps-peugeot-2008-p1-gt.html) · [2008 GT Line, Rosny](https://www.rosnyautopieces.fr/produit/ecran-gps-peugeot-2008-2/) · [Sigla del pannello, EuroFrance](https://eurofrance24.com/display-peugeot-208-2008-9824619980-dgt10c.html)

Nell’ottobre 2026 è comparsa nei riscontri pubblici la revisione `44.06.44.22_NAC-r1`. La segnalazione riporta metadati di distribuzione, ma nessuna modifica alla geometria di Android Auto. Non ho trovato note Peugeot che documentino questa funzione per la `44.07.33.32_NAC-r0` in esame o un aggiornamento che la introduca. [Segnalazione del 14 ottobre e metadati riportati](https://www.forum-peugeot.com/Forum/threads/logiciel-de-l%C3%A9cran-tactile-44-06-44-22_nac-r1.141608/)

## Verifica della variante sudamericana

Il 19 maggio 2022 Peugeot ha presentato una nuova unità multimediale da 10″ per la 208 argentina. La casa documenta anche Android Auto via cavo in un video ufficiale. La scheda tecnica della 208 Roadtrip identifica il sistema come **Crony**. [Comunicato Peugeot](https://www.media.stellantis.com/ar-es/peugeot/press/la-nueva-pantalla-multimedia-de-10-llega-a-toda-la-gama-del-exitoso-peugeot-208) · [Video ufficiale](https://www.youtube.com/watch?v=EbQUgdm2Qho) · [Scheda tecnica Roadtrip](https://www.peugeot.com.ar/content/dam/peugeot/argentina/b2c/our-range/fichas-tecnicas/FichaTecnicaPeugeot208RoadtripAM24.pdf)

Il manuale brasiliano della 208 identifica il Connect Touchscreen 10″ mediante l’omologazione ANATEL 00800-22-09215. Il registro pubblico riprodotto da Radar da Telecom associa tale numero al modello CRONY 2010 di Visteon Corporation. L’identificazione è coerente con il nome della variante argentina. Si tratta di una piattaforma distinta dal NAC europeo. [Manuale Peugeot 208 Brasile](https://carros.peugeot.com.br/content/dam/peugeot/brazil/b2c/owners/maintain-your-car/manuais/2024/Peugeot.208-II-2023.pdf) · [Registro della certificazione](https://www.radardatelecom.com/certificacoes/008002209215)

La 2008 europea del restyling 2023 adotta a sua volta il sistema i-Connect. La disponibilità di queste piattaforme documenta configurazioni di fabbrica successive. Resta da confermare un eventuale retrofit ufficiale sulla 2008 GT del 2020. [Stellantis, nuovo 2008](https://www.media.stellantis.com/it-it/peugeot/press/nuovo-peugeot-2008)

## Moduli per il display originale

| Prodotto | Esito documentale |
| --- | --- |
| Naviradio MMI NAC 2017–2023 | Il fornitore include la 2008 dal 2019, ma resta da confermare il supporto esplicito del pannello da 10″ e del fullscreen con touch e funzioni originali. [Scheda](https://naviradiostore.com/products/peugeot-2017-2023-mmi-carplay-box-android-auto-car-interface-adapter-208-308-508-2008-3008) |
| Car-Interface CI-CARPLAY-NAC-PE | Compatibilità limitata ai pannelli da 7″ e 8″. [Scheda](https://www.car-interface.com/vendita/it/carplay-android-auto-peugeot/1577-interfaccia-carplay-android-auto-per-peugeot-nac-rcc-bosch.html) |
| ISUDAR NAC e BKAP HENAC | ISUDAR dichiara compatibili 7″ e 8″. BKAP esclude esplicitamente 9″ e 10″. [ISUDAR](https://isudar.com/collections/black-friday-sale/products/wireless-carplay-android-auto-for-peugeot-citroen-308-508-c4-c5-ds5-rt6-with-rneg2-system-toyota-peugeot-ds-citroen-opel-fiat-with-nac-system-%EF%BD%8Dodule-box-airplay) · [BKAP](https://www.bkap.pt/collections/interfaces-carplay-e-android-auto/products/wireless-carplay-android-auto-peugeot-nac-connect-nav-henac) |
| NavLinkz HDV-NAC12 | Il manuale include la 2008 II con monitor panoramico. L’interfaccia aggiunge un ingresso HDMI e documenta limiti di integrazione della retrocamera e dei sensori. La proiezione Android Auto con touch originale resta da dimostrare. [Manuale, pp. 6–7](https://www.navlinkz.de/artikel/HDV-NAC12/ins_eng_HDV-NAC12.pdf#page=6) |
| AAWireless TWO | Consente di cambiare la densità dell’interfaccia di Android Auto. Un’estensione della finestra riservata dal NAC resta da verificare. [Documentazione del produttore](https://www.aawireless.io/en/articles/best-wireless-android-auto-adapter-2026-aawireless-two-vs-two-plus) |

## Alternativa temporanea con schermo indipendente

ATOTO P9 da 9″ è un candidato portatile con pannello 1280 × 720 e supporto USB documentato (porta dati del caricatore incluso). La sua superficie teorica è circa il 58% maggiore rispetto alla finestra centrale di riferimento della 2008. Resta da verificare quale porzione del pannello venga effettivamente occupata durante la proiezione con lo Xiaomi 14. [Scheda P9](https://www.atotodirect.com/products/atoto-p909pr1n-9inch-portable-car-stereo-with-backup-cam) · [Manuale, capp. 7 e 15](https://www.atotodirect.com/it-it/pages/manual-435-en)

Carpuride C92 da 9,3″ documenta Android Auto via cavo, mentre la scheda del W103 da 10,3″ esclude esplicitamente il fullscreen di Android Auto. Per il C92 resta da verificare la resa a tutta larghezza. [Manuale C92](https://m.media-amazon.com/images/I/A12s5FZ-dcL.pdf) · [Scheda W103](https://carpuride.com/it/collections/car-10-inch-series/products/carpuride-w103-portable-smart-multimedia-dual-bluetooth-dashboard-console)

Un tablet Android con Headunit Reloaded dispone di una modalità USB documentata e di una dimostrazione indipendente di Android Auto a schermo intero su tablet nel 2024. La compatibilità con il telefono specifico e l’affidabilità della connessione restano da collaudare. [Google Play](https://play.google.com/store/apps/details?hl=it&id=gb.xxy.hr) · [Prova CarPlayLife](https://www.carplaylife.com/how-to/turn-any-android-tablet-into-a-wireless-car-head-unit-display-in-2024-android-auto-tablet-display-how-to-guide/)

Per una sostituzione integrale del sistema, Phonocar SM352 è dichiarato compatibile con la 2008 2019–2022 e comprende un proprio pannello da 9″ e Android Auto wireless. Il manuale prevede il recupero della retrocamera e dei comandi al volante. Restano da verificare la climatizzazione della GT e la proiezione via USB. [Manuale SM352](https://s1.medias-norauto.fr/pdf/8020065703526_instruction.pdf)

## Stato della verifica

La ricerca documentale ha corroborato la geometria di riferimento e identificato le piattaforme regionali e le incompatibilità più importanti. Per il display originale di questa 2008 resta aperta la verifica di un aggiornamento o retrofit supportato che soddisfi contemporaneamente 10″, Android Auto via USB, touch e conservazione delle funzioni di bordo. Il completamento richiede una prova indipendente sull’hardware corrispondente o una conferma di compatibilità del produttore.
