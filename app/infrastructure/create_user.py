from app.infrastructure.database import SessionLocal
from app.domain.entities import User
from app.infrastructure.security import get_password_hash

db = SessionLocal()

user_kusnadi = db.query(User).filter(User.username == "kusnadi").first()
if not user_kusnadi:
    new_user_1 = User(
        username="kusnadi",
        password_hash=get_password_hash("password123"),
        full_name="Kusnadi",
        role="Kasi Pelayanan"
    )
    db.add(new_user_1)
    print("User Kusnadi ditambahkan.")
else:
    print("User Kusnadi sudah ada.")

user_udin = db.query(User).filter(User.username == "udin").first()
if not user_udin:
    new_user_2 = User(
        username="udin",
        password_hash=get_password_hash("password123"),
        full_name="Udin",
        role="Kaur Perencanaan"
    )
    db.add(new_user_2)
    print("User Udin ditambahkan.")
else:
    print("User Udin sudah ada.")

db.commit()
print("Proses selesai!")