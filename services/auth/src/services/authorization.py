from user_registration import UserRegistration
from user_validation import UserValidator
import jwt
from datetime import datetime, timedelta, timezone

class UserAuthorization(UserRegistration):
    secret_key = 'some_key'
    def __init__(self, username : str, email : str, password : str):
        if UserRegistration.valid_email(email) and UserRegistration.valid_username(username) and UserRegistration.valid_password(password):
            self.__username = username
            self.__email = email
            self.__password = password
            self.__hash_password = UserRegistration.hash_password(password)
    def create_token(self, user_id : int, role : str) -> str:
        pay_load = {
            'sub': user_id,
            'role': role,
            'iat': datetime.now(timezone.utc).isoformat(),
            'exp': datetime.now(timezone.utc) + timedelta(minutes=30)
        }
        token = jwt.encode(pay_load, self.secret_key, algorithms=['HS256'])
        return token
    def verify_token(self, token : str):
        try:
            pay_load = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return pay_load
        except jwt.InvalidTokenError as e:
            print(e)
        except jwt.ExpiredSignatureError as e:
            print(e)

obj = UserAuthorization('test1', 'test1@mail.ru', 'test1pw')
token = obj.create_token('1', 'user')
print(obj.verify_token(token))
