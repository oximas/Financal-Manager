from gui import FinanceManagerGUI

"""Entry point for the Finance Manager application"""


def main():
    """Main entry point"""
    app = FinanceManagerGUI()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nApplication closed by user")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise


if __name__ == "__main__":
    main()