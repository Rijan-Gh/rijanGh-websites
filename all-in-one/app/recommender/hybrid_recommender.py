import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class HybridRecommender:
    """Hybrid recommendation system combining multiple approaches"""
    
    def __init__(self):
        self.user_item_matrix = None
        self.item_features = None
        self.user_similarity = None
        self.item_similarity = None
        
    def fit(self, interactions: pd.DataFrame, items: pd.DataFrame):
        """Fit the recommender with data"""
        # Collaborative Filtering setup
        self._build_user_item_matrix(interactions)
        self._calculate_similarities()
        
        # Content-based setup
        self._extract_item_features(items)
        
    def _build_user_item_matrix(self, interactions: pd.DataFrame):
        """Build user-item interaction matrix"""
        self.user_item_matrix = interactions.pivot_table(
            index='user_id',
            columns='item_id',
            values='rating',
            fill_value=0
        )
    
    def _calculate_similarities(self):
        """Calculate user-user and item-item similarities"""
        if self.user_item_matrix is not None:
            self.user_similarity = cosine_similarity(self.user_item_matrix)
            self.item_similarity = cosine_similarity(self.user_item_matrix.T)
    
    def _extract_item_features(self, items: pd.DataFrame):
        """Extract features for content-based filtering"""
        # Combine text features
        items['features'] = items.apply(
            lambda row: ' '.join([
                str(row.get('name', '')),
                str(row.get('category', '')),
                str(row.get('description', '')),
                ' '.join(row.get('tags', []))
            ]),
            axis=1
        )
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.item_features = vectorizer.fit_transform(items['features'])
        self.feature_names = vectorizer.get_feature_names_out()
    
    def recommend(
        self,
        user_id: str,
        business_id: str,
        context: Optional[Dict[str, Any]] = None,
        n_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate hybrid recommendations"""
        recommendations = []
        
        # 1. Collaborative Filtering
        cf_recs = self._collaborative_filtering(user_id, n_recommendations)
        recommendations.extend(cf_recs)
        
        # 2. Content-Based Filtering
        cb_recs = self._content_based_filtering(user_id, context, n_recommendations)
        recommendations.extend(cb_recs)
        
        # 3. Popularity-Based
        pop_recs = self._popularity_based(business_id, n_recommendations)
        recommendations.extend(pop_recs)
        
        # 4. Context-Based
        if context:
            ctx_recs = self._context_based_filtering(context, n_recommendations)
            recommendations.extend(ctx_recs)
        
        # Remove duplicates and rank
        unique_recs = self._deduplicate_and_rank(recommendations)
        
        return unique_recs[:n_recommendations]
    
    def _collaborative_filtering(
        self,
        user_id: str,
        n_recommendations: int
    ) -> List[Dict[str, Any]]:
        """User-based collaborative filtering"""
        recommendations = []
        
        if user_id in self.user_item_matrix.index:
            user_idx = self.user_item_matrix.index.get_loc(user_id)
            similar_users = np.argsort(self.user_similarity[user_idx])[::-1][1:6]
            
            for sim_user_idx in similar_users:
                sim_user_id = self.user_item_matrix.index[sim_user_idx]
                
                # Get items rated by similar user but not by target user
                target_ratings = self.user_item_matrix.loc[user_id]
                sim_ratings = self.user_item_matrix.loc[sim_user_id]
                
                new_items = sim_ratings[target_ratings == 0].nlargest(5)
                
                for item_id, rating in new_items.items():
                    recommendations.append({
                        'item_id': item_id,
                        'score': rating * self.user_similarity[user_idx, sim_user_idx],
                        'type': 'collaborative',
                        'source': f'similar_user_{sim_user_id}'
                    })
        
        return recommendations
    
    def _content_based_filtering(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]],
        n_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Content-based recommendations"""
        recommendations = []
        
        # Get user's previously liked items
        if user_id in self.user_item_matrix.index:
            user_items = self.user_item_matrix.loc[user_id]
            liked_items = user_items[user_items > 3].index.tolist()
            
            if liked_items:
                # Calculate similarity to liked items
                for liked_item in liked_items[:3]:  # Consider top 3 liked items
                    # Find similar items
                    similar_items = self._find_similar_items(liked_item, n_recommendations)
                    recommendations.extend(similar_items)
        
        return recommendations
    
    def _find_similar_items(
        self,
        item_id: str,
        n_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Find items similar to given item"""
        recommendations = []
        
        if item_id in self.user_item_matrix.columns:
            item_idx = self.user_item_matrix.columns.get_loc(item_id)
            similar_items = np.argsort(self.item_similarity[item_idx])[::-1][1:n_recommendations+1]
            
            for sim_idx in similar_items:
                sim_item_id = self.user_item_matrix.columns[sim_idx]
                similarity = self.item_similarity[item_idx, sim_idx]
                
                recommendations.append({
                    'item_id': sim_item_id,
                    'score': similarity,
                    'type': 'content',
                    'source': f'similar_to_{item_id}'
                })
        
        return recommendations
    
    def _popularity_based(
        self,
        business_id: str,
        n_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Popularity-based recommendations"""
        recommendations = []
        
        # In production, fetch from database
        # Mock implementation
        popular_items = [
            {
                'item_id': f'item_{i}',
                'score': 0.9 - (i * 0.1),
                'type': 'popularity',
                'source': 'trending'
            }
            for i in range(n_recommendations)
        ]
        
        return popular_items
    
    def _context_based_filtering(
        self,
        context: Dict[str, Any],
        n_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Context-based recommendations (time, location, weather)"""
        recommendations = []
        
        # Time-based recommendations
        current_hour = datetime.now().hour
        
        if 6 <= current_hour < 11:  # Morning
            recommendations.append({
                'item_id': 'breakfast_special',
                'score': 0.8,
                'type': 'context',
                'source': 'time_morning'
            })
        elif 11 <= current_hour < 16:  # Afternoon
            recommendations.append({
                'item_id': 'lunch_special',
                'score': 0.8,
                'type': 'context',
                'source': 'time_afternoon'
            })
        elif 16 <= current_hour < 22:  # Evening
            recommendations.append({
                'item_id': 'dinner_special',
                'score': 0.8,
                'type': 'context',
                'source': 'time_evening'
            })
        
        # Weather-based recommendations (mock)
        if context.get('weather') == 'rainy':
            recommendations.append({
                'item_id': 'hot_soup',
                'score': 0.9,
                'type': 'context',
                'source': 'weather_rainy'
            })
        elif context.get('weather') == 'hot':
            recommendations.append({
                'item_id': 'cold_drink',
                'score': 0.9,
                'type': 'context',
                'source': 'weather_hot'
            })
        
        return recommendations
    
    def _deduplicate_and_rank(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicates and rank by score"""
        unique_recs = {}
        
        for rec in recommendations:
            item_id = rec['item_id']
            if item_id not in unique_recs:
                unique_recs[item_id] = rec
            else:
                # Keep higher score
                if rec['score'] > unique_recs[item_id]['score']:
                    unique_recs[item_id] = rec
        
        # Sort by score descending
        sorted_recs = sorted(
            unique_recs.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return sorted_recs