import datetime

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create an in-memory SQLite database for testing
engine = create_engine("sqlite:///:memory:")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Override the Base in database.py
import database

database.Base = Base

# Import models after overriding Base
from models import AccountHolder, PixMessage, MessageStream

# Create tables
Base.metadata.create_all(bind=engine)


def test_models():
    # Create a session
    db = SessionLocal()

    try:
        # Create account holders
        payer = AccountHolder(
            nome="João Silva",
            cpfCnpj="19419610020",
            ispb="12345678",
            agencia="1234",
            contaTransacional="12345678",
            tipoConta="CACC",
        )

        receiver = AccountHolder(
            nome="Maria Souza",
            cpfCnpj="98765432101",
            ispb="87654321",
            agencia="4321",
            contaTransacional="87654321",
            tipoConta="CACC",
        )

        db.add_all([payer, receiver])
        db.commit()

        # Create a message stream
        stream = MessageStream(stream_id="stream123", ispb="12345678", is_active=True)

        db.add(stream)
        db.commit()

        # Create a PIX message
        message = PixMessage(
            endToEndId="E2E123456789",
            valor=100.50,
            payer_id=payer.id,
            receiver_id=receiver.id,
            campoLivre="Payment for services",
            txId="TX123456789",
            dataHoraPagamento=datetime.datetime(2023, 5, 23, 10, 30, 0),
            stream_id=stream.stream_id,
        )

        db.add(message)
        db.commit()

        # Test retrieving the message
        retrieved_message = (
            db.query(PixMessage).filter_by(endToEndId="E2E123456789").first()
        )

        print("Model test successful!")
        print(f"Message: {retrieved_message}")
        print(f"Payer: {retrieved_message.pagador.nome}")
        print(f"Receiver: {retrieved_message.recebedor.nome}")

        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_models()
    print(f"Test {'passed' if success else 'failed'}")
