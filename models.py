from typing import Optional

from sqlmodel import SQLModel, Field

# Database Models
class UserTable(SQLModel, table=True):
    __tablename__ = "user"
    username: str = Field(primary_key=True, index=True)
    password: str
    name: str
    voice_passphrase: str
    mpin: str = Field(default="0000")
    savings_balance: float = 0.0
    checking_balance: float = 0.0
    security_question: Optional[str] = Field(default=None)
    security_answer: Optional[str] = Field(default=None)
    face_image: Optional[str] = Field(default=None)


class TransactionTable(SQLModel, table=True):
    __tablename__ = "transaction"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(foreign_key="user.username", index=True)
    date: str
    type: str  # 'Debit' or 'Credit'
    amount: float
    description: str
    category: str
    channel: str = Field(default="Web")

class FixedDepositTable(SQLModel, table=True):
    __tablename__ = "fixed_deposit"
    id: str = Field(primary_key=True)
    username: str = Field(foreign_key="user.username", index=True)
    principal_amount: float
    interest_rate: str
    tenure: str
    booking_date: str
    maturity_date: str
    status: str
