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
    """
    if not ispb.isdigit() or len(ispb) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ISPB must be an 8-digit code",
        )

    single_message = True
    if accept and "multipart/json" in accept.lower():
        single_message = False

    try:
        messages, stream_id = await MessageProcessor.fetch_messages(
            ispb=ispb,
            stream_id=None,
            db=db,
            max_wait=8,
            single_message=single_message,
        )

        headers = MessageProcessor.format_response_headers(
            ispb=ispb, stream_id=stream_id, has_messages=len(messages) > 0
        )

        if not messages:
            return Response(status_code=status.HTTP_204_NO_CONTENT, headers=headers)

        if single_message:
            return JSONResponse(content=messages[0], headers=headers)
        else:
            return JSONResponse(content=messages, headers=headers)

    except HTTPException as e:
        raise e
    except Exception as e:
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
    """

    if not ispb.isdigit() or len(ispb) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ISPB must be an 8-digit code",
        )

    single_message = True
    if accept and "multipart/json" in accept.lower():
        single_message = False

    try:
        messages, stream_id = await MessageProcessor.fetch_messages(
            ispb=ispb,
            stream_id=interationId,
            db=db,
            max_wait=8,
            single_message=single_message,
        )

        headers = MessageProcessor.format_response_headers(
            ispb=ispb, stream_id=stream_id, has_messages=len(messages) > 0
        )

        if not messages:
            return Response(status_code=status.HTTP_204_NO_CONTENT, headers=headers)

        if single_message:
            return JSONResponse(content=messages[0], headers=headers)
        else:
            return JSONResponse(content=messages, headers=headers)

    except HTTPException as e:
        raise e
    except Exception as e:
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
    """
    if not ispb.isdigit() or len(ispb) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ISPB must be an 8-digit code",
        )

    try:
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

        success = MessageProcessor.mark_messages_delivered(interationId, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to mark messages as delivered",
            )

        return {}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the request: {str(e)}",
        )
