# Confronto delle distribuzioni NAC Wave 4

Il 24 novembre 2026 sono stati confrontati direttamente i metadati dei tre archivi della distribuzione Continental per NAC europeo Wave 4. La versione di partenza della 2008 GT è `44.07.33.32_NAC-r0`.

La revisione `44.06.44.22_NAC-r1`, pubblicata nell'ottobre 2026, dichiara il medesimo contenuto dei quattro componenti rilevanti per la proiezione della vecchia `44.06.44.22_NAC-r0`. Su 63 voci dei manifesti, 62 hanno lo stesso SHA-256 e l'unica differenza riguarda `FirmwareList.ini`. Anche la dimensione dell'aggiornamento indicata in `UpdateInfo.xml` coincide. Le quattro voci sono invece diverse rispetto alla versione già installata sulla 2008.

| Componente | 44.06 r0 rispetto a 44.06 r1 | 44.07 r0 rispetto a 44.06 r1 |
| --- | --- | --- |
| Filesystem NAND | Identico | Diverso |
| Filesystem eMMC | Identico | Diverso |
| Risorse QML | Identico | Diverso |
| Risorse grafiche HD | Identico | Diverso |

Il confronto riguarda gli hash dichiarati nei manifesti. Le porzioni archivio lette non consentono una verifica completa dei contenuti. Il risultato esclude la revisione r1 come nuova implementazione documentata del fullscreen.

Un riscontro del 13 novembre 2026 descrive r1 come una ripubblicazione della precedente versione. Il 17 ottobre una discussione sulla possibilità di passare da 44.07 a 44.06 r1 riporta l'impossibilità di installare la versione inferiore. Sono testimonianze pubbliche e non un collaudo sulla 2008 GT di riferimento. [Discussione, messaggi 14–17](https://www.forum-peugeot.com/Forum/threads/logiciel-de-l%C3%A9cran-tactile-44-06-44-22_nac-r1.141608/)

I metadati della versione corrente risultano coerenti con l'UpdateID analizzato nella revisione 5 del progetto. Il confronto non individua un nuovo aggiornamento grafico Peugeot che estenda la proiezione. L'applicazione del candidato attraverso un canale supportato e il collaudo sul NAC fisico restano aperti. MyPeugeot offre la verifica degli aggiornamenti della vettura, e Service Box offre le funzioni diagnostiche per le configurazioni supportate. Non è documentato nelle fonti consultate un parametro specifico per il fullscreen. [MyPeugeot](https://mypeugeot.peugeot.it/) · [Service Box, condizioni diagnostiche di settembre 2026](https://public.servicebox.peugeot.com/cgv/AP/A2DR_ctc_en.pdf)

## Controllo della nuova pubblicazione segnalata il 24 novembre

Una [segnalazione pubblica aggiornata il 24 novembre 2026](https://www.forum-peugeot.com/Forum/threads/nac-wave-4-maj-firmware-44-07-33-32_nac-r0.135811/page-6) menziona la possibile preparazione di un nuovo archivio della versione 44.07.33.32. Le richieste HEAD dirette del 25 novembre alle due distribuzioni pubbliche conosciute restituiscono ancora queste intestazioni:

| Distribuzione 44.07.33.32_NAC-r0 | Content-Length | Last-Modified (GMT) |
| --- | ---: | --- |
| CDN Continental | 6.312.212.480 | 21 ottobre 2026, 15:40:17 |
| majestic-web.mpsa.com | 6.312.212.480 | 21 gennaio 2026, 12:37:21 |

La data e la dimensione del CDN coincidono con quelle già osservate il 24 novembre. Il controllo legge soltanto le intestazioni HTTP e non attesta l'uguaglianza completa dei payload, l'idoneità per uno specifico VIN o l'accettazione da parte del NAC. Non conferma la pubblicazione del nuovo archivio segnalato. Nessun aggiornamento personalizzato o nuovo percorso di installazione della funzione risulta verificato; per questo non viene prodotto un pacchetto USB da installare sulla vettura.

## Controllo riproducibile delle distribuzioni · 27 novembre

Il nuovo [strumento di osservazione](../../tools/observe_release_distribution.py) effettua esclusivamente quattro richieste HTTP HEAD agli archivi pubblici già documentati: 44.06 r0, 44.06 r1, 44.07 r0 sul CDN e 44.07 r0 sul mirror Peugeot. Le dimensioni e le date coincidono con le osservazioni del 24–25 novembre; sono stati registrati anche gli ETag di tutti e quattro gli archivi. Non è stato scaricato il payload e non è stata interrogata alcuna centralina.

```sh
python tools/observe_release_distribution.py
python -m unittest test_release_distribution
```

Una variazione delle intestazioni viene classificata come `headers_changed`, da verificare separatamente mediante metadati e prove di compatibilità. Un errore di rete, una risposta non valida o la mancanza di un campo atteso non sono interpretati come conferma di assenza di cambiamenti. Corrispondenza di dimensione, data ed ETag non significa verifica dell'identità del payload, né dell'installazione. I controlli offline coprono otto casi. [Risultati del 27 novembre](distribution-headers-2026-11-27.json)

## Riproduzione

I riferimenti agli archivi, le dimensioni HTTP, gli intervalli effettivamente letti e i due confronti sono registrati nel [risultato JSON](release-metadata-2026-11-24.json). Per ripetere la verifica basta scaricare gli intervalli indicati tramite HTTP Range e salvarli localmente. Dopo aver nominato le porzioni `44-06-44-22_NAC-r0.tail`, `44-06-44-22_NAC-r1.header`, `44-06-44-22_NAC-r1.tail` e `44-07-33-32_NAC-r0.header`, usare la CLI dalla radice del repository:

```sh
python tools/compare_release_metadata.py \
    --baseline 44-06-44-22_NAC-r0.tail \
    --candidate 44-06-44-22_NAC-r1.header 44-06-44-22_NAC-r1.tail
python tools/compare_release_metadata.py \
    --baseline 44-07-33-32_NAC-r0.header \
    --candidate 44-06-44-22_NAC-r1.header 44-06-44-22_NAC-r1.tail
```

La CLI legge le sole due voci di metadati, confronta gli identificativi di aggiornamento e verifica la presenza dei componenti. Il test automatico copre inoltre le versioni con risorse grafiche diverse o mancanti e i manifesti incompatibili o incompleti. I risultati di installazione rimangono esplicitamente non verificati.
