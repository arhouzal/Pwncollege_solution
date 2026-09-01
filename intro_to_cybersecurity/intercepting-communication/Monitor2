Ce document présente l'analyse technique, les concepts théoriques et la démarche méthodologique appliqués pour capturer,
 isoler et reconstruire un flag transmis de manière fragmentée et lente via une socket TCP sur le port 31337.
1. Principes Théoriques et Notions Réseau Exploitées

------Le Modèle TCP et la Notion de Flux (Stream)--------
Le protocole TCP (Transmission Control Protocol) est orienté connexion. Contrairement à UDP, il garantit la livraison ordonnée et sans perte des données en établissant un canal de communication bidirectionnel.
 
 Qu'est-ce qu'un flux TCP ? Une connexion TCP unique ne se résume pas seulement à un port d'écoute. Elle est identifiée de manière unique par un quadruplet (4-tuple) :

1 : Adresse IP source

2 : Port source (attribué dynamiquement par le client)

3 : Adresse IP de destination

4 : Port de destination (ex: 31337)

Le fait que plusieurs connexions successives ou simultanées pointent vers le même port 31337 du serveur ne crée pas une seule
conversation, mais plusieurs flux distincts (tcp.stream 0, tcp.stream 1, etc.), chacun possédant son propre port source unique.

----------Guide Pratique et Explication des Commandes--------

Pour intercepter l'ensemble des communications arrivant sur le port du challenge sans saturer le disque :

#1 : tshark -i eth0 -f "port 31337" -w capture_longue.pcap

-i eth0 : Désigne l'interface réseau à écouter.

-f "port 31337" : Filtre de capture BPF (Berkeley Packet Filter). Il s'applique au niveau du noyau pour ne capturer que les paquets liés au port cible, 
éliminant le trafic parasite (DNS, SSH, etc.).

-w capture_longue.pcap : Enregistre les paquets bruts dans un fichier pcap standard pour une analyse différée.

#2 : tshark -r capture_longue.pcap -Y "tcp.port == 31337" -T fields -e tcp.stream | sort -u

-r : Lit le fichier de capture existant.

-Y : Applique un filtre d'affichage post-capture.

-T fields -e tcp.stream : Extrait uniquement le numéro de flux attribué par Wireshark à chaque conversation.

sort -u : Trie la liste et supprime les doublons pour obtenir la liste de tous les essais de connexion (de 0 à N).
# 3 :tshark -r capture_longue.pcap -Y "tcp.stream eq 0 and tcp.len > 0" -T fields -e tcp.payload | xxd -r -p 

-Y "tcp.stream eq 0 and tcp.len > 0" : Sélectionne exclusivement le flux numéro 0 (où la transmission s'est déroulée du début à la fin) et écarte les paquets vides (tcp.len > 0), comme les paquets d'acquittement pur (ACK) qui ne contiennent aucune donnée utile.

-T fields -e tcp.payload : Demande à TShark d'isoler uniquement la charge utile (payload) brute de chaque paquet, restituée sous forme de chaînes hexadécimales.

| xxd -r -p : Transmet ces données hexadécimales à l'utilitaire xxd (-r pour inverser/convertir, -p pour le format brut continu), transformant les octets bruts en texte ASCII lisible d'un seul bloc, révélant instantanément le flag complet.
