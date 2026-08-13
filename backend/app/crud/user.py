from sqlalchemy.orm import Session
from database.models import User

def get_user_by_account(
    db:Session,
    account:str
):
    return db.query(
        User
    ).filter(
        User.account==account
    ).first()


def get_user_by_id(
    db: Session,
    user_id: int
):
    return db.query(
        User
    ).filter(
        User.id == user_id
    ).first()
    
def create_user(
    db,
    username,
    account,
    password_hash
):
    user=User(
        username=username,
        account=account,
        password_hash=password_hash
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

