import datetime
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session, select
from models import UserTable, TransactionTable, FixedDepositTable

# Load environment variables
load_dotenv()

# Database Setup
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/banking")
engine = create_engine(database_url)

# Helper to run migrations & seed data
def init_db():
    SQLModel.metadata.create_all(engine)
    
    # Check if 'mpin' column exists in 'user' table, and add it if missing (migration)
    from sqlalchemy import text, inspect
    inspector = inspect(engine)
    try:
        columns = [col['name'] for col in inspector.get_columns('user')]
        user_table_name = '"user"' if engine.dialect.name == 'postgresql' else 'user'
        if 'mpin' not in columns:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE {user_table_name} ADD COLUMN mpin VARCHAR(255) DEFAULT '0000'"))
                conn.commit()
        if 'security_question' not in columns:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE {user_table_name} ADD COLUMN security_question VARCHAR(255) DEFAULT NULL"))
                conn.commit()
        if 'security_answer' not in columns:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE {user_table_name} ADD COLUMN security_answer VARCHAR(255) DEFAULT NULL"))
                conn.commit()
        if 'face_image' not in columns:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE {user_table_name} ADD COLUMN face_image TEXT DEFAULT NULL"))
                conn.commit()

                
        # Check if 'channel' column exists in 'transaction' table, and add it if missing (migration)
        tx_columns = [col['name'] for col in inspector.get_columns('transaction')]
        if 'channel' not in tx_columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE transaction ADD COLUMN channel VARCHAR(255) DEFAULT 'Web'"))
                conn.commit()
                
        # Synchronize PostgreSQL auto-increment sequence for transactions
        if engine.dialect.name == "postgresql":
            with engine.connect() as conn:
                conn.execute(text("SELECT setval(pg_get_serial_sequence('transaction', 'id'), COALESCE((SELECT MAX(id) FROM transaction), 1))"))
                conn.commit()
    except Exception as e:
        print(f"Migration check/alter warning: {e}")
        
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
                mpin="1111",
                savings_balance=5420.50,
                checking_balance=1250.75,
                security_question="What is your favorite pet's name?",
                security_answer="Spot"
            )
            bob = UserTable(
                username="bob",
                password="password123",
                name="Bob Jones",
                voice_passphrase="access code red",
                mpin="2222",
                savings_balance=3200.00,
                checking_balance=850.00,
                security_question="In which city were you born?",
                security_answer="New York"
            )
            charlie = UserTable(
                username="charlie",
                password="password123",
                name="Charlie Brown",
                voice_passphrase="let me into my account",
                mpin="3333",
                savings_balance=1500.00,
                checking_balance=400.00,
                security_question="What is your favorite book?",
                security_answer="Harry Potter"
            )
            david = UserTable(
                username="david",
                password="password123",
                name="David Miller",
                voice_passphrase="shield walls up",
                mpin="4444",
                savings_balance=8900.00,
                checking_balance=3100.00,
                security_question="What was the name of your first school?",
                security_answer="Lincoln"
            )
            emma = UserTable(
                username="emma",
                password="password123",
                name="Emma Watson",
                voice_passphrase="open the nidhivani vault",
                mpin="5555",
                savings_balance=12400.00,
                checking_balance=4500.00,
                security_question="What is your mother's maiden name?",
                security_answer="Smith"
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
            session.commit()
            
            # Seed Fixed Deposits
            fd1 = FixedDepositTable(id="FD-9842", username="alice", principal_amount=10000.00, interest_rate="6.5% p.a.", tenure="24 months", booking_date="2025-10-15", maturity_date="2027-10-15", status="Active")
            fd2 = FixedDepositTable(id="FD-1120", username="bob", principal_amount=5000.00, interest_rate="5.8% p.a.", tenure="12 months", booking_date="2026-01-10", maturity_date="2027-01-10", status="Active")
            fd3 = FixedDepositTable(id="FD-3040", username="david", principal_amount=25000.00, interest_rate="7.0% p.a.", tenure="36 months", booking_date="2024-05-12", maturity_date="2027-05-12", status="Active")
            
            session.add_all([fd1, fd2, fd3])
            session.commit()
        else:
            # Ensure seeded users have their proper MPINs if they were migrated with default
            updates = {
                "alice": "1111",
                "bob": "2222",
                "charlie": "3333",
                "david": "4444",
                "emma": "5555"
            }
            has_updates = False
            for username, default_mpin in updates.items():
                user = session.exec(select(UserTable).where(UserTable.username == username)).first()
                if user and (user.mpin is None or user.mpin == "0000"):
                    user.mpin = default_mpin
                    session.add(user)
                    has_updates = True
            if has_updates:
                session.commit()

# Session Dependency injection helper for endpoints
def get_db_session():
    with Session(engine) as session:
        yield session
