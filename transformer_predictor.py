#!/usr/bin/env python3
"""
Transformer 기반 시계열 예측 모델
- 어텐션 메커니즘 활용
- 다중 시간대 분석
- 시계열 패턴 학습
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict
import logging
from datetime import datetime, timedelta

try:
    import tensorflow as tf
    from tensorflow.keras.layers import (
        Input, Dense, LayerNormalization, MultiHeadAttention,
        Dropout, GlobalAveragePooling1D, Reshape
    )
    from tensorflow.keras.models import Model
    from tensorflow.keras.optimizers import Adam
    HAS_TF = True
except ImportError:
    HAS_TF = False
    print("⚠️ TensorFlow를 사용할 수 없습니다. 간단한 모델을 사용합니다.")

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransformerBlock(tf.keras.layers.Layer):
    """
Transformer 블록
    """
    
    def __init__(self, embed_dim, num_heads, ff_dim, dropout_rate=0.1):
        super(TransformerBlock, self).__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        
        if HAS_TF:
            self.attention = MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
            self.ffn = tf.keras.Sequential([
                Dense(ff_dim, activation="relu"),
                Dense(embed_dim),
            ])
            self.layernorm1 = LayerNormalization(epsilon=1e-6)
            self.layernorm2 = LayerNormalization(epsilon=1e-6)
            self.dropout1 = Dropout(dropout_rate)
            self.dropout2 = Dropout(dropout_rate)
    
    def call(self, inputs, training):
        if not HAS_TF:
            return inputs
            
        attn_output = self.attention(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)

class TimeSeriesTransformer:
    """
    시계열 예측을 위한 Transformer 모델
    """
    
    def __init__(self, 
                 sequence_length: int = 60,
                 embed_dim: int = 64,
                 num_heads: int = 4,
                 ff_dim: int = 64,
                 num_transformer_blocks: int = 2,
                 dropout_rate: float = 0.1):
        
        self.sequence_length = sequence_length
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.num_transformer_blocks = num_transformer_blocks
        self.dropout_rate = dropout_rate
        
        self.model = None
        self.scaler = MinMaxScaler()
        self.is_fitted = False
        
        if HAS_TF:
            self._build_model()
        else:
            logger.warning("TensorFlow가 없어 간단한 예측 모델을 사용합니다.")
    
    def _build_model(self):
        """모델 아키텍처 생성"""
        if not HAS_TF:
            return
            
        inputs = Input(shape=(self.sequence_length, 1))
        
        # Positional Encoding (간단한 버전)
        x = Dense(self.embed_dim)(inputs)
        
        # Transformer 블록들
        for _ in range(self.num_transformer_blocks):
            x = TransformerBlock(self.embed_dim, self.num_heads, 
                               self.ff_dim, self.dropout_rate)(x)
        
        # Global Average Pooling
        x = GlobalAveragePooling1D()(x)
        
        # 최종 예측 레이어
        x = Dropout(self.dropout_rate)(x)
        x = Dense(32, activation="relu")(x)
        outputs = Dense(1)(x)  # 단일 값 예측
        
        self.model = Model(inputs, outputs)
        self.model.compile(optimizer=Adam(learning_rate=0.001), 
                          loss="mse", 
                          metrics=["mae"])
        
        logger.info(f"Transformer 모델 생성 완료: {self.model.count_params():,} 파라미터")
    
    def prepare_data(self, data: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
        """데이터 전처리"""
        # 데이터 정규화
        scaled_data = self.scaler.fit_transform(data.values.reshape(-1, 1))
        
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i, 0])
            y.append(scaled_data[i, 0])
        
        return np.array(X), np.array(y)
    
    def fit(self, 
            price_data: pd.Series, 
            epochs: int = 50,
            batch_size: int = 32,
            validation_split: float = 0.2):
        """모델 학습"""
        
        if not HAS_TF or self.model is None:
            # 간단한 대체 모델 (이동평균 기반)
            self.simple_model_data = price_data.rolling(window=20).mean()
            self.is_fitted = True
            logger.info("간단한 이동평균 모델 학습 완료")
            return
        
        try:
            # 데이터 준비
            X, y = self.prepare_data(price_data)
            X = X.reshape((X.shape[0], X.shape[1], 1))
            
            logger.info(f"학습 데이터 크기: {X.shape}")
            
            # 모델 학습
            history = self.model.fit(
                X, y,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                verbose=1,
                callbacks=[
                    tf.keras.callbacks.EarlyStopping(
                        patience=10, restore_best_weights=True
                    )
                ]
            )
            
            self.is_fitted = True
            
            # 훈련 결과 로그
            final_loss = history.history['loss'][-1]
            val_loss = history.history.get('val_loss', [0])[-1]
            logger.info(f"Transformer 학습 완료 - Loss: {final_loss:.4f}, Val Loss: {val_loss:.4f}")
            
            return history
            
        except Exception as e:
            logger.error(f"Transformer 모델 학습 오류: {e}")
            # 대체 모델로 되돌리기
            self.simple_model_data = price_data.rolling(window=20).mean()
            self.is_fitted = True
    
    def predict_next_price(self, recent_prices: pd.Series) -> float:
        """다음 가격 예측"""
        if not self.is_fitted:
            logger.warning("모델이 학습되지 않았습니다.")
            return recent_prices.iloc[-1]  # 마지막 가격 반환
        
        if not HAS_TF or self.model is None:
            # 간단한 예측 (이동평균)
            return recent_prices.rolling(window=min(20, len(recent_prices))).mean().iloc[-1]
        
        try:
            if len(recent_prices) < self.sequence_length:
                return recent_prices.iloc[-1]
            
            # 마지막 sequence_length 개 데이터 사용
            last_sequence = recent_prices.tail(self.sequence_length)
            
            # 데이터 정규화
            scaled_sequence = self.scaler.transform(last_sequence.values.reshape(-1, 1))
            
            # 모델 입력 형태로 변환
            X = scaled_sequence.reshape(1, self.sequence_length, 1)
            
            # 예측 수행
            prediction_scaled = self.model.predict(X, verbose=0)[0][0]
            
            # 역정규화
            prediction = self.scaler.inverse_transform([[prediction_scaled]])[0][0]
            
            return prediction
            
        except Exception as e:
            logger.error(f"예측 오류: {e}")
            return recent_prices.iloc[-1]
    
    def predict_trend(self, recent_prices: pd.Series, horizon: int = 5) -> List[float]:
        """향후 여러 시점의 가격 예측"""
        predictions = []
        current_prices = recent_prices.copy()
        
        for _ in range(horizon):
            next_price = self.predict_next_price(current_prices)
            predictions.append(next_price)
            
            # 다음 예측을 위해 예측값을 추가
            new_index = len(current_prices)
            current_prices = pd.concat([
                current_prices, 
                pd.Series([next_price], index=[new_index])
            ])
        
        return predictions
    
    def get_prediction_confidence(self, recent_prices: pd.Series) -> Dict[str, float]:
        """예측 신룰도 계산"""
        if not self.is_fitted:
            return {'confidence': 0.5, 'volatility': 0.02}
        
        # 최근 변동성 계산
        returns = recent_prices.pct_change().dropna()
        volatility = returns.std()
        
        # 간단한 신룰도 지표
        # 변동성이 낮을수록 신룰도 높음
        confidence = max(0.3, 1.0 - volatility * 10)
        confidence = min(0.9, confidence)
        
        return {
            'confidence': confidence,
            'volatility': volatility,
            'trend_strength': abs(returns.mean() / (volatility + 1e-8))
        }
    
    def save_model(self, filepath: str):
        """모델 저장"""
        if self.model and HAS_TF:
            self.model.save(filepath)
            logger.info(f"Transformer 모델 저장: {filepath}")
        else:
            import pickle
            with open(f"{filepath}.pkl", 'wb') as f:
                pickle.dump({
                    'simple_model_data': getattr(self, 'simple_model_data', None),
                    'scaler': self.scaler
                }, f)
            logger.info(f"간단한 모델 저장: {filepath}.pkl")
    
    def load_model(self, filepath: str):
        """모델 로드"""
        try:
            if HAS_TF:
                self.model = tf.keras.models.load_model(filepath)
                self.is_fitted = True
                logger.info(f"Transformer 모델 로드: {filepath}")
            else:
                import pickle
                with open(f"{filepath}.pkl", 'rb') as f:
                    data = pickle.load(f)
                    self.simple_model_data = data['simple_model_data']
                    self.scaler = data['scaler']
                    self.is_fitted = True
                logger.info(f"간단한 모델 로드: {filepath}.pkl")
        except Exception as e:
            logger.error(f"모델 로드 오류: {e}")

# 전역 예측기 인스턴스
transformer_predictor = TimeSeriesTransformer()

def get_transformer_predictor() -> TimeSeriesTransformer:
    """예측기 인스턴스 반환"""
    return transformer_predictor

def main():
    """테스트용 메인 함수"""
    print("🧠 Transformer 시계열 예측 시스템")
    print("=" * 50)
    
    # 예측기 인스턴스 가져오기
    predictor = get_transformer_predictor()
    
    print("📊 Transformer 모델 정보:")
    print(f"  - 시퀀스 길이: {predictor.sequence_length}")
    print(f"  - 임베딩 차원: {predictor.embed_dim}")
    print(f"  - 어텐션 헤드: {predictor.num_heads}")
    print(f"  - 피드포워드 차원: {predictor.ff_dim}")
    print(f"  - Transformer 블록 수: {predictor.num_transformer_blocks}")
    
    if HAS_TF:
        print(f"  - TensorFlow 버전: {tf.__version__}")
        print(f"  - 모델 파라미터: {predictor.model.count_params():,}개")
    else:
        print("  - 간단한 이동평균 모델 사용 중")
    
    print("\n🔮 가상 데이터로 예측 테스트:")
    
    # 가상 주가 데이터 생성 (삼성전자 유사)
    np.random.seed(42)
    base_price = 70000
    days = 100
    
    # 트렌드 + 노이즈
    trend = np.linspace(0, 10000, days)
    noise = np.random.normal(0, 2000, days)
    prices = base_price + trend + noise
    
    # 음수 방지
    prices = np.maximum(prices, 50000)
    
    price_series = pd.Series(prices)
    print(f"  📈 가상 주가 데이터: {len(price_series)}일")
    print(f"  💰 시작가: {prices[0]:,.0f}원")
    print(f"  💰 종료가: {prices[-1]:,.0f}원")
    
    # 모델 학습
    print("\n🎓 모델 학습 중...")
    try:
        history = predictor.fit(price_series, epochs=10, batch_size=16)
        print("✅ 모델 학습 완료")
    except Exception as e:
        print(f"⚠️ 학습 오류: {e}")
    
    # 예측 수행
    print("\n🔮 가격 예측:")
    try:
        # 단일 예측
        next_price = predictor.predict_next_price(price_series.tail(60))
        print(f"  🎯 다음 가격 예측: {next_price:,.0f}원")
        
        current_price = prices[-1]
        expected_return = (next_price - current_price) / current_price * 100
        print(f"  📊 예상 수익률: {expected_return:+.2f}%")
        
        # 다중 예측 (5일)
        future_prices = predictor.predict_trend(price_series.tail(60), horizon=5)
        print(f"\n📅 향후 5일 예측:")
        for i, price in enumerate(future_prices):
            day_return = (price - current_price) / current_price * 100
            print(f"    {i+1}일 후: {price:,.0f}원 ({day_return:+.2f}%)")
        
        # 신룰도 분석
        confidence_info = predictor.get_prediction_confidence(price_series.tail(30))
        print(f"\n🎯 예측 신룰도:")
        print(f"  - 신룰도: {confidence_info['confidence']:.1%}")
        print(f"  - 변동성: {confidence_info['volatility']:.3f}")
        print(f"  - 트렌드 강도: {confidence_info.get('trend_strength', 0):.3f}")
        
    except Exception as e:
        print(f"❌ 예측 오류: {e}")
    
    # 모델 저장 테스트
    print("\n💾 모델 저장/로드 테스트:")
    try:
        model_path = "models/test_transformer"
        predictor.save_model(model_path)
        print("✅ 모델 저장 완료")
        
        # 새 인스턴스로 로드 테스트
        new_predictor = TimeSeriesTransformer()
        new_predictor.load_model(model_path)
        print("✅ 모델 로드 완료")
        
        # 예측 비교
        original_pred = predictor.predict_next_price(price_series.tail(60))
        loaded_pred = new_predictor.predict_next_price(price_series.tail(60))
        
        if abs(original_pred - loaded_pred) < 1:
            print("✅ 모델 일관성 검증 통과")
        else:
            print("⚠️ 모델 일관성 차이 발생")
            
    except Exception as e:
        print(f"❌ 모델 저장/로드 오류: {e}")
    
    print("\n🎉 Transformer 예측 시스템 테스트 완료!")
    print("💡 실제 거래에 사용 시:")
    print("  1. 충분한 과거 데이터로 모델 훈련")
    print("  2. 정기적인 모델 재훈련")
    print("  3. 다른 지표와 함께 신중한 활용 권장")

if __name__ == "__main__":
    main()
