"""
Microservices Gateway

Coordinates all AI microservices for the Intelligent LMS.

Services:
- AI Content Service (Port 8001)
- AI Assessment Service (Port 8002)  
- AI Communication Service (Port 8003)
- AI Search Service (Port 8004)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from typing import Dict, Any

# Initialize FastAPI app
app = FastAPI(
    title="Intelligent LMS Microservices Gateway",
    description="Gateway for coordinating AI microservices in the Intelligent LMS",
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

# Service configuration
SERVICES = {
    "ai_content": "http://localhost:8001",
    "ai_assessment": "http://localhost:8002", 
    "ai_communication": "http://localhost:8003",
    "ai_search": "http://localhost:8004"
}

@app.get("/")
async def root():
    """Welcome endpoint with service overview."""
    return {
        "message": "Welcome to the Intelligent LMS Microservices Gateway",
        "version": "1.0.0",
        "services": {
            "ai_content": {
                "description": "AI-powered content generation and enhancement",
                "port": 8001,
                "endpoints": "/ai-content/*"
            },
            "ai_assessment": {
                "description": "AI-powered assessment generation and grading",
                "port": 8002,
                "endpoints": "/ai-assessment/*"
            },
            "ai_communication": {
                "description": "AI-powered communication and email management",
                "port": 8003, 
                "endpoints": "/ai-communication/*"
            },
            "ai_search": {
                "description": "AI-powered semantic search with RAG",
                "port": 8004,
                "endpoints": "/ai-search/*"
            }
        },
        "documentation": {
            "gateway": "/docs",
            "ai_content": "http://localhost:8001/docs",
            "ai_assessment": "http://localhost:8002/docs", 
            "ai_communication": "http://localhost:8003/docs",
            "ai_search": "http://localhost:8004/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Check health of all microservices."""
    health_status = {}
    
    async with httpx.AsyncClient() as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                if response.status_code == 200:
                    health_status[service_name] = {
                        "status": "healthy",
                        "response_time_ms": response.elapsed.total_seconds() * 1000,
                        "details": response.json()
                    }
                else:
                    health_status[service_name] = {
                        "status": "unhealthy", 
                        "error": f"HTTP {response.status_code}"
                    }
            except Exception as e:
                health_status[service_name] = {
                    "status": "unreachable",
                    "error": str(e)
                }
    
    # Determine overall health
    all_healthy = all(status["status"] == "healthy" for status in health_status.values())
    
    return {
        "overall_status": "healthy" if all_healthy else "degraded",
        "gateway_version": "1.0.0",
        "services": health_status,
        "timestamp": "2025-09-09T16:57:10Z"
    }

@app.get("/services")
async def get_service_info():
    """Get information about all available microservices."""
    service_info = {}
    
    async with httpx.AsyncClient() as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/info", timeout=10.0)
                if response.status_code == 200:
                    service_info[service_name] = response.json()
                else:
                    service_info[service_name] = {
                        "error": f"HTTP {response.status_code}",
                        "status": "unavailable"
                    }
            except Exception as e:
                service_info[service_name] = {
                    "error": str(e),
                    "status": "unreachable"
                }
    
    return {
        "gateway": "Intelligent LMS Microservices Gateway",
        "total_services": len(SERVICES),
        "services": service_info
    }

# Proxy endpoints for each service
@app.api_route("/ai-content/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_ai_content(path: str, request):
    """Proxy requests to AI Content Service."""
    return await proxy_request("ai_content", path, request)

@app.api_route("/ai-assessment/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_ai_assessment(path: str, request):
    """Proxy requests to AI Assessment Service."""
    return await proxy_request("ai_assessment", path, request)

@app.api_route("/ai-communication/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_ai_communication(path: str, request):
    """Proxy requests to AI Communication Service."""
    return await proxy_request("ai_communication", path, request)

@app.api_route("/ai-search/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_ai_search(path: str, request):
    """Proxy requests to AI Search Service."""
    return await proxy_request("ai_search", path, request)

async def proxy_request(service_name: str, path: str, request):
    """Generic proxy function for forwarding requests to microservices."""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    service_url = SERVICES[service_name]
    target_url = f"{service_url}/{path}"
    
    # Get request data
    try:
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        else:
            body = None
    except Exception:
        body = None
    
    # Forward request to microservice
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=dict(request.query_params),
                headers={k: v for k, v in request.headers.items() 
                        if k.lower() not in ['host', 'content-length']},
                content=body,
                timeout=30.0
            )
            
            # Return the response from the microservice
            from fastapi.responses import Response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Service {service_name} is unreachable: {str(e)}"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail=f"Service {service_name} request timed out"
            )

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Intelligent LMS Microservices Gateway...")
    print("\nAvailable Services:")
    for service_name, service_url in SERVICES.items():
        print(f"  • {service_name.replace('_', ' ').title()}: {service_url}")
    
    print(f"\n📖 API Documentation: http://localhost:8000/docs")
    print(f"🔍 Health Check: http://localhost:8000/health")
    print(f"📊 Services Info: http://localhost:8000/services")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
