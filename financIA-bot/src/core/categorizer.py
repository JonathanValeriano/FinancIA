from transformers import BertForSequenceClassification, BertTokenizer
import torch

class SmartCategorizer:
    def __init__(self, model_path: str):
        self.tokenizer = BertTokenizer.from_pretrained(model_path)
        self.model = BertForSequenceClassification.from_pretrained(model_path)
        self.rules = {
            'PIX': 'Transferência',
            'TED': 'Transferência',
            'DOC': 'Transferência'
        }
    
    def categorize(self, description: str, bank: str = None) -> str:
        # 1. Aplica regras bancárias
        for pattern, category in self.rules.items():
            if pattern in description:
                return category
        
        # 2. Usa modelo BERT como fallback
        inputs = self.tokenizer(description, return_tensors="pt", truncation=True, max_length=64)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return self.model.config.id2label[torch.argmax(outputs.logits).item()]