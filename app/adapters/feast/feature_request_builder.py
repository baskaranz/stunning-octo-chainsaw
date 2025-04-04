from typing import Any, Dict, List, Optional

class FeatureRequestBuilder:
    """Builds feature requests for Feast feature store."""
    
    @staticmethod
    def build_entity_rows(entity_type: str, entity_ids: List[str], entity_column: str = None) -> List[Dict[str, Any]]:
        """Build entity rows for feature retrieval.
        
        Args:
            entity_type: Type of entity (e.g., 'customer', 'order')
            entity_ids: List of entity IDs
            entity_column: Column name for the entity ID (default: {entity_type}_id)
            
        Returns:
            List of entity dictionaries
        """
        if entity_column is None:
            entity_column = f"{entity_type}_id"
        
        return [{entity_column: entity_id} for entity_id in entity_ids]
    
    @staticmethod
    def build_feature_refs(project: str, feature_view: str, features: List[str]) -> List[str]:
        """Build fully qualified feature references.
        
        Args:
            project: Feast project name
            feature_view: Feature view name
            features: List of feature names
            
        Returns:
            List of fully qualified feature references
        """
        return [f"{project}/{feature_view}:{feature}" for feature in features]
    
    @staticmethod
    def filter_features(features: Dict[str, List[Any]], prefix: Optional[str] = None, 
                      exclude_nulls: bool = True) -> Dict[str, List[Any]]:
        """Filter feature results.
        
        Args:
            features: Dictionary of feature results
            prefix: Optional prefix to filter by
            exclude_nulls: Whether to exclude null values
            
        Returns:
            Filtered feature dictionary
        """
        result = {}
        
        for feature_name, values in features.items():
            # Apply prefix filter if specified
            if prefix and not feature_name.startswith(prefix):
                continue
                
            # Apply null filter if specified
            if exclude_nulls and all(v is None for v in values):
                continue
                
            result[feature_name] = values
        
        return result
    
    @staticmethod
    def format_feature_result(features: Dict[str, List[Any]], entity_column: str) -> List[Dict[str, Any]]:
        """Format feature results into a list of entity records.
        
        Args:
            features: Dictionary of feature results
            entity_column: Column name for the entity ID
            
        Returns:
            List of entity records with features
        """
        if entity_column not in features:
            return []
            
        # Get the number of entities
        n_entities = len(features[entity_column])
        
        # Create a list of records, one per entity
        records = []
        for i in range(n_entities):
            record = {}
            for feature_name, values in features.items():
                if i < len(values):
                    record[feature_name] = values[i]
            records.append(record)
        
        return records
