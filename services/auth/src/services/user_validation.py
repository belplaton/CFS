from email_validator import validate_email, EmailNotValidError
import re


class UserValidator:
    ALLOWED_CHARS = r'^[a-zA-Z0-9_.-]+$'
    RESERVED_NAMES = {
        'admin', 'administrator', 'root', 'system',
        'support', 'help', 'info', 'security',
        'moderator', 'mod', 'user', 'guest',
        'anonymous', 'api', 'service', 'bot'
    }

    def __init__(self, username: str, email: str, password: str):
        self.__username = username
        self.__password = password
        self.__email = email

    def is_too_simple_password(self, password):
        sybs = set()
        for syb in password:
            sybs.add(syb)
        if len(sybs) <= 5:
            return False
        else:
            return True

    @staticmethod
    def valid_password(password: str) -> bool:
        if len(password) < 8 or len(password) > 16:
            return False
        for syb in password:
            if ord(syb) > 126 or ord(syb) < 32:
                return False
        if password == UserValidator.__username:
            return False
        if password == UserValidator.__email:
            return False
        if UserValidator.is_too_simple_password(password) == False:
            return False
        return True

    @staticmethod
    def valid_email(email: str) -> bool:
        try:
            valid = validate_email(email)
            normalized_email = valid.normalized
            return True
        except EmailNotValidError as e:
            print(f'Ошибка : {e}')
            return False

    @staticmethod
    def valid_username(username: str) -> bool:
        if len(username) < 6 or len(username) > 30:
            return False
        for syb in username:
            if not re.match(UserValidator.ALLOWED_CHARS, UserValidator.__username):
                return False
        flag = -1
        for syb in username:
            if syb not in '0123456789':
                flag = 1
        if flag == -1:
            return False
        for reversed_name in UserValidator.RESERVED_NAMES:
            if reversed_name == username:
                return False
        return True





