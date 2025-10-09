from Database import Database as DB

class Manager:
    def __init__(self,db_file):
        self.db = DB(db_file)
        self.username = None
    
    def login(self,username,password):
        if self.db.user_exists(username):
            correct_password = self.db.check_user_password(username,password)
            if correct_password:
                return True
            else:
                raise InvalidPasswordError(f"Incorrect Password: {password}")
        else:
            raise InvalidUsernameError(f"Username '{username}' Doesnt Exist")
    
    def signup(self,username,password,check_password):
        if not self.db.user_exists(username):
            if password==check_password:
                self.db.add_user(username,password)
                return True
            else:
                raise InvalidPasswordError("Passwords must match")
        else:
            raise InvalidUsernameError(f"Username '{username}' Already Exists")

class InvalidUsernameError(Exception):
    '''When the username is wrong'''
    pass

class InvalidPasswordError(Exception):
    '''When the username is wrong'''
    pass

if __name__ == "__main__":
    pass