import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/banking")

print(f"Connecting to: {database_url.split('@')[-1] if '@' in database_url else database_url}")

try:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        print("[1/3] Testing PostgreSQL connection... OK")
        
        print("[2/3] Checking if 'vector' extension can be enabled...")
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print("[2/3] Extension 'vector' enabled successfully! (pgvector is available!)")
            
            print("[3/3] Testing vector column creation...")
            conn.execute(text("CREATE TEMPORARY TABLE _test_vec (id serial primary key, embedding vector(3));"))
            conn.execute(text("INSERT INTO _test_vec (embedding) VALUES ('[0.1, 0.2, 0.3]');"))
            result = conn.execute(text("SELECT id, embedding FROM _test_vec;")).fetchone()
            conn.commit()
            print(f"[3/3] Vector query test passed: {result}")
            print("\nRESULT: PGVECTOR_SUPPORTED")
        except Exception as ext_err:
            print(f"\n[!] pgvector extension error: {ext_err}")
            print("\nRESULT: PGVECTOR_NOT_SUPPORTED")
except Exception as conn_err:
    print(f"\n[!] Database connection error: {conn_err}")
    print("\nRESULT: DB_CONNECTION_FAILED")
