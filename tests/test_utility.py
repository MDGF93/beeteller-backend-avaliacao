from fastapi import status
from fastapi.testclient import TestClient


def test_generate_test_messages(client: TestClient, db_session):
    """Test generating test messages"""
    response = client.post("/api/util/msgs/12345678/5")

    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content}")

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["status"] == "success"
    assert data["messages_generated"] == 5
    assert data["receiver_ispb"] == "12345678"
    assert "total_value" in data
    assert "message" in data

    from models.pix_message import PixMessage
    from models.account_holder import AccountHolder

    messages = db_session.query(PixMessage).all()
    assert len(messages) == 5

    account_holders = db_session.query(AccountHolder).all()
    assert len(account_holders) > 0

    for message in messages:
        receiver = (
            db_session.query(AccountHolder)
            .filter(AccountHolder.id == message.receiver_id)
            .first()
        )
        assert receiver.ispb == "12345678"


def test_generate_test_messages_invalid_ispb(client: TestClient, db_session):
    """Test generating test messages with an invalid ISPB"""
    response = client.post("/api/util/msgs/1234/5")

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = response.json()
    assert "detail" in data
    assert "ISPB" in data["detail"]


def test_generate_test_messages_invalid_number(client: TestClient, db_session):
    """Test generating test messages with an invalid number"""
    response = client.post("/api/util/msgs/12345678/101")

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = response.json()
    assert "detail" in data
    assert "Number of messages" in data["detail"]

    response = client.post("/api/util/msgs/12345678/-1")

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = response.json()
    assert "detail" in data
    assert "Number of messages" in data["detail"]


def test_generate_test_messages_verify_content(client: TestClient, db_session):
    """Test the content of generated test messages"""
    response = client.post("/api/util/msgs/12345678/1")

    assert response.status_code == status.HTTP_201_CREATED

    from models.pix_message import PixMessage

    message = db_session.query(PixMessage).first()

    assert message is not None
    assert message.endToEndId is not None
    assert message.valor > 0
    assert message.txId is not None
    assert message.dataHoraPagamento is not None
    assert message.delivered is False
    assert message.stream_id is None

    assert message.pagador is not None
    assert message.recebedor is not None
    assert message.recebedor.ispb == "12345678"
