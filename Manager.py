from Database import Database as DB
from enum import Enum
class Manager:
    def __init__(self,db_file):
        self.db = DB(db_file)
        self.username = ""
    
    def login(self,username,password,command_on_success,command_on_wrong_password,command_on_wrong_username):
        username = username.capitalize()
        if self.db.user_exists(username):
            correct_password = self.db.check_user_password(username,password)
            if correct_password:
                self.username=username
                command_on_success()
            else:
                command_on_wrong_password()
        else:
            command_on_wrong_username()
    
    def signup(self,username,password,check_password,command_on_success, command_on_wrong_password,command_on_wrong_username):
        if not self.db.user_exists(username):
            if password==check_password:
                self.db.add_user(username,password)
                self.username=username
                command_on_success()
            else:
                command_on_wrong_password()
        else:
            command_on_wrong_username()

    def process_transaction(self, transaction_type,vault,money_amount,category_name,description,on_insufficent_funds,quantity,unit,date):
        try:
            if transaction_type==TransactionType.WITHDRAW:
                print(f"Withdrew {money_amount} from vault({vault}) for user({self.get_current_username()}), category({category_name}), description:{description},quantity: {quantity}, unit:{unit}, date:{date}")   
                return self.db.withdraw(self.get_current_username(),vault,
                                money_amount,category_name,
                                description,on_insufficent_funds,quantity,
                                unit,date)
            elif transaction_type==TransactionType.DEPOSIT:
                print(f"Deposited {money_amount} into vault({vault}) for user({self.get_current_username()}), category({category_name}), description:{description}, date:{date}")
                return self.db.deposit(self.get_current_username(),vault,
                                money_amount,category_name,
                                description,date)
        except:
            return False
        else:
            return True
    def process_transfer(self,from_vault,to_user,to_vault,amount,on_insufficent_funds,reason):
        try:
            if(float(amount)<0):
                raise IncorrectMoneyAmmount()
            elif(self.get_current_username()==to_user and from_vault==to_vault):
                raise IncorrectVaultTransfer()
            self.db.transfer(self.get_current_username(),from_vault,to_user,to_vault,amount,on_insufficent_funds,reason)
        except ValueError:
            raise InsufficentFunds()
    ##user access functions
    def get_current_username(self):
        '''returns the username of the current user in the current session'''
        return self.username
    def get_current_user_vault_names(self):
        '''retruns a list of vault names that the current user owns'''
        return self.db.get_user_vault_names(self.username)
    def get_current_user_vaults_as_dict(self):
        '''retruns a dictionary of vault names and the balance in each for the current user'''
        return self.db.get_user_vaults(self.username)
    def get_current_user_balance(self):
        return self.db.get_user_balance(self.username)
    
    def get_current_user_vault_balance(self,vault_name):
        vault_dict = self.get_current_user_vaults_as_dict()
        vault_balance = vault_dict[vault_name]
        return vault_balance

class TransactionType(Enum):
    WITHDRAW = "withdraw"
    DEPOSIT = "deposit"

    def __str__(self):
        return self.value

class IncorrectMoneyAmmount(Exception):
    pass
class IncorrectVaultTransfer(Exception):
    pass
class InsufficentFunds(Exception):
    pass

if __name__ == "__main__":
    pass