from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ISPBPathParam(BaseModel):
    """Path parameter model for ISPB validation"""

    ispb: str = Field(
        ...,
        description="8-digit code identifying a payment institution",
        examples=["12345678"],
        min_length=8,
        max_length=8,
    )

    @classmethod
    @field_validator("ispb")
    def validate_ispb(cls, v):
        if not v.isdigit() or len(v) != 8:
            raise ValueError("ISPB must be an 8-digit code")
        return v

    model_config = {"json_schema_extra": {"example": {"ispb": "32074986"}}}


class StreamPathParams(ISPBPathParam):
    """Path parameters for stream operations"""

    interationId: str = Field(
        ...,
        description="Unique identifier for the message stream",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )


class GenerateMessagesPathParams(ISPBPathParam):
    """Path parameters for message generation"""

    number: int = Field(
        ...,
        description="Number of messages to generate (1-100)",
        examples=[10],
        gt=0,
        le=100,
    )


# Response Models
class PixMessageBase(BaseModel):
    """Base model for PIX message data"""

    endToEndId: str = Field(
        ...,
        description="Unique identifier for the PIX transaction",
        examples=["E12345678202205121456789ABCDEF"],
    )
    valor: float = Field(
        ..., description="Transaction amount in BRL", examples=[123.45]
    )
    horario: str = Field(
        ...,
        description="Transaction timestamp in ISO format",
        examples=["2023-05-12T14:56:00Z"],
    )
    tipo: str = Field(
        ..., description="Transaction type (PIX, DEVOLUCAO, etc)", examples=["PIX"]
    )
    chave: Optional[str] = Field(
        None,
        description="PIX key used for the transaction",
        examples=["email@example.com"],
    )
    infoPagador: Optional[str] = Field(
        None,
        description="Additional information provided by the payer",
        examples=["Payment for services"],
    )


class PixMessageResponse(PixMessageBase):
    """Complete PIX message model for responses"""

    ispbRemetente: str = Field(
        ..., description="ISPB of the sending institution", examples=["87654321"]
    )
    ispbDestinatario: str = Field(
        ..., description="ISPB of the receiving institution", examples=["12345678"]
    )
    status: str = Field(
        ..., description="Message processing status", examples=["PENDING"]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "endToEndId": "E12345678202205121456789ABCDEF",
                "valor": 123.45,
                "horario": "2023-05-12T14:56:00Z",
                "tipo": "PIX",
                "chave": "email@example.com",
                "infoPagador": "Payment for services",
                "ispbRemetente": "87654321",
                "ispbDestinatario": "12345678",
                "status": "PENDING",
            }
        }
    }


class StreamResponseHeaders(BaseModel):
    """Model for stream response headers"""

    X_Stream_Id: str = Field(
        ...,
        description="Unique identifier for the message stream",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    X_Has_More: bool = Field(
        ..., description="Indicates if more messages are available", examples=[True]
    )


class GenerateMessagesResponse(BaseModel):
    """Response model for test message generation"""

    status: str = Field(..., description="Operation status", examples=["success"])
    messages_generated: int = Field(
        ..., description="Number of messages generated", examples=[10]
    )
    receiver_ispb: str = Field(
        ..., description="ISPB of the receiving institution", examples=["12345678"]
    )
    total_value: float = Field(
        ..., description="Total value of all generated messages", examples=[1234.56]
    )
    message: str = Field(
        ...,
        description="Operation summary message",
        examples=["Successfully generated 10 test messages for ISPB 12345678"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "messages_generated": 10,
                "receiver_ispb": "12345678",
                "total_value": 1234.56,
                "message": "Successfully generated 10 test messages for ISPB 12345678",
            }
        }
    }


class TerminateStreamResponse(BaseModel):
    model_config = {"json_schema_extra": {"example": {}}}


# Examples for documentation
EXAMPLES = {
    "single_message": {
        "summary": "Single PIX message",
        "description": "Example of a single PIX message response",
        "value": {
            "endToEndId": "E12345678202205121456789ABCDEF",
            "valor": 123.45,
            "horario": "2023-05-12T14:56:00Z",
            "tipo": "PIX",
            "chave": "email@example.com",
            "infoPagador": "Payment for services",
            "ispbRemetente": "87654321",
            "ispbDestinatario": "12345678",
            "status": "PENDING",
        },
    },
    "multiple_messages": {
        "summary": "Multiple PIX messages",
        "description": "Example of multiple PIX messages response",
        "value": [
            {
                "endToEndId": "E12345678202205121456789ABCDEF",
                "valor": 123.45,
                "horario": "2023-05-12T14:56:00Z",
                "tipo": "PIX",
                "chave": "email@example.com",
                "infoPagador": "Payment for services",
                "ispbRemetente": "87654321",
                "ispbDestinatario": "12345678",
                "status": "PENDING",
            },
            {
                "endToEndId": "E87654321202205121456789FEDCBA",
                "valor": 543.21,
                "horario": "2023-05-12T14:57:00Z",
                "tipo": "PIX",
                "chave": "+5511999999999",
                "infoPagador": "Monthly rent",
                "ispbRemetente": "87654321",
                "ispbDestinatario": "12345678",
                "status": "PENDING",
            },
        ],
    },
    "generate_messages": {
        "summary": "Generate test messages",
        "description": "Example response after generating test messages",
        "value": {
            "status": "success",
            "messages_generated": 10,
            "receiver_ispb": "12345678",
            "total_value": 1234.56,
            "message": "Successfully generated 10 test messages for ISPB 12345678",
        },
    },
    "terminate_stream": {
        "summary": "Terminate stream",
        "description": "Empty response after successfully terminating a stream",
        "value": {},
    },
}
