import json
import os
from typing import Optional, List
import requests

DATA_FILE = os.path.join(os.path.dirname(__file__), "obligations.json")

def load_obligations() -> List[dict]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_obligations(status: Optional[str] = None, category: Optional[str] = None) -> List[dict]:
    obligations = load_obligations()
    if status:
        obligations = [o for o in obligations if o["status"] == status]
    if category:
        obligations = [o for o in obligations if o["category"] == category]
    return obligations

def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    if from_currency.upper() == to_currency.upper():
        return amount
    url = f"https://api.frankfurter.app/latest?from={from_currency.upper()}&to={to_currency.upper()}"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        rate = data["rates"][to_currency.upper()]
        return round(amount * rate, 2)
    except KeyError:
        raise RuntimeError(f"Валюта {to_currency} не найдена в ответе API")
    except Exception as e:
        raise RuntimeError(f"Ошибка конвертации {from_currency}->{to_currency}: {str(e)}")
