import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import logging

logger = logging.getLogger(__name__)

class CollaborativeFiltering:
    """Collaborative filtering recommender"""
    
    def __init__(self, n_factors: int = 50, n_neighbors: int = 5):
        self.n_factors = n_factors
        self.n_neighbors = n_neighbors
        self.user_factors = None
        self.item_factors = None
        self.user_ids = None
        self.item_ids = None
        self.svd = TruncatedSVD(n_components=n_factors)
        
    def fit(self, user_item_matrix: pd.DataFrame):
        """Fit the model with user-item interactions"""
        self.user_ids = user_item_matrix.index.tolist()
        self.item_ids = user_item_matrix.columns.tolist()
        
        # Convert to numpy array
        R = user_item_matrix.values
        
        # Apply SVD for dimensionality reduction
        self.user_factors = self.svd.fit_transform(R)
        self.item_factors = self.svd.components_.T
        
        logger.info(f"Fitted collaborative filtering with {len(self.user_ids)} users and {len(self.item_ids)} items")
    
    def recommend_for_user(
        self,
        user_id: str,
        n_recommendations: int = 10,
        exclude_items: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for a user"""
        if user_id not in self.user_ids:
            return []
        
        user_idx = self.user_ids.index(user_id)
        user_vector = self.user_factors[user_idx]
        
        # Calculate similarity to all items
        item_scores = np.dot(self.item_factors, user_vector)
        
        # Create recommendations
        recommendations = []
        exclude_set = set(exclude_items or [])
        
        # Sort items by score
        sorted_indices = np.argsort(item_scores)[::-1]
        
        for idx in sorted_indices:
            if len(recommendations) >= n_recommendations:
                break
            
            item_id = self.item_ids[idx]
            if item_id not in exclude_set:
                recommendations.append({
                    'item_id': item_id,
                    'score': float(item_scores[idx]),
                    'type': 'collaborative'
                })
        
        return recommendations
    
    def get_similar_users(
        self,
        user_id: str,
        n_users: int = 5
    ) -> List[Dict[str, Any]]:
        """Find users similar to given user"""
        if user_id not in self.user_ids:
            return []
        
        user_idx = self.user_ids.index(user_id)
        user_vector = self.user_factors[user_idx]
        
        # Calculate similarity to all users
        similarities = cosine_similarity([user_vector], self.user_factors)[0]
        
        # Get top similar users (excluding self)
        similar_indices = np.argsort(similarities)[::-1][1:n_users+1]
        
        similar_users = []
        for idx in similar_indices:
            similar_users.append({
                'user_id': self.user_ids[idx],
                'similarity': float(similarities[idx])
            })
        
        return similar_users
    
    def get_similar_items(
        self,
        item_id: str,
        n_items: int = 10
    ) -> List[Dict[str, Any]]:
        """Find items similar to given item"""
        if item_id not in self.item_ids:
            return []
        
        item_idx = self.item_ids.index(item_id)
        item_vector = self.item_factors[item_idx]
        
        # Calculate similarity to all items
        similarities = cosine_similarity([item_vector], self.item_factors.T)[0]
        
        # Get top similar items (excluding self)
        similar_indices = np.argsort(similarities)[::-1][1:n_items+1]
        
        similar_items = []
        for idx in similar_indices:
            similar_items.append({
                'item_id': self.item_ids[idx],
                'similarity': float(similarities[idx])
            })
        
        return similar_items
    
    def predict_rating(
        self,
        user_id: str,
        item_id: str
    ) -> Optional[float]:
        """Predict user rating for an item"""
        if user_id not in self.user_ids or item_id not in self.item_ids:
            return None
        
        user_idx = self.user_ids.index(user_id)
        item_idx = self.item_ids.index(item_id)
        
        user_vector = self.user_factors[user_idx]
        item_vector = self.item_factors[item_idx]
        
        # Predicted rating is dot product
        prediction = np.dot(user_vector, item_vector)
        
        # Clamp to reasonable range (1-5)
        prediction = max(1.0, min(5.0, prediction))
        
        return float(prediction)
    
    def batch_predict(
        self,
        user_item_pairs: List[tuple]
    ) -> List[Dict[str, Any]]:
        """Predict ratings for multiple user-item pairs"""
        predictions = []
        
        for user_id, item_id in user_item_pairs:
            rating = self.predict_rating(user_id, item_id)
            if rating is not None:
                predictions.append({
                    'user_id': user_id,
                    'item_id': item_id,
                    'predicted_rating': rating
                })
        
        return predictions