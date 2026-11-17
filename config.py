import os, json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError



class GetEnvironment:
    def __init__(self):
        load_dotenv()

        self.db_url = None
        self.table_config = {}
        self.yf_table_config = {}

        self.init_db()
        self.init_tables()
        #self.test_connection()


    def init_db(self):
        db_user = os.environ.get("DB_USER")
        db_password = os.environ.get("DB_PASSWORD")
        db_host = os.environ.get("DB_HOST")
        db_port = os.environ.get("DB_PORT")
        db_name = os.environ.get("DB_NAME")

        self.db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        self.engine = create_engine(self.db_url)

    def init_tables(self):
        table_config = os.environ.get("TABLE_CONFIG")
        self.table_config = json.loads(table_config)

        for table, config in self.table_config.items():
            if config.get("yf_data_table",None):
                self.yf_table_config[table]=config



    def test_connection(self):
        print("Attempting to connect to PostgreSQL...")
        try:
            # The 'with' block ensures the connection is closed automatically
            with self.engine.connect() as connection:
                # Wrap the raw SQL in the text() function
                query = text("SELECT 1;")
                
                # Execute the query and fetch the result
                result = connection.execute(query).scalar()
                
                if result == 1:
                    print(f"✅ Success! Connection to PostgreSQL is active.\n")
        
        except UnicodeDecodeError as e:
        
            print("\n🚨 CRASH PREVENTED: Translating hidden Windows error...")
            
            # e contains unreadable byte string from Windows, manually decoded using German Windows encoding (cp1252)
            translated_error = e.object.decode('cp1252', errors='replace')
            print(f"--- REAL DATABASE ERROR ---\n{translated_error}")            
        
        except OperationalError as e:
            print("❌ Connection failed. Please check your .env file and ensure PostgreSQL is running.")
            print(f"Error Details: {e}")



