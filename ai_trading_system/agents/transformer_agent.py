#!/usr/bin/env python3
"""
Transformer 기반 시계열 예측 에이전트
블로그 분석 기반 구현
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, Dataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("⚠️ PyTorch를 사용할 수 없습니다. 간단한 모델을 사용합니다.")

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

logger = logging.getLogger('ai_trading.transformer')


class TimeSeriesDataset(Dataset):
    """시계열 데이터셋"""
    
    def __init__(self, data: np.ndarray, seq_length: int = 30):
        self.data = data
        self.seq_length = seq_length
    
    def __len__(self):
        return len(self.data) - self.seq_length
    
    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_length]
        y = self.data[idx + self.seq_length]
        return torch.FloatTensor(x), torch.FloatTensor([y])


class MultiHeadAttention(nn.Module):
    """멀티헤드 어텐션"""
    
    def __init__(self, d_model: int, num_heads: int = 8):
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads
        
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"
        
        self.q_linear = nn.Linear(d_model, d_model)
        self.k_linear = nn.Linear(d_model, d_model)
        self.v_linear = nn.Linear(d_model, d_model)
        self.out_linear = nn.Linear(d_model, d_model)
        
    def forward(self, x):
        batch_size, seq_len, _ = x.size()
        
        # Q, K, V 계산
        Q = self.q_linear(x).view(batch_size, seq_len, self.num_heads, self.head_dim)
        K = self.k_linear(x).view(batch_size, seq_len, self.num_heads, self.head_dim)
        V = self.v_linear(x).view(batch_size, seq_len, self.num_heads, self.head_dim)
        
        # Transpose for attention computation
        Q = Q.transpose(1, 2)  # (batch_size, num_heads, seq_len, head_dim)
        K = K.transpose(1, 2)
        V = V.transpose(1, 2)
        
        # Attention scores
        scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.head_dim)
        attention_weights = F.softmax(scores, dim=-1)
        
        # Apply attention to values
        attention_output = torch.matmul(attention_weights, V)
        
        # Concatenate heads
        attention_output = attention_output.transpose(1, 2).contiguous().view(
            batch_size, seq_len, self.d_model
        )
        
        return self.out_linear(attention_output)


class TransformerBlock(nn.Module):
    """Transformer 블록"""
    
    def __init__(self, d_model: int, num_heads: int, ff_dim: int, dropout: float = 0.1):
        super().__init__()
        self.attention = MultiHeadAttention(d_model, num_heads)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, ff_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, d_model),
            nn.Dropout(dropout)
        )
    
    def forward(self, x):
        # Self-attention with residual connection
        attn_output = self.attention(x)
        x = self.norm1(x + attn_output)
        
        # Feed forward with residual connection
        ff_output = self.feed_forward(x)
        x = self.norm2(x + ff_output)
        
        return x


class TransformerPredictor(nn.Module):
    """Transformer 기반 가격 예측 모델"""
    
    def __init__(self, 
                 input_dim: int = 1,
                 d_model: int = 64,
                 num_heads: int = 8,
                 num_layers: int = 4,
                 ff_dim: int = 256,
                 seq_length: int = 30,
                 dropout: float = 0.1):
        super().__init__()
        
        self.d_model = d_model
        self.seq_length = seq_length
        
        # Input projection
        self.input_projection = nn.Linear(input_dim, d_model)
        
        # Positional encoding
        self.pos_encoding = nn.Parameter(
            torch.randn(seq_length, d_model)
        )
        
        # Transformer layers
        self.transformer_layers = nn.ModuleList([
            TransformerBlock(d_model, num_heads, ff_dim, dropout)
            for _ in range(num_layers)
        ])
        
        # Output layers
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        self.dropout = nn.Dropout(dropout)
        self.output_layer = nn.Linear(d_model, 1)
    
    def forward(self, x):
        # Input shape: (batch_size, seq_length, input_dim)
        batch_size, seq_len, _ = x.size()
        
        # Project to d_model dimensions
        x = self.input_projection(x)
        
        # Add positional encoding
        x = x + self.pos_encoding[:seq_len].unsqueeze(0)
        
        # Apply transformer layers
        for layer in self.transformer_layers:
            x = layer(x)
        
        # Global average pooling
        x = x.transpose(1, 2)  # (batch_size, d_model, seq_length)
        x = self.global_pool(x)  # (batch_size, d_model, 1)
        x = x.squeeze(-1)  # (batch_size, d_model)
        
        # Output prediction
        x = self.dropout(x)
        output = self.output_layer(x)
        
        return output


class TransformerAgent:
    """Transformer 기반 예측 에이전트"""
    
    def __init__(self, 
                 seq_length: int = 30,
                 d_model: int = 64,
                 num_heads: int = 8,
                 num_layers: int = 4,
                 learning_rate: float = 0.001):
        
        self.seq_length = seq_length
        self.scaler = MinMaxScaler()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        if not HAS_TORCH:
            logger.warning("PyTorch 미설치로 간단한 예측 모델 사용")
            self.model = None
        else:
            self.model = TransformerPredictor(
                input_dim=1,
                d_model=d_model,
                num_heads=num_heads,
                num_layers=num_layers,
                seq_length=seq_length
            ).to(self.device)
            
            self.optimizer = torch.optim.Adam(
                self.model.parameters(), 
                lr=learning_rate
            )
            self.criterion = nn.MSELoss()
        
        self.is_trained = False
        logger.info(f"Transformer Agent initialized on {self.device}")
    
    def prepare_data(self, price_data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """데이터 전처리"""
        if 'close' not in price_data.columns:
            raise ValueError("Price data must contain 'close' column")
        
        prices = price_data['close'].values.reshape(-1, 1)
        scaled_prices = self.scaler.fit_transform(prices)
        
        X, y = [], []
        for i in range(self.seq_length, len(scaled_prices)):
            X.append(scaled_prices[i-self.seq_length:i])
            y.append(scaled_prices[i])
        
        return np.array(X), np.array(y)
    
    def train(self, price_data: pd.DataFrame, epochs: int = 100) -> Dict:
        """모델 학습"""
        if not HAS_TORCH:
            return {'loss': 0, 'message': 'PyTorch 미설치로 학습 생략'}
        
        X, y = self.prepare_data(price_data)
        
        if len(X) < 10:
            return {'loss': float('inf'), 'message': '학습 데이터 부족'}
        
        dataset = TimeSeriesDataset(X.squeeze(), self.seq_length)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        self.model.train()
        total_loss = 0
        
        for epoch in range(epochs):
            epoch_loss = 0
            for batch_x, batch_y in dataloader:
                batch_x = batch_x.unsqueeze(-1).to(self.device)
                batch_y = batch_y.to(self.device)
                
                self.optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = self.criterion(outputs, batch_y)
                
                loss.backward()
                self.optimizer.step()
                
                epoch_loss += loss.item()
            
            total_loss += epoch_loss
            
            if epoch % 20 == 0:
                logger.debug(f"Epoch {epoch}, Loss: {epoch_loss:.6f}")
        
        self.is_trained = True
        avg_loss = total_loss / epochs
        
        return {
            'loss': avg_loss,
            'epochs': epochs,
            'message': '학습 완료'
        }
    
    def predict_next_price(self, price_data: pd.DataFrame) -> float:
        """다음 가격 예측"""
        if not HAS_TORCH or not self.is_trained:
            # 단순 이동평균 예측
            recent_prices = price_data['close'].tail(5).values
            return np.mean(recent_prices)
        
        if len(price_data) < self.seq_length:
            return price_data['close'].iloc[-1]
        
        # 최근 데이터 준비
        recent_prices = price_data['close'].tail(self.seq_length).values.reshape(-1, 1)
        scaled_prices = self.scaler.transform(recent_prices)
        
        # 예측
        self.model.eval()
        with torch.no_grad():
            input_tensor = torch.FloatTensor(scaled_prices).unsqueeze(0).unsqueeze(-1).to(self.device)
            prediction = self.model(input_tensor)
            
            # 역정규화
            prediction_np = prediction.cpu().numpy().reshape(-1, 1)
            predicted_price = self.scaler.inverse_transform(prediction_np)[0, 0]
        
        return predicted_price
    
    def get_trend_signal(self, price_data: pd.DataFrame) -> Dict:
        """트렌드 신호 생성"""
        current_price = price_data['close'].iloc[-1]
        predicted_price = self.predict_next_price(price_data)
        
        price_change_rate = (predicted_price - current_price) / current_price
        
        # 신호 강도 계산
        if price_change_rate > 0.02:  # 2% 상승 예상
            signal = 1.0  # 강한 매수
        elif price_change_rate > 0.005:  # 0.5% 상승 예상
            signal = 0.5  # 약한 매수
        elif price_change_rate < -0.02:  # 2% 하락 예상
            signal = -1.0  # 강한 매도
        elif price_change_rate < -0.005:  # 0.5% 하락 예상
            signal = -0.5  # 약한 매도
        else:
            signal = 0.0  # 관망
        
        return {
            '신호': signal,
            'confidence': abs(signal),
            'predicted_price': predicted_price,
            'price_change_rate': price_change_rate,
            'trend': 'up' if signal > 0 else 'down' if signal < 0 else 'sideways'
        }
    
    def analyze_pattern(self, price_data: pd.DataFrame) -> Dict:
        """패턴 분석"""
        if len(price_data) < 20:
            return {'pattern': 'insufficient_data', 'confidence': 0}
        
        # 최근 20일 가격 변화 분석
        recent_prices = price_data['close'].tail(20).values
        returns = np.diff(recent_prices) / recent_prices[:-1]
        
        # 변동성 계산
        volatility = np.std(returns)
        
        # 트렌드 분석 (선형 회귀 기울기)
        x = np.arange(len(recent_prices))
        slope = np.polyfit(x, recent_prices, 1)[0]
        
        # 패턴 분류
        if slope > 0 and volatility < 0.02:
            pattern = 'stable_uptrend'
            confidence = 0.8
        elif slope > 0 and volatility >= 0.02:
            pattern = 'volatile_uptrend'
            confidence = 0.6
        elif slope < 0 and volatility < 0.02:
            pattern = 'stable_downtrend'
            confidence = 0.8
        elif slope < 0 and volatility >= 0.02:
            pattern = 'volatile_downtrend'
            confidence = 0.6
        else:
            pattern = 'sideways'
            confidence = 0.4
        
        return {
            'pattern': pattern,
            'confidence': confidence,
            'slope': slope,
            'volatility': volatility,
            'trend_strength': abs(slope) / np.mean(recent_prices)
        }