import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime

class FeatureExtractor:
    """Extracts relevant features from processed session data"""
    
    def __init__(self):
        self.feature_names = [
            'session_duration_minutes',
            'avg_time_between_actions',
            'error_recovery_time',
            'error_count',
            'error_types',
            'keystrokes_per_minute',
            'backspace_ratio',
            'autocomplete_usage',
            'menu_exploration_depth',
            'code_complexity_score',
            'syntax_error_rate',
            'successful_compilations',
            'ide_feature_usage',
            'code_evolution_rate'
        ]
    
    def _calculate_time_features(self, session: Dict) -> Dict:
        """Calculate time-based features"""
        raw_data = session['raw_data']
        duration = (session['end_time'] - session['start_time']).total_seconds() / 60
        
        time_diffs = []
        for i in range(1, len(raw_data)):
            diff = (raw_data[i]['time'] - raw_data[i-1]['time']).total_seconds()
            time_diffs.append(diff)
        
        return {
            'session_duration_minutes': duration,
            'avg_time_between_actions': np.mean(time_diffs) if time_diffs else 0
        }
    
    def _calculate_error_features(self, session: Dict) -> Dict:
        """Calculate error-related features"""
        raw_data = session['raw_data']
        errors = [entry for entry in raw_data if entry['action'] == 'Hata']
        
        error_recovery_times = []
        for error in errors:
            error_time = error['time']
            # Find next successful compilation
            next_success = next(
                (entry for entry in raw_data 
                 if entry['time'] > error_time and entry['action'] == 'Eylem: Çalıştır'
                 and 'hata_listesi' not in entry),
                None
            )
            if next_success:
                recovery_time = (next_success['time'] - error_time).total_seconds()
                error_recovery_times.append(recovery_time)
        
        return {
            'error_count': len(errors),
            'error_recovery_time': np.mean(error_recovery_times) if error_recovery_times else 0,
            'error_types': len(set(str(error.get('hata_listesi', {})) for error in errors))
        }
    
    def _calculate_coding_features(self, session: Dict) -> Dict:
        """Calculate coding behavior features"""
        raw_data = session['raw_data']
        keystrokes = [entry for entry in raw_data if entry['action'].startswith('Basılan Tuş')]
        backspaces = [entry for entry in keystrokes if 'BCKSPC' in entry['action']]
        
        duration = session['session_duration_minutes']
        
        return {
            'keystrokes_per_minute': len(keystrokes) / duration if duration > 0 else 0,
            'backspace_ratio': len(backspaces) / len(keystrokes) if keystrokes else 0,
            'autocomplete_usage': len([entry for entry in raw_data if entry['action'].startswith('Autocomplete')])
        }
    
    def _calculate_complexity_features(self, session: Dict) -> Dict:
        """Calculate code complexity features"""
        raw_data = session['raw_data']
        
        # Track code length evolution
        code_lengths = [entry.get('totalchars', 0) for entry in raw_data]
        code_changes = np.diff(code_lengths)
        
        # Calculate complexity score based on various factors
        menu_items = [entry['action'] for entry in raw_data if entry['action'].startswith('Solmenü_Tıkla')]
        concept_weights = {
            'Değişkenler': 1,
            'Veri Tipleri': 2,
            'Operatörler': 3,
            'Koşullu ve  Mantıksal  İfadeler': 4,
            'Döngüler': 5
        }
        
        complexity_score = sum(
            concept_weights.get(action.split(': ')[1], 0)
            for action in menu_items
        )
        
        return {
            'code_complexity_score': complexity_score,
            'code_evolution_rate': np.mean(np.abs(code_changes)) if len(code_changes) > 0 else 0
        }
    
    def extract_features(self, session: Dict) -> Dict:
        """Extract all features from a single session"""
        features = {}
        
        # Combine features from all categories
        features.update(self._calculate_time_features(session))
        features.update(self._calculate_error_features(session))
        features.update(self._calculate_coding_features(session))
        features.update(self._calculate_complexity_features(session))
        
        return features
    
    def create_feature_matrix(self, processed_data: pd.DataFrame) -> pd.DataFrame:
        """Create feature matrix from all processed sessions"""
        all_features = []
        
        for _, session in processed_data.iterrows():
            features = self.extract_features(session)
            features['student_id'] = session['student_id']
            features['session_id'] = session['session_id']
            all_features.append(features)
        
        return pd.DataFrame(all_features)

# Usage example:
if __name__ == "__main__":
    # Load processed data
    processed_data = pd.read_pickle('processed_sessions.pkl')
    
    # Extract features
    extractor = FeatureExtractor()
    feature_matrix = extractor.create_feature_matrix(processed_data)
    
    # Save feature matrix
    feature_matrix.to_pickle('feature_matrix.pkl')
