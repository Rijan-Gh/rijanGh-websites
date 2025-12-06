import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer
import logging

logger = logging.getLogger(__name__)

class ContentBasedRecommender:
    """Content-based recommender using item attributes"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,
            ngram_range=(1, 2)
        )
        self.mlb = MultiLabelBinarizer()
        self.item_features = None
        self.item_ids = None
        self.feature_names = None
        
    def fit(self, items: pd.DataFrame):
        """Fit the model with item features"""
        self.item_ids = items['id'].tolist()
        
        # Prepare text features
        items['combined_features'] = items.apply(
            self._combine_features,
            axis=1
        )
        
        # Create TF-IDF vectors
        self.item_features = self.vectorizer.fit_transform(items['combined_features'])
        self.feature_names = self.vectorizer.get_feature_names_out()
        
        logger.info(f"Fitted content-based recommender with {len(self.item_ids)} items")
    
    def _combine_features(self, row: pd.Series) -> str:
        """Combine various item features into text"""
        features = []
        
        # Name
        features.append(str(row.get('name', '')))
        
        # Description
        features.append(str(row.get('description', '')))
        
        # Category
        features.append(str(row.get('category', '')))
        
        # Business type
        features.append(str(row.get('business_type', '')))
        
        # Tags/categories
        if 'tags' in row and row['tags']:
            features.extend([str(tag) for tag in row['tags']])
        
        # Dietary info
        if row.get('is_vegetarian'):
            features.append('vegetarian')
        if row.get('is_vegan'):
            features.append('vegan')
        
        # Price range (categorical)
        price = row.get('price', 0)
        if price < 100:
            features.append('budget')
        elif price < 500:
            features.append('midrange')
        else:
            features.append('premium')
        
        return ' '.join(features)
    
    def recommend_similar_items(
        self,
        item_id: str,
        n_recommendations: int = 10,
        exclude_items: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Find items similar to given item"""
        if item_id not in self.item_ids:
            return []
        
        item_idx = self.item_ids.index(item_id)
        item_vector = self.item_features[item_idx]
        
        # Calculate similarity to all items
        similarities = cosine_similarity(item_vector, self.item_features)[0]
        
        # Create recommendations
        recommendations = []
        exclude_set = set(exclude_items or [])
        
        # Sort items by similarity
        sorted_indices = np.argsort(similarities)[::-1]
        
        for idx in sorted_indices:
            if len(recommendations) >= n_recommendations:
                break
            
            current_item_id = self.item_ids[idx]
            if current_item_id != item_id and current_item_id not in exclude_set:
                recommendations.append({
                    'item_id': current_item_id,
                    'similarity': float(similarities[idx]),
                    'type': 'content_based'
                })
        
        return recommendations
    
    def recommend_for_user_profile(
        self,
        user_profile: Dict[str, Any],
        n_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """Recommend items based on user profile"""
        # Create user profile vector
        profile_text = self._create_profile_text(user_profile)
        profile_vector = self.vectorizer.transform([profile_text])
        
        # Calculate similarity to all items
        similarities = cosine_similarity(profile_vector, self.item_features)[0]
        
        # Create recommendations
        recommendations = []
        
        # Sort items by similarity
        sorted_indices = np.argsort(similarities)[::-1]
        
        for idx in sorted_indices[:n_recommendations]:
            recommendations.append({
                'item_id': self.item_ids[idx],
                'similarity': float(similarities[idx]),
                'type': 'content_profile'
            })
        
        return recommendations
    
    def _create_profile_text(self, profile: Dict[str, Any]) -> str:
        """Create text representation of user profile"""
        features = []
        
        # Preferred categories
        if 'preferred_categories' in profile:
            features.extend(profile['preferred_categories'])
        
        # Dietary preferences
        if profile.get('is_vegetarian'):
            features.append('vegetarian')
        if profile.get('is_vegan'):
            features.append('vegan')
        
        # Price preference
        price_pref = profile.get('price_preference', 'midrange')
        features.append(price_pref)
        
        # Previous purchases/likes
        if 'preferred_items' in profile:
            # Get features of preferred items
            for item_id in profile['preferred_items'][:5]:
                if item_id in self.item_ids:
                    idx = self.item_ids.index(item_id)
                    # We could add the item's features here
                    pass
        
        return ' '.join(features)
    
    def get_item_features(
        self,
        item_id: str,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most important features for an item"""
        if item_id not in self.item_ids:
            return []
        
        item_idx = self.item_ids.index(item_id)
        item_vector = self.item_features[item_idx]
        
        # Get non-zero features
        feature_indices = item_vector.nonzero()[1]
        feature_values = item_vector.data
        
        # Sort by importance
        sorted_indices = np.argsort(feature_values)[::-1][:top_n]
        
        features = []
        for idx in sorted_indices:
            if idx < len(feature_indices):
                feature_idx = feature_indices[idx]
                if feature_idx < len(self.feature_names):
                    features.append({
                        'feature': self.feature_names[feature_idx],
                        'importance': float(feature_values[idx])
                    })
        
        return features
    
    def explain_recommendation(
        self,
        source_item_id: str,
        target_item_id: str
    ) -> Dict[str, Any]:
        """Explain why an item was recommended"""
        if source_item_id not in self.item_ids or target_item_id not in self.item_ids:
            return {}
        
        source_idx = self.item_ids.index(source_item_id)
        target_idx = self.item_ids.index(target_item_id)
        
        source_vector = self.item_features[source_idx]
        target_vector = self.item_features[target_idx]
        
        # Get common features
        source_features = set(
            self.feature_names[idx] 
            for idx in source_vector.nonzero()[1]
        )
        target_features = set(
            self.feature_names[idx] 
            for idx in target_vector.nonzero()[1]
        )
        
        common_features = source_features.intersection(target_features)
        
        return {
            'source_item': source_item_id,
            'target_item': target_item_id,
            'common_features': list(common_features)[:10],
            'common_count': len(common_features)
        }