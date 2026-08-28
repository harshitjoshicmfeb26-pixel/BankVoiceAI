from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from database import get_db_session
from models import UserTable, TransactionTable
from utils import get_user_current_state, get_current_user

router = APIRouter()

@router.get("/api/transactions")
async def transactions_endpoint(
    username: str,
    limit: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    session: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    username = username.lower().strip()
    if username != current_user:
        raise HTTPException(status_code=403, detail="Forbidden: You can only view transactions for your own account.")
    try:
        query = select(TransactionTable).where(TransactionTable.username == username).order_by(TransactionTable.date.desc())
        
        if start_date:
            query = query.where(TransactionTable.date >= start_date)
        if end_date:
            if len(end_date) == 10:
                query = query.where(TransactionTable.date <= f"{end_date} 23:59")
            else:
                query = query.where(TransactionTable.date <= end_date)
                
        if limit:
            query = query.limit(limit)
            
        txs = session.exec(query).all()
        return [
            {
                "id": tx.id,
                "date": tx.date,
                "type": tx.type,
                "amount": tx.amount,
                "description": tx.description,
                "category": tx.category
            }
            for tx in txs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/state")
async def state_endpoint(
    username: str, 
    session: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    username = username.lower().strip()
    if username != current_user:
        raise HTTPException(status_code=403, detail="Forbidden: You can only view account state for your own account.")
    try:
        return get_user_current_state(username, session)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/users")
async def get_users_endpoint(
    exclude: Optional[str] = None, 
    session: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    users = session.exec(select(UserTable)).all()
    return [
        {"username": u.username, "name": u.name}
        for u in users
        if not exclude or u.username != exclude.lower().strip()
    ]
