# -*- coding: utf-8 -*-
"""
Historical Database for GeoLift Tests.
Stores and retrieves past test configurations and results for benchmarking.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd


class TestHistory:
    """
    Manage historical test data for benchmarking and learning.
    Uses JSON file storage for simplicity and portability.
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the history manager.
        
        Args:
            storage_path: Path to the JSON file for storage.
                         Defaults to 'test_history.json' in the current directory.
        """
        if storage_path is None:
            # Default to user's home directory for persistence
            storage_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'data',
                'test_history.json'
            )
        
        self.storage_path = storage_path
        self._ensure_storage_exists()
        self.history = self._load_history()
    
    def _ensure_storage_exists(self):
        """Ensure the storage directory and file exist."""
        storage_dir = os.path.dirname(self.storage_path)
        if storage_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
        
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w') as f:
                json.dump({'tests': []}, f)
    
    def _load_history(self) -> Dict:
        """Load history from storage."""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {'tests': []}
    
    def _save_history(self):
        """Save history to storage."""
        with open(self.storage_path, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)
    
    def save_pretest(
        self,
        name: str,
        treatment_cities: List[str],
        control_cities: List[str],
        duration_days: int,
        expected_lift: float,
        confidence_level: float,
        power_result: Dict,
        notes: str = ""
    ) -> str:
        """
        Save a pre-test configuration.
        
        Returns:
            test_id: Unique identifier for this test
        """
        test_id = f"pre_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        test_record = {
            'id': test_id,
            'type': 'pretest',
            'name': name,
            'created_at': datetime.now().isoformat(),
            'status': 'planned',
            'config': {
                'treatment_cities': treatment_cities,
                'control_cities': control_cities,
                'duration_days': duration_days,
                'expected_lift': expected_lift,
                'confidence_level': confidence_level
            },
            'results': {
                'power_percent': power_result.get('power_percent'),
                'mde_percent': power_result.get('mde_percent'),
                'is_powered': power_result.get('is_powered', False)
            },
            'notes': notes
        }
        
        self.history['tests'].append(test_record)
        self._save_history()
        
        return test_id
    
    def save_posttest(
        self,
        name: str,
        pretest_id: str = None,
        treatment_cities: List[str] = None,
        control_cities: List[str] = None,
        actual_duration: int = None,
        lift_result: Dict = None,
        roi_result: Dict = None,
        notes: str = ""
    ) -> str:
        """
        Save post-test results.
        
        Returns:
            test_id: Unique identifier for this test result
        """
        test_id = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        test_record = {
            'id': test_id,
            'type': 'posttest',
            'name': name,
            'pretest_id': pretest_id,
            'created_at': datetime.now().isoformat(),
            'status': 'completed',
            'config': {
                'treatment_cities': treatment_cities or [],
                'control_cities': control_cities or [],
                'actual_duration_days': actual_duration
            },
            'results': {
                'lift_percent': lift_result.get('lift_percent') if lift_result else None,
                'is_significant': lift_result.get('is_significant') if lift_result else None,
                'p_value': lift_result.get('p_value') if lift_result else None,
                'ci_lower': lift_result.get('ci_lower_percent') if lift_result else None,
                'ci_upper': lift_result.get('ci_upper_percent') if lift_result else None,
                'roi_percent': roi_result.get('roi_percent') if roi_result else None,
                'iroas': roi_result.get('iroas') if roi_result else None
            },
            'notes': notes
        }
        
        # Link to pretest if exists
        if pretest_id:
            for test in self.history['tests']:
                if test['id'] == pretest_id:
                    test['status'] = 'completed'
                    test['posttest_id'] = test_id
                    break
        
        self.history['tests'].append(test_record)
        self._save_history()
        
        return test_id
    
    def get_all_tests(self, test_type: str = None) -> List[Dict]:
        """
        Get all tests, optionally filtered by type.
        
        Args:
            test_type: 'pretest', 'posttest', or None for all
        """
        tests = self.history.get('tests', [])
        
        if test_type:
            tests = [t for t in tests if t['type'] == test_type]
        
        # Sort by date, newest first
        tests.sort(key=lambda x: x['created_at'], reverse=True)
        
        return tests
    
    def get_test_by_id(self, test_id: str) -> Optional[Dict]:
        """Get a specific test by ID."""
        for test in self.history.get('tests', []):
            if test['id'] == test_id:
                return test
        return None
    
    def delete_test(self, test_id: str) -> bool:
        """Delete a test by ID."""
        tests = self.history.get('tests', [])
        original_len = len(tests)
        
        self.history['tests'] = [t for t in tests if t['id'] != test_id]
        
        if len(self.history['tests']) < original_len:
            self._save_history()
            return True
        return False
    
    def get_benchmarks(self) -> Dict:
        """
        Calculate benchmark statistics from historical tests.
        Useful for comparing new test designs against past performance.
        """
        completed_tests = [
            t for t in self.history.get('tests', [])
            if t['type'] == 'posttest' and t['results'].get('lift_percent') is not None
        ]
        
        if not completed_tests:
            return {
                'n_tests': 0,
                'message': 'No hay tests completados para calcular benchmarks'
            }
        
        lifts = [t['results']['lift_percent'] for t in completed_tests]
        significant_tests = [t for t in completed_tests if t['results'].get('is_significant')]
        
        rois = [t['results']['roi_percent'] for t in completed_tests if t['results'].get('roi_percent') is not None]
        
        return {
            'n_tests': len(completed_tests),
            'n_significant': len(significant_tests),
            'significance_rate': len(significant_tests) / len(completed_tests) * 100,
            'lift_stats': {
                'mean': sum(lifts) / len(lifts),
                'median': sorted(lifts)[len(lifts) // 2],
                'min': min(lifts),
                'max': max(lifts),
                'std': pd.Series(lifts).std()
            },
            'roi_stats': {
                'mean': sum(rois) / len(rois) if rois else None,
                'median': sorted(rois)[len(rois) // 2] if rois else None,
                'positive_rate': sum(1 for r in rois if r > 0) / len(rois) * 100 if rois else None
            } if rois else None
        }
    
    def get_similar_tests(
        self,
        treatment_cities: List[str],
        control_cities: List[str],
        expected_lift: float
    ) -> List[Dict]:
        """
        Find similar past tests for comparison.
        
        Args:
            treatment_cities: Current test's treatment cities
            control_cities: Current test's control cities
            expected_lift: Current test's expected lift
        """
        similar = []
        
        for test in self.history.get('tests', []):
            config = test.get('config', {})
            
            # Check for city overlap
            test_treatment = set(config.get('treatment_cities', []))
            test_control = set(config.get('control_cities', []))
            
            treatment_overlap = len(set(treatment_cities) & test_treatment)
            control_overlap = len(set(control_cities) & test_control)
            
            # Check lift similarity
            test_lift = config.get('expected_lift', 0)
            lift_diff = abs(expected_lift - test_lift)
            
            # Score similarity
            similarity_score = (
                treatment_overlap * 2 +  # Weight treatment overlap more
                control_overlap +
                (1 if lift_diff < 0.05 else 0)  # Bonus for similar lift
            )
            
            if similarity_score > 0:
                test_copy = test.copy()
                test_copy['similarity_score'] = similarity_score
                similar.append(test_copy)
        
        # Sort by similarity
        similar.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similar[:5]  # Return top 5
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """Export all test history to a pandas DataFrame."""
        tests = self.history.get('tests', [])
        
        if not tests:
            return pd.DataFrame()
        
        rows = []
        for test in tests:
            row = {
                'id': test['id'],
                'type': test['type'],
                'name': test['name'],
                'created_at': test['created_at'],
                'status': test.get('status', ''),
                'treatment_cities': ', '.join(test['config'].get('treatment_cities', [])),
                'control_cities': ', '.join(test['config'].get('control_cities', [])),
                'duration_days': test['config'].get('duration_days') or test['config'].get('actual_duration_days'),
                'expected_lift': test['config'].get('expected_lift'),
                'power_percent': test['results'].get('power_percent'),
                'mde_percent': test['results'].get('mde_percent'),
                'actual_lift': test['results'].get('lift_percent'),
                'is_significant': test['results'].get('is_significant'),
                'p_value': test['results'].get('p_value'),
                'roi_percent': test['results'].get('roi_percent'),
                'iroas': test['results'].get('iroas'),
                'notes': test.get('notes', '')
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def clear_history(self):
        """Clear all history (use with caution)."""
        self.history = {'tests': []}
        self._save_history()
