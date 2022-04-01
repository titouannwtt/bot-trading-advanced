#
#NAME : BOT BigWill
#STRATEGIES : BigWill
#AUTHORS : Crypto Robot, updated by TitouannWtt/Moutonneux
#ORIGINAL CODE : https://github.com/CryptoRobotFr/cBot-Project/blob/main/live_strategy/big_will_v2_live.py
#VERSION : 2.1
#
#=============================
#	 IMPORTS NECESSAIRES
#=============================

from optparse import Values
import sys
from constantly import ValueConstant
import telegram_send
from numpy import NaN, float64, little_endian
sys.path.append('cBot-Project/utilities')
from cBot_perp_ftx import cBot_perp_ftx
from custom_indicators import CustomIndocators as ci
from spot_ftx import SpotFtx
import ta
import pandas as pd
import time
import ccxt
import datetime
import configparser
import json

#===================================
# INITIALISATION DES CONFIGURATIONS
#===================================

config = configparser.ConfigParser()
now = datetime.datetime.now()
config.read('/home/ubuntu/bot-bigwill/config-bot.cfg')
print("========================\nBOT BIGWILL - "+str(datetime.datetime.now()))
print("Sections recupérées dans le fichier de configuration: "+str(config.sections()))

#=============================
#	AUTHENTIFICATION PART
#=============================

ftx = SpotFtx(
		apiKey=str(config['FTX.AUTHENTIFICATION']['apiKey']),
		secret=str(config['FTX.AUTHENTIFICATION']['secret']),
		subAccountName=str(config['FTX.AUTHENTIFICATION']['subAccountName'])
	)

#=====================
# CONFIGS PAR DEFAULT 
#=====================

timeframe=str(config['STRATEGIE']['timeframe'])
print("Timeframe utilisé :"+str(timeframe))

#=============
# INDICATEURS
#=============
aoParam1=int(config['INDICATORS']['aoParam1'])
aoParam2=int(config['INDICATORS']['aoParam2'])
stochWindow=int(config['INDICATORS']['stochWindow'])
willWindow=int(config['INDICATORS']['willWindow'])

#=================
# HYPERPARAMETRES
#=================
maxOpenPosition = int(config['HYPERPARAMETRES']['maxOpenPosition'])
stochOverBought = float(config['HYPERPARAMETRES']['stochOverBought'])
stochOverSold = float(config['HYPERPARAMETRES']['stochOverSold'])
willOverSold = float(config['HYPERPARAMETRES']['willOverSold'])
willOverBought = float(config['HYPERPARAMETRES']['willOverBought'])
TpPct = float(config['HYPERPARAMETRES']['TpPct'])


#====================
# COLLECTE DES PRIX
#====================
pairList = [
    'BTC/USD',
    'ETH/USD',
    'BNB/USD',
    'LTC/USD',
    'DOGE/USD',
    'XRP/USD',
    'SOL/USD',
    'AVAX/USD',
    'SHIB/USD',
    'LINK/USD',
    'UNI/USD',
    'MATIC/USD',
    'AXS/USD',
    'CRO/USD',
    'FTT/USD',
    'TRX/USD',
    'BCH/USD',
    'FTM/USD',
    'GRT/USD',
    'AAVE/USD',
    'OMG/USD',
    'SUSHI/USD',
    'MANA/USD',
    'SRM/USD',
    'RUNE/USD',
    'SAND/USD',
    'CHZ/USD',
    'CRV/USD'
]

dfList = {}
for pair in pairList:
    # print(pair)
    df = ftx.get_last_historical(pair, timeframe, 210)
    dfList[pair.replace('/USD','')] = df

#===========================
# COLLECTE DES INDICATEURS
#===========================

for coin in dfList:
    # -- Drop all columns we do not need --
    dfList[coin].drop(columns=dfList[coin].columns.difference(['open','high','low','close','volume']), inplace=True)

    # -- Indicators, you can edit every value --
    dfList[coin]['AO']= ta.momentum.awesome_oscillator(dfList[coin]['high'],dfList[coin]['low'],window1=aoParam1,window2=aoParam2)
    dfList[coin]['STOCH_RSI'] = ta.momentum.stochrsi(close=dfList[coin]['close'], window=stochWindow)
    dfList[coin]['WillR'] = ta.momentum.williams_r(high=dfList[coin]['high'], low=dfList[coin]['low'], close=dfList[coin]['close'], lbp=willWindow)
    dfList[coin]['EMA100'] =ta.trend.ema_indicator(close=dfList[coin]['close'], window=100)
    dfList[coin]['EMA200'] =ta.trend.ema_indicator(close=dfList[coin]['close'], window=200)

#=======================================
#  CONDITIONS NECESSAIRES POUR L'ACHAT
#=======================================
def buyCondition(row, previousRow=None):
    if (
        row['AO'] >= 0
        and previousRow['AO'] > row['AO']
        and row['WillR'] < willOverSold
        and row['EMA100'] > row['EMA200']
    ):
        return True
    else:
        return False

#=======================================
#  CONDITIONS NECESSAIRES POUR LA VENTE
#=======================================
def sellCondition(row, previousRow=None):
    if (
        (row['AO'] < 0
        and row['STOCH_RSI'] > stochOverSold)
        or row['WillR'] > willOverBought
    ):
        return True
    else:
        return False

#=========================================================================================
#  PERMET D'AJOUTER DES ELEMENTS DE TEXTE AU MESSAGE FINAL QUI SERA ENVOYE SUR Telegram
#=========================================================================================
message=" "
def addMessageComponent(string):
	global message
	message=message+"\n"+string
	
#==============================================================
# RECUPERE LA DATE EXACTE DU JOUR
#==============================================================

date = datetime.datetime.now()
todayJour=date.day
todayMois=date.month
todayAnnee=date.year
todayHeure=date.hour
todayMinutes=date.minute
addMessageComponent(f"{date}\nBOT-BIGWILL")
addMessageComponent("===================\n")
addMessageComponent("Actions prises par le bot :")

#==============================================================
# RECUPERE LE MONTANT TOTAL D'USD SUR LE SUBACCOUNT SPECIFIE
#==============================================================
coinBalance = ftx.get_all_balance()
coinInUsd = ftx.get_all_balance_in_usd()
print(coinBalance)
usdBalance = coinBalance['USD']
del coinBalance['USD']
del coinInUsd['USD']
totalBalanceInUsd = usdBalance + sum(coinInUsd.values())
coinPositionList = []
for coin in coinInUsd:
    if coinInUsd[coin] > 0.05 * totalBalanceInUsd:
        coinPositionList.append(coin)
openPositions = len(coinPositionList)

#cette variable nous servira à la fin pour déterminer si on a fait des actions ou pas
#si la variable est toujours à 0 c'est qu'il n'y a eu aucun changement et qu'on ne prévient pas le bot telegram de nous notifier
changement=0

# On vérifie si on a des cryptos actuellement achetés 
for coin in coinPositionList:
        #On vérifie si c'est le moment de les vendre ou pas
        if sellCondition(dfList[coin].iloc[-2], dfList[coin].iloc[-3]) == True:
            openPositions -= 1
            changement=changement+1
            symbol = coin+'/USD'
            cancel = ftx.cancel_all_open_order(symbol)
            time.sleep(1)
            sell = ftx.place_market_order(symbol,'sell',coinBalance[coin])
            print(cancel)
            print("Vente", coinBalance[coin], coin, sell)
            addMessageComponent(f"Vente :\n • {coin}\n • Prix actuel {coinBalance[coin]} $\n")
        else:
            print("On garde")
            addMessageComponent(f"On garde :\n • {coin}\n • Prix actuel {coinBalance[coin]}\n")

#On vérifie si on peut acheter
if openPositions < maxOpenPosition:
    for coin in dfList:
        if coin not in coinPositionList:
            #On vérifie si il y a des choses intéressantes
            if buyCondition(dfList[coin].iloc[-2], dfList[coin].iloc[-3]) == True and openPositions < maxOpenPosition:
                time.sleep(1)
                changement=changement+1
                usdBalance = ftx.get_balance_of_one_coin('USD')
                symbol = coin+'/USD'

                buyPrice = float(ftx.convert_price_to_precision(symbol, ftx.get_bid_ask_price(symbol)['ask'])) 
                tpPrice = float(ftx.convert_price_to_precision(symbol, buyPrice + TpPct * buyPrice))
                buyQuantityInUsd = usdBalance * 1/(maxOpenPosition-openPositions)

                if openPositions == maxOpenPosition - 1:
                    buyQuantityInUsd = 0.95 * buyQuantityInUsd

                buyAmount = ftx.convert_amount_to_precision(symbol, buyQuantityInUsd/buyPrice)

                buy = ftx.place_market_order(symbol,'buy',buyAmount)
                time.sleep(2)
                tp = ftx.place_limit_order(symbol,'sell',buyAmount,tpPrice)
                try:
                    tp["id"]
                except:
                    time.sleep(2)
                    tp = ftx.place_limit_order(symbol,'sell',buyAmount,tpPrice)
                    pass
                addMessageComponent(f"Achat :\n • {coin}\n • Prix actuel {buyPrice}\n • Quantité {buyAmount}\n")
                addMessageComponent(f"Place : {buyAmount} {coin} TP à {tpPrice} $\n")
                print("Achat",buyAmount,coin,'at',buyPrice,buy)
                print("Place",buyAmount,coin,"TP at",tpPrice, tp)

                openPositions += 1

coinBalance = ftx.get_all_balance()
coinInUsd = ftx.get_all_balance_in_usd()
print(coinBalance)
usdBalance = coinBalance['USD']
del coinBalance['USD']
del coinInUsd['USD']
totalBalanceInUsd = usdBalance + sum(coinInUsd.values())
usdAmount = totalBalanceInUsd
soldeMaxAnnee=usdAmount
soldeMaxMois=usdAmount
soldeMaxJour=usdAmount
soldeMinAnnee=usdAmount
soldeMinMois=usdAmount
soldeMinJour=usdAmount

jourMinAnnee=moisMinAnnee=anneeMinAnnee=heureMinAnnee=0
jourMinMois=moisMinMois=anneeMinMois=heureMinMois=0
jourMinJour=moisMinJour=anneeMinJour=heureMinJour=0

jourMaxAnnee=moisMaxAnnee=anneeMaxAnnee=heureMaxAnnee=0
jourMaxMois=moisMaxMois=anneeMaxMois=heureMaxMois=0
jourMaxJour=moisMaxJour=anneeMaxJour=heureMaxJour=0

print(f"Solde du compte => {usdAmount} $")

#==================================================
# Lecture des anciennes données dans le fichier .dat
#==================================================
with open(str(config['FICHIER.HISTORIQUE']['soldeFile']), "r") as f:
	for line in f:
		if "#" in line:
			# on saute la ligne
			continue
		data = line.split()
		jour=int(data[0])
		mois=int(data[1])
		annee=int(data[2])
		heure=int(data[3])
		minutes=int(data[4])
		solde=float(data[5])
        
		#permet de trouver le jour où vous avez eu le plus petit solde cette année
		if(soldeMinAnnee>solde and annee==todayAnnee):
			soldeMinAnnee=solde
			jourMinAnnee=jour
			moisMinAnnee=mois
			anneeMinAnnee=annee
			heureMinAnnee=heure
            
		#permet de trouver le jour où vous avez eu le plus petit solde ce mois-ci
		if(soldeMinMois>solde and annee==todayAnnee and mois==todayMois):
			soldeMinMois=solde
			jourMinMois=jour
			moisMinMois=mois
			anneeMinMois=annee
			heureMinMois=heure

		#permet de trouver l'heure où vous avez eu le plus petit solde aujourd'hui
		if(soldeMinJour>solde and annee==todayAnnee and mois==todayMois and jour==todayJour):
			soldeMinJour=solde
			jourMinJour=jour
			moisMinJour=mois
			anneeMinJour=annee
			heureMinJour=heure

		#permet de trouver le jour où vous avez eu le plus gros solde cette année
		if(soldeMaxAnnee<solde and annee==todayAnnee):
			soldeMaxAnnee=solde
			jourMaxAnnee=jour
			moisMaxAnnee=mois
			anneeMaxAnnee=annee
			heureMaxAnnee=heure
            
		#permet de trouver le jour où vous avez eu le plus gros solde ce mois-ci
		if(soldeMaxMois<solde and annee==todayAnnee and mois==todayMois):
			soldeMaxMois=solde
			jourMaxMois=jour
			moisMaxMois=mois
			anneeMaxMois=annee
			heureMaxMois=heure

		#permet de trouver l'heure où vous avez eu le plus gros solde aujourd'hui
		if(soldeMaxJour<solde and annee==todayAnnee and mois==todayMois and jour==todayJour):
			soldeMaxJour=solde
			jourMaxJour=jour
			moisMaxJour=mois
			anneeMaxJour=annee
			heureMaxJour=heure

		#permet de trouver le solde de 6 heures auparavant
		if(todayHeure<=6):
			if ((todayJour-1==jour) and (todayMois==mois) and (todayAnnee==annee)) :
				if((24-(6-todayHeure)==heure)):
					solde6heures=solde
			elif (todayJour==1 and ((todayMois-1==mois) and (todayAnnee==annee)) or ((todayMois==1) and (todayAnnee-1==annee) and (jour==31))) :
				if((24-(6-todayHeure)==heure)):
					solde6heures=solde
		elif ( (todayHeure-6==heure) and (todayJour==jour) and (todayMois==mois) and (todayAnnee==annee) ) :
			solde6heures=solde
			
		#permet de trouver le solde de 12 heures auparavant
		if(todayHeure<=12):
			if ((todayJour-1==jour) and (todayMois==mois) and (todayAnnee==annee)) :
				if((24-(12-todayHeure)==heure)):
					solde12heures=solde
			elif (todayJour==1 and ((todayMois-1==mois) and (todayAnnee==annee)) or ((todayMois==1) and (todayAnnee-1==annee) and (jour==31))) :
				if((24-(12-todayHeure)==heure)):
					solde12heures=solde
		elif ( (todayHeure-12==heure) and (todayJour==jour) and (todayMois==mois) and (todayAnnee==annee) ) :
			solde12heures=solde
		#permet de trouver le solde de 1 jours auparavant
		if(todayJour<=1):
			if ((todayMois-1==mois) and (todayAnnee==annee)) or ((todayMois==1 and mois==12) and (todayAnnee-1==annee)) :
				if (mois==1 or mois==3 or mois==5 or mois==7 or mois==8 or mois==10 or mois==12) :
					if((31-todayJour+1==jour)):
						solde1jours=solde
				else :
					if((30-todayJour+1==jour)):
						solde1jours=solde
		elif ( (todayJour-1==jour) and (todayMois==mois) and (todayAnnee==annee) ) :
			solde1jours=solde
		#permet de trouver le solde de 3 jours auparavant
		if(todayJour<=3):
			if ((todayMois-1==mois) and (todayAnnee==annee)) or ((todayMois==1 and mois==12) and (todayAnnee-1==annee)) :
				if (mois==1 or mois==3 or mois==5 or mois==7 or mois==8 or mois==10 or mois==12) :
					if((31-todayJour+3==jour)):
						solde3jours=solde
				else :
					if((30-todayJour+3==jour)):
						solde3jours=solde
		elif ( (todayJour-3==jour) and (todayMois==mois) and (todayAnnee==annee) ) :
			solde3jours=solde
		
		#permet de trouver le solde de 7 jours auparavant
		if(todayJour<=7):
			if ((todayMois-1==mois) and (todayAnnee==annee)) or ((todayMois==1 and mois==12) and (todayAnnee-1==annee)) :
				if (mois==1 or mois==3 or mois==5 or mois==7 or mois==8 or mois==10 or mois==12) :
					if((31-todayJour+7==jour)):
						solde7jours=solde
				else :
					if((30--todayJour+7==jour)):
						solde7jours=solde
		elif ( (todayJour-7==jour) and (todayMois==mois) and (todayAnnee==annee) ) :
			solde7jours=solde
			
		#permet de trouver le solde de 14 jours auparavant
		if(todayJour<=14):
			if ((todayMois-1==mois) and (todayAnnee==annee)) or ((todayMois==1 and mois==12) and (todayAnnee-1==annee)) :
				if (mois==1 or mois==3 or mois==5 or mois==14 or mois==8 or mois==10 or mois==12) :
					if((31-todayJour+14==jour)):
						solde14jours=solde
				else :
					if((30-todayJour+14==jour)):
						solde14jours=solde
		elif ( (todayJour-14==jour) and (todayMois==mois) and (todayAnnee==annee) ) :
			solde14jours=solde
			
		#permet de trouver le solde de 1 mois auparavant
		if(todayMois==1 and mois==12 and annee==todayAnnee-1 and todayJour==jour) :
			solde1mois=solde
		elif(todayMois-1==mois and annee==todayAnnee and todayJour==jour) :
			solde1mois=solde
			
		#permet de trouver le solde de 2 mois auparavant
		if(todayMois==1 and mois==11 and annee==todayAnnee-1 and todayJour==jour) :
			solde2mois=solde
		if(todayMois==2 and mois==12 and annee==todayAnnee-1 and todayJour==jour) :
			solde2mois=solde
		elif(todayMois-2==mois and annee==todayAnnee and todayJour==jour) :
			solde2mois=solde
		soldeLastExec=solde

#==================================================
# Enregistrement du solde dans le fichier .dat
#==================================================

todaySolde=usdAmount
with open(str(config['FICHIER.HISTORIQUE']['soldeFile']), "a") as f:
	f.write(f"{todayJour} {todayMois} {todayAnnee} {todayHeure} {todayMinutes} {todaySolde} \n")
	
#=======================================================
# Affiche le bilan de perf dans le message telegram
#=======================================================
addMessageComponent("\n===================\n")
addMessageComponent("Bilan de performance :")
if 'soldeMaxJour' in locals() :
	soldeMaxJour=round(soldeMaxJour,3)
	addMessageComponent(f" - Best solde aujourd'hui : {soldeMaxJour}$ à {heureMaxJour}h")
if 'soldeMaxMois' in locals() and (moisMaxMois !=0):
	soldeMaxMois=round(soldeMaxMois,3)
	addMessageComponent(f" - Best solde ce mois-ci : {soldeMaxMois}$ le {jourMaxMois}/{moisMaxMois} à {heureMaxMois}h")
if 'soldeMaxAnnee' in locals() and (moisMaxAnnee !=0):
	soldeMaxAnnee=round(soldeMaxAnnee,3)
	addMessageComponent(f" - Best solde cette année : {soldeMaxAnnee}$ le {jourMaxAnnee}/{moisMaxAnnee}/{anneeMaxAnnee} à {heureMaxAnnee}h")
    
addMessageComponent(" ")

if 'soldeMinJour' in locals():
	soldeMinJour=round(soldeMinJour,3)
	addMessageComponent(f" - Pire solde aujourd'hui : {soldeMinJour}$ à {heureMinJour}h")
if ('soldeMinMois' in locals()) and (moisMinMois !=0):
	soldeMinMois=round(soldeMinMois,3)
	addMessageComponent(f" - Pire solde ce mois-ci : {soldeMinMois}$ le {jourMinMois}/{moisMinMois} à {heureMinMois}h")
if ('soldeMinAnnee' in locals()) and (moisMinAnnee !=0):
	soldeMinAnnee=round(soldeMinAnnee,3)
	addMessageComponent(f" - Pire solde cette année : {soldeMinAnnee}$ le {jourMinAnnee}/{moisMinAnnee}/{anneeMinAnnee} à {heureMinAnnee}h")
    

#=================================================================
# Affiche le bilan d'évolution continue dans le message telegram
#=================================================================
addMessageComponent("\n-------------------\n")
addMessageComponent("Bilan d'évolution continue :")
if 'soldeLastExec' in locals():
	bonus=100*(todaySolde-soldeLastExec)/soldeLastExec 
	gain=bonus/100*soldeLastExec
	bonus=round(bonus,3)
	gain=round(gain,5)
	soldeLastExecRounded=round(soldeLastExec,3)
	if gain<0 :
		addMessageComponent(f" - Dernière execution du bot : {bonus}% ({soldeLastExecRounded}$ {gain}$)")
	else :
		addMessageComponent(f" - Dernière execution du bot : +{bonus}% ({soldeLastExecRounded}$ +{gain}$)")
if 'solde6heures' in locals():
	bonus=100*(todaySolde-solde6heures)/solde6heures 
	gain=round(bonus/100*todaySolde,2)
	bonus=round(bonus,3)
	gain=round(gain,5)
	solde6heures=round(solde6heures,3)
	if gain<0 :
		addMessageComponent(f" - il y a 6h : {bonus}% ({solde6heures}$ {gain}$)")
	else :
		addMessageComponent(f" - il y a 6h : +{bonus}% ({solde6heures}$ +{gain}$)")
if 'solde12heures' in locals():
	bonus=100*(todaySolde-solde12heures)/solde12heures 
	gain=round(bonus/100*todaySolde,2)
	bonus=round(bonus,3)
	gain=round(gain,5)
	solde12heures=round(solde12heures,3)
	if gain<0 :
		addMessageComponent(f" - il y a 12h : {bonus}% ({solde12heures}${gain}$)")
	else :
		addMessageComponent(f" - il y a 12h : +{bonus}% ({solde12heures}$ +{gain}$)")
if 'solde1jours' in locals():
	bonus=100*(todaySolde-solde1jours)/solde1jours
	gain=round(bonus/100*todaySolde,2)
	bonus=round(bonus,3)
	gain=round(gain,5)
	solde1jours=round(solde1jours,5)
	if gain<0 :
		addMessageComponent(f" - il y a 1j : {bonus}% ({solde1jours}$ {gain}$)")
	else :
		addMessageComponent(f" - il y a 1j : +{bonus}% ({solde1jours}$ +{gain}$)")
if 'solde3jours' in locals():
	bonus=100*(todaySolde-solde3jours)/solde3jours
	gain=round(bonus/100*todaySolde,2)
	bonus=round(bonus,3)
	gain=round(gain,5)
	solde3jours=round(solde3jours,3)
	if gain<0 :
		addMessageComponent(f" - il y a 3j : {bonus}% ({solde3jours}$ {gain}$)")
	else :
		addMessageComponent(f" - il y a 3j : +{bonus}% ({solde3jours}$ +{gain}$)")
if 'solde7jours' in locals():
	bonus=100*(todaySolde-solde7jours)/solde7jours
	gain=round(bonus/100*todaySolde,2)
	bonus=round(bonus,3)
	gain=round(gain,5)
	solde7jours=round(solde7jours,3)
	if gain<0 :
		addMessageComponent(f" - il y a 7j : {bonus}% ({solde7jours}$ {gain}$)")
	else :
		addMessageComponent(f" - il y a 7j : +{bonus}% ({solde7jours}$ +{gain}$)")
if 'solde14jours' in locals():
	bonus=100*(todaySolde-solde14jours)/solde14jours
	gain=round(bonus/100*todaySolde,2)
	bonus=round(bonus,3)
	gain=round(gain,5)
	solde14jours=round(solde14jours,3)
	if gain<0 :
		addMessageComponent(f" - il y a 14j : {bonus}% ({solde14jours}$ {gain}$)")
	else :
		addMessageComponent(f" - il y a 14j : +{bonus}% ({solde14jours}$ +{gain}$)")
if 'solde1mois' in locals():
	bonus=100*(todaySolde-solde1mois)/solde1mois
	gain=round(bonus/100*todaySolde,2)
	bonus=round(bonus,3)
	gain=round(gain,5)
	solde1mois=round(solde1mois,3)
	if gain<0 :
		addMessageComponent(f" - il y a 1 mois : {bonus}% ({solde1mois}$ {gain}$)")
	else :
		addMessageComponent(f" - il y a 1 mois : +{bonus}% ({solde1mois}$ +{gain}$)")
if 'solde2mois' in locals():
	bonus=100*(todaySolde-solde2mois)/solde2mois
	gain=round(bonus/100*todaySolde,2)
	bonus=round(bonus,3)
	gain=round(gain,5)
	solde2mois=round(solde2mois,3)
	if gain<0 :
		addMessageComponent(f" - il y a 2 mois : {bonus}% ({solde2mois}$ {gain}$)")
	else :
		addMessageComponent(f" - il y a 2 mois : +{bonus}% ({solde2mois}$ +{gain}$)")


totalInvestment = float(config['SOLDE']['totalInvestment'])
bonus=100*(todaySolde-totalInvestment)/totalInvestment
gain=round(bonus/100*todaySolde,2)
bonus=round(bonus,3)
gain=round(gain,5)
totalInvestment=round(totalInvestment,5)
addMessageComponent("\n===================\n")
addMessageComponent(f"INVESTISSEMENT INITIAL => {totalInvestment} $")
if gain<0 :
	addMessageComponent(f"PERTE TOTAL => {bonus}% ({gain}$)\n")
else :
	addMessageComponent(f"PROFIT TOTAL => +{bonus}% (+{gain}$)\n")
addMessageComponent(f"SOLDE TOTAL => {usdAmount} $")


message = message.replace('-USD','')
message = message.replace(' , ',' ')
if (changement==0 and (int(todayHeure)!=8 and int(todayHeure)!=12 and int(todayHeure)!=18 and int(todayHeure)!=0)):
	print("Aucun changement de données, aucune information n'a été envoyé à Telegram")
else :
	telegram_send.send(messages=[f"{message}"])