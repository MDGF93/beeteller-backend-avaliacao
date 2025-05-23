import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
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

app = FastAPI(
    title="PIX Message Collection API",
    description="""
    API for collecting and retrieving PIX messages with long polling support.
    
    ## Features
    
    * Long polling support for efficient message retrieval
    * Stream-based message delivery to ensure all messages are processed
    * Support for both single and multiple message retrieval
    * Test utilities for generating sample messages
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Support",
        "email": "placeholder@email.com",
        "url": "https://www.placeholder.com/support",
    },
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        "status": "operational",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
