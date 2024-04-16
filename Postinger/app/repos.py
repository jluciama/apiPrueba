from app import db, bcrypt
from app.models import User
from pydantic import ValidationError


class UserRepository():

    async def findOne(self, username):
        try:
            user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one()
        except:
            user = None
        return user


    async def checkPassword(self, user, password):
        validPassword = bcrypt.check_password_hash(self.password_hash, password)
        return validPassword
    

    async def isActive(self, user):
        return user.status == "active"
    
    async def isDeactivated(self, user):
        return user.status == "deactivated"
    
    async def isDeleted(self, user):
        return user.status == "deleted"
    

    async def reactivate(self, user):
        try:
            user.status = "active"
            for post in user.posts:
                post.status = 'active'
            db.session.commit()
            reactivateOk = True
        except ValidationError as e:
            reactivateOk = False
        return reactivateOk
    

    async def deactivate(self, user):
        try:
            user.status = "deactivated"
            for post in user.posts:
                post.status = 'deactivated'
            db.session.commit()
            deactivateOk = True
        except ValidationError as e:
            deactivateOk = False
        return deactivateOk
    

    async def delete(self, user):
        try:
            user.status = "deleted"
            for post in user.posts:
                post.status = 'deleted'
            db.session.commit()
            deleteOk = True
        except ValidationError as e:
            deleteOk = False
        return deleteOk
    

    async def checkEmail(self, user, email):
        validEmail = user.email_address == email
        return validEmail
    

    async def setPassword(self, user, password):
        try:
            user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            
            db.session.commit()
            passwordChangeOk = True
        except:
            passwordChangeOk = False
        return passwordChangeOk

class PostRepository():
    pass



user_repo = UserRepository()
post_repo = PostRepository()


# Aquí hacer lógica de raise exceptions si hay errores