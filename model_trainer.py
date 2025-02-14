import tensorflow as tf
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Dict

class ModelTrainer:
    """Handles model creation, training, and evaluation"""
    
    def __init__(self, input_dim: int):
        self.model = self._build_model(input_dim)
        self.scaler = StandardScaler()
        self.history = None
    
    def _build_model(self, input_dim: int) -> tf.keras.Model:
        """Build neural network model"""
        model = tf.keras.Sequential([
            # Input layer
            tf.keras.layers.Dense(128, activation='relu', input_shape=(input_dim,)),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.3),
            
            # Hidden layers
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.2),
            
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.2),
            
            # Output layer
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=[
                'accuracy',
                tf.keras.metrics.AUC(),
                tf.keras.metrics.Precision(),
                tf.keras.metrics.Recall()
            ]
        )
        
        return model
    
    def prepare_data(self, feature_matrix: pd.DataFrame, labels: pd.Series) -> Tuple:
        """Prepare data for training"""
        # Remove non-feature columns
        feature_cols = [col for col in feature_matrix.columns 
                       if col not in ['student_id', 'session_id']]
        X = feature_matrix[feature_cols]
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        return X_train, X_val, y_train, y_val
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray, y_val: np.ndarray,
              epochs: int = 100, batch_size: int = 32) -> Dict:
        """Train the model"""
        # Define callbacks
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001
            )
        ]
        
        # Train model
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        return self.history.history
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """Evaluate model performance"""
        results = self.model.evaluate(X_test, y_test, verbose=0)
        metrics = dict(zip(self.model.metrics_names, results))
        
        # Generate predictions
        y_pred = self.model.predict(X_test)
        
        # Add additional metrics if needed
        
        return metrics
    
    def predict_talent(self, features: np.ndarray) -> np.ndarray:
        """Predict talent scores for new data"""
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Generate predictions
        predictions = self.model.predict(features_scaled)
        
        return predictions
    
    def save_model(self, model_path: str, scaler_path: str) -> None:
        """Save model and scaler"""
        self.model.save(model_path)
        import joblib
        joblib.dump(self.scaler, scaler_path)
    
    def load_model(self, model_path: str, scaler_path: str) -> None:
        """Load saved model and scaler"""
