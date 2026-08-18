import os
from dotenv import load_dotenv
from sqlmodel import create_engine, Session, select
from models import UserTable, TransactionTable

load_dotenv()
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/banking")
engine = create_engine(POSTGRES_URL)

with Session(engine) as session:
    users = session.exec(select(UserTable)).all()
    print("=== USERS ===")
    for u in users:
        print(f"Username: {u.username}, Name: {u.name}, Savings: {u.savings_balance}, Checking: {u.checking_balance}")
        
    txs = session.exec(select(TransactionTable).order_by(TransactionTable.id.desc()).limit(10)).all()
    print("\n=== RECENT TRANSACTIONS ===")
    for t in txs:
        print(f"ID: {t.id}, User: {t.username}, Date: {t.date}, Type: {t.type}, Amount: {t.amount}, Desc: {t.description}")
