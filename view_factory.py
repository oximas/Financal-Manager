import customtkinter as ctk
from config import UIConfig

class ViewFactory:
    """
    Factory class for creating view controllers.
    Hanldes view instantiation and window resizing
    """

    @staticmethod
    def _resize_window(master:ctk.CTk):
        """Resize window to fit content"""
        master.update_idletasks()
        width = master.winfo_reqwidth()
        height = master.winfo_reqheight()
        margin = UIConfig.WINDOW_MARGIN

        new_width = max(width + margin, UIConfig.DEFAULT_WIDTH)
        new_height = max(height + margin, UIConfig.DEFAULT_HEIGHT)
        
        master.geometry(f"{new_width}x{new_height}")
    
    @staticmethod
    def show_main_menu(master: ctk.CTk, manager, database):
        """Show the main menu"""
        from view_controllers import MainMenuController
        controller = MainMenuController(master, manager, database)
        controller.show()
        ViewFactory._resize_window(master)
    
    @staticmethod
    def show_login(master: ctk.CTk, manager, database):
        """Show the login screen"""
        from view_controllers import LoginController
        controller = LoginController(master, manager, database)
        controller.show()
        ViewFactory._resize_window(master)

    @staticmethod
    def show_signup(master: ctk.CTk, manager, database):
        """Show the signup screen"""
        from view_controllers import SignupController
        controller = SignupController(master, manager, database)
        controller.show()
        ViewFactory._resize_window(master)

    @staticmethod
    def show_user_menu(master: ctk.CTk, manager, database):
        """Show the user menu"""
        from view_controllers import UserMenuController
        controller = UserMenuController(master, manager, database)
        controller.show()
        ViewFactory._resize_window(master)
    
    @staticmethod
    def show_transaction(master: ctk.CTk, manager, database, transaction_type: str):
        """Show the transaction screen (deposit/withdraw)"""
        from view_controllers import TransactionController
        controller = TransactionController(master, manager, database, transaction_type)
        controller.show()
        ViewFactory._resize_window(master)
    @staticmethod
    def show_transfer(master: ctk.CTk, manager, database):
        """Show the transfer screen"""
        from view_controllers import TransferController
        controller = TransferController(master, manager, database)
        controller.show()
        ViewFactory._resize_window(master)
    
    @staticmethod
    def show_summary(master: ctk.CTk, manager, database):
        """Show the summary screen"""
        from view_controllers import SummaryController
        controller = SummaryController(master, manager, database)
        controller.show()
        ViewFactory._resize_window(master)
    
    @staticmethod
    def show_account(master: ctk.CTk, manager, database):
        """Show the account settings screen"""
        from view_controllers import AccountController
        controller = AccountController(master, manager, database)
        controller.show()
        ViewFactory._resize_window(master)