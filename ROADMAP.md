# Roadmap Android Auto a schermo intero

L’obiettivo è usare tutta la larghezza del display originale da 10″ della Peugeot 2008 GT 2020, con NAC Wave 4 `44.07.33.32_NAC-r0` e Xiaomi 14 via USB.

L’integrità del pacchetto da PC è stata verificata e i tre profili per il simulatore Android Auto sono pronti. Restano da provare la proiezione con il telefono e il funzionamento sul NAC. [Build da PC](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/commit/c0899fdd67399dd079d5aef9cd5a5d0cf65840ad) · [Profili del simulatore](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/blob/691494acf56b8023f5574595c6469379f599d182/docs/validation/dhu/README.md)

**Misura sulla 2008 · 30–60 minuti.** A veicolo fermo, fotografare Android Auto via USB e misurare la larghezza occupata e quella delle fasce. Confermare il modello del display e la modalità attiva tramite la documentazione del veicolo o l’assistenza Peugeot. [Manuale Peugeot Connect Nav](https://public.servicebox.peugeot.com/APddb/modeles/2008.p2/eGuide_p24_ed01-19/pdfs/9999_9999_288_it-IT.pdf)

**Demo da PC · geometria verificata, prova col telefono da eseguire.** Sulla tela di riferimento il profilo centrale copre il 66,7% della larghezza e i due panoramici il 100%. I profili e l’anteprima sono pronti per il confronto con lo Xiaomi 14. [Risultati e procedura](docs/validation/dhu/README.md)

**Verifica sul NAC · documentazione consultata.** La documentazione pubblica lascia da confermare il fullscreen nativo su questa versione del Wave 4. Verificare l’auto in MyPeugeot o con assistenza Peugeot. L’interfaccia HDMI esaminata richiede conferme su touch e funzioni originali. [Riscontri](docs/validation/dhu/README.md#compatibilità-del-display-originale)

**Collaudo · una sessione dopo la conferma di compatibilità.** La prova riesce se Android Auto occupa tutta la larghezza senza deformazioni, il touch risponde ai bordi, tre riconnessioni USB vanno a buon fine e funzionano audio, microfono, clima, retrocamera e sensori. Registrare l’esito e la procedura verificata su GitHub.
