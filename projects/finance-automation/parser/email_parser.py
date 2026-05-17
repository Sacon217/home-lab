import re
from bs4 import BeautifulSoup
import logging
import os
import json

logger = logging.getLogger("email_parser")
bank_cards = json.loads(os.getenv("BANK_CARDS", "{}"))

def normalize_label(text: str) -> str:
    """Lowercase, strip accents, remove trailing colon."""
    replacements = {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ü":"u","ñ":"n"}
    t = text.strip(":").lower()
    return "".join(replacements.get(c, c) for c in t)

def parse_bac(html: str):
    try: 
        soup = BeautifulSoup(html, features="html.parser")
    except Exception as e:
        logger.error(f"Failed to load html parser: {e}")
        raise

    transaction = {}
    transaction_data = {}

    try:
        
        for tr in soup.find_all("tr"):
            td = tr.find_all("td",recursive=False)
            if len(td) != 2: # Most trs that contain the values actually have two tds.
                continue
            
            p1 = td[0].find("p")
            p2 = td[1].find("p")

            if p1 and p2:
                label = normalize_label(p1.get_text(" ",strip=True))
                value = p2.get_text(" ",strip=True)
                transaction_data[label] = value

        for brand in ("visa","amex","mastercard"):
            if brand in transaction_data:
                transaction["card_last4"] = transaction_data.get(brand)[-4:]  
                transaction["card_type"]  = bank_cards.get(transaction.get("card_last4"), "Not Categorized")

        transaction["cardholder"] = soup.find('h2', string=re.compile(r'Hola',re.I)).text.replace("Hola ","")
        transaction["currency"], transaction["amount"] = transaction_data.get("monto").split(" ")
        transaction["referencia"] = transaction_data.get("referencia")
        transaction["merchant"] = transaction_data.get("comercio")
        transaction["date"] = transaction_data.get("fecha")
        
    except Exception as e:
        logger.error(f"Failed to parse bac email: {e}")
        raise
    
    return transaction

def parse_proamerica(html: str):
    try: 
        soup = BeautifulSoup(html, features="html.parser")
    except Exception as e:
        logger.error(f"Failed to load html parser: {e}")
        raise

    transaction = {}
    transaction_data = {}

    try:
        table = soup.find("table",{"class":"table1"})
        for tr in table.find_all("tr"):
            td = tr.find_all("td",recursive=False)
            if len(td) != 2: # Most trs that contain the values actually have two tds.
                continue
            
            p1 = td[0].get_text(" ", strip=True)
            p2 = td[1].get_text(" ", strip=True)

            if p1 and p2:
                label = normalize_label(p1)
                value = p2
                transaction_data[label] = value

        transaction["card_last4"] = transaction_data.get("numero de tarjeta")[-4:]        
        transaction["card_type"]  = bank_cards.get(transaction.get("card_last4"), "Not Categorized")
        transaction["cardholder"] = soup.find("td", string=re.compile(r'Adjuntamos transacción realizada',re.I)).find_parent("table").find("strong").get_text(strip=True)
        transaction["currency"], transaction["amount"] = transaction_data.get("monto").split(": ", 1)
        transaction["referencia"] = transaction_data.get("numero de referencia")
        transaction["merchant"] = " ".join(transaction_data.get("comercio", "").split())
        transaction["date"] = transaction_data.get("fecha/hora")
    except Exception as e:
        logger.error(f"Failed to parse proamerica email: {e}")
        raise

    return transaction