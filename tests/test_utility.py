from fastapi import status
from fastapi.testclient import TestClient

def test_generate_test_messages(client: TestClient, db_session):
    """Test generating test messages"""
    # Make request to generate 5 test messages
    response = client.post("/api/util/msgs/12345678/5")
    
    # Print response for debugging
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content}")
    
    # Should return 201 Created
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verify response content
    data = response.json()
    assert data["status"] == "success"
    assert data["messages_generated"] == 5
    assert data["receiver_ispb"] == "12345678"
    assert "total_value" in data
    assert "message" in data
    
    # Verify messages were created in the database
    from models.pix_message import PixMessage
    from models.account_holder import AccountHolder
    
    # Check for messages
    messages = db_session.query(PixMessage).all()
    assert len(messages) == 5
    
    # Check for account holders
    account_holders = db_session.query(AccountHolder).all()
    assert len(account_holders) > 0  # Should have created at least some account holders
    
    # Verify all messages have the correct receiver ISPB
    for message in messages:
        receiver = db_session.query(AccountHolder).filter(AccountHolder.id == message.receiver_id).first()
        assert receiver.ispb == "12345678"

def test_generate_test_messages_invalid_ispb(client: TestClient, db_session):
    """Test generating test messages with an invalid ISPB"""
    # Make request with an invalid ISPB
    response = client.post("/api/util/msgs/1234/5")
    
    # Should return 400 Bad Request
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Verify error message
    data = response.json()
    assert "detail" in data
    assert "ISPB" in data["detail"]

def test_generate_test_messages_invalid_number(client: TestClient, db_session):
    """Test generating test messages with an invalid number"""
    # Make request with an invalid number (too many)
    response = client.post("/api/util/msgs/12345678/101")
    
    # Should return 400 Bad Request
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Verify error message
    data = response.json()
    assert "detail" in data
    assert "Number of messages" in data["detail"]
    
    # Make request with an invalid number (negative)
    response = client.post("/api/util/msgs/12345678/-1")
    
    # Should return 400 Bad Request
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Verify error message
    data = response.json()
    assert "detail" in data
    assert "Number of messages" in data["detail"]

def test_generate_test_messages_verify_content(client: TestClient, db_session):
    """Test the content of generated test messages"""
    # Make request to generate a single test message
    response = client.post("/api/util/msgs/12345678/1")
    
    # Should return 201 Created
    assert response.status_code == status.HTTP_201_CREATED
    
    # Get the message from the database
    from models.pix_message import PixMessage
    message = db_session.query(PixMessage).first()
    
    # Verify message structure
    assert message is not None
    assert message.endToEndId is not None
    assert message.valor > 0
    assert message.txId is not None
    assert message.dataHoraPagamento is not None
    assert message.delivered is False
    assert message.stream_id is None
    
    # Verify relationships
    assert message.pagador is not None
    assert message.recebedor is not None
    assert message.recebedor.ispb == "12345678"
