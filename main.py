
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
# Import routers
from routes import message_routes, utility_routes

# Create all tables if they don't exist
Base.metadata.create_all(bind=engine)

# Load environment variables
load_dotenv()

# Define API tags metadata
tags_metadata = [
    {
        "name": "PIX Messages",
        "description": "Operations for retrieving PIX messages with long polling support",
    },
    {
        "name": "Utilities",
        "description": "Utility operations for testing and administration",
    },
]

# Initialize FastAPI app
app = FastAPI(
    title="PIX Message Collection API",
    description="""
    API for collecting and retrieving PIX messages with long polling support.
    
    ## Features
    
    * Long polling support for efficient message retrieval
    * Stream-based message delivery to ensure all messages are processed
    * Support for both single and multiple message retrieval
    * Test utilities for generating sample messages
    
    ## Authentication
    
    This API uses API keys for authentication. Contact the administrator to obtain your API key.
    
    ## Rate Limiting
    
    Rate limiting is applied to prevent abuse. Contact the administrator for details.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "API Support",
        "email": "support@pixmessageapi.com",
        "url": "https://www.pixmessageapi.com/support",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(message_routes.router, tags=["PIX Messages"])
app.include_router(utility_routes.router, prefix="/api", tags=["Utilities"])

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that provides basic API information
    
    Returns:
        A welcome message with basic API information
    """
    return {
        "message": "Welcome to PIX Message Collection API",
        "version": "1.0.0",
        "documentation": "/docs",
        "status": "operational"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
