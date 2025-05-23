import asyncio
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.pix_message import PixMessage, MessageStream


class MessageProcessor:
    """
    Utility class for processing PIX messages
    """

    @staticmethod
    async def acquire_stream(
        ispb: str, db: Session
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Acquire a stream for a specific ISPB, enforcing the limit of 6 active streams per ISPB
        """

        active_streams_count = MessageStream.get_active_streams_count_by_ispb(db, ispb)

        if active_streams_count >= 6:
            return (
                False,
                None,
                "Maximum number of active streams (6) reached for this ISPB",
            )

        stream_id = str(uuid.uuid4())

        stream = MessageStream.create_stream(db, ispb, stream_id)
        if not stream:
            return False, None, "Failed to create stream"

        db.commit()
        return True, stream_id, None

    @staticmethod
    async def fetch_messages(
        ispb: str,
        stream_id: Optional[str],
        db: Session,
        max_wait: int = 8,
        single_message: bool = True,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Fetch messages for a specific ISPB and stream with long polling support.
        Returns a list of messages and the stream_id for continuation.
        """

        async def get_or_create_stream_id(
            ispb: str, stream_id: Optional[str], db: Session
        ) -> str:
            """
            Returns a valid stream_id, creating a new stream if needed.
            """
            if not stream_id:
                success, new_stream_id, error = await MessageProcessor.acquire_stream(
                    ispb, db
                )
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=error
                    )
                return new_stream_id

            stream = MessageStream.get_by_stream_id(db, stream_id)
            if not stream:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Stream {stream_id} not found",
                )
            if not stream.is_active:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail=f"Stream {stream_id} is no longer active",
                )
            stream.update_activity(db)
            db.commit()
            return stream_id

        stream_id = await get_or_create_stream_id(ispb, stream_id, db)

        start_time = time.time()
        messages: List[Dict[str, Any]] = []
        message_limit = 1 if single_message else 10

        while time.time() - start_time < max_wait:
            query = (
                db.query(PixMessage)
                .filter(
                    PixMessage.stream_id == stream_id, PixMessage.delivered == False
                )
                .order_by(PixMessage.dataHoraPagamento)
                .limit(message_limit)
            )
            messages_db = query.all()

            if messages_db:
                messages = [msg.to_dict() for msg in messages_db]
                for msg in messages_db:
                    msg.stream_id = stream_id
                db.commit()
                break

            await asyncio.sleep(0.5)

        return messages, stream_id

    @staticmethod
    def mark_messages_delivered(stream_id: str, db: Session) -> bool:
        """
        Mark all messages in a stream as delivered
        """
        try:
            messages = (
                db.query(PixMessage)
                .filter(
                    PixMessage.stream_id == stream_id, PixMessage.delivered == False
                )
                .all()
            )

            for msg in messages:
                msg.delivered = True

            stream = MessageStream.get_by_stream_id(db, stream_id)
            if stream:
                stream.is_active = False

            db.commit()
            return True
        except Exception as _:
            db.rollback()
            return False

    @staticmethod
    def format_response_headers(
        ispb: str, stream_id: str, has_messages: bool
    ) -> Dict[str, str]:
        """
        Format response headers according to the API specification
        """
        headers = {"Pull-Next": f"/api/pix/{ispb}/stream/{stream_id}"}

        return headers
