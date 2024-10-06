from Database import Database as DB
class User:
    def __init__(self,db,username):
        self.db = DB() #make "db" later
        self.username = username
        self.vaults = self.db.get_user_vaults(username)
    def deposit(self,vault_name,amount,category_name,description,quantity=None,unit=None):
        self.add_to_vault(self.username,vault_name,amount)

        user_id = self.get_user_id(self.username)
        vault_id = self.get_vault_id(vault_name)
        category_id = self.get_category_id(category_name)
        self.db.add_transaction(user_id,vault_id,"Deposit",amount,category_id,description,quantity,unit)
        return True
    def withdraw(self,vault_name,amount,category_name,description,quantity=None,unit=None):
        self.db.remove_from_vault(self.username,vault_name,amount)

        user_id = self.get_user_id(self.username)
        vault_id = self.get_vault_id(vault_name)
        category_id = self.get_category_id(category_name)
        self.db.add_transaction(user_id,vault_id,"Withdraw",-amount,category_id,description,quantity,unit)
        return True
    def transfer(self,from_vault,to_vault,amount):
        self.withdraw(from_vault,amount,"Transaction","Transfer")
        self.deposit(to_vault,amount,"Transaction","Transfer")
        return True
    def loan(self,from_name,to_name,amount):
        if not self.db.user_exists(from_name):
            self.db.add_user(from_name)
            self.db.add_to_vault(from_user,"Main",amount)
        if not self.db.user_exists(to_name):
            self.db.add_user(to_name)
        from_user = User(from_name)
        to_user = User(to_name)
        from_user.withdraw("Main",amount,"Transaction","Loan")
        to_user.deposit("Main",amount,"Transaction","Loan")

        
        




    
    
       