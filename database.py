import datetime
from sqlmodel import SQLModel, create_engine, Session, select
from models import UserTable, TransactionTable, FixedDepositTable

# Database Setup
mysql_url = "mysql+pymysql://root:root@localhost:3306/banking"
engine = create_engine(mysql_url)

# Helper to run migrations & seed data
def init_db():
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # Check if database has any seeded users
        user_check = session.exec(select(UserTable)).first()
        if not user_check:
            # Seed 5 Dummy Users
            alice = UserTable(
                username="alice",
                password="password123",
                name="Alice Smith",
                voice_passphrase="my voice is my secure password",
                savings_balance=5420.50,
                checking_balance=1250.75
            )
            bob = UserTable(
                username="bob",
                password="password123",
                name="Bob Jones",
                voice_passphrase="access code red",
                savings_balance=3200.00,
                checking_balance=850.00
            )
            charlie = UserTable(
                username="charlie",
                password="password123",
                name="Charlie Brown",
                voice_passphrase="let me into my account",
                savings_balance=1500.00,
                checking_balance=400.00
            )
            david = UserTable(
                username="david",
                password="password123",
                name="David Miller",
                voice_passphrase="shield walls up",
                savings_balance=8900.00,
                checking_balance=3100.00
            )
            emma = UserTable(
                username="emma",
                password="password123",
                name="Emma Watson",
                voice_passphrase="open the finova vault",
                savings_balance=12400.00,
                checking_balance=4500.00
            )
            
            session.add_all([alice, bob, charlie, david, emma])
            session.commit()
            
            # Seed Transactions
            now = datetime.datetime.now()
            tx1 = TransactionTable(username="alice", date=(now - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), type="Debit", amount=12.50, description="Starbucks Coffee", category="Food/Drinks")
            tx2 = TransactionTable(username="alice", date=(now - datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), type="Credit", amount=2500.00, description="Monthly Salary", category="Income")
            tx3 = TransactionTable(username="alice", date=(now - datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M"), type="Debit", amount=85.20, description="Shell Gas Station", category="Transport")
            
            tx4 = TransactionTable(username="bob", date=(now - datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M"), type="Debit", amount=45.00, description="Trader Joe's", category="Groceries")
            tx5 = TransactionTable(username="charlie", date=(now - datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), type="Credit", amount=150.00, description="Refund from Amazon", category="Shopping")
            tx6 = TransactionTable(username="david", date=(now - datetime.timedelta(days=4)).strftime("%Y-%m-%d %H:%M"), type="Debit", amount=120.00, description="Gym Membership", category="Health")
            tx7 = TransactionTable(username="emma", date=(now - datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M"), type="Credit", amount=4500.00, description="Dividend Payout", category="Investments")
            
            session.add_all([tx1, tx2, tx3, tx4, tx5, tx6, tx7])
            
            # Seed Fixed Deposits
            fd1 = FixedDepositTable(id="FD-9842", username="alice", principal_amount=10000.00, interest_rate="6.5% p.a.", tenure="24 months", booking_date="2025-10-15", maturity_date="2027-10-15", status="Active")
            fd2 = FixedDepositTable(id="FD-1120", username="bob", principal_amount=5000.00, interest_rate="5.8% p.a.", tenure="12 months", booking_date="2026-01-10", maturity_date="2027-01-10", status="Active")
            fd3 = FixedDepositTable(id="FD-3040", username="david", principal_amount=25000.00, interest_rate="7.0% p.a.", tenure="36 months", booking_date="2024-05-12", maturity_date="2027-05-12", status="Active")
            
            session.add_all([fd1, fd2, fd3])
            session.commit()

# Session Dependency injection helper for endpoints
def get_db_session():
    with Session(engine) as session:
        yield session
