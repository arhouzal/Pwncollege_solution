echo "Hello, World!" | nc -u 10.0.0.2 31337
#!! on supprime le \n
#Le mystère vient du comportement de la commande echo sous Linux : par défaut, un simple echo "texte" ajoute automatiquement un retour à la ligne (\n)
#à la fin de la chaîne de caractères avant de l'envoyer. C'est pour cela que le challenge a validé la syntaxe, car le \n était bien présent,
#envoyé de manière implicite par echo.

