# Peugeot 2008 Android Auto fullscreen

Revisione 4 del 30 ottobre 2026. Il prototipo coordinato sviluppato nella revisione 3 per 44.07.33.32_NAC-r0 resta invariato: geometria Android Auto, fasce laterali, ritaglio video e coordinate touch. La cartella installazione_v4 aggiunge audit dei controlli di firma, kernel e avvio, con 25 nuovi test superati.

L’installazione senza chiave OEM resta un percorso condizionato da verificare. La pista principale è il controllo transitorio degli argomenti dell’avvio originale, non ancora dimostrato sulla scheda. Leggere prima installazione_v4/README.md e PROVA_BANCO_DA_ESEGUIRE.md nella stessa cartella.

Il risultato è un candidato per banco, ricostruibile da copie locali dei file originali. Non è un aggiornamento USB installabile. Non è stato eseguito su un NAC acceso, sulla vettura o con lo Xiaomi.

## Risultati verificati offline

Nel controllo QML desktop, contenitore e maschera passano da 1280 a 1920 pixel nel caso WHD 1920×720. Il codice ARM candidato restituisce il rettangolo 0,0,1920,720 per Android Auto.

Con il monitor delle zone simulato, il codice nativo richiede di nascondere entrambe le fasce quando Android Auto ha il focus. Richiede di ripristinarle quando lo perde o subentra un contesto diverso. Sono le chiamate originali del sistema a mostrare e nascondere le due fasce.

Il profilo usa video 1920×1080, margine verticale totale 360 e area visibile 1920×720. La correzione imposta y=-180 nel solo caso previsto. I callback touch e i convertitori originali restituiscono coordinate corrette nei casi di prova, compresi angoli, movimenti e due identificativi di dito. L'invio finale a Cinemo e al telefono non è eseguito.

Nella revisione 3 sono passati **53 test senza test saltati**. Questi test restano documentati e non sono stati rieseguiti nella fase 4. Le tre sorgenti ARM personalizzate, riassemblate, coincidono con il piano. Il ripristino delle due librerie e del QML è verificato byte per byte.
Nove componenti delle immagini NAND ed eMMC dello stesso pacchetto sono identici. Le prove native del prototipo producono lo stesso esito sulle copie estratte da entrambe.

## Usare il prototipo

Leggere PROCEDURA_LABORATORIO.md. Il generatore principale è patch_fullscreen_lab.py. Produce nuove copie delle due librerie e del solo QML Android Auto, un cfg candidato e un profilo DHU.

Rifiuta hash diversi, un piano modificato, una seconda applicazione sul candidato e destinazioni esistenti. Non contiene rete, USB, CAN, UDS, installazione o flash.

## File principali

- patch_fullscreen_plan.json e native_geometry_guard.s, native_status_guard.s, native_crop_guard.s: piano e sorgenti ARM.
- prove_native_fullscreen.py e esito_nativo_coordinato.json: percorsi ARM con ingressi controllati.
- prove_qml_fullscreen.py e esito_qml_coordinato.json: layout desktop Qt 5.15.19 e limiti dei tipi NAC simulati.
- verifica_asm.py e esito_asm_coordinato.json: corrispondenza tra sorgenti ARM e piano.
- test_fullscreen_coordinato.py e test_esiti.txt: nuovi test e log complessivo di 53 test.
- sviluppo_integrato_v3.json: riscontri, indirizzi e ostacoli.
- confronto_NAND_eMMC.json: confronto dei nove componenti.
- fonti.json e CHECKSUMS_SHA256.txt: riferimenti e integrità dell'allegato.

Le dipendenze ARM sono in requirements-laboratorio.txt. Il controllo QML richiede anche requirements-qt-laboratorio.txt; il riassemblaggio facoltativo richiede requirements-asm-laboratorio.txt. Il generatore usa soltanto la libreria standard Python.

## Limiti

Unicorn esegue blocchi e alcune funzioni ARM con ingressi Qt o del monitor delle zone simulati. Il controllo desktop usa Qt 5.15.19, non il Qt 5.5 del NAC. BaseScreen, LayerWidget, API e stile sono simulati; tre binding Separator del footer nascosto vengono rimossi soltanto dalla fixture desktop. Tali adattamenti non si applicano al candidato.

Non sono provati negoziazione Android Auto, decoder H264, composizione Wayland completa, focus e tempi reali, installazione firmata, comportamento in eccezione o conservazione delle funzioni del veicolo. Mancano hardware e calibrazione della specifica auto.

SurfaceManager può leggere offset da /opt/ui/UIFwkTelecoding/hmi-telecoding.ini. Le regole effettive nell'unità dell'utente restano da acquisire. È stato verificato il percorso nativo di geometria predefinita, non il compositore con quelle regole.

Non sono inclusi immagini firmware, ELF completi, QML Continental completi, certificati o chiavi. Il piano contiene i piccoli intervalli necessari alla reversibilità delle copie.

## Revisioni precedenti

README_v3.md conserva la descrizione del prototipo precedente. test_esiti.txt e i risultati V3 appartengono a quella esecuzione; test_esiti_v4.txt nella sottocartella documenta i 25 nuovi test. Nessun conteggio è una prova di avvio completo o di integrazione sul NAC.

Gli audit e i vecchi strumenti restano disponibili. patch_laboratorio.py genera soltanto il precedente candidato parziale di un byte.

README_v2.md, PROCEDURA_LABORATORIO_v2.md, sviluppo_patch_offline.json e test_esiti_v2.txt documentano la revisione 2 con trenta test. Il valore screenHeight=720 nei vecchi stimoli di emulazione non era un profilo verificato del decoder. Il nuovo profilo usa 1080.

Il backup pubblico e2008 non proviene dall'auto dell'utente e non deve esservi ripristinato.
