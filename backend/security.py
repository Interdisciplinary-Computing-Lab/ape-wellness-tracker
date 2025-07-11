from flask_security import Security, SQLAlchemyUserDatastore
from backend.extensions import db
from backend.models.entry import User, Role

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security()