# Roadmap Android Auto a schermo intero

L’obiettivo è usare tutta la larghezza del display originale da 10″ della Peugeot 2008 GT 2020, con NAC Wave 4 `44.07.33.32_NAC-r0` e Xiaomi 14 via USB.

L’integrità del pacchetto da PC è stata verificata e i tre profili per il simulatore Android Auto sono pronti. Restano da provare la proiezione con il telefono e il funzionamento sul NAC. [Build da PC](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/commit/c0899fdd67399dd079d5aef9cd5a5d0cf65840ad) · [Profili del simulatore](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/blob/691494acf56b8023f5574595c6469379f599d182/docs/validation/dhu/README.md)

**Misura sulla 2008 · 30–60 minuti.** A veicolo fermo, fotografare Android Auto via USB e misurare la larghezza occupata e quella delle fasce. Confermare il modello del display e la modalità attiva tramite la documentazione del veicolo o l’assistenza Peugeot. [Manuale Peugeot Connect Nav](https://public.servicebox.peugeot.com/APddb/modeles/2008.p2/eGuide_p24_ed01-19/pdfs/9999_9999_288_it-IT.pdf)

**Demo da PC · 1–2 ore.** Con lo Xiaomi 14, confrontare la finestra centrale con i due profili panoramici nel simulatore di Google. Verificare che mappa, barra dei comandi e pulsanti ai bordi siano leggibili e utilizzabili. Salvare schermate e versioni per ripetere la prova. [Simulatore Android Auto di Google](https://developer.android.com/training/cars/testing/dhu#video-configuration)

**Verifica sul NAC · in parallelo.** Verificare in MyPeugeot e presso la rete di assistenza se esiste un aggiornamento o una configurazione ufficiale che estenda Android Auto sul pannello identificato. Se la via nativa resta senza conferma, il traguardo intermedio è la demo da PC. Un’eventuale interfaccia reversibile va valutata sulla compatibilità documentata con il display, il touch e le funzioni originali. [MyPeugeot](https://mypeugeot.peugeot.it/)

**Collaudo · una sessione dopo la conferma di compatibilità.** La prova riesce se Android Auto occupa tutta la larghezza senza deformazioni, il touch risponde ai bordi, tre riconnessioni USB vanno a buon fine e funzionano audio, microfono, clima, retrocamera e sensori. Registrare l’esito e la procedura verificata su GitHub.
