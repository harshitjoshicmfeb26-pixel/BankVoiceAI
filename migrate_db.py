import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session, select
from models import UserTable, TransactionTable, FixedDepositTable

# Load environment variables
load_dotenv()

# Database Connections
MYSQL_URL = "mysql+pymysql://root:root@localhost:3306/banking"
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/banking")

print("Initializing database engines...")
mysql_engine = create_engine(MYSQL_URL)
postgres_engine = create_engine(POSTGRES_URL)

def migrate():
    print("Connecting to MySQL (Source) and PostgreSQL (Target)...")
    
    # 1. Fetch data from MySQL
    with Session(mysql_engine) as mysql_session:
        print("Reading users from MySQL...")
        users = mysql_session.exec(select(UserTable)).all()
        
        print("Reading transactions from MySQL...")
        transactions = mysql_session.exec(select(TransactionTable)).all()
        
        print("Reading fixed deposits from MySQL...")
        fds = mysql_session.exec(select(FixedDepositTable)).all()
        
        print(f"Found in MySQL: {len(users)} users, {len(transactions)} transactions, {len(fds)} fixed deposits.")

    # 2. Write data to PostgreSQL
    with Session(postgres_engine) as pg_session:
        print("\nMigrating Users to PostgreSQL...")
        for user in users:
            # Create a new transient SQLModel instance to avoid bound session conflicts
            new_user = UserTable(
                username=user.username,
                password=user.password,
                name=user.name,
                voice_passphrase=user.voice_passphrase,
                mpin=user.mpin,
                savings_balance=user.savings_balance,
                checking_balance=user.checking_balance,
                security_question=user.security_question,
                security_answer=user.security_answer
            )
            pg_session.merge(new_user)
        pg_session.commit()
        print("Users migration complete.")

        print("\nMigrating Transactions to PostgreSQL...")
        for tx in transactions:
            new_tx = TransactionTable(
                id=tx.id,
                username=tx.username,
                date=tx.date,
                type=tx.type,
                amount=tx.amount,
                description=tx.description,
                category=tx.category,
                channel=tx.channel
            )
            pg_session.merge(new_tx)
        pg_session.commit()
        print("Transactions migration complete.")

        print("\nMigrating Fixed Deposits to PostgreSQL...")
        for fd in fds:
            new_fd = FixedDepositTable(
                id=fd.id,
                username=fd.username,
                principal_amount=fd.principal_amount,
                interest_rate=fd.interest_rate,
                tenure=fd.tenure,
                booking_date=fd.booking_date,
                maturity_date=fd.maturity_date,
                status=fd.status
            )
            pg_session.merge(new_fd)
        pg_session.commit()
        print("Fixed Deposits migration complete.")

    print("\nSUCCESS: All data successfully migrated from MySQL to PostgreSQL!")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\nERROR during migration: {e}")
