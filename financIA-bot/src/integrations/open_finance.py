import requests
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class OpenFinanceIntegration:
    def __init__(self, client_id: str, client_secret: str):
        self.auth_url = "https://auth.openfinance.br/oauth/token"
        self.api_url = "https://api.openfinance.br/open-banking/v1"
        self.credentials = {
            'client_id': client_id,
            'client_secret': client_secret
        }
        self.access_token = None
    
    def _get_access_token(self) -> str:
        """Obtém token de acesso OAuth 2.0"""
        response = requests.post(
            self.auth_url,
            data={**self.credentials, 'grant_type': 'client_credentials'},
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        response.raise_for_status()
        return response.json()['access_token']
    
    def get_transactions(self, account_id: str, start_date: str, end_date: str) -> List[Dict]:
        """Busca transações via API Open Finance"""
        try:
            if not self.access_token:
                self.access_token = self._get_access_token()
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'fromBookingDate': start_date,
                'toBookingDate': end_date
            }
            
            response = requests.get(
                f"{self.api_url}/accounts/{account_id}/transactions",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            return self._normalize_data(response.json()['data']['transactions'])
        except Exception as e:
            logger.error(f"Erro no Open Finance: {str(e)}")
            raise

    def _normalize_data(self, raw_transactions: List) -> List[Dict]:
        """Padroniza formato das transações"""
        return [{
            'date': datetime.strptime(t['bookingDate'], '%Y-%m-%d').strftime('%Y-%m-%d'),
            'description': t.get('remittanceInformation', ''),
            'value': float(t['amount']),
            'source': 'open_finance',
            'metadata': {'transactionId': t['transactionId']}
        } for t in raw_transactions]