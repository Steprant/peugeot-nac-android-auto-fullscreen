# Roadmap Android Auto a schermo intero

L’obiettivo è usare tutta la larghezza del display originale da 10″ della Peugeot 2008 GT 2020, con NAC Wave 4 `44.07.33.32_NAC-r0` e Xiaomi 14 via USB.

L’integrità del pacchetto da PC è stata verificata e i tre profili per il simulatore Android Auto sono pronti. Restano da provare la proiezione con il telefono e il funzionamento sul NAC. [Build da PC](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/commit/c0899fdd67399dd079d5aef9cd5a5d0cf65840ad) · [Profili del simulatore](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/blob/691494acf56b8023f5574595c6469379f599d182/docs/validation/dhu/README.md)

**Misura di riferimento · riscontro indipendente acquisito.** Tre prove pubbliche della 2008 corroborano la geometria WHD e l’area centrale stimata in 7,16″ di diagonale. La misura sul modello esatto con firmware 44.07.33.32 resta da acquisire tramite una prova indipendente. [Riscontri e calcoli](docs/validation/fullscreen-options.md#riscontri-sullo-schermo-europeo)

**Demo da PC · geometria verificata, prova col telefono da eseguire.** Sulla tela di riferimento il profilo centrale copre il 66,7% della larghezza e i due panoramici il 100%. I profili e l’anteprima sono pronti per il confronto con lo Xiaomi 14. [Risultati e procedura](docs/validation/dhu/README.md)

**Verifica sul NAC · 24 novembre 2026.** Il manuale Peugeot conferma che sul 10″ i riquadri laterali sono permanenti. Il codice display `9824619980`, riscontrato su una 2008 GT e una GT Line del 2020, permette di circoscrivere la ricerca di un’interfaccia compatibile. Resta aperta la verifica di Android Auto via USB a tutta larghezza con touch ai bordi su questo pannello e firmware. [Riscontri sul NAC](docs/validation/fullscreen-options.md#che-cosa-può-mostrare-il-nac-originale) · [Moduli esaminati](docs/validation/fullscreen-options.md#moduli-per-il-display-originale)

**Collaudo · una sessione dopo la conferma di compatibilità.** La prova riesce se Android Auto occupa tutta la larghezza senza deformazioni, il touch risponde ai bordi, tre riconnessioni USB vanno a buon fine e funzionano audio, microfono, clima, retrocamera e sensori. Registrare l’esito e la procedura verificata su GitHub.
