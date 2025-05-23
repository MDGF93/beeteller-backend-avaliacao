from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Header, Response, status, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from models.api_models import PixMessageResponse, TerminateStreamResponse, EXAMPLES
from models.pix_message import MessageStream
from utils.message_processor import MessageProcessor

router = APIRouter(prefix="/api/pix")


@router.get(
    "/{ispb}/stream/start",
    summary="Start a new message stream",
    description="""
    Initiates message retrieval for a specific institution. This endpoint uses long polling 
    (up to 8 seconds) to efficiently retrieve messages. If no messages are available within 
    the polling period, a 204 No Content response is returned.
    
    The response includes headers that provide information about the stream:
    - X-Stream-Id: Unique identifier for the stream, used in subsequent requests
    - X-Has-More: Indicates if more messages are available (true/false)
    
    The Accept header can be used to control the response format:
    - application/json: Returns a single message (default)
    - multipart/json: Returns multiple messages in an array
    """,
    response_model=Union[PixMessageResponse, List[PixMessageResponse]],
    response_model_exclude_none=True,
    responses={
        200: {
            "description": "Successful response with PIX message(s)",
            "content": {
                "application/json": {
                    "examples": {
                        "single": EXAMPLES["single_message"],
                        "multiple": EXAMPLES["multiple_messages"],
                    }
                }
            },
            "headers": {
                "X-Stream-Id": {
                    "description": "Unique identifier for the message stream",
                    "schema": {"type": "string"},
                },
                "X-Has-More": {
                    "description": "Indicates if more messages are available",
                    "schema": {"type": "boolean"},
                },
            },
        },
        204: {
            "description": "No messages available",
            "headers": {
                "X-Stream-Id": {
                    "description": "Unique identifier for the message stream",
                    "schema": {"type": "string"},
                },
                "X-Has-More": {
                    "description": "Indicates if more messages are available (always false for 204)",
                    "schema": {"type": "boolean"},
                },
            },
        },
        400: {"description": "Invalid ISPB format"},
        500: {"description": "Internal server error"},
    },
)
async def start_stream(
    ispb: str = Path(
        ...,
        description="8-digit code identifying a payment institution",
        example="12345678",
    ),
    response: Response = None,
    accept: Optional[str] = Header(
        None,
        description="Determines response format - application/json for single message, multipart/json for multiple messages",
    ),
    db: Session = Depends(get_db),
):
    """
    Initiates message retrieval for a specific institution

    Args:
        ispb: 8-digit code identifying a payment institution
        accept: Determines response format - application/json for single message, multipart/json for multiple messages

    Returns:
        PIX message(s) or 204 No Content if no messages available
    """
    # Validate ISPB format (8 digits)
    if not ispb.isdigit() or len(ispb) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ISPB must be an 8-digit code",
        )

    # Determine if single or multiple messages are requested
    single_message = True
    if accept and "multipart/json" in accept.lower():
        single_message = False

    try:
        # Fetch messages with long polling (up to 8 seconds)
        messages, stream_id = await MessageProcessor.fetch_messages(
            ispb=ispb,
            stream_id=None,  # New stream
            db=db,
            max_wait=8,
            single_message=single_message,
        )

        # Set appropriate headers
        headers = MessageProcessor.format_response_headers(
            ispb=ispb, stream_id=stream_id, has_messages=len(messages) > 0
        )

        # Return appropriate response
        if not messages:
            return Response(status_code=status.HTTP_204_NO_CONTENT, headers=headers)

        if single_message:
            return JSONResponse(content=messages[0], headers=headers)
        else:
            return JSONResponse(content=messages, headers=headers)

    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error and return a 500 response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the request: {str(e)}",
        )


@router.get(
    "/{ispb}/stream/{interationId}",
    summary="Continue an existing message stream",
    description="""
    Continues message retrieval from a previously started stream. This endpoint uses long polling 
    (up to 8 seconds) to efficiently retrieve messages. If no messages are available within 
    the polling period, a 204 No Content response is returned.
    
    The response includes headers that provide information about the stream:
    - X-Stream-Id: Unique identifier for the stream, used in subsequent requests
    - X-Has-More: Indicates if more messages are available (true/false)
    
    The Accept header can be used to control the response format:
    - application/json: Returns a single message (default)
    - multipart/json: Returns multiple messages in an array
    """,
    response_model=Union[PixMessageResponse, List[PixMessageResponse]],
    response_model_exclude_none=True,
    responses={
        200: {
            "description": "Successful response with PIX message(s)",
            "content": {
                "application/json": {
                    "examples": {
                        "single": EXAMPLES["single_message"],
                        "multiple": EXAMPLES["multiple_messages"],
                    }
                }
            },
            "headers": {
                "X-Stream-Id": {
                    "description": "Unique identifier for the message stream",
                    "schema": {"type": "string"},
                },
                "X-Has-More": {
                    "description": "Indicates if more messages are available",
                    "schema": {"type": "boolean"},
                },
            },
        },
        204: {
            "description": "No messages available",
            "headers": {
                "X-Stream-Id": {
                    "description": "Unique identifier for the message stream",
                    "schema": {"type": "string"},
                },
                "X-Has-More": {
                    "description": "Indicates if more messages are available (always false for 204)",
                    "schema": {"type": "boolean"},
                },
            },
        },
        400: {"description": "Invalid ISPB format"},
        404: {"description": "Stream not found"},
        500: {"description": "Internal server error"},
    },
)
async def continue_stream(
    ispb: str = Path(
        ...,
        description="8-digit code identifying a payment institution",
        example="12345678",
    ),
    interationId: str = Path(
        ...,
        description="The stream ID from a previous request",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    response: Response = None,
    accept: Optional[str] = Header(
        None,
        description="Determines response format - application/json for single message, multipart/json for multiple messages",
    ),
    db: Session = Depends(get_db),
):
    """
    Continues message retrieval from a previously started stream

    Args:
        ispb: 8-digit code identifying a payment institution
        interationId: The stream ID from a previous request
        accept: Determines response format - application/json for single message, multipart/json for multiple messages

    Returns:
        PIX message(s) or 204 No Content if no messages available
    """
    # Validate ISPB format (8 digits)
    if not ispb.isdigit() or len(ispb) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ISPB must be an 8-digit code",
        )

    # Determine if single or multiple messages are requested
    single_message = True
    if accept and "multipart/json" in accept.lower():
        single_message = False

    try:
        # Fetch messages with long polling (up to 8 seconds)
        messages, stream_id = await MessageProcessor.fetch_messages(
            ispb=ispb,
            stream_id=interationId,
            db=db,
            max_wait=8,
            single_message=single_message,
        )

        # Set appropriate headers
        headers = MessageProcessor.format_response_headers(
            ispb=ispb, stream_id=stream_id, has_messages=len(messages) > 0
        )

        # Return appropriate response
        if not messages:
            return Response(status_code=status.HTTP_204_NO_CONTENT, headers=headers)

        if single_message:
            return JSONResponse(content=messages[0], headers=headers)
        else:
            return JSONResponse(content=messages, headers=headers)

    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error and return a 500 response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the request: {str(e)}",
        )


@router.delete(
    "/{ispb}/stream/{interationId}",
    summary="Terminate a message stream",
    description="""
    Terminates a stream and confirms successful message receipt. This endpoint should be called 
    after all messages have been successfully processed to acknowledge receipt and prevent 
    message duplication.
    
    The stream will be deactivated and all associated messages will be marked as delivered.
    """,
    response_model=TerminateStreamResponse,
    responses={
        200: {
            "description": "Stream successfully terminated",
            "content": {
                "application/json": {"example": EXAMPLES["terminate_stream"]["value"]}
            },
        },
        400: {"description": "Invalid ISPB format"},
        403: {"description": "Stream does not belong to the specified ISPB"},
        404: {"description": "Stream not found"},
        500: {"description": "Internal server error"},
    },
)
async def terminate_stream(
    ispb: str = Path(
        ...,
        description="8-digit code identifying a payment institution",
        example="12345678",
    ),
    interationId: str = Path(
        ...,
        description="The stream ID to terminate",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    ),
    db: Session = Depends(get_db),
):
    """
    Terminates a stream and confirms successful message receipt

    Args:
        ispb: 8-digit code identifying a payment institution
        interationId: The stream ID to terminate

    Returns:
        Empty JSON object
    """
    # Validate ISPB format (8 digits)
    if not ispb.isdigit() or len(ispb) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ISPB must be an 8-digit code",
        )

    try:
        # Verify the stream exists and belongs to the specified ISPB
        stream = MessageStream.get_by_stream_id(db, interationId)
        if not stream:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stream {interationId} not found",
            )

        if stream.ispb != ispb:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Stream {interationId} does not belong to ISPB {ispb}",
            )

        # Mark messages as delivered and deactivate the stream
        success = MessageProcessor.mark_messages_delivered(interationId, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to mark messages as delivered",
            )

        # Return empty JSON object as specified
        return {}

    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error and return a 500 response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the request: {str(e)}",
        )
