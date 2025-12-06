import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
import faiss
import pickle
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store for efficient similarity search"""
    
    def __init__(self, dimension: int = 100):
        self.dimension = dimension
        self.index = None
        self.item_ids = []
        self.item_vectors = []
        self.item_metadata = {}
        self.is_trained = False
        
    def build_index(self, vectors: np.ndarray):
        """Build FAISS index from vectors"""
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(vectors)
        
        # Create index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.index.add(vectors)
        
        self.item_vectors = vectors
        self.is_trained = True
        
        logger.info(f"Built FAISS index with {len(vectors)} vectors")
    
    def add_items(
        self,
        item_ids: List[str],
        vectors: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None
    ):
        """Add items to vector store"""
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dimension)
        
        # Normalize and add vectors
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        
        # Store item data
        self.item_ids.extend(item_ids)
        self.item_vectors = np.vstack([self.item_vectors, vectors]) if len(self.item_vectors) > 0 else vectors
        
        if metadata:
            for i, item_id in enumerate(item_ids):
                self.item_metadata[item_id] = metadata[i] if i < len(metadata) else {}
        
        logger.info(f"Added {len(item_ids)} items to vector store")
    
    def search_similar(
        self,
        query_vector: np.ndarray,
        k: int = 10,
        filter_func: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar items"""
        if self.index is None or len(self.item_ids) == 0:
            return []
        
        # Normalize query vector
        query_vector = query_vector.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_vector)
        
        # Search
        distances, indices = self.index.search(query_vector, min(k, len(self.item_ids)))
        
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.item_ids):
                item_id = self.item_ids[idx]
                
                # Apply filter if provided
                if filter_func and not filter_func(item_id, self.item_metadata.get(item_id, {})):
                    continue
                
                results.append({
                    'item_id': item_id,
                    'similarity': float(distance),  # Cosine similarity
                    'rank': i + 1,
                    'metadata': self.item_metadata.get(item_id, {})
                })
        
        return results
    
    def get_similar_items(
        self,
        item_id: str,
        k: int = 10,
        exclude_self: bool = True
    ) -> List[Dict[str, Any]]:
        """Get items similar to given item"""
        if item_id not in self.item_ids:
            return []
        
        idx = self.item_ids.index(item_id)
        item_vector = self.item_vectors[idx].reshape(1, -1)
        
        results = self.search_similar(item_vector, k + (1 if exclude_self else 0))
        
        # Exclude the item itself if requested
        if exclude_self:
            results = [r for r in results if r['item_id'] != item_id]
        
        return results[:k]
    
    def batch_search(
        self,
        query_vectors: np.ndarray,
        k: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """Batch search for multiple queries"""
        if self.index is None:
            return []
        
        # Normalize query vectors
        query_vectors = query_vectors.astype('float32')
        faiss.normalize_L2(query_vectors)
        
        # Batch search
        distances, indices = self.index.search(query_vectors, min(k, len(self.item_ids)))
        
        all_results = []
        for i in range(len(query_vectors)):
            results = []
            for j, (distance, idx) in enumerate(zip(distances[i], indices[i])):
                if idx < len(self.item_ids):
                    item_id = self.item_ids[idx]
                    results.append({
                        'item_id': item_id,
                        'similarity': float(distance),
                        'rank': j + 1,
                        'metadata': self.item_metadata.get(item_id, {})
                    })
            all_results.append(results)
        
        return all_results
    
    def build_from_dataframe(
        self,
        df,
        vector_column: str,
        id_column: str = 'id',
        metadata_columns: Optional[List[str]] = None
    ):
        """Build vector store from pandas DataFrame"""
        item_ids = df[id_column].tolist()
        vectors = np.vstack(df[vector_column].values).astype('float32')
        
        metadata = []
        if metadata_columns:
            for _, row in df.iterrows():
                meta = {col: row[col] for col in metadata_columns}
                metadata.append(meta)
        
        self.add_items(item_ids, vectors, metadata)
    
    def save(self, filepath: str):
        """Save vector store to disk"""
        data = {
            'dimension': self.dimension,
            'item_ids': self.item_ids,
            'item_vectors': self.item_vectors,
            'item_metadata': self.item_metadata,
            'is_trained': self.is_trained,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Save FAISS index separately
        if self.index:
            faiss.write_index(self.index, f"{filepath}.index")
        
        with open(f"{filepath}.pkl", 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Saved vector store to {filepath}")
    
    def load(self, filepath: str):
        """Load vector store from disk"""
        try:
            # Load data
            with open(f"{filepath}.pkl", 'rb') as f:
                data = pickle.load(f)
            
            self.dimension = data['dimension']
            self.item_ids = data['item_ids']
            self.item_vectors = data['item_vectors']
            self.item_metadata = data['item_metadata']
            self.is_trained = data['is_trained']
            
            # Load FAISS index
            self.index = faiss.read_index(f"{filepath}.index")
            
            logger.info(f"Loaded vector store from {filepath} with {len(self.item_ids)} items")
            return True
            
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_items': len(self.item_ids),
            'dimension': self.dimension,
            'is_trained': self.is_trained,
            'metadata_fields': list(self.item_metadata.values())[0].keys() if self.item_metadata else [],
            'vector_shape': self.item_vectors.shape if len(self.item_vectors) > 0 else None
        }
    
    def create_item_vectors(
        self,
        items: List[Dict[str, Any]],
        feature_extractor: callable
    ) -> np.ndarray:
        """Create vectors from items using feature extractor"""
        vectors = []
        for item in items:
            vector = feature_extractor(item)
            vectors.append(vector)
        
        return np.array(vectors).astype('float32')
    
    def hybrid_search(
        self,
        query_vector: np.ndarray,
        text_query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """Hybrid search combining vector similarity and filters"""
        # Get vector similarity results
        vector_results = self.search_similar(query_vector, k * 2)
        
        # Apply text filter if provided
        if text_query:
            filtered_results = []
            for result in vector_results:
                metadata = result['metadata']
                item_text = ' '.join([
                    str(metadata.get('name', '')),
                    str(metadata.get('description', '')),
                    str(metadata.get('category', ''))
                ]).lower()
                
                if text_query.lower() in item_text:
                    filtered_results.append(result)
            
            vector_results = filtered_results
        
        # Apply additional filters
        if filters:
            filtered_results = []
            for result in vector_results:
                metadata = result['metadata']
                matches = True
                
                for key, value in filters.items():
                    if key in metadata:
                        if isinstance(value, list):
                            if metadata[key] not in value:
                                matches = False
                                break
                        else:
                            if metadata[key] != value:
                                matches = False
                                break
                
                if matches:
                    filtered_results.append(result)
            
            vector_results = filtered_results
        
        return vector_results[:k]