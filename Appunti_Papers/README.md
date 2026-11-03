# Appunti paper tesi di laurea Magistrale

## Idee e Metodi dai paper proposti

### Bongard in Wonderland: Visual Puzzles that Still Make AI Go Mad?
Link: https://arxiv.org/pdf/2410.19546

Riassunto e concetti chiave:

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
6. Gli umani sembrano migliori nei concetti spaziali, i modelli nei ragionamenti geometrici astratti.
7. Gli autori individuano 4 comportamenti per i vlm:
    - Tipo I   :  il modello fa bene i primi due test ma non riesce nel terzo; non succede quasi mai, l'idea è che se il modello stabilisce la regola e la riconosce negli esempi allora riesce anche a generarla nelle 20 ipotesi
    - Tipo II  :  il modello fa bene gli utlimi due test; significa che il modello non riesce a "unire i puntini", gli autori mostrano che c'è un numero discreto di errori di questo tipo, l'errore suggerisce una mancanza nel riuscire appunto a integrare la percezione col ragionamento. 
    - Tipo III :  il modello fa bene il primo e il terzo; capisce cioè la regola generale ma non riesce a ritrovarla nelle singole istanze, gran parte degli errori che il modello compie appartengono a questa categoria, ovvero il modello quando si tratta di capire il quadro generale eccelle, mentre pecca nel particolare (ciò potrebbe essere dovuto anche all'architettura dei vit e transformer in generale ma ciò richiederebbe un'analisi più approfondita).
    - Tipo IV  :  il modello si comporta bene in tutti e tre i test

Dettagli Interessanti:

Partendo dalle caratteristiche del punto 4., gli autori definisco i tre test del punto 5. e vanno ad analizzare le intersezioni di successi/fallimenti in 7.
I test sono una tupla booleana del tipo (t1, t2, t3) = (X, X, X) dove X è un valore 0/1 che indica il fallimento o il superamento del test; scartati i singoli fallimenti e successi, le casistiche da analizzare sono quelle in cui almeno due test sono superati e l'altro no. 

I bongard più ardui da risolvere per il vlm sono:
- collinearità dei punti: da un lato, i punti all'interno del contorno sono allineati su una retta; dall'altro, non lo sono.
- figure identiche: i quadrilateri pieni devono essere identici fra loro oppure differenti.
- inviluppo: la regola riguarda il fatto che l'inviluppo convesso delle croci formi oppure no un triangolo equilatero.

Punti di forza:

Interessante analisi delle capacità del modello e degli errori del modello.

Criticità:

- classificatore automatico: usano un llm-as-judge, questo permette di considerare due risposte espresse in modo diverso come equivalenti in modo automatico; d'altrocanto potrebbe non capirez(?)
- pre-training su bongard problems: i problemi bongard potrebbero essere stati impiegati nel pre-training del modello
- non è stato rilevato il motivo che causa queste discrepanze tra i tipi di errori ottenuti


### BONGARD-RWR+: REAL-WORLD REPRESENTATIONS OF FINE-GRAINED CONCEPTS IN BONGARD PROBLEMS
Link: https://arxiv.org/pdf/2508.12026

Riassunto e concetti chiave:

1. Si utilizza un dataset sintetico simile a Bongard-Hoi e discendente diretto di Bongard-RWR, il quale ci permette di verficare la capacità del modello di estrarre concetti astratti da immagini reali
2. La generazione delle immagini segue questa pipeline:
    - Si prendono in esami problemi uguali a quelli visti nel test 1 del paper precedente (6 problemi vengono esclusi perché non si riescono a generari esempi nel mondo reale)
    - Un modello genera una descrizione positiva e una descrizione negativa dell'esempio fornito
    - Si ampliano tali descrizioni dell'immagine tramite un modello, questo introduce frasi tipo "la linea potrebbe essere un uomo in pidi o un albero" (15 varianti per esempio)
    - Si vanno a generare immagini a partire dalle descrizioni ottenute
    - Le immagini vengono poi annotate da due esperti
    - Le immagini vengono poi raggruppate in esempi composti da 6 immagini basandosi sulla similarità coseno su coppie di embeddings, si scelgono 6 immagini che minimizzano tale metrica
    - Per ciascuna delle 54 matrici orginali, 10 matrici alternative destre e 10 matrici alternative sinistre per cui 54x10x10 matrici totali, cioè 5400
    - Per ciasun esempio si ha anche un esempio di test quindi gli insiemi sono composti da 6 immagini + 1 di test
3. Gli autori stabiliscono 4 comportamenti chiave:
   - Percezione  : il modello riesce a ricavare info visive pertinenti
   - Confronto   : il modello riesce a stabilire quale regola divide i due gruppi
   - Selezione   : il modello riesce a scegliere la coppia di regole giusta
   - Generazione : il modello riesce a generare la regola corretta
4. Gli autori stabiliscono poi sei esperimenti chiave:
    - Il modello riceve le dodici immagini di contesto e una singola immagine di test. Deve stabilire se quest'ultima appartenga al gruppo sinistro oppure al destro; misura la capacità di utilizzare il contesto per assegnare un nuovo esempio alla categoria corretta
    - Il modello riceve entrambe le immagini di test, una per ciascun lato, e deve assegnarle ai rispettivi gruppi; misura la capacità di classificare due esempi in presenza dello stesso contesto, con una possibile difficoltà aggiuntiva legata alla coerenza fra le risposte
    - Prima, un modello image-to-text trasforma le immagini di contesto e di test in descrizioni linguistiche. Poi un modello testuale utilizza queste descrizioni per assegnare l'immagine di test al gruppo corretto; misura La capacità di classificare due esempi sulla base di descrizioni linguistiche, mantenendo la distinzione fra i due concetti
    - Si applica la stessa idea del D1S, ma alle due immagini di test. Entrambe vengono descritte in linguaggio naturale e il modello deve assegnarle ai lati corretti; misura La capacità di classificare due esempi sulla base di descrizioni linguistiche, mantenendo la distinzione fra i due concetti
    - Il modello riceve la matrice Bongard e un insieme di concetti candidati. Deve selezionare quello che descrive correttamente la distinzione fra i due gruppi; misura la capacità di identificare il concetto corretto fra alternative esplicitamente disponibili
    - Il modello riceve la matrice e deve descrivere autonomamente in linguaggio naturale il concetto che distingue i due gruppi. Gli autori esaminano sia la generazione da immagini sia quella da descrizioni linguistiche; misura la capacità di produrre una spiegazione linguistica della regola senza avere a disposizione una lista di risposte candidate
5. Vengono stabilite tre tipi di risultati:
   - prestazioni basse con input visivi, alte con input testuali; difficoltà nella percezione
   - prestazione basse con generazione e alte in selezione; difficoltà nella formulazione
   - prestazioni migliori con una sola immagine rispetto che due; difficoltà di mantenere coerenti due classificazioni ma anche differenze nei prompt e nel formato dell'output
6. I risultati sono i seguenti:
   - i VLM open-weight ottengono prestazioni vicine al caso nel task I1S (circa 48–50%), mostrando difficoltà nell'individuare la proprietà discriminante a partire dagli esempi visivi
   - trasformare le immagini in descrizioni testuali può migliorare la classificazione. In D1S, Qwen2-VL raggiunge il 58%, mentre InternVL2.5 e DeepSeek-R1 raggiungono il 57%. Il miglioramento, però, non si verifica uniformemente in tutti i task
   - InternVL2.5 78B raggiunge il 91% con due alternative, ma scende al 57% con sedici. Aumentare il numero di distrattori rende la selezione più difficile
   - i modelli ottengono punteggi generalmente bassi nelle metriche testuali. Generare autonomamente una descrizione del concetto è più difficile che selezionare una risposta già formulata.
   - proprietà come forma, dimensione e ramificazione risultano generalmente più accessibili; contorno, rotazione e angoli sono più difficili da riconoscere
   - modelli più grandi tendono a ottenere risultati migliori
   - le immagini in scala di grigi producono risultati simili o talvolta migliori di quelle a colori, suggerendo che il colore possa introdurre distrazioni quando non è rilevante per il concetto.
   - mostrare lo stesso concetto attraverso immagini più varie può facilitare il riconoscimento. Nel Concept Selection con 16 candidati, InternVL2.5 passa dal 50% sui problemi a bassa diversità al 62% su quelli ad alta diversità
   - l'inclusione di immagini scartate durante la verifica umana peggiora le prestazioni dei modelli, confermando l'importanza del controllo della qualità concettuale.
   -  Gemini 2.5 Pro raggiunge il 65% in I1S, il 70% in D1S e l'82% nel Concept Selection con 16 alternative, superando i modelli open esaminati, ma senza risolvere tutte le difficoltà del benchmark
7. I vlm faticano a riconoscere e formulare concetti astratti quando devono individuare caratteristiche visive sottili o relazioni geometriche. Le prestazioni migliorano in condizioni più guidate, come la selezione multipla o l'uso di descrizioni testuali

Dettagli Interessanti:
- metodo di generazione
- immagini scartate da umani peggiorano la perfomance
- gemini sembra il migliore, quindi forse gemma avrebbe performance migliori
- contorno, rotazioni e angoli sembrano essere i più difficili

Punti di forza:
-idea generale del paper

Criticità:

### BONGARD-LOGO: A New Benchmark for Human-Level Concept Learning and Reasoning
Link: https://arxiv.org/pdf/2010.00763

Riassunto e concetti chiave:

1. Paper "capostipite": gli autori fanno notare che mentre gli umani, anche i bambini, riescono a generalizzare anche con pochi dati a disposizione, le macchine invece sembrano avere bisogno di ingenti quantità di dati e spesso non riescono a generalizzare alla stessa maniera
2. Gli autori dunque vorrebbero far passare i modelli dal semplice pattern-recognition alla capacità di generalizzazione degli umani
3. I bongard originali sono 100 quesiti, ma per addestrare un modello sono pochi, quindi si passa a 12.000 problemi. Il modello osserva 6 esempi positivi, 6 negativi e poi classifica nuovi esempi. Si tratta di un task di classificazione few-shot
4. Nel paper gli autori individuano 3 proprietà fondamentali della cognizione umana:
   - Context-dependent Perception: cioè una stessa configurazione può essere interpretata differentemente in base al contesto in cui si trova, (ex. un un triangolo equilatero ha un significato diverso se è mostrato assieme ad altri 5 triangoli o ad altri 5 poligoni regolari). In altre parole la percezione P dell'umano può essere espressa come una funzione dell'oggetto visivo X e del contesto C, cioè P(X,C).
   - Analogy-making perception: cioè gli umani possono reinterpretare una struttura visiva attraverso un concetto differente, trasferendo alla nuova rappresentazione caratteristiche che la definiscono. (ex. posso interpretare una sequenza di zigzag come una linea, oppure quattro triangoli alla stessa distanza tra loro con quattro angoli retti tra di loro come un quadrato)
   - Few sample, infinite vocabulary: gli umani anche da pocchissimi esempi riescono a identificare quelle caratteristiche che vanno a definire la "matrice" di tutti i possibili problemi. I modelli dunque non possono semplicemente limitarsi a riconoscere un insieme finito di forme, ma deve riuscire ad apprendere come viene generato il nuovo concetto. (ex. vogliamo addestrare il modello su traingolo e quadrato ma vogliamo che poi, in autonomia, capisca che mettendo il triangolo sopra il quadrato si ottenga una casa.)
5. Gli autori "disegnano" gli esempi attraverso il linguaggio di programmazione LOGO; l'idea è che ci sia una tartaruga che si muove su una superficie seguendo delle istruzioni, la traiettoria definisce una figura. Questo benchmark utilizza solo due azioni Action € {line, arc}, ogni Azione a = (tipo di movimento, lunghezza del movimento e angolo), il tipo può essere normale, a zigzag, cerchio ecc... In questo modo possiamo generare molti esempi mmantenendo indicazioni su come tali forme sono state generate.
6. Gli autori testano poi i modelli sia con Few-Shot Learning, la cui filosofia è quella di utilizzare pochi esempi e poi testare, e tramite tecniche di Meta-Learning, come MAML, in cui l'obbiettivo è quello di "imparare a imparare", o meglio imparare una rappresentazione che sia abbastanza vicina a tutte le altre rappresentazioni.

s = start, a = arrive

    o-o-a            o-o-o
    o-o-o            o-a-o
    s-o-o            o-o-o

più difficile        più facile      raggiungere i vari punti

7. Il meta-learning sembra più efficace dei modelli tradizionali, modelli diversi hanno punti di forza diversi.
8. Quando si fa pre-training le perfomance migliorano ma si ha comunque un po' di overfitting.
9. Quando vengono eliminati dai problemi, quelli relativi a Context-dependent Perception e Analogy-making perception, il task diventa più simile a un task few-shot learning e quindi le perfomance migliorano.
10. Gli esperti umani restano sempre migliori.

Dettagli Interessanti:
- cognizione umana vs modelli

Punti di forza:
- analisi cognizione umana
- tecniche di meta-learning
- provano a cambiare tipo di problemi

Criticità:
- ormai tecniche e modelli risultano datati(?)

### The KANDY Benchmark: Incremental Neuro-Symbolic Learning and Reasoning with Kandinsky Patterns
Link: https://arxiv.org/pdf/2402.17431

Riassunto e concetti chiave:

1. Binding problem: associare correttamente caratteristiche le caratteristiche percettive ai singoli oggetti.
2. Si vuole andare a studiare gli approcci neuro-simbolici.
3. L'idea è quella di far imparare prima concetti semplici e poi farli rituilizzare in task via va più complessi.
4. Un altro spunto è quello di andare a rimuovere via via le etichette dai dati, in modo che il modello impari anche dagli esempi non etichettati.
5. Continual Learning: apprendere progressivamente da task o dati che arrivano nel tempo, cercando di preservare quanto già acquisito
6. Semi-Supervised learning: apprendere una combinazione di esempi etichettati e non etichettati.
7. Gli autori mettono a disposizione un generatore per andare a generare benchmark e curricula di apprendimento.
8. Come funziona la generazione degli esempi:
    1. Definizione task: si specificano regole positivem negative, proprietà, operatori, numero di esmepi e impostazioni di supervisione.
    2. Generazione simbolica: si costruiscono gli alberi di composizione a partire dalle regole yaml.
    3. Il sistema controlla che gli alberi non siano ridondanti e, quando è disponibile, verifica la compatibilità con la regola prolog.
    4. Rendering immagini: gli alberi diventano immagini andando ad applciare alcune variazioni percettive
    5. Assegnazione supervisione: a ogni campione viene associato supervised o unsupervised a seconda della specifica.
    6. Gli esempi vengono separati nei gruppi di trainig, validation e test.
9. Meccanismo di supervisione sparsa: f(t) = ye^-st dove:
    - t€ \[0,1] è la posizione normalizzata dell'esempio nella sequenza
    - y è la prob iniziale di supervisione
    - b è la probabilità finale di supervision
    - s controlla la velocità di decadimento
    - s = log(y/b) questo ci garantisce f(0)=y e f(1)=b
10. Vengono proposte 4 configurazioni sperimentali:
    1. Apprendimento indipentente: ogni classificatore viene addestrato su un task differente
    2. Backbone condiviso: il backbone del modello è lo stesso ma la testa di classificazione è specifica per ogni task
    3. Incrementale: il modello riceve solo i dati del task x e addestra, poi del task x+1 e addestra ecc... permette comunque più epoche sugli stessi dati
    4. Continual Online: elabora un esempio alla volta, non permette più epoche sugli stessi dati.
11. Sono stati usati sia approcci neurali CNN, Resnet e ViT le cui performance si attestano tra 61-72% su kandy easy e 59% su kandy hard, con i modelli senza attention che sembrano essere migliori (+ dettaglio - globale = migliore?); sia apporcci simbolici come Aleph che in kandy easy (benché non venga testato nella percezione) può arrivare sino al 96% mentre su kandy hard arriva massimo al 66%.
12. Per valutare i modelli sono state usate le seguenti metriche:
    - Average Accuracy: sum accuracy / numero task
    - Average Forgetting: quanto il modello abbia perso in prestazioni sui task precdenti rispetto alla migliore accuratezza raggiunta
    - Backward Trasfer: misura quanto l'apprendimento di task successivi abbia impattato sui task precedentemente appresi
    - Forward Transfer: misura quanto ciò che è già stato appreso migliori l'apprendimento di task successivi

Dettagli Interessanti:
- Binding Problem
- Framework Generazione Dataset

Punti di forza:
- Dataset
- Framework Generazione Dataset
- Ampio ventaglio di possibilità di sviluppo con molti modelli base già testati

Criticità:
- Costruzione del dataset personalizzato tramite yaml
