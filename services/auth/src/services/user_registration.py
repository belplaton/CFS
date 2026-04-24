import bcrypt
import user_validation
import psycopg2
from user_validation import UserValidator
class UserRegistration(UserValidator):
    def __init__(self, username : str,  email : str, password : str):
        if UserValidator.check_validation(username, email, password):
            self.__username = username
            self.__password = password
            self.__email = email
            self.__hash_password = self.hash_password(password)

    @staticmethod
    def check_validation(self, username : str, email : str, password : str) -> bool:
        try:
            if UserValidator.valid_password(password) == False:
                raise("Invalid password")
            elif UserValidator.valid_email(email) == False:
                raise("Invalid email")
            elif UserValidator.valid_username(username) == False:
                raise("Invalid username")
            return True
        except Exception as e:
            print(e)
            return False

    @staticmethod
    def hash_password(self, password):
        sault = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password, sault)

    @staticmethod
    def put_new_user(self, username : str, email : str, password : str):
        with psycopg2.connect(database="postgres", user="postgres", password="", host="localhost") as conn:
            with conn.cursor() as cursor:
                sql = 'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)'
                data = (username, email, self.hash_password(password))
                cursor.execute(sql, data)







