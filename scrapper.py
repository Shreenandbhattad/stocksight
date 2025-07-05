import yfinance as yf
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import datetime
import sys

# Check for required packages
try:
    import yfinance as yf
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    print("Required packages not found. Please run 'pip install -r requirements.txt' first.")
    print("Required packages: yfinance, gspread, oauth2client")
    sys.exit(1)

# Configuration
SERVICE_ACCOUNT_FILE = 'service_account.json'  # Google Sheets API credentials
SPREADSHEET_ID = '1-vSxLQ1qcSEzmMXQkaRgDL17rv3cvM8fwlX8nARo2mw'  # Your Google Sheets ID
GOOGLE_SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def authenticate_google_sheets():
    """Authenticate with Google Sheets API using service account credentials."""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, GOOGLE_SHEETS_SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Error authenticating with Google Sheets: {e}")
        return None

def fetch_market_data(symbol):
    """Fetch market data (OHLCV) from Yahoo Finance."""
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y")
        return hist.reset_index().to_json(orient='records')
    except Exception as e:
        print(f"Error fetching market data for {symbol}: {e}")
        return None

def fetch_financial_statements(symbol):
    """Fetch financial statements from Yahoo Finance."""
    try:
        stock = yf.Ticker(symbol)
        income_stmt = stock.income_stmt.to_json(orient='index')
        balance_sheet = stock.balance_sheet.to_json(orient='index')
        cash_flow = stock.cashflow.to_json(orient='index')
        return {
            'income_stmt': income_stmt,
            'balance_sheet': balance_sheet,
            'cash_flow': cash_flow
        }
    except Exception as e:
        print(f"Error fetching financial statements for {symbol}: {e}")
        return None

def initialize_sheet(client, spreadsheet_id, sheet_name):
    """Initialize a new sheet if it doesn't exist."""
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        try:
            return spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            return spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)
    except Exception as e:
        print(f"Error initializing sheet {sheet_name}: {e}")
        return None

def update_google_sheet(client, spreadsheet_id, symbol, market_data, financial_data):
    """Update Google Sheets with fetched data."""
    try:
        # Initialize sheets
        raw_data_sheet = initialize_sheet(client, spreadsheet_id, f"{symbol}_Raw_Data")
        analysis_sheet = initialize_sheet(client, spreadsheet_id, f"{symbol}_Analysis")
        output_sheet = initialize_sheet(client, spreadsheet_id, f"{symbol}_Output")

        if not all([raw_data_sheet, analysis_sheet, output_sheet]):
            print("Error creating sheets")
            return False

        # Clear existing data
        raw_data_sheet.clear()
        analysis_sheet.clear()
        output_sheet.clear()

        # Update raw data sheet
        raw_data_sheet.update('A1', 'Symbol')
        raw_data_sheet.update('B1', symbol)
        raw_data_sheet.update('A2', 'Market Data')
        raw_data_sheet.update('B2', market_data)
        raw_data_sheet.update('A3', 'Financial Data')
        raw_data_sheet.update('B3', json.dumps(financial_data))

        print(f"Successfully updated Google Sheets with data for {symbol}")
        return True
    except Exception as e:
        print(f"Error updating Google Sheets for {symbol}: {e}")
        return False

def main():
    """Main function to scrape data and update Google Sheets."""
    # Authentication
    client = authenticate_google_sheets()
    if not client:
        return

    # List of symbols to process (example with RELIANCE.BO)
    symbols = ["RELIANCE.BO", "TCS.BO", "HDFCBANK.BO"]  # Add more BSE symbols as needed

    for symbol in symbols:
        print(f"Processing {symbol}...")

        # Fetch data
        market_data = fetch_market_data(symbol)
        financial_data = fetch_financial_statements(symbol)

        if market_data and financial_data:
            success = update_google_sheet(client, SPREADSHEET_ID, symbol, market_data, financial_data)
            if not success:
                print(f"Failed to update Google Sheets for {symbol}")
        else:
            print(f"Failed to fetch data for {symbol}")

if __name__ == "__main__":
    main()
