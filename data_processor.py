import json
import pandas as pd
from datetime import datetime
from typing import List, Dict

class DataProcessor:
    """Handles loading and preprocessing of raw session data"""
    
    def __init__(self):
        self.raw_sessions = {}
        self.processed_data = None
        
    def load_session(self, student_id: str, file_path: str) -> None:
        """Load a single session file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
            if student_id not in self.raw_sessions:
                self.raw_sessions[student_id] = []
            self.raw_sessions[student_id].append(session_data)
    
    def load_multiple_sessions(self, session_mapping: Dict[str, List[str]]) -> None:
        """Load multiple session files for multiple students"""
        for student_id, file_paths in session_mapping.items():
            for file_path in file_paths:
                self.load_session(student_id, file_path)
    
    def _clean_session_data(self, session_data: List[Dict]) -> List[Dict]:
        """Clean and validate session data"""
        cleaned_data = []
        for entry in session_data:
            # Ensure required fields exist
            if all(key in entry for key in ['time', 'action', 'totalchars', 'totallines']):
                # Convert time string to datetime
                entry['time'] = datetime.fromisoformat(entry['time'])
                cleaned_data.append(entry)
        return cleaned_data
    
    def preprocess_all_sessions(self) -> pd.DataFrame:
        """Preprocess all loaded sessions into a structured format"""
        processed_sessions = []
        
        for student_id, sessions in self.raw_sessions.items():
            for session_idx, session in enumerate(sessions):
                cleaned_session = self._clean_session_data(session)
                
                session_info = {
                    'student_id': student_id,
                    'session_id': f"{student_id}_{session_idx}",
                    'raw_data': cleaned_session,
                    'start_time': cleaned_session[0]['time'],
                    'end_time': cleaned_session[-1]['time'],
                    'total_actions': len(cleaned_session)
                }
                
                processed_sessions.append(session_info)
        
        self.processed_data = pd.DataFrame(processed_sessions)
        return self.processed_data

    def save_processed_data(self, file_path: str) -> None:
        """Save processed data to file"""
        if self.processed_data is not None:
            self.processed_data.to_pickle(file_path)
    
    def load_processed_data(self, file_path: str) -> pd.DataFrame:
        """Load previously processed data"""
        self.processed_data = pd.read_pickle(file_path)
        return self.processed_data

# Usage example:
if __name__ == "__main__":
    # Initialize processor
    processor = DataProcessor()
    
    # Example session mapping
    session_mapping = {
        'student1': ['path/to/session1.json', 'path/to/session2.json'],
        'student2': ['path/to/session3.json']
    }
    
    # Load and process data
    processor.load_multiple_sessions(session_mapping)
    processed_data = processor.preprocess_all_sessions()
    
    # Save processed data
    processor.save_processed_data('processed_sessions.pkl')
