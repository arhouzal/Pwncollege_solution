from scapy.all import IP, TCP, sr1, send

# 1. Création et envoi du SYN en attendant une réponse (sr1 au lieu de send)
syn_packet = IP(dst="10.0.0.2") / TCP(sport=31337, dport=31337, seq=31337, flags="S")

print("[*] Envoi du SYN...")
syn_ack = sr1(syn_packet, timeout=2) # Capture du paquet SYN+ACK

if syn_ack and syn_ack.haslayer(TCP) and syn_ack[TCP].flags == "SA":
    print(f"[+] SYN+ACK reçu ! Seq du serveur (B) : {syn_ack.seq}")
    
    # 2. Construction du ACK final en utilisant les variables capturées
    ack_packet = IP(dst="10.0.0.2") / TCP(
        sport=31337, 
        dport=31337, 
        seq=syn_ack.ack,       # A + 1 (Le serveur nous dicte notre prochaine seq)
        ack=syn_ack.seq + 1,   # B + 1 (On incrémente la seq aléatoire du serveur)
        flags="A"
    )
    
    print("[*] Envoi du ACK...")
    send(ack_packet)
    print("[+] Handshake terminé !")
else:
    print("[-] Aucune réponse SYN+ACK reçue ou mauvais flags.")

"""
if syn_ack (Vérification de la réception) :
La fonction sr1() possède un timeout (un délai d'attente maximum). Si le serveur cible ne répond pas, ou si le paquet se perd,
la variable syn_ack contiendra None. Cette première condition vérifie qu'un paquet a bien été capturé. 
Si c'est None, Python s'arrête là et passe au else.

and syn_ack.haslayer(TCP) (Vérification de l'encapsulation) :
Sur un réseau, beaucoup de trafic circule (ARP, ICMP, etc.). Scapy aurait très bien pu capturer un paquet de broadcast ou un ping au lieu de la réponse du serveur.
La méthode .haslayer(TCP) confirme que le paquet capturé possède bien une couche Transport de type TCP. Sans cette vérification, la condition suivante
ferait planter le script avec une erreur d'attribut.

and syn_ack[TCP].flags == "SA" (Vérification de l'état du protocole) :
En Scapy, la syntaxe paquet[Couche] permet d'accéder aux champs d'un protocole spécifique. Ici, on accède à l'en-tête TCP et on vérifie son champ flags.
On s'assure que le serveur a bien répondu avec les drapeaux SYN et ACK ("SA"). Si le serveur avait refusé la connexion (par exemple avec un drapeau RST ou FIN),
cette condition empêcherait le script d'envoyer le troisième paquet du handshake dans le vide.
"
