class OpenFinanceIntegration:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_transactions(self, account_id, start_date, end_date):
        # Implementação básica inicial
        return []