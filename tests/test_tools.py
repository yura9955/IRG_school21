import pytest
from unittest.mock import patch, MagicMock
from src.tools import get_obligations, convert_currency


class TestGetObligations:
    """Тесты для функции get_obligations."""
    
    def test_get_all_obligations(self):
        """Проверяет получение всех обязательств без фильтров."""
        obligations = get_obligations()
        assert len(obligations) == 13
        assert all("id" in o for o in obligations)
        assert all("title" in o for o in obligations)
        assert all("amount" in o for o in obligations)
        assert all("currency" in o for o in obligations)
    
    def test_filter_by_active_status(self):
        """Проверяет фильтрацию по статусу 'active'."""
        active = get_obligations(status="active")
        assert len(active) == 12
        assert all(o["status"] == "active" for o in active)
    
    def test_filter_by_paused_status(self):
        """Проверяет фильтрацию по статусу 'paused'."""
        paused = get_obligations(status="paused")
        assert len(paused) == 1
        assert paused[0]["title"] == "Dropbox Plus"
    
    def test_filter_by_category(self):
        """Проверяет фильтрацию по категории."""
        software = get_obligations(category="software")
        assert len(software) == 3
        titles = {o["title"] for o in software}
        assert titles == {"Adobe CC", "Dropbox Plus", "Notion Plus"}
    
    def test_filter_by_status_and_category(self):
        """Проверяет комбинированную фильтрацию."""
        result = get_obligations(status="active", category="music")
        assert len(result) == 2
        assert all(o["status"] == "active" and o["category"] == "music" for o in result)
    
    def test_empty_result_for_nonexistent_category(self):
        """Проверяет пустой результат для несуществующей категории."""
        result = get_obligations(category="nonexistent")
        assert len(result) == 0


class TestConvertCurrency:
    """Тесты для функции convert_currency."""
    
    def test_same_currency_no_conversion(self):
        """Конвертация в ту же валюту возвращает исходную сумму."""
        result = convert_currency(100.50, "USD", "USD")
        assert result == 100.50
        
        result = convert_currency(500, "RUB", "rub")
        assert result == 500
    
    @patch("src.tools.requests.get")
    def test_successful_conversion_usd_to_rub(self, mock_get):
        """Успешная конвертация USD -> RUB."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "amount": 1.0,
            "base": "USD",
            "date": "2026-07-08",
            "rates": {"RUB": 89.45}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = convert_currency(10, "USD", "RUB")
        assert result == 894.50
        mock_get.assert_called_once_with(
            "https://api.frankfurter.app/latest?from=USD&to=RUB",
            timeout=5
        )
    
    @patch("src.tools.requests.get")
    def test_successful_conversion_eur_to_usd(self, mock_get):
        """Успешная конвертация EUR -> USD."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "rates": {"USD": 1.12}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = convert_currency(50, "EUR", "USD")
        assert result == 56.00
    
    @patch("src.tools.requests.get")
    def test_api_error_handling(self, mock_get):
        """Обработка ошибки API."""
        mock_get.side_effect = Exception("Connection refused")
        
        with pytest.raises(RuntimeError, match="Ошибка конвертации"):
            convert_currency(100, "EUR", "USD")
    
    @patch("src.tools.requests.get")
    def test_missing_currency_in_response(self, mock_get):
        """Обработка отсутствия валюты в ответе API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": {}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with pytest.raises(RuntimeError, match="не найдена"):
            convert_currency(100, "USD", "XXX")