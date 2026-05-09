# SmartCart-E-commerce-app-
A FastAPI-based microservice providing intelligent features for the LuxIQ e-commerce platform.

## Features

### 🤖 Machine Learning Capabilities
- **Content-based Filtering**: TF-IDF on product descriptions + tags → cosine similarity
- **Collaborative Filtering**: User-item matrix on purchase history
- **Homepage Personalisation**: Personalized product recommendations
- **Trending Products**: Most purchased/viewed products in last 7 days
- **AI Search Suggestions**: Autocomplete with NLP-based query understanding
- **Dynamic Pricing Signals**: Price drop/selling fast indicators
- **Model Retraining**: Scheduled weekly retraining on latest data

### 📊 API Endpoints

#### Recommendations
- `POST /recommendations` - Get personalized recommendations
- `GET /homepage/{userId}` - Get personalized homepage

#### Search & Discovery
- `POST /search/autocomplete` - AI-powered search autocomplete
- `GET /products/trending` - Get trending products

#### Pricing Intelligence
- `POST /products/pricing-signals/{productId}` - Get dynamic pricing signals

#### Model Management
- `POST /retrain-models` - Trigger model retraining
- `GET /models/status` - Get model status
- `GET /health` - Health check

## 🚀 Quick Start

### Option 1: Direct Python
```bash
# Clone and setup
cd ml-service
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download language models
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
python -m spacy download en_core_web_sm

# Start the service
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Docker
```bash
# Build and run
docker-compose up --build
```

### Option 3: Startup Script
```bash
# Make executable and run
chmod +x start.sh
./start.sh
```

## 🔧 Configuration

Environment variables (see `.env` file):
- `API_HOST`: Service host (default: 0.0.0.0)
- `API_PORT`: Service port (default: 8000)
- `SPRING_BOOT_API_URL`: Backend API URL (default: http://localhost:5000)
- `FRONTEND_URL`: Frontend URL (default: http://localhost:5173)

## 📈 Model Details

### TF-IDF Vectorizer
- Max features: 5000
- N-gram range: (1, 2)
- Stop words: English
- Min document frequency: 2
- Max document frequency: 0.8

### Collaborative Filtering
- Algorithm: Truncated SVD
- Components: 50
- Random state: 42

### Similarity Thresholds
- Content-based: 0.1 minimum relevance
- Search autocomplete: 0.1 minimum similarity

## 🔄 Model Retraining

Models are automatically retrained weekly on:
- Latest product data
- User interaction history
- Purchase patterns
- Search queries

Manual retraining:
```bash
curl -X POST http://localhost:8000/retrain-models
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Model Status
```bash
curl http://localhost:8000/models/status
```

## 🔗 Integration

### Spring Boot Backend
The ML service integrates with the Spring Boot backend via HTTP calls. See `MLController.java` for implementation details.

### Frontend Components
- `MLRecommendations.tsx` - Personalized product recommendations
- `AISearch.tsx` - AI-powered search with autocomplete
- `PricingSignals.tsx` - Dynamic pricing indicators

## 🧪 Testing

### Test Recommendations
```bash
curl -X POST http://localhost:8000/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "num_recommendations": 5,
    "recommendation_type": "content_based"
  }'
```

### Test Search Autocomplete
```bash
curl -X POST http://localhost:8000/search/autocomplete \
  -H "Content-Type: application/json" \
  -d '{
    "query": "laptop",
    "limit": 5
  }'
```

## 📝 Logs

Logs are written to `ml_service.log` and include:
- Model initialization
- API requests/responses
- Error details
- Retraining status

## 🐛 Troubleshooting

### Common Issues
1. **Port conflicts**: Ensure port 8000 is available
2. **Backend connection**: Verify Spring Boot is running on port 5000
3. **Memory issues**: Increase system RAM for large datasets
4. **Model loading**: Check if language models are downloaded

### Debug Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

## 🚀 Production Deployment

### Docker Production
```bash
# Build production image
docker build -t luxiq-ml-service .

# Run with production settings
docker run -d \
  --name luxiq-ml \
  -p 8000:8000 \
  -e SPRING_BOOT_API_URL=http://backend:5000 \
  luxiq-ml-service
```

### Environment Variables
Set these in production:
- `LOG_LEVEL=INFO`
- `RETRAINING_SCHEDULE=weekly`
- `API_HOST=0.0.0.0`

## 📚 Dependencies

- FastAPI 0.104.1
- scikit-learn 1.3.2
- pandas 2.1.3
- numpy 1.25.2
- nltk 3.8.1
- spacy 3.7.2

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details
