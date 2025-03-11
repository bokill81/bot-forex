import MetaTrader5 as mt5
import pandas as pd
import time
import datetime
import talib
import numpy as np

# Connexion à MetaTrader 5
if not mt5.initialize():
    print("⚠️ Erreur : Impossible de se connecter à MetaTrader 5")
    quit()
else:
    print("✅ Connexion réussie à MetaTrader 5")

# Vérifier les infos du compte
account_info = mt5.account_info()
if account_info is None:
    print("⚠️ Problème de connexion à MetaTrader 5. Assurez-vous que vous êtes bien connecté à un compte de trading.")
    quit()
else:
    print(f"✅ Compte connecté : {account_info.login}, Solde : {account_info.balance}")

# Paramètres du bot
SYMBOL = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_M1  # Scalping sur 1 minute
LOTS = 0.1
STOP_LOSS = 10  # en pips
TAKE_PROFIT = 10  # en pips

# Récupération des données de marché
def get_data(symbol, timeframe, n=100):
    print(f"📡 Récupération des données pour {symbol}...")
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    
    if rates is None or len(rates) == 0:
        print(f"⚠️ Aucune donnée reçue de MetaTrader 5 pour {symbol}")
        return pd.DataFrame()
    
    df = pd.DataFrame(rates)
    print(df.head())  # Affiche les premières lignes pour voir la structure des données
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

# Calcul des indicateurs techniques
def calculate_indicators(df):
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)
    df['macd'], df['macd_signal'], _ = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(df['close'], timeperiod=20)
    return df

# Détection des signaux d'achat et de vente
def detect_signal(df):
    latest = df.iloc[-1]
    
    # Condition d'achat
    if latest['rsi'] < 40 and latest['macd'] > latest['macd_signal'] and latest['close'] <= latest['lower_band']:
        return "buy"
    
    # Condition de vente
    elif latest['rsi'] > 70 and latest['macd'] < latest['macd_signal'] and latest['close'] >= latest['upper_band']:
        return "sell"
    
    return None

# Passer un ordre de trading
def place_order(order_type):
    symbol_info = mt5.symbol_info(SYMBOL)
    if symbol_info is None:
        print(f"⚠️ L'actif {SYMBOL} n'est pas trouvé sur MetaTrader 5. Vérifiez son nom exact dans la liste des actifs.")
        return
    
    if not symbol_info.trade_mode:
        print(f"⚠️ Le trading est désactivé pour {SYMBOL} sur ce compte.")
        return
    
    print(f"✅ Envoi d'un ordre {order_type} sur {SYMBOL}...")
    
    order = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOTS,
        "type": mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL,
        "price": mt5.symbol_info_tick(SYMBOL).ask if order_type == "buy" else mt5.symbol_info_tick(SYMBOL).bid,
        "deviation": 10,
        "magic": 123456,
        "comment": "Bot Trading XAU/USD",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC
    }
    
    result = mt5.order_send(order)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"⚠️ Erreur lors de l'envoi de l'ordre : {result.comment}")
    else:
        print(f"✅ Ordre {order_type} exécuté avec succès !")

# Boucle principale du bot
while True:
    print("🔄 Vérification des signaux de trading...")
    data = get_data(SYMBOL, TIMEFRAME)
    
    if data.empty:
        print("⚠️ Pas de données disponibles. Attente avant la prochaine vérification...")
        time.sleep(5)
        continue
    
    data = calculate_indicators(data)
    signal = detect_signal(data)
    
    if signal:
        print(f"🚀 Signal détecté : {signal.upper()} - Envoi d'un ordre")
        place_order(signal)
    else:
        print("⏳ Aucun signal détecté, on attend...")
    
    time.sleep(60)  # Vérification toutes les 60 secondes
