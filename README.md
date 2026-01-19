# Personal Financial Manager

A desktop application for tracking personal finances with support for multiple vaults, transactions, and detailed reporting.

## Features

- **User Management**: Secure login and signup system
- **Vaults**: Organize money into categories like "Food," "Savings," "Fun," etc.
- **Transaction Types**:
  1. **Deposit**: Add money to a vault
  2. **Withdraw**: Remove money from a vault with category tracking
  3. **Transfer**: Move money between vaults or send to other users
  4. **Loan**: *(Coming soon)* Track money owed to/from others

- **Detailed Tracking**: Every transaction includes category, description, date, and optional quantity/unit
- **Export**: Export transaction history to Excel
- **Summary Dashboard**: View total balance and vault breakdowns

## Project Structure
```
finance_manager/
├── config/          # Configuration settings
├── core/            # Business logic layer
├── data/            # Database access layer
├── ui/              # User interface components
├── utils/           # Utility modules
├── tests/           # Test suite
└── main.py          # Application entry point
```

## Installation

### Prerequisites
- Python 3.8 or higher

### Setup

1. **Clone the repository**
```bash
   git clone <your-repo-url>
   cd finance_manager
```

2. **Create virtual environment**
```bash
   python -m venv venv
```

3. **Activate virtual environment**
   - Windows:
```bash
     venv\Scripts\activate
```
   - macOS/Linux:
```bash
     source venv/bin/activate
```

4. **Install dependencies**
```bash
   pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

### First Time Setup
1. Click "Sign Up" to create a new account
2. Enter a username and password
3. A default "Main" vault will be created automatically

### Keyboard Shortcuts
- **Enter**: Submit forms
- **Ctrl+Backspace**: Go back
- **Escape**: Cancel/Go back

## Development

### Running Tests
```bash
pytest tests/
```

### Project Architecture

The application follows a layered architecture:

- **Data Layer** (`data/`): SQLite database operations
- **Business Logic** (`core/`): Transaction processing, validation
- **Presentation Layer** (`ui/`): GUI components and controllers
- **Configuration** (`config/`): Application settings
- **Utilities** (`utils/`): Reusable helpers (key bindings, etc.)

### Adding New Features

1. Add business logic to `core/manager.py`
2. Create UI controller in `ui/controllers.py`
3. Register view in `ui/factory.py`
4. Add tests in `tests/`

## Database Schema

- **users**: User accounts
- **vaults**: Money containers per user
- **transactions**: All financial movements
- **categories**: Transaction categories
- **units**: Measurement units for items

## Future Enhancements

- [ ] Loan tracking system
- [ ] Budget planning and forecasts
- [ ] Data visualization (charts/graphs)
- [ ] Recurring transactions
- [ ] Mobile companion app
- [ ] Cloud sync
- [ ] Cloud sync

## License

*(Add your license here)*

## Contributing

*(Add contribution guidelines if needed)*