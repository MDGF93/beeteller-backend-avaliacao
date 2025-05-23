import datetime
import uuid
import uuid


def test_account_holder_model(db_session):
    """Test the AccountHolder model"""
    from models.account_holder import AccountHolder

    # Create a new account holder
    account_data = {
        "nome": "Test User",
        "cpfCnpj": "12345678901",
        "ispb": "12345678",
        "agencia": "1234",
        "contaTransacional": "123456",
        "tipoConta": "CACC",
    }

    account = AccountHolder(**account_data)
    db_session.add(account)
    db_session.commit()

    # Retrieve the account holder
    retrieved = (
        db_session.query(AccountHolder)
        .filter(AccountHolder.cpfCnpj == "12345678901")
        .first()
    )

    # Verify attributes
    assert retrieved.nome == "Test User"
    assert retrieved.cpfCnpj == "12345678901"
    assert retrieved.ispb == "12345678"
    assert retrieved.agencia == "1234"
    assert retrieved.contaTransacional == "123456"
    assert retrieved.tipoConta == "CACC"

    # Test create_or_update method
    updated_data = account_data.copy()
    updated_data["nome"] = "Updated User"

    updated = AccountHolder.create_or_update(db_session, updated_data)
    db_session.commit()

    # Verify update
    assert updated.id == account.id  # Same record
    assert updated.nome == "Updated User"  # Updated name

    # Test creating a new account
    new_data = account_data.copy()
    new_data["cpfCnpj"] = "98765432101"

    new_account = AccountHolder.create_or_update(db_session, new_data)
    db_session.commit()

    # Verify new account
    assert new_account.id != account.id  # Different record
    assert new_account.cpfCnpj == "98765432101"


def test_pix_message_model(db_session):
    """Test the PixMessage model"""
    from models.pix_message import PixMessage
    from models.account_holder import AccountHolder

    # Create account holders
    payer = AccountHolder(
        nome="Payer",
        cpfCnpj="12345678901",
        ispb="12345678",
        agencia="1234",
        contaTransacional="123456",
        tipoConta="CACC",
    )

    receiver = AccountHolder(
        nome="Receiver",
        cpfCnpj="98765432101",
        ispb="87654321",
        agencia="5678",
        contaTransacional="654321",
        tipoConta="SVGS",
    )

    db_session.add_all([payer, receiver])
    db_session.commit()

    end_to_end_id = str(uuid.uuid4())
    message = PixMessage(
        endToEndId=end_to_end_id,
        valor=100.50,
        payer_id=payer.id,
        receiver_id=receiver.id,
        campoLivre="Test payment",
        txId="TX" + str(uuid.uuid4())[:28],
        dataHoraPagamento=datetime.datetime.now(datetime.timezone.utc),
        delivered=False,
    )

    db_session.add(message)
    db_session.commit()

    retrieved = PixMessage.get_by_endToEndId(db_session, end_to_end_id)

    assert retrieved.endToEndId == end_to_end_id
    assert retrieved.valor == 100.50
    assert retrieved.payer_id == payer.id
    assert retrieved.receiver_id == receiver.id
    assert retrieved.campoLivre == "Test payment"
    assert retrieved.delivered is False
    assert retrieved.stream_id is None

    assert retrieved.pagador.nome == "Payer"
    assert retrieved.recebedor.nome == "Receiver"

    message_dict = retrieved.to_dict()
    assert message_dict["endToEndId"] == end_to_end_id
    assert message_dict["valor"] == 100.50
    assert message_dict["pagador"]["nome"] == "Payer"
    assert message_dict["recebedor"]["nome"] == "Receiver"
    assert message_dict["campoLivre"] == "Test payment"
    assert "dataHoraPagamento" in message_dict


def test_message_stream_model(db_session):
    """Test the MessageStream model"""
    from models.pix_message import MessageStream

    stream_id = str(uuid.uuid4())
    stream = MessageStream(stream_id=stream_id, ispb="12345678", is_active=True)

    db_session.add(stream)
    db_session.commit()

    retrieved = MessageStream.get_by_stream_id(db_session, stream_id)

    assert retrieved.stream_id == stream_id
    assert retrieved.ispb == "12345678"
    assert retrieved.is_active is True

    old_last_active = retrieved.last_active
    retrieved.update_activity(db_session)
    db_session.commit()

    db_session.refresh(retrieved)
    assert retrieved.last_active > old_last_active

    new_stream_id = str(uuid.uuid4())
    new_stream = MessageStream.create_stream(db_session, "87654321", new_stream_id)
    db_session.commit()

    assert new_stream.stream_id == new_stream_id
    assert new_stream.ispb == "87654321"
    assert new_stream.is_active is True

    # Test stream limit (6 per ISPB)
    for i in range(5):  # Already created one above
        MessageStream.create_stream(db_session, "12345678", str(uuid.uuid4()))
    db_session.commit()

    # This should be the 7th stream for ISPB 12,345,678, should return None
    seventh_stream = MessageStream.create_stream(
        db_session, "12345678", str(uuid.uuid4())
    )
    assert seventh_stream is None

    # Test deactivate_inactive_streams
    retrieved.last_active = datetime.datetime.now(
        datetime.timezone.utc
    ) - datetime.timedelta(hours=1)
    db_session.add(retrieved)
    db_session.commit()

    # Deactivate streams inactive for 30 minutes
    deactivated = MessageStream.deactivate_inactive_streams(
        db_session, timeout_minutes=30
    )
    db_session.commit()

    assert deactivated >= 1

    # Verify the stream is now inactive
    updated = MessageStream.get_by_stream_id(db_session, stream_id)
    assert updated.is_active is False
