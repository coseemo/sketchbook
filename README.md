# SketchBook Tesi

In questa repository si trova tutto il materiale raccolto e prodotto per la mia tesi di Laurea Magistrale. Al momento la "roadmap" è la seguente:

## TODO

1. [X] Rileggere i paper che mi erano stati forniti per il laboratorio.
2. [ ] Eseguire alcuni esperimenti preliminari con uno o più VLM, in modo da ottenere una baseline e analizzarne i risultati.
3. [ ] Approfondire meglio il funzionamento degli agenti, la rappresentazione della conoscenza in Prolog e riguardare il sistema Aleph.
4. [ ] Sviluppare una prima pipeline per estrarre i predicati dalle istanze del benchmark (KANDY) e convertirli in rappresentazione simbolica.
5. [ ] Utilizzare Aleph per provare ad apprendere regole a partire dagli esempi etichettati e valutarne i risultati.

---

## Fonti Utilizzate

- Bongard in Wonderland: Visual Puzzles that Still Make AI Go Mad?[https://arxiv.org/pdf/2410.19546]
- BONGARD-RWR+: REAL-WORLD REPRESENTATIONS OF FINE-GRAINED CONCEPTS IN BONGARD PROBLEMS[https://arxiv.org/pdf/2508.12026]
- BONGARD-LOGO: A New Benchmark for Human-Level Concept Learning and Reasoning[https://arxiv.org/pdf/2010.00763]
- The KANDY Benchmark: Incremental Neuro-Symbolic Learning and Reasoning with Kandinsky Patterns[https://arxiv.org/pdf/2402.17431]
- 
-
-
-

---

## Prima parte: 

Tutti gli appunti presi durante la rilettura si trovano nel README della cartella Appunti_Papers. Per la seconda parte andrò a utilizzare i concetti che seguono.

### Da Bongard in Wonderland

1. Il fatto che un VLM descriva correttamente un'immagine, non significa che riesca a capire quale sia la regola astratta che lega quella immagine ad altre immagini e la separa dalle altre.
2. Il modello può dare la risposta giusta senza aver "in mente" il concetto: può azzeccare per caso o per via di un forte pre-training sul problema proposto.
3. Si cerca dunque di formulare degli esperimenti per capire se il modello "capisca" le regole astratte che legano delle immagini oppure le indovini e basta.
4. Il paper valuta tre caratteristiche fondamentali:
   - riconoscimento: ovvero il modello risponde correttamente alla domanda "in questa immagine c'è un triangolo"?
   - induzione: ovvero il modello riesce a formulare la regola che collega tra di loro le varie immagini.
   - applicazione: una volta nota la regola, il modello riesce a stabilire con certezza se l'immagine possiede o non possiede quella regola.
5. Gli autori propongono tre test principalmete:
   - Ricevute 12 immagini, 6 gruppo a e 6 gruppo b, stabilire quali sono le regole dei due gruppi.
   - Data la coppia di regola vengono proposte singolarmente le 12 immagini e il modello deve capire se vale a oppure b.
   - Il modello vede le 12 immagini e deve produrre 20 ipotesi tra cui quella giusta.
7. Gli autori individuano 4 comportamenti per i vlm:
    - Tipo I   :  il modello fa bene i primi due test ma non riesce nel terzo; non succede quasi mai, l'idea è che se il modello stabilisce la regola e la riconosce negli esempi allora riesce anche a generarla nelle 20 ipotesi
    - Tipo II  :  il modello fa bene gli utlimi due test; significa che il modello non riesce a "unire i puntini", gli autori mostrano che c'è un numero discreto di errori di questo tipo, l'errore suggerisce una mancanza nel riuscire appunto a integrare la percezione col ragionamento. 
    - Tipo III :  il modello fa bene il primo e il terzo; capisce cioè la regola generale ma non riesce a ritrovarla nelle singole istanze, gran parte degli errori che il modello compie appartengono a questa categoria, ovvero il modello quando si tratta di capire il quadro generale eccelle, mentre pecca nel particolare (ciò potrebbe essere dovuto anche all'architettura dei vit e transformer in generale ma ciò richiederebbe un'analisi più approfondita).
    - Tipo IV  :  il modello si comporta bene in tutti e tre i test

### Da BONGARD-RWR+

1. Si utilizza un dataset sintetico simile a Bongard-Hoi e discendente diretto di Bongard-RWR, il quale ci permette di verficare la capacità del modello di estrarre concetti astratti da immagini reali
3. Gli autori stabiliscono 4 comportamenti chiave:
   - Percezione  : il modello riesce a ricavare info visive pertinenti
   - Confronto   : il modello riesce a stabilire quale regola divide i due gruppi
   - Selezione   : il modello riesce a scegliere la coppia di regole giusta
   - Generazione : il modello riesce a generare la regola corretta
4. Gli autori stabiliscono poi sei esperimenti chiave:
    - Il modello riceve le dodici immagini di contesto e una singola immagine di test. Deve stabilire se quest'ultima appartenga al gruppo sinistro oppure al destro; misura la capacità di utilizzare il contesto per assegnare un nuovo esempio alla categoria corretta
    - Il modello riceve entrambe le immagini di test, una per ciascun lato, e deve assegnarle ai rispettivi gruppi; misura la capacità di classificare due esempi in presenza dello stesso contesto, con una possibile difficoltà aggiuntiva legata alla coerenza fra le risposte
    - Prima, un modello image-to-text trasforma le immagini di contesto e di test in descrizioni linguistiche. Poi un modello testuale utilizza queste descrizioni per assegnare l'immagine di test al gruppo corretto; misura la capacità di classificare due esempi sulla base di descrizioni linguistiche, mantenendo la distinzione fra i due concetti
    - Si applica la stessa idea del D1S, ma alle due immagini di test. Entrambe vengono descritte in linguaggio naturale e il modello deve assegnarle ai lati corretti; misura La capacità di classificare due esempi sulla base di descrizioni linguistiche, mantenendo la distinzione fra i due concetti
    - Il modello riceve la matrice Bongard e un insieme di concetti candidati. Deve selezionare quello che descrive correttamente la distinzione fra i due gruppi; misura la capacità di identificare il concetto corretto fra alternative esplicitamente disponibili
    - Il modello riceve la matrice e deve descrivere autonomamente in linguaggio naturale il concetto che distingue i due gruppi. Gli autori esaminano sia la generazione da immagini sia quella da descrizioni linguistiche; misura la capacità di produrre una spiegazione linguistica della regola senza avere a disposizione una lista di risposte candidate
5. Vengono stabilite tre tipi di risultati:
   - prestazioni basse con input visivi, alte con input testuali; difficoltà nella percezione
   - prestazione basse con generazione e alte in selezione; difficoltà nella formulazione
   - prestazioni migliori con una sola immagine rispetto che due; difficoltà di mantenere coerenti due classificazioni ma anche differenze nei prompt e nel formato dell'output

### Da BONGARD-LOGO

1. Paper "capostipite": gli autori fanno notare che mentre gli umani, anche i bambini, riescono a generalizzare anche con pochi dati a disposizione, le macchine invece sembrano avere bisogno di ingenti quantità di dati e spesso non riescono a generalizzare alla stessa maniera
2. Gli autori dunque vorrebbero far passare i modelli dal semplice pattern-recognition alla capacità di generalizzazione degli umani
3. I bongard originali sono 100 quesiti, ma per addestrare un modello sono pochi, quindi si passa a 12.000 problemi. Il modello osserva 6 esempi positivi, 6 negativi e poi classifica nuovi esempi. Si tratta di un task di classificazione few-shot
4. Nel paper gli autori individuano 3 proprietà fondamentali della cognizione umana:
   - Context-dependent Perception: cioè una stessa configurazione può essere interpretata differentemente in base al contesto in cui si trova, (ex. un un triangolo equilatero ha un significato diverso se è mostrato assieme ad altri 5 triangoli o ad altri 5 poligoni regolari). In altre parole la percezione P dell'umano può essere espressa come una funzione dell'oggetto visivo X e del contesto C, cioè P(X,C).
   - Analogy-making perception: cioè gli umani possono reinterpretare una struttura visiva attraverso un concetto differente, trasferendo alla nuova rappresentazione caratteristiche che la definiscono. (ex. posso interpretare una sequenza di zigzag come una linea, oppure quattro triangoli alla stessa distanza tra loro con quattro angoli retti tra di loro come un quadrato)
   - Few sample, infinite vocabulary: gli umani anche da pocchissimi esempi riescono a identificare quelle caratteristiche che vanno a definire la "matrice" di tutti i possibili problemi. I modelli dunque non possono semplicemente limitarsi a riconoscere un insieme finito di forme, ma deve riuscire ad apprendere come viene generato il nuovo concetto. (ex. vogliamo addestrare il modello su traingolo e quadrato ma vogliamo che poi, in autonomia, capisca che mettendo il triangolo sopra il quadrato si ottenga una casa.)

### Da KANDY

1. Binding problem: associare correttamente le caratteristiche percettive ai singoli oggetti.
2. L'idea è quella di far imparare prima concetti semplici e poi farli riutilizzare in task via va più complessi.
8. Come funziona la generazione degli esempi:
    1. Definizione task: si specificano regole positivem negative, proprietà, operatori, numero di esmepi e impostazioni di supervisione.
    2. Generazione simbolica: si costruiscono gli alberi di composizione a partire dalle regole yaml.
    3. Il sistema controlla che gli alberi non siano ridondanti e, quando è disponibile, verifica la compatibilità con la regola prolog.
    4. Rendering immagini: gli alberi diventano immagini andando ad applciare alcune variazioni percettive
    5. Assegnazione supervisione: a ogni campione viene associato supervised o unsupervised a seconda della specifica.
    6. Gli esempi vengono separati nei gruppi di trainig, validation e test.

---

## Seconda Parte:

In questa seconda parte andremo a eseguire dei test sui VLM scelti; prima, tuttavia dobbiamo concentrarci su alcuni aspetti fondamentali, quali:

1. Analisi Esplorativa dei Datasets (EDA):
    Esploreremo in particolare, KANDY-Easy, Kandy-Hard, Kandy-Bongard, Bongard-RWR+.
2. Definizione test e metriche di valutazioni:
    Una volta esplorato il dataset, stabiliremo dapprima quali capacità dei modelli vogliamo testare sui dati a disposizione, di conseguenza definiremo le esempi di test e metriche di valutazione; in caso si presenti la necessità, andremo a creare un dataset a partire dal dataset di KANDY.
3. Sceglieremo i modelli di VLM da mettere alla prova sui nostri esempi.

### Analisi Esplorativa dei Dataset

Esplorando i quattro datasets si rileva che:

### Definizione Datasets, Test e Metriche

Si costruiscono dunque tre datasets diversi:

1. KANDY Bongard, di cui prendiamo gli esempi già forniti e li andiamo a decomporre per ottenere anche le singole immagini.
2. Un sottoinsieme di task da Bongard RWR+, da cui anche qui prendiamo la figura intera e la decomposizione.
3. Un sottoinsieme di task da KANDY easy/hard/bongard e Bongard RWR+.

I datasets 1. e 2. verranno testati nelle stesse modalità, ovvero le tre che vengono utilizzate nel paper di Bongard in Wonderland più una ispirata a RWR+ ovvero:

- Ricevuto un fondale, 6 immagini gruppo a e 6 immagine gruppo b, stabilire quali sono le regole dei due gruppi.
- Data la coppia di regola vengono proposte singolarmente le 12 immagini e il modello deve capire se vale a oppure b.
- Il modello vede le 12 immagini e deve produrre 20 ipotesi tra cui quella giusta.
- Date n-1 immagini di contesto (dove n sono le immagini disponibili), si chiede al modello di valutare la n-esima.

Per il dataset 3. che sarà un dataset piccolo, risultato dell'intersezione tra KANDY e RWR+, il quarto test diverrà:

- Date n-1 immagini di contesto di KANDY si chiede al modello di valutare un'immagine di test di RWR+.

Per il momento si è deciso di scartare i test introdotti da RWR+ utilizzando le descrizioni testuali.

Perché vengono svolti questi test?

Si vuole dunque verificare la capacità dei VLM di riuscire a individuare le regole astratte che distinguono due gruppi di immagini, applicarle a nuovi esempi e generalizzarle quando cambia la natura dei dati. Il confronto tra KANDY, Bongard-RWR+ e il dataset misto permette di osservare queste capacità sia su immagini "astratta"e sia su immagini "concrete"; l'idea del test misto, ovvero quello con l'intersezione dei due tipi di esempi, sarebbe quella di verificare se un contesto appreso da immagini astratte aiuti la classificazione di esempi provenienti da RWR+.

Come metriche di valutazione utilizzeremo le seguenti:

- Accuracy: quota di classificazioni corrette; fornisce una misura immediata delle prestazioni sui singoli esempi.
- Balanced accuracy: media del richiamo dei due gruppi; è utile perché il numero di immagini per lato non è sempre identico.
- Correttezza semantica della regola: valuta se la regola formulata dal modello corrisponde al concetto atteso, anche quando usa parole diverse; serve a misurare induzione e generazione senza basarsi sulla sola uguaglianza testuale.
- Hit@20: verifica se la regola corretta compare tra le 20 ipotesi prodotte; corrisponde direttamente al test di generazione con 20 proposte.

### Overview dei modelli utilizzati e impostazioni di utilizzo