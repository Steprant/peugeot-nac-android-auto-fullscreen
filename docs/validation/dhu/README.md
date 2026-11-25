# Prova panoramica di Android Auto

## Risultato da PC

Per la tela WHD da 1920 × 720 usata come riferimento, la finestra centrale occupa **il 66,7% della larghezza**. I tre profili panoramici arrivano al **100%** nel modello geometrico. Il WHD 1080p ha già le dimensioni utili del pannello ed è il primo candidato da provare dopo la misura di riferimento.

| Profilo DHU | Fotogramma | Margine verticale per lato | Area utile nel profilo | Larghezza sulla tela WHD |
| --- | ---: | ---: | ---: | ---: |
| [Centrale 720p](central-720p.ini) | 1280 × 720 | 0 px | 1280 × 720 | 66,7% |
| [WHD 1080p](whd-1080p.ini) | 1920 × 1080 | 180 px | 1920 × 720 | 100% |
| [Panoramico 720p](wide-720p.ini) | 1280 × 720 | 120 px | 1280 × 480 | 100% con scala uniforme ×1,5 |
| [Panoramico 480p](wide-480p.ini) | 800 × 480 | 90 px | 800 × 300 | 100% con scala uniforme ×2,4 |

Il riferimento aggiornato del 25 novembre 2026 verifica la decodifica H.264, i quattro angoli e l'assenza di deformazioni su 120 fotogrammi, insieme al modello touch per tutte e quattro le configurazioni. [Risultati e codice](../reference-and-readiness.md)

Il modello WHD lascia 320 px per lato con il profilo centrale. La misura sul veicolo servirà a verificare che corrisponda al pannello e alla modalità attiva della 2008 GT. [Profili di partenza](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/tree/691494acf56b8023f5574595c6469379f599d182/docs/validation/dhu) · [Opzioni video del DHU](https://developer.android.com/training/cars/testing/dhu#video-configuration)

Per generare l’anteprima e aprirla nel browser, eseguire dalla radice del repository con Python 3.

```sh
python3 tools/render_dhu_preview.py ../confronto-android-auto.html
```

Su Windows il comando equivalente è `py -3 tools/render_dhu_preview.py ../confronto-android-auto.html`. L’anteprima mostra sagome di prova, con le proporzioni e le aree utili calcolate dai file INI.

## Misura del video H.264 decodificato su PC

Il 24 novembre 2026 sono stati generati quattro filmati sintetici di 30 fotogrammi a 30 fps con FFmpeg 7.1.5 e libx264. Un bordo chiaro di quattro pixel identifica i limiti del contenuto in movimento. Dopo la decodifica, il filtro `cropdetect` ha misurato l'area del contenuto prima di ogni ritaglio o ridimensionamento. Le misure sono rimaste stabili per tutti i 30 fotogrammi di ogni filmato.

| Filmato | Fotogramma codificato | Contenuto rilevato | Inizio del contenuto (x, y) |
| --- | --- | --- | --- |
| Centrale 720p | 1280 × 720 | 1280 × 720 | 0, 0 |
| WHD 1080p | 1920 × 1080 | 1920 × 720 | 0, 180 |
| Panoramico 720p | 1280 × 720 | 1280 × 480 | 0, 120 |
| Controllo 1080p senza margini | 1920 × 1080 | 1920 × 1080 | 0, 0 |

Per riprodurre la misura del profilo WHD in una cartella temporanea:

```sh
ffmpeg -f lavfi -i 'testsrc2=size=1920x720:rate=30,drawbox=color=white:t=4,pad=1920:1080:0:180:black' -frames:v 30 -c:v libx264 -pix_fmt yuv420p -threads 2 whd-test.h264
ffmpeg -hide_banner -nostats -i whd-test.h264 -vf 'cropdetect=limit=32:round=2:reset=1:skip=0' -f null -
```

Il risultato atteso è `crop=1920:720:0:180`. Questa prova verifica che il contenuto panoramico è recuperabile dal flusso di test. Per la 2008 restano da dimostrare la negoziazione USB con il telefono, la decodifica sul NAC, la visualizzazione fino ai bordi e il touch.

## Misura sulla 2008

A veicolo fermo, fotografare di fronte il display acceso con Android Auto via USB e tutti i bordi visibili. Sulla stessa linea orizzontale segnare il bordo sinistro e destro del display attivo e i bordi della finestra Android Auto. Calcolare `100 × larghezza Android Auto ÷ larghezza display`. Annotare anche le due fasce in percentuale, la versione NAC e, se disponibile tramite assistenza, il codice del pannello. Oscurare dati personali prima di condividere lo scatto. [Manuale Peugeot Connect Nav, p. 228](https://public.servicebox.peugeot.com/APddb/modeles/2008.p2/eGuide_p24_ed01-19/pdfs/9999_9999_288_it-IT.pdf#page=229)

## Sessione con lo Xiaomi 14

Installare **Android Auto Desktop Head Unit Emulator** da **SDK Manager → SDK Tools** in Android Studio. Collegare lo Xiaomi 14 con un cavo USB dati. Aprire il terminale nella cartella `extras/google/auto` dell’SDK e provare un profilo per volta, sostituendo il percorso. Se il collegamento USB diretto su Windows richiede un driver, consultare l’alternativa ADB nella guida Google. [Installazione e collegamento](https://developer.android.com/training/cars/testing/dhu#run-dhu)

```powershell
.\desktop-head-unit.exe --usb --config="C:\Peugeot\docs\validation\dhu\central-720p.ini"
```

Su Linux o macOS usare `./desktop-head-unit --usb --config=/percorso/central-720p.ini`. Ripetere con `whd-1080p.ini`, `wide-720p.ini` e `wide-480p.ini`, chiudendo il DHU tra una prova e l’altra. Per ogni profilo, aprire la stessa mappa e il menu delle app, provare i pulsanti verso entrambi i bordi e salvare le schermate dalla console del DHU con `screenshot nome.png`. Annotare le versioni del DHU e di Android Auto, le dimensioni osservate e gli eventuali ritagli. [Comandi del DHU](https://developer.android.com/training/cars/testing/dhu#dhu-commands)

## Compatibilità del display originale

| Opzione | Riscontro al 18 novembre 2026 |
| --- | --- |
| Peugeot Connect Nav | Il manuale della 2008 descrive Android Auto via USB. La ricerca nella documentazione Peugeot consultata lascia senza conferma il fullscreen per il NAC Wave 4 con firmware `44.07.33.32_NAC-r0`. Il controllo per la singola vettura passa dalla sezione touchscreen di MyPeugeot o dall’assistenza. [Manuale](https://public.servicebox.peugeot.com/APddb/modeles/2008.p2/eGuide_p24_ed01-19/pdfs/9999_9999_288_it-IT.pdf#page=229) · [MyPeugeot](https://mypeugeot.peugeot.it/) · [Guida agli aggiornamenti](https://www.peugeot.co.uk/buy/mobility-connectivity/map-system-updates.html) |
| NavLinkz HDV-NAC12 | Il manuale comprende la 2008 II con NAC e display da 10,25″ fra le varianti compatibili. Documenta un ingresso video HDMI e limiti di commutazione della retrocamera e della grafica dei sensori. Per la GT di riferimento restano da confermare il codice display, il controllo touch della sorgente e la proiezione Android Auto su tutta la larghezza. [Manuale, pp. 6–7](https://www.navlinkz.de/artikel/HDV-NAC12/ins_eng_HDV-NAC12.pdf#page=6) |
| CarVision CV-NAC-CPAA | Il manuale della revisione esaminata documenta display originali da 7″ e 8″. Il pannello da 10″ della GT resta fuori dalla compatibilità documentata. [Manuale, p. 7](https://www.carvision.nl/UserFiles/File/Shop/300526.PDF) |

Per la verifica con Peugeot bastano il modello, la versione NAC e la richiesta di confermare se un aggiornamento ufficiale o una configurazione supportata porta **Android Auto via USB** a tutta larghezza sul display originale. La disponibilità di aggiornamenti cartografici va registrata a parte.
