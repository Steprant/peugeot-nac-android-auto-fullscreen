# Ritaglio video nel processo Android Auto

Il candidato di laboratorio riguarda la funzione `CGraphic::onSetVideoParams` di `conn_AndroidAutoProjection.out`, nel firmware NAC Wave 4 `44.07.33.32_NAC-r0`. La revisione 3 interviene già sulla superficie dell’interfaccia e sui margini. La revisione 5 include anche il componente che prepara i rettangoli per la proiezione.

La segnalazione di kapiszon53 ha identificato il componente in una sessione QEMU. Il collaudo qui descritto confronta il codice originale con la correzione del progetto sullo stesso ingresso. [Segnalazione indipendente](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/issues/1#issuecomment-6631735029)

## Risultati sul firmware in emulazione ARM

Con il profilo 1080p e 360 pixel di margine verticale totale, il processo originale passa al ricevitore il rettangolo da (0, 180) a (800, 300), largo 800 pixel e alto 120. Il candidato passa da (0, 180) a (1920, 900) per sorgente e destinazione. I bordi destro e inferiore sono esclusivi. L’area utile misura **1920 × 720**. I restanti campi del blocco di impostazioni da 588 byte coincidono.

Il confronto usa i tre profili DHU del progetto e sette configurazioni di controllo, a quattro livelli di tracciamento. Negli altri nove casi le due versioni inviano gli stessi parametri grafici e producono la stessa sequenza di messaggi diagnostici. La prova esegue il codice che copia e inoltra le impostazioni. Un ricevitore simulato cattura i dati all’ultima chiamata del processo. Le impostazioni iniziali fornite dal servizio grafico sono azzerate.

| Profilo | Area sorgente originale | Area sorgente candidata |
| --- | ---: | ---: |
| Centrale 720p | 1280 × 720 | 1280 × 720 |
| Panoramico 720p | 1280 × 480 | 1280 × 480 |
| WHD 1080p | 800 × 120 | 1920 × 720 |
| 480p senza margini | 800 × 480 | 800 × 480 |

Nella stessa versione candidata, due contatti Wayland simulati hanno attraversato tutti e quattro gli angoli. Il ricevitore simulato dell’interfaccia di proiezione ha registrato sei eventi con coordinate, identificativi e indice del dito corretti, comprese le due pressioni contemporanee e i rilasci separati. La prova inizializza la geometria di input con i frammenti originali del firmware e assume la superficie a y = −180. La consegna al telefono e il comportamento del compositore e del pannello rimangono da misurare. [Dati del collaudo](projection-crop-results.json)

## Riproduzione su PC

Con le dipendenze di `requirements.txt` e le copie originali indicate nella [procedura di laboratorio](../../PROCEDURA_LABORATORIO.md), eseguire dalla radice del repository in una nuova cartella di destinazione.

```sh
python prove_projection_whd.py --rootfs /percorso/rootfs
python patch_fullscreen_lab.py prepare --with-projection-crop \
  --rootfs /percorso/rootfs --ui-file /percorso/INTERNET_0033SkinLogic.qml \
  --output candidato_whd
python patch_fullscreen_lab.py restore-copy --component projection_whd \
  candidato_whd/projection_whd.offline.out proiezione.restored.out
```

Il generatore opera su copie locali e confronta gli hash. La sessione USB con uno smartphone, il touch sul pannello fisico e l’installazione attraverso un canale previsto restano da verificare.
