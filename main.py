from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi import HTTPException, status
from email_service import send_invite_email, login_alert, password_change_alert
import uvicorn, random
import models, schemas, utils


SQLALCHEMY_DATABASE_URL = \
    "<YOUR_DATABASE_URL_HERE>"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = utils.decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload["sub"]  # The user's email


@app.post("/signup")
def sign_up(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        already_exist = db.query(models.User).filter(models.User.email == user_data.email).first()
        if already_exist:
            return {"message": "user already exist"}
        user = models.User(email=user_data.email, password=utils.hash_password(user_data.password))
        db.add(user)
        db.commit()
        db.refresh(user)

        org = models.Organization(name=user_data.organization_name)
        db.add(org)
        db.commit()
        db.refresh(org)

        role = models.Role(name="owner", description="", org_id=org.id)
        db.add(role)
        db.commit()
        db.refresh(role)

        member = models.Member(user_id=user.id, org_id=org.id, role_id=role.id)
        db.add(member)
        db.commit()
        send_invite_email(user_data.email, "")
        # db.rollback()
        return {"message": "User signed up successfully"}
    except:
        db.rollback()
        db.commit()
        return {"Message": "Error occurred try after sometime"}


@app.post("/signin")
def sign_in(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not utils.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = utils.create_access_token(data={"sub": user.email})
    login_alert(form_data.username)
    return {"access_token": access_token, "token_type": "bearer"}


@app.delete("/member/{member_id}")
def delete_member(member_id: int, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if member:
        user = db.query(models.User).filter(models.User.id == member.user_id).first()
        if user:
            db.delete(member)
            db.delete(user)
            db.commit()
        return {"message": "Member deleted successfully"}
    else:
        return {"message": "No user found"}


@app.post("/invite_member")
def invite_member(member_data: schemas.MemberCreate, current_user: str = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    try:
        ex_user = db.query(models.User).filter(models.User.email == member_data.email).first()
        if ex_user:
            return {"message": "user already exist"}
        user = models.User(email=member_data.email, password=utils.hash_password(str(random.randint(10000000, 99999999))))
        db.add(user)
        db.commit()
        db.refresh(user)

        al_user = db.query(models.User).filter(models.User.email == current_user).first()
        mem = db.query(models.Member).filter(models.Member.user_id == al_user.id).first()
        role = models.Role(name="Level1", description="", org_id=mem.org_id)
        db.add(role)
        db.commit()
        db.refresh(role)

        member = models.Member(user_id=user.id, org_id=al_user.id, role_id=role.id)
        db.add(member)
        db.commit()
        send_invite_email(member_data.email, "")
        db.rollback()
        return {"message": "Member successfully added"}
    except:
        db.rollback()
        db.commit()
        return {"Message": "Error occurred try after sometime"}


@app.post("/reset_password")
def reset_password(data: schemas.ResetPassword, db: Session = Depends(get_db)):
    ex_user = db.query(models.User).filter(models.User.email == data.email).first()
    if not ex_user:
        return {"message": "Invalid user email"}
    if utils.verify_password(data.password, ex_user.password):
        return {"message": "New password can not be same as old password"}
    ex_user.password = utils.hash_password(data.password)
    password_change_alert(data.email)
    db.commit()
    return {"message": "Password updated successfully"}


@app.get("/role_based_users")
def role_based_users(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = db.query(models.Role).all()
    new_dict = {}
    for item in roles:
        if item.name not in new_dict.keys():
            new_dict[item.name] = db.query(models.Member).filter(models.Member.role_id == item.id).count()
    return new_dict


@app.get("/org_based_users")
def org_based_users(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(models.Organization).all()
    new_dict = {}
    for item in org:
        if item.name not in new_dict.keys():
            new_dict[item.name] = db.query(models.Member).filter(models.Member.org_id == item.id).count()
    return new_dict


@app.get("/get_users_role_org")
def get_users_role_org(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(models.Organization.name, models.Role.name, models.Member).filter(models.Organization.id == models.Role.org_id).filter(models.Member.role_id == models.Role.id).all()
    new_l = {}
    for org, role, member in query:
        if org in new_l.keys():
            new_l[org][role] += 1
        else:
            new_l[org] = {}
            new_l[org][role] = 1
        # print(org, role, member.id)
    return new_l


if __name__ == "__main__":
    uvicorn.run(app)
