<div id="top"></div>

[![LinkedIn][linkedin-shield]][linkedin-url]

## Qu'est-ce qu'une stratégie ? Qu'est-ce que "BigWill" ?

BigWill est une stratégie de trading de crypto-monnaie créée par [CryptoRobots](https://github.com/CryptoRobotFr/) .

Une stratégie étant : sous quelles conditions le bot va acheter et/ou vendre. Si vous voulez comprendre comment fonctionne la stratégie du BigWill, vous pouvez regarder [cette vidéo technique](https://www.youtube.com/watch?v=OLnftTstVks) qui explique le fonctionnement de cette stratégie, vous n'êtes en aucun obligé de comprendre le fonctionnement de la stratégie pour mettre en place le bot, mais si le bot ne performe pas comme vous le souhaitez, il est intéressant de comprendre pourquoi.

## Qu'est-ce que le Bot-Trading-Advanced ?

Bot-Trading-Advanced est un bot de trading qui va devoir être executé une fois par heure. Contrairement aux bots d'origine, il simplifie toutes les notifications que fera votre bot de trading.

Le bot utilise l'API de la plateforme d'exchange [FTX](https://ftx.com/eu/referrals#a=102285520) pour intéragir avec le marché des cryptos-monnaies.
Il va détecter et choisir : quand acheter et quand vendre telle ou telle crypto-monnaie selon la stratégie que vous lui indiquerez (par défaut c'est la stratégie BigWill qui est en place dans le code (d'autres stratégies sont proposées sur le compte de [CryptoRobots](https://github.com/CryptoRobotFr/) .)). 

/!\ Attention, je ne garantie en aucun cas les performances de ce bot en l'état, à utiliser à vos risques.

Je vous recommande de mettre en place votre propre stratégie que vous aurez déterminer à l'aide de backtests.
Vous pouvez également consulter un autre de mes projets github pour limiter la sur-optimisation d'une stratégie lors d'un backtest : [Analyseur-PBM](https://github.com/titouannwtt/Analyseur-PBM)


Depuis le fichier de configuration, il est possible de lister toutes les crypto-monnaies que l'on souhaite acheter et vendre.

Une fois le bot mis en place, vous devrez mettre un montant de départ sur la plateforme [FTX](https://ftx.com/eu/referrals#a=102285520), configurer vos API, paramétrer les notifications telegram puis laisser le bot faire son travail sur une longue période (1 mois, 1 an, 3 ans, 10 ans, ...) en espérant faire du profit.

## Exemple de retours Telegram :
![](https://i.gyazo.com/34b079ce0117ed43c123a59d56af3a2e.png)

## Exemple de retours logs lors de l'execution :
![](https://i.gyazo.com/718a524187989a679b041f9e72943c67.png)

## Code

Réalisé en Python, ce code a initialement été réalisé par :
[CryptoRobots](https://github.com/CryptoRobotFr/cBot-Project/blob/main/live_strategy/big_will_v2_live.py) 

J'ai amélioré et rajouté du contenu à ce code permettant :
* de centraliser l'entièreté des configurations en un même fichier config.
* de recevoir des notifications Telegram lorsque vous le désirez
* d'obtenir des statistiques détaillées sur l'évolution du solde du compte et un suivi des performances du bot sur du long terme

### Installation

1. Héberger le bot de trading (tous les fichiers présents sur ce repos) sur une machine ubuntu ou debian continuellement allumée : 
>git clone https://github.com/titouannwtt/bot-trading-advanced.git

Si vous rencontrez des difficultés, vous pouvez suivre [cette vidéo](https://www.youtube.com/watch?v=TbZ9BVAW_SA), le début de cette vidéo explique comment obtenir et se connecter à une machine ubuntu.

2. Installer les librairies nécessaires :
>pip install -r requirements.txt 

3. Installer et configurer [telegram_send](https://github.com/rahiel/telegram-send#installation) sur votre machine pour recevoir les notifications Telegram. Si vous rencontrez des difficultés, vous pouvez suivre [cette vidéo](https://www.youtube.com/watch?v=dtLnO9AuFuk).

4. Entrez votre clé API de la plateforme [FTX](https://ftx.com/eu/referrals#a=102285520) dans le fichier de configuration "config-bot.cfg".

5. Indiquer l'emplacement de votre fichier historiques-soldes.dat dans le fichier de configuration "config-bot.cfg".

6. Aller à la ligne 34 du bot : "bot_bigwill.py" et changer le chemin vers le fichier de configuration : config.read('/home/ubuntu/bot-bigwill/config-bot.cfg')

7. Lancer le bot toutes les heures via la commande "python3 bot_bigwill.py" dans le crontab-e comme expliqué dans [la vidéo](https://www.youtube.com/watch?v=TbZ9BVAW_SA) de l'étape 1.

## Exemples de ligne à ajouter dans crontab pour executer le bot toutes les heures

* 0 * * * * python3 /home/ubuntu/bot-bigwill/bot_bigwill.py >> /home/ubuntu/bot-bigwill/logs-executions.log
* 0 * * * * python3 bot_bigwill.py
* 0 * * * * python3 /home/ubuntu/bot_bigwill.py

# Remerciement :
Ce code vous est partagé gratuitement, vous pouvez me remercier en utilisant un de mes liens d'affiliations :

- FTX : https://ftx.com/eu/profile#a=titouannwtt

- Binance : https://www.binance.me/fr/activity/referral/offers/claim?ref=CPA_00C08H2X8E

Ou en me faisant des dons cryptos :

- Adresse BTC : 3GYhBgZMfgzqjYhVhc2w53oMcvZb4jfGfL

- Adresse ETH (Réseau ERC20) : 0x43fC6F9B8b1CfBd83b52a1FD1de510effe0A49a7

- Adresse SOL : 5QKaHfJWxAZ6sbU5QMb2e14yAAZ45iBH91SBgnheK26v

<p align="right">(<a href="#top">back to top</a>)</p>

[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/titouan-wtt/
