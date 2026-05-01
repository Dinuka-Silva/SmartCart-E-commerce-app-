from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
from datetime import datetime, timedelta
import requests
import json
import re
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LuxIQ ML Service", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class Product(BaseModel):
    _id: str
    name: str
    description: str
    category: str
    price: float
    tags: List[str] = []

class UserInteraction(BaseModel):
    user_id: str
    product_id: str
    interaction_type: str  # 'view', 'purchase', 'cart', 'wishlist'
    timestamp: datetime

class RecommendationRequest(BaseModel):
    user_id: str
    product_id: Optional[str] = None
    num_recommendations: int = 10
    recommendation_type: str = "content_based"  # 'content_based', 'collaborative', 'hybrid'

class SearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    limit: int = 10

class PricingSignal(BaseModel):
    product_id: str
    current_price: float
    historical_prices: List[float]
    view_count: int
    purchase_count: int
    stock_level: int

class SizeRecommendationRequest(BaseModel):
    user_id: str
    product_id: str
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    past_sizes: Dict[str, str] = {}

class PricePredictionRequest(BaseModel):
    product_id: str
    current_price: float
    category: str
    season: Optional[str] = None

# Global variables for ML models
tfidf_vectorizer = None
product_tfidf_matrix = None
products_df = None
user_item_matrix = None
collaborative_model = None
trending_products = []
pricing_signals = {}

# Initialize data and models
async def initialize_ml_service():
    """Initialize ML models and load data"""
    global tfidf_vectorizer, product_tfidf_matrix, products_df, user_item_matrix, collaborative_model, trending_products, pricing_signals
    
    try:
        # Load product data from Spring Boot API
        response = requests.get("http://localhost:5000/api/products")
        if response.status_code == 200:
            products_data = response.json()
            products_df = pd.DataFrame(products_data.get('products', []))
            
            # Preprocess product data
            products_df['combined_text'] = products_df['name'] + ' ' + products_df['description'] + ' ' + products_df['category'].apply(str)
            products_df['tags_str'] = products_df.get('tags', []).apply(lambda x: ' '.join(x) if isinstance(x, list) else str(x))
            products_df['full_text'] = products_df['combined_text'] + ' ' + products_df['tags_str']
            
            # Initialize TF-IDF Vectorizer
            tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.8
            )
            
            # Fit TF-IDF on product descriptions
            product_tfidf_matrix = tfidf_vectorizer.fit_transform(products_df['full_text'])
            
            # Initialize collaborative filtering model
            collaborative_model = TruncatedSVD(n_components=50, random_state=42)
            
            logger.info(f"ML Service initialized with {len(products_df)} products")
        else:
            logger.error("Failed to fetch products from API")
            
    except Exception as e:
        logger.error(f"Error initializing ML service: {e}")

@app.on_event("startup")
async def startup_event():
    await initialize_ml_service()

@app.get("/")
async def root():
    return {"message": "LuxIQ ML Service is running", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "models_loaded": tfidf_vectorizer is not None}

# Content-based Filtering
def get_content_based_recommendations(product_id: str, num_recommendations: int = 10):
    """Get content-based recommendations using TF-IDF and cosine similarity"""
    try:
        if product_tfidf_matrix is None or products_df is None:
            return []
        
        # Find the product index
        product_idx = products_df[products_df['_id'] == product_id].index
        if len(product_idx) == 0:
            return []
        
        product_idx = product_idx[0]
        
        # Calculate cosine similarity
        cosine_similarities = cosine_similarity(
            product_tfidf_matrix[product_idx:product_idx+1], 
            product_tfidf_matrix
        ).flatten()
        
        # Get top similar products (excluding the product itself)
        similar_indices = cosine_similarities.argsort()[::-1][1:num_recommendations+1]
        
        recommendations = []
        for idx in similar_indices:
            if idx < len(products_df):
                product = products_df.iloc[idx]
                recommendations.append({
                    "product_id": product['_id'],
                    "name": product['name'],
                    "category": product['category'],
                    "price": product['price'],
                    "similarity_score": float(cosine_similarities[idx]),
                    "reason": "Similar products you might like"
                })
        
        return recommendations[:num_recommendations]
        
    except Exception as e:
        logger.error(f"Error in content-based recommendations: {e}")
        return []

# Collaborative Filtering
def get_collaborative_recommendations(user_id: str, num_recommendations: int = 10):
    """Get collaborative filtering recommendations based on user behavior"""
    try:
        # This would typically use user-item interaction matrix
        # For now, return popular products as placeholder
        if products_df is None:
            return []
        
        # Get top products by rating/popularity
        top_products = products_df.nlargest(num_recommendations, 'price')  # Placeholder logic
        
        recommendations = []
        for _, product in top_products.iterrows():
            recommendations.append({
                "product_id": product['_id'],
                "name": product['name'],
                "category": product['category'],
                "price": product['price'],
                "similarity_score": 0.8,  # Placeholder score
                "reason": "Customers also bought this"
            })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error in collaborative recommendations: {e}")
        return []

@app.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """Get personalized recommendations"""
    try:
        recommendations = []
        
        if request.recommendation_type == "content_based" and request.product_id:
            recommendations = get_content_based_recommendations(
                request.product_id, 
                request.num_recommendations
            )
        elif request.recommendation_type == "collaborative":
            recommendations = get_collaborative_recommendations(
                request.user_id, 
                request.num_recommendations
            )
        else:
            # Hybrid approach
            content_recs = get_content_based_recommendations(
                request.product_id, 
                request.num_recommendations // 2
            ) if request.product_id else []
            
            collab_recs = get_collaborative_recommendations(
                request.user_id, 
                request.num_recommendations // 2
            )
            
            recommendations = content_recs + collab_recs
        
        return {
            "user_id": request.user_id,
            "recommendations": recommendations[:request.num_recommendations],
            "type": request.recommendation_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@app.post("/search/autocomplete")
async def search_autocomplete(request: SearchRequest):
    """AI-powered search autocomplete with NLP understanding"""
    try:
        if tfidf_vectorizer is None or products_df is None:
            return {"suggestions": []}
        
        # Preprocess query
        query_processed = re.sub(r'[^\w\s]', '', request.query.lower())
        
        # Transform query using TF-IDF
        query_vector = tfidf_vectorizer.transform([query_processed])
        
        # Calculate similarity with all products
        similarities = cosine_similarity(query_vector, product_tfidf_matrix).flatten()
        
        # Get top matches
        top_indices = similarities.argsort()[::-1][:request.limit]
        
        suggestions = []
        for idx in top_indices:
            if similarities[idx] > 0.1 and idx < len(products_df):  # Threshold for relevance
                product = products_df.iloc[idx]
                suggestions.append({
                    "product_id": product['_id'],
                    "name": product['name'],
                    "category": product['category'],
                    "price": product['price'],
                    "relevance_score": float(similarities[idx]),
                    "highlight": f"Match found in {product['category']}"
                })
        
        return {"query": request.query, "suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Error in search autocomplete: {e}")
        return {"suggestions": []}

@app.get("/products/trending")
async def get_trending_products(days: int = 7, limit: int = 10):
    """Get trending products based on recent activity"""
    try:
        # This would typically analyze recent views, purchases, etc.
        # For now, return a mix of products as trending
        if products_df is None:
            return {"trending_products": []}
        
        # Simulate trending by selecting random products
        trending_sample = products_df.sample(min(limit, len(products_df)))
        
        trending_products_list = []
        for _, product in trending_sample.iterrows():
            trending_products_list.append({
                "product_id": product['_id'],
                "name": product['name'],
                "category": product['category'],
                "price": product['price'],
                "trending_score": np.random.uniform(0.7, 1.0),  # Placeholder score
                "views_last_7d": np.random.randint(100, 1000),
                "purchases_last_7d": np.random.randint(10, 100),
                "reason": "Trending in your area"
            })
        
        # Sort by trending score
        trending_products_list.sort(key=lambda x: x['trending_score'], reverse=True)
        
        return {
            "trending_products": trending_products_list[:limit],
            "period_days": days,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting trending products: {e}")
        return {"trending_products": []}

@app.post("/products/pricing-signals")
async def get_pricing_signals(product_id: str, current_data: PricingSignal):
    """Generate dynamic pricing signals based on ML"""
    try:
        signals = []
        
        # Price drop signal
        if len(current_data.historical_prices) > 1:
            price_change = (current_data.historical_prices[-1] - current_data.historical_prices[0]) / current_data.historical_prices[0]
            if price_change < -0.1:  # More than 10% drop
                signals.append({
                    "type": "price_drop",
                    "message": f"Price dropped by {abs(price_change)*100:.1f}%",
                    "urgency": "high",
                    "confidence": 0.9
                })
        
        # Selling fast signal
        if current_data.stock_level < 20 and current_data.view_count > 100:
            signals.append({
                "type": "selling_fast",
                "message": "Only a few left - selling fast!",
                "urgency": "high",
                "confidence": 0.85
            })
        
        # Popular item signal
        if current_data.purchase_count > 50:
            signals.append({
                "type": "popular_choice",
                "message": f"{current_data.purchase_count} people bought this recently",
                "urgency": "medium",
                "confidence": 0.8
            })
        
        # Low stock alert
        if current_data.stock_level < 10:
            signals.append({
                "type": "low_stock",
                "message": "Running low on stock",
                "urgency": "high",
                "confidence": 0.95
            })
        
        return {
            "product_id": product_id,
            "signals": signals,
            "current_price": current_data.current_price,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating pricing signals: {e}")
        return {"signals": []}

@app.post("/size-recommendation")
async def get_size_recommendation(request: SizeRecommendationRequest):
    """AI size guide based on user metrics and brand data"""
    try:
        # Placeholder logic for size prediction
        # In a real app, this would use a trained regression/classification model
        recommended_size = "M"
        confidence = 0.85
        
        if request.height_cm and request.height_cm > 185:
            recommended_size = "XL"
        elif request.height_cm and request.height_cm > 175:
            recommended_size = "L"
        elif request.height_cm and request.height_cm < 165:
            recommended_size = "S"
            
        return {
            "product_id": request.product_id,
            "recommended_size": recommended_size,
            "confidence": confidence,
            "reason": "Based on your height and typical brand fit"
        }
    except Exception as e:
        logger.error(f"Error in size recommendation: {e}")
        return {"error": str(e)}

@app.post("/predict-price-drop")
async def predict_price_drop(request: PricePredictionRequest):
    """Predict price drops using XGBoost model"""
    try:
        # Mock prediction logic (representing XGBoost output)
        import random
        probability = random.uniform(0.1, 0.9)
        days_to_drop = random.randint(1, 30)
        
        return {
            "product_id": request.product_id,
            "drop_probability": probability,
            "estimated_days": days_to_drop,
            "action": "Buy now" if probability < 0.4 else "Wait for drop",
            "confidence": 0.78
        }
    except Exception as e:
        logger.error(f"Error in price prediction: {e}")
        return {"error": str(e)}

@app.post("/retrain-models")
async def retrain_models(background_tasks: BackgroundTasks):
    """Trigger model retraining job"""
    try:
        # Add retraining task to background
        background_tasks.add_task(retrain_all_models)
        
        return {
            "message": "Model retraining started",
            "status": "in_progress",
            "started_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting model retraining: {e}")
        raise HTTPException(status_code=500, detail="Failed to start retraining")

async def retrain_all_models():
    """Background task to retrain all ML models"""
    try:
        logger.info("Starting model retraining...")
        
        # Retrain TF-IDF vectorizer
        await initialize_ml_service()
        
        # Save updated models
        if tfidf_vectorizer:
            joblib.dump(tfidf_vectorizer, "models/tfidf_vectorizer.joblib")
        
        if product_tfidf_matrix is not None:
            joblib.dump(product_tfidf_matrix, "models/product_tfidf_matrix.joblib")
        
        logger.info("Model retraining completed successfully")
        
    except Exception as e:
        logger.error(f"Error in model retraining: {e}")

@app.get("/models/status")
async def get_model_status():
    """Get status of all ML models"""
    return {
        "tfidf_vectorizer": tfidf_vectorizer is not None,
        "product_tfidf_matrix": product_tfidf_matrix is not None,
        "collaborative_model": collaborative_model is not None,
        "products_loaded": products_df is not None,
        "total_products": len(products_df) if products_df is not None else 0,
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
