import os
import sys
from typing import Generator, Dict, Any

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import Base, get_db
from main import app
from models.pix_message import PixMessage, MessageStream
from models.account_holder import AccountHolder

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db) -> Generator:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(test_db) -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
def test_account_holder(db_session) -> Dict[str, Any]:
    """Create a test account holder"""
    account_data = {
        "nome": "Test User",
        "cpfCnpj": "12345678901",
        "ispb": "12345678",
        "agencia": "1234",
        "contaTransacional": "123456",
        "tipoConta": "CACC",
    }

    account = AccountHolder.create_or_update(db_session, account_data)
    db_session.commit()

    return {
        "id": account.id,
        "nome": account.nome,
        "cpfCnpj": account.cpfCnpj,
        "ispb": account.ispb,
        "agencia": account.agencia,
        "contaTransacional": account.contaTransacional,
        "tipoConta": account.tipoConta,
    }


@pytest.fixture(scope="function")
def test_message(db_session, test_account_holder) -> Dict[str, Any]:
    """Create a test PIX message"""
    receiver_data = {
        "nome": "Receiver User",
        "cpfCnpj": "98765432101",
        "ispb": "12345678",
        "agencia": "5678",
        "contaTransacional": "654321",
        "tipoConta": "CACC",
    }

    receiver = AccountHolder.create_or_update(db_session, receiver_data)
    db_session.flush()  # Ensure the receiver has an ID

    import uuid
    import datetime

    message = PixMessage(
        endToEndId=str(uuid.uuid4()),
        valor=100.50,
        payer_id=test_account_holder["id"],
        receiver_id=receiver.id,
        campoLivre="Test payment",
        txId=str(uuid.uuid4())[:30],
        dataHoraPagamento=datetime.datetime.now(datetime.timezone.utc),
        delivered=False,
        stream_id=None,
    )

    db_session.add(message)
    db_session.commit()

    return {
        "id": message.id,
        "endToEndId": message.endToEndId,
        "valor": message.valor,
        "payer_id": message.payer_id,
        "receiver_id": message.receiver_id,
        "campoLivre": message.campoLivre,
        "txId": message.txId,
        "dataHoraPagamento": message.dataHoraPagamento,
        "delivered": message.delivered,
        "stream_id": message.stream_id,
    }


@pytest.fixture(scope="function")
def test_stream(db_session) -> Dict[str, Any]:
    """Create a test message stream"""
    import uuid

    stream_id = str(uuid.uuid4())
    stream = MessageStream(stream_id=stream_id, ispb="12345678", is_active=True)

    db_session.add(stream)
    db_session.commit()

    return {
        "id": stream.id,
        "stream_id": stream.stream_id,
        "ispb": stream.ispb,
        "is_active": stream.is_active,
    }
