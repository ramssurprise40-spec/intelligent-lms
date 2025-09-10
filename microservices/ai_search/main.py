"""
AI Search Service

Handles AI-powered search functionality for the LMS using RAG (Retrieval-Augmented Generation).

Features:
- Semantic search across all content
- Natural language query processing
- Hybrid retrieval (vector + keyword search)
- Context-aware answers with source citations
- Search analytics and personalization
- Multi-modal search (text, images, documents)
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import uuid
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="AI Search Service",
    description="AI-powered semantic search with RAG for Intelligent LMS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class SearchType(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    FUZZY = "fuzzy"

class ContentType(str, Enum):
    COURSE = "course"
    LESSON = "lesson"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    DISCUSSION = "discussion"
    DOCUMENT = "document"
    VIDEO = "video"
    EMAIL = "email"
    ALL = "all"

class SearchScope(str, Enum):
    PERSONAL = "personal"  # User's enrolled courses
    COURSE = "course"      # Specific course
    GLOBAL = "global"      # All public content
    DEPARTMENT = "department"

# Pydantic models
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    search_type: SearchType = SearchType.HYBRID
    content_types: List[ContentType] = [ContentType.ALL]
    scope: SearchScope = SearchScope.PERSONAL
    user_id: Optional[str] = None
    course_id: Optional[str] = None
    max_results: int = Field(default=20, ge=1, le=100)
    include_snippets: bool = True
    include_similar: bool = False
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    id: str
    title: str
    content_type: ContentType
    snippet: Optional[str] = None
    full_content: Optional[str] = None
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    source_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class SearchResponse(BaseModel):
    query: str
    search_type: SearchType
    total_results: int
    results: List[SearchResult]
    search_time_ms: float
    suggestions: Optional[List[str]] = []
    filters_applied: Optional[Dict[str, Any]] = {}
    search_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class AnswerRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    context_sources: Optional[List[str]] = None  # Specific content IDs to use as context
    user_id: Optional[str] = None
    course_id: Optional[str] = None
    answer_length: str = Field(default="medium", regex="^(short|medium|long)$")
    include_sources: bool = True

class AnswerResponse(BaseModel):
    query: str
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: List[SearchResult] = []
    related_questions: List[str] = []
    answer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = Field(default_factory=datetime.now)

class IndexRequest(BaseModel):
    content_id: str
    title: str
    content: str
    content_type: ContentType
    metadata: Optional[Dict[str, Any]] = {}
    course_id: Optional[str] = None
    user_id: Optional[str] = None
    tags: Optional[List[str]] = []

class SimilarContentRequest(BaseModel):
    content_id: str
    content_type: Optional[ContentType] = None
    max_results: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

class SearchAnalytics(BaseModel):
    total_searches: int
    popular_queries: List[Dict[str, Any]]
    search_trends: Dict[str, Any]
    user_engagement: Dict[str, Any]
    performance_metrics: Dict[str, Any]

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring."""
    return {"status": "healthy", "service": "ai-search", "version": "1.0.0"}

# Core search endpoints
@app.post("/search", response_model=SearchResponse)
async def search_content(request: SearchRequest):
    """
    Perform AI-powered search across LMS content.
    
    - **query**: Search query (natural language supported)
    - **search_type**: Type of search to perform
    - **content_types**: Types of content to include in search
    - **scope**: Search scope (personal, course, global)
    - **max_results**: Maximum number of results to return
    - **include_snippets**: Include content snippets in results
    - **filters**: Additional filters to apply
    """
    try:
        from rag_engine import get_rag_engine
        import time
        start_time = time.time()
        
        # Get RAG engine instance
        rag_engine = get_rag_engine()
        
        # Perform search using RAG engine
        search_results = rag_engine.search(
            query=request.query,
            search_type=request.search_type.value,
            max_results=request.max_results
        )
        
        # Convert RAG results to API response format
        api_results = []
        for doc in search_results:
            # Map content type from metadata
            content_type = ContentType.LESSON  # Default
            if 'content_type' in doc.get('metadata', {}):
                try:
                    content_type = ContentType(doc['metadata']['content_type'])
                except ValueError:
                    pass
            
            result = SearchResult(
                id=doc['id'],
                title=doc.get('metadata', {}).get('title', 'Untitled'),
                content_type=content_type,
                snippet=doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'] if request.include_snippets else None,
                relevance_score=doc.get('final_score', doc.get('similarity_score', 0.0)),
                source_url=doc.get('metadata', {}).get('source_url'),
                metadata=doc.get('metadata', {}),
                created_at=datetime.fromisoformat(doc.get('metadata', {}).get('created_at', datetime.now().isoformat()))
            )
            api_results.append(result)
        
        search_time = (time.time() - start_time) * 1000
        
        # Generate query suggestions
        suggestions = [
            f"{request.query} tutorial",
            f"{request.query} examples", 
            f"{request.query} fundamentals",
            f"advanced {request.query}",
            f"{request.query} practice"
        ]
        
        return SearchResponse(
            query=request.query,
            search_type=request.search_type,
            total_results=len(api_results),
            results=api_results,
            search_time_ms=search_time,
            suggestions=suggestions[:3],
            filters_applied=request.filters or {}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/answer", response_model=AnswerResponse)
async def generate_answer(request: AnswerRequest):
    """
    Generate AI-powered answers using RAG (Retrieval-Augmented Generation).
    
    - **query**: Question to answer
    - **context_sources**: Specific content to use as context
    - **answer_length**: Desired answer length (short, medium, long)
    - **include_sources**: Whether to include source citations
    """
    try:
        from rag_engine import get_rag_engine
        
        # Get RAG engine instance
        rag_engine = get_rag_engine()
        
        # Generate answer using RAG
        rag_result = rag_engine.generate_answer(
            query=request.query,
            context_ids=request.context_sources,
            answer_length=request.answer_length
        )
        
        # Convert RAG sources to API format
        api_sources = []
        if request.include_sources and rag_result.get('sources'):
            for doc in rag_result['sources']:
                # Map content type from metadata
                content_type = ContentType.LESSON  # Default
                if 'content_type' in doc.get('metadata', {}):
                    try:
                        content_type = ContentType(doc['metadata']['content_type'])
                    except ValueError:
                        pass
                
                source = SearchResult(
                    id=doc['id'],
                    title=doc.get('metadata', {}).get('title', 'Untitled'),
                    content_type=content_type,
                    snippet=doc['content'][:150] + '...' if len(doc['content']) > 150 else doc['content'],
                    relevance_score=doc.get('final_score', doc.get('similarity_score', 0.0)),
                    source_url=doc.get('metadata', {}).get('source_url'),
                    metadata=doc.get('metadata', {})
                )
                api_sources.append(source)
        
        return AnswerResponse(
            query=request.query,
            answer=rag_result.get('answer', 'Unable to generate answer.'),
            confidence=rag_result.get('confidence', 0.0),
            sources=api_sources,
            related_questions=rag_result.get('related_questions', [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answer generation failed: {str(e)}")

@app.post("/index")
async def index_content(request: IndexRequest):
    """
    Index new content for search.
    
    - **content_id**: Unique identifier for the content
    - **title**: Content title
    - **content**: Full text content to index
    - **content_type**: Type of content being indexed
    - **metadata**: Additional metadata for the content
    """
    try:
        from rag_engine import get_rag_engine
        import time
        start_time = time.time()
        
        # Get RAG engine instance
        rag_engine = get_rag_engine()
        
        # Index the document
        success = rag_engine.index_document(
            doc_id=request.content_id,
            title=request.title,
            content=request.content,
            metadata={
                'content_type': request.content_type.value,
                'course_id': request.course_id,
                'user_id': request.user_id,
                'tags': request.tags or [],
                **request.metadata
            }
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        if success:
            return {
                "status": "success",
                "content_id": request.content_id,
                "message": "Content successfully indexed",
                "indexed_at": datetime.now(),
                "processing_info": {
                    "text_length": len(request.content),
                    "embedding_dimensions": 384,  # all-MiniLM-L6-v2 dimensions
                    "processing_time_ms": round(processing_time, 2),
                    "index_version": "v2.1"
                }
            }
        else:
            return {
                "status": "error",
                "content_id": request.content_id,
                "message": "Failed to index content",
                "error": "Indexing operation failed"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content indexing failed: {str(e)}")

@app.delete("/index/{content_id}")
async def remove_from_index(content_id: str):
    """
    Remove content from search index.
    
    - **content_id**: ID of content to remove from index
    """
    try:
        from rag_engine import get_rag_engine
        
        # Get RAG engine instance
        rag_engine = get_rag_engine()
        
        # Remove document from index
        success = rag_engine.delete_document(content_id)
        
        if success:
            return {
                "status": "success",
                "content_id": content_id,
                "message": "Content removed from index",
                "removed_at": datetime.now()
            }
        else:
            return {
                "status": "error",
                "content_id": content_id,
                "message": "Failed to remove content from index",
                "error": "Removal operation failed"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content removal failed: {str(e)}")

@app.post("/similar", response_model=List[SearchResult])
async def find_similar_content(request: SimilarContentRequest):
    """
    Find content similar to a given piece of content.
    
    - **content_id**: ID of the reference content
    - **max_results**: Maximum number of similar items to return
    - **similarity_threshold**: Minimum similarity score to include
    """
    try:
        # TODO: Implement similarity search using vector embeddings
        
        # Mock similar content
        similar_results = []
        for i in range(min(request.max_results, 5)):
            result = SearchResult(
                id=f"similar_{i+1}",
                title=f"Similar Content {i+1}",
                content_type=ContentType.LESSON,
                snippet="This content covers related topics and concepts...",
                relevance_score=max(request.similarity_threshold + 0.1, 0.9 - (i * 0.1)),
                source_url=f"/content/similar_{i+1}",
                metadata={"similarity_type": "semantic", "algorithm": "cosine"}
            )
            similar_results.append(result)
            
        return similar_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")

@app.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial query for suggestions"),
    limit: int = Query(default=10, ge=1, le=20, description="Number of suggestions")
):
    """
    Get search query suggestions based on partial input.
    
    - **q**: Partial query string
    - **limit**: Maximum number of suggestions to return
    """
    try:
        # TODO: Implement intelligent query suggestions
        # This would use query history, popular searches, and semantic similarity
        
        base_suggestions = [
            f"{q} tutorial",
            f"{q} guide",
            f"{q} examples",
            f"{q} definition",
            f"{q} overview",
            f"how to {q}",
            f"{q} best practices",
            f"{q} fundamentals",
            f"advanced {q}",
            f"{q} applications"
        ]
        
        return {
            "query": q,
            "suggestions": base_suggestions[:limit],
            "suggestion_types": ["completion", "related", "popular"],
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestion generation failed: {str(e)}")

@app.get("/analytics", response_model=SearchAnalytics)
async def get_search_analytics(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    user_id: Optional[str] = Query(None, description="User ID for personalized analytics")
):
    """
    Get search analytics and insights.
    
    - **days**: Number of days to include in analytics
    - **user_id**: Optional user ID for personalized analytics
    """
    try:
        # TODO: Implement search analytics
        # This would analyze search patterns, popular queries, performance metrics
        
        return SearchAnalytics(
            total_searches=1547,
            popular_queries=[
                {"query": "machine learning", "count": 89, "trend": "up"},
                {"query": "database design", "count": 67, "trend": "stable"},
                {"query": "python programming", "count": 56, "trend": "up"}
            ],
            search_trends={
                "peak_hours": ["10-11 AM", "2-3 PM", "7-8 PM"],
                "popular_content_types": {"lesson": 45, "document": 32, "quiz": 23},
                "avg_results_per_query": 8.3,
                "avg_search_time_ms": 245
            },
            user_engagement={
                "click_through_rate": 0.73,
                "avg_session_searches": 3.2,
                "bounce_rate": 0.15,
                "satisfaction_score": 4.2
            },
            performance_metrics={
                "search_latency_p95": 380,
                "index_size_mb": 2847,
                "total_documents": 15429,
                "indexing_rate_per_hour": 450
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics generation failed: {str(e)}")

@app.post("/feedback")
async def submit_search_feedback(
    search_id: str,
    rating: int = Query(..., ge=1, le=5, description="Rating from 1-5"),
    feedback: Optional[str] = Query(None, description="Optional text feedback"),
    user_id: Optional[str] = Query(None, description="User ID")
):
    """
    Submit feedback for search results to improve the system.
    
    - **search_id**: ID of the search session
    - **rating**: Rating from 1-5 stars
    - **feedback**: Optional text feedback
    - **user_id**: Optional user ID
    """
    try:
        # TODO: Store feedback for model improvement
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully",
            "search_id": search_id,
            "rating": rating,
            "feedback_id": str(uuid.uuid4()),
            "thank_you": "Your feedback helps us improve search results!"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")

# Service information endpoint
@app.get("/info")
async def service_info():
    """Get information about the AI Search Service."""
    return {
        "service": "AI Search Service",
        "version": "1.0.0", 
        "description": "AI-powered semantic search with RAG capabilities",
        "endpoints": {
            "POST /search": "Perform semantic search across content",
            "POST /answer": "Generate AI answers using RAG",
            "POST /index": "Index new content for search",
            "DELETE /index/{content_id}": "Remove content from index", 
            "POST /similar": "Find similar content",
            "GET /suggestions": "Get search query suggestions",
            "GET /analytics": "Get search analytics and insights",
            "POST /feedback": "Submit search feedback",
            "GET /health": "Health check",
            "GET /info": "Service information"
        },
        "search_capabilities": [
            "Semantic Search",
            "Keyword Search", 
            "Hybrid Search",
            "Fuzzy Matching",
            "Multi-modal Search"
        ],
        "ai_features": [
            "RAG-based Q&A",
            "Content Similarity",
            "Query Suggestions", 
            "Search Analytics",
            "Personalization"
        ],
        "supported_content_types": [ct.value for ct in ContentType],
        "search_types": [st.value for st in SearchType]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
