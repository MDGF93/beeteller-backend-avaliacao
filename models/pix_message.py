import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Float,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class PixMessage(Base):
    __tablename__ = "pix_messages"

    id = Column(Integer, primary_key=True, index=True)
    endToEndId = Column(String, unique=True, index=True, nullable=False)
    valor = Column(Float, nullable=False)
    payer_id = Column(Integer, ForeignKey("account_holders.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("account_holders.id"), nullable=False)
    campoLivre = Column(Text, nullable=True)
    txId = Column(String, index=True, nullable=False)
    dataHoraPagamento = Column(DateTime, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    delivered = Column(Boolean, default=False)
    stream_id = Column(
        String, ForeignKey("message_streams.stream_id"), nullable=True, index=True
    )

    pagador = relationship(
        "AccountHolder",
        foreign_keys="[PixMessage.payer_id]",
        back_populates="payer_messages",
    )
    recebedor = relationship(
        "AccountHolder",
        foreign_keys="[PixMessage.receiver_id]",
        back_populates="receiver_messages",
    )
    stream = relationship("MessageStream", back_populates="messages")

    __table_args__ = (
        UniqueConstraint("endToEndId", "stream_id", name="uix_message_stream"),
    )

    def __repr__(self):
        return f"<PixMessage(endToEndId='{self.endToEndId}', valor={self.valor}, txId='{self.txId}')>"

    @classmethod
    def get_by_endToEndId(cls, session, endToEndId):
        """Find a message by its endToEndId"""
        return session.query(cls).filter(cls.endToEndId == endToEndId).first()

    @classmethod
    def get_undelivered_messages(cls, session, stream_id, limit=100):
        """Get undelivered messages for a specific stream"""
        return (
            session.query(cls)
            .filter(cls.stream_id == stream_id, cls.delivered == False)
            .order_by(cls.dataHoraPagamento)
            .limit(limit)
            .all()
        )

    def to_dict(self):
        """Convert the message to a dictionary format matching the API spec"""
        return {
            "endToEndId": self.endToEndId,
            "valor": self.valor,
            "pagador": {
                "nome": self.pagador.nome,
                "cpfCnpj": self.pagador.cpfCnpj,
                "ispb": self.pagador.ispb,
                "agencia": self.pagador.agencia,
                "contaTransacional": self.pagador.contaTransacional,
                "tipoConta": self.pagador.tipoConta,
            },
            "recebedor": {
                "nome": self.recebedor.nome,
                "cpfCnpj": self.recebedor.cpfCnpj,
                "ispb": self.recebedor.ispb,
                "agencia": self.recebedor.agencia,
                "contaTransacional": self.recebedor.contaTransacional,
                "tipoConta": self.recebedor.tipoConta,
            },
            "campoLivre": self.campoLivre,
            "txId": self.txId,
            "dataHoraPagamento": self.dataHoraPagamento.isoformat(),
        }


class MessageStream(Base):
    __tablename__ = "message_streams"

    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String, unique=True, index=True, nullable=False)
    ispb = Column(String, index=True, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    last_active = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    is_active = Column(Boolean, default=True)

    messages = relationship("PixMessage", back_populates="stream")
    messages = relationship("PixMessage", back_populates="stream")

    __table_args__ = (UniqueConstraint("stream_id", name="uix_stream_id"),)

    def __repr__(self):
        return f"<MessageStream(stream_id='{self.stream_id}', ispb='{self.ispb}', is_active={self.is_active})>"

    def update_activity(self, session):
        """Update the last_active timestamp"""
        self.last_active = datetime.datetime.now(datetime.timezone.utc)
        session.add(self)

    @classmethod
    def get_active_streams_count_by_ispb(cls, session, ispb):
        """Count active streams for a specific ISPB"""
        return (
            session.query(func.count(cls.id))
            .filter(cls.ispb == ispb, cls.is_active == True)
            .scalar()
        )

    @classmethod
    def get_by_stream_id(cls, session, stream_id):
        """Find a stream by its ID"""
        return session.query(cls).filter(cls.stream_id == stream_id).first()

    @classmethod
    def create_stream(cls, session, ispb, stream_id):
        """Create a new message stream if ISPB limit not exceeded"""
        active_streams = cls.get_active_streams_count_by_ispb(session, ispb)
        if active_streams >= 6:
            return None

        stream = cls(stream_id=stream_id, ispb=ispb)
        session.add(stream)
        return stream

    @classmethod
    def deactivate_inactive_streams(cls, session, timeout_minutes=30):
        """Deactivate streams that have been inactive for a specified period"""
        timeout = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            minutes=timeout_minutes
        )
        inactive_streams = (
            session.query(cls)
            .filter(cls.is_active == True, cls.last_active < timeout)
            .all()
        )

        for stream in inactive_streams:
            stream.is_active = False
            session.add(stream)

        return len(inactive_streams)
