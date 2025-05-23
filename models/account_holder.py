import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from validate_docbr import CPF, CNPJ

from database import Base


class AccountHolder(Base):
    __tablename__ = "account_holders"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    cpfCnpj = Column(String, nullable=False, index=True)
    ispb = Column(String, nullable=False, index=True)
    agencia = Column(String, nullable=False)
    contaTransacional = Column(String, nullable=False)
    tipoConta = Column(String, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    payer_messages = relationship(
        "PixMessage", foreign_keys="PixMessage.payer_id", back_populates="pagador"
    )
    receiver_messages = relationship(
        "PixMessage", foreign_keys="PixMessage.receiver_id", back_populates="recebedor"
    )

    def __repr__(self):
        return f"<AccountHolder(nome='{self.nome}', cpfCnpj='{self.cpfCnpj}', ispb='{self.ispb}')>"

    @classmethod
    def get_by_cpfCnpj_and_ispb(cls, session, cpfCnpj, ispb):
        """Find an account holder by CPF/CNPJ and ISPB"""
        return (
            session.query(cls).filter(cls.cpfCnpj == cpfCnpj, cls.ispb == ispb).first()
        )

    @classmethod
    def create_or_update(cls, session, account_data):
        """Create a new account holder or update if exists"""

        cpfCnpj = account_data["cpfCnpj"]
        if len(cpfCnpj) == 11:
            if not CPF().validate(cpfCnpj):
                raise ValueError("Invalid CPF")
        elif len(cpfCnpj) == 14:
            if not CNPJ().validate(cpfCnpj):
                raise ValueError("Invalid CNPJ")
        else:
            raise ValueError("cpfCnpj must be either 11 (CPF) or 14 (CNPJ) digits")

        account = cls.get_by_cpfCnpj_and_ispb(
            session, account_data["cpfCnpj"], account_data["ispb"]
        )

        if not account:
            account = cls(**account_data)
            session.add(account)
        else:
            for key, value in account_data.items():
                setattr(account, key, value)

        return account

    def is_valid_cpf(cpf: str) -> bool:
        return CPF().validate(cpf)

    def is_valid_cnpj(cnpj: str) -> bool:
        return CNPJ().validate(cnpj)
