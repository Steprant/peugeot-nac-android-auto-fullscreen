# Roadmap Android Auto a schermo intero

L’obiettivo è usare tutta la larghezza del display originale da 10″ della Peugeot 2008 GT 2020, con NAC Wave 4 `44.07.33.32_NAC-r0` e Xiaomi 14 via USB. Lo sviluppo è circoscritto a una soluzione software con l’hardware di serie.

L’integrità del pacchetto da PC è stata verificata e i tre profili per il simulatore Android Auto sono pronti. Restano da provare la proiezione con il telefono e il funzionamento sul NAC. [Build da PC](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/commit/c0899fdd67399dd079d5aef9cd5a5d0cf65840ad) · [Profili del simulatore](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/blob/691494acf56b8023f5574595c6469379f599d182/docs/validation/dhu/README.md)

**Misura di riferimento · riscontro indipendente acquisito.** Tre prove pubbliche della 2008 corroborano la geometria WHD e l’area centrale stimata in 7,16″ di diagonale. La misura sul modello esatto con firmware 44.07.33.32 resta da acquisire tramite una prova indipendente. [Riscontri e calcoli](docs/validation/fullscreen-options.md#riscontri-sullo-schermo-europeo)

**Verifica video su PC.** Dopo la decodifica dei 30 fotogrammi H.264 sintetici del profilo panoramico 1080p, l'area utile misurava 1920 × 720. Il controllo 1080p senza margini ha restituito un'area di 1920 × 1080. La prova sul NAC resta aperta. [Misure e riproduzione](docs/validation/dhu/README.md#misura-del-video-h264-decodificato-su-pc)

**Verifica software · 24 novembre 2026.** La documentazione Google attribuisce all’unità di bordo la configurazione della risoluzione e dei margini. Il manuale Peugeot conferma che sul 10″ i riquadri laterali sono permanenti. Anche la sola modifica della risoluzione da smartphone ha dato esito negativo in una prova pubblica sulla 508. La ricerca si concentra sulle impostazioni e sugli aggiornamenti supportati dal NAC Wave 4 per estendere la proiezione. Al momento manca una procedura di installazione software verificata sulla 2008. [Valutazione software](docs/validation/fullscreen-options.md#valutazione-della-soluzione-software)

**Collaudo · una sessione dopo la conferma di compatibilità.** La prova riesce se Android Auto occupa tutta la larghezza senza deformazioni, il touch risponde ai bordi, tre riconnessioni USB vanno a buon fine e funzionano audio, microfono, clima, retrocamera e sensori. Registrare l’esito e la procedura verificata su GitHub.
