echo "Hello, World!" | nc -u -p 31338 10.0.0.2 31337
# le  -p pour la source  port 

#------- alternatife code python --------------
from scapy.all import IP, UDP, Raw, sr1

# Construction du paquet avec sport=31338 pour satisfaire la condition du serveur
udp = IP(dst="10.0.0.2") / UDP(sport=31338, dport=31337) / Raw(load=b"Hello, World!\n")

print("[*] Envoi du paquet UDP...")
# sr1 envoie le paquet et attend la réponse du serveur contenant le flag
reponse = sr1(udp, timeout=3)

if reponse and reponse.haslayer(Raw):   #  reponse.haslayer pour verifier que c est du udp traffic + reponse = None si la reponse est vide!
    print("\n[+] FLAG REÇU :")
    print(reponse[Raw].load.decode('utf-8', errors='ignore'))  # .load.decode pour acceder au champ de payload  et .decode pour etre en code ascci
else:
    print("[-] Pas de réponse du serveur.")
