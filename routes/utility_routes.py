from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from database import get_db
from models.api_models import GenerateMessagesResponse, EXAMPLES
from utils.test_data_generator import create_test_messages

router = APIRouter()


@router.post(
    "/util/msgs/{ispb}/{number}",
    status_code=status.HTTP_201_CREATED,
    summary="Generate test PIX messages",
    description="""
    Generate and insert random PIX messages for testing purposes. This endpoint creates 
    the specified number of random PIX messages with the given ISPB as the receiver.
    
    The generated messages will have random:
    - Sender ISPBs
    - Transaction amounts
    - PIX keys
    - Transaction types
    - Additional information
    
    This endpoint is intended for testing and development purposes only.
    """,
    response_model=GenerateMessagesResponse,
    responses={
        201: {
            "description": "Messages successfully generated",
            "content": {
                "application/json": {"example": EXAMPLES["generate_messages"]["value"]}
            },
        },
        400: {"description": "Invalid ISPB format or number of messages"},
        500: {"description": "Internal server error"},
    },
)
async def generate_test_messages(
    ispb: str = Path(
        ...,
        description="Institution to set as receiver (8-digit code)",
        example="12345678",
    ),
    number: int = Path(
        ...,
        description="Number of messages to generate (1-100)",
        example=10,
        gt=0,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    """
    Generate and insert random PIX messages for testing
    """
    if not ispb.isdigit() or len(ispb) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ISPB must be an 8-digit code",
        )

    if number <= 0 or number > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of messages must be between 1 and 100",
        )

    try:
        created_messages = create_test_messages(ispb, number, db)

        total_value = sum(msg["valor"] for msg in created_messages)

        return {
            "status": "success",
            "messages_generated": number,
            "receiver_ispb": ispb,
            "total_value": round(total_value, 2),
            "message": f"Successfully generated {number} test messages for ISPB {ispb}",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating test messages: {str(e)}",
        )
