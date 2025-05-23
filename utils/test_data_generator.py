import datetime
import random
import uuid
from faker import Faker
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from models.account_holder import AccountHolder
from models.pix_message import PixMessage

faker_br = Faker("pt_BR")

BANK_NAMES = [
    "Banco do Brasil",
    "Itaú",
    "Bradesco",
    "Santander",
    "Caixa",
    "Nubank",
    "Inter",
    "BTG Pactual",
]
ACCOUNT_TYPES = ["CACC", "SVGS"]
TRANSACTION_DESCRIPTIONS = [
    "Pagamento de serviço",
    "Transferência",
    "Compra online",
    "Pagamento de fatura",
    "Depósito",
    "Pagamento de boleto",
    "Transferência PIX",
    "Pagamento de aluguel",
    "Pagamento de salário",
    "Reembolso",
]


def generate_random_cpf() -> str:
    """Generate a valid random CPF using Faker"""
    return faker_br.cpf().replace(".", "").replace("-", "")


def generate_random_cnpj() -> str:
    """Generate a valid random CNPJ using Faker"""
    return faker_br.cnpj().replace(".", "").replace("/", "").replace("-", "")


def generate_random_ispb() -> str:
    """Generate a random ISPB (Brazilian payment system identification)"""
    return "".join([str(random.randint(0, 9)) for _ in range(8)])


def generate_random_account() -> str:
    """Generate a random account number"""
    return "".join([str(random.randint(0, 9)) for _ in range(random.randint(5, 10))])


def generate_random_agency() -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(4)])


def generate_random_account_holder(ispb: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate random account holder data
    """
    is_person = random.random() < 0.7

    if is_person:
        nome = f"{faker_br.first_name()} {faker_br.last_name()}"
        cpfCnpj = generate_random_cpf()
    else:
        nome = f"{random.choice(BANK_NAMES)} {random.choice(['Ltda', 'S.A.', 'Inc.'])}"
        cpfCnpj = generate_random_cnpj()

    return {
        "nome": nome,
        "cpfCnpj": cpfCnpj,
        "ispb": ispb if ispb else generate_random_ispb(),
        "agencia": generate_random_agency(),
        "contaTransacional": generate_random_account(),
        "tipoConta": random.choice(ACCOUNT_TYPES),
    }


def generate_random_pix_message(receiver_ispb: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a random PIX message for testing
    """
    pagador_data = generate_random_account_holder()
    recebedor_data = generate_random_account_holder(receiver_ispb)

    valor = round(random.uniform(1.0, 10000.0), 2)
    end_to_end_id = str(uuid.uuid4())
    tx_id = str(uuid.uuid4())[:30]

    days_ago = random.randint(0, 30)
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    seconds_ago = random.randint(0, 59)

    payment_time = datetime.datetime.now() - datetime.timedelta(
        days=days_ago, hours=hours_ago, minutes=minutes_ago, seconds=seconds_ago
    )

    campo_livre = (
        random.choice(TRANSACTION_DESCRIPTIONS) if random.random() < 0.8 else None
    )

    return {
        "endToEndId": end_to_end_id,
        "valor": valor,
        "pagador": pagador_data,
        "recebedor": recebedor_data,
        "campoLivre": campo_livre,
        "txId": tx_id,
        "dataHoraPagamento": payment_time,
    }


def create_test_messages(ispb: str, count: int, db: Session) -> List[Dict[str, Any]]:
    """
    Create multiple test PIX messages and save them to the database
    """
    created_messages = []

    for _ in range(count):
        message_data = generate_random_pix_message(receiver_ispb=ispb)

        pagador = AccountHolder.create_or_update(db, message_data["pagador"])
        db.flush()

        recebedor = AccountHolder.create_or_update(db, message_data["recebedor"])
        db.flush()

        pix_message = PixMessage(
            endToEndId=message_data["endToEndId"],
            valor=message_data["valor"],
            payer_id=pagador.id,
            receiver_id=recebedor.id,
            campoLivre=message_data["campoLivre"],
            txId=message_data["txId"],
            dataHoraPagamento=message_data["dataHoraPagamento"],
            delivered=False,
        )

        db.add(pix_message)
        created_messages.append(message_data)

    db.commit()

    return created_messages
