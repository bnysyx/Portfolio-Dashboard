from storage_engine import get_storage
from config import GetEnvironment

from process_engine import LoadFinancials
from process_engine import PrepareFinancials

import sys

class Argus:
    
    def __init__(self):

        env = GetEnvironment() 

        self.db_path = env.db_url

        self.table_config = env.table_config
        self.yf_table_config = env.yf_table_config


    def init_local_data(self):
        
        """
        Load transactions and create base calendar. 
        Create ticker-timeframe for loading necessary datapoints based on first / last observation transactions
        """

        # Load transactional information
        trades_storage = get_storage(tb_name = "stock_transactions", tb_dict=self.table_config, db_path=self.db_path)       
        trades = LoadFinancials(storage=trades_storage)

        # Create base calendar
        self.start_date, self.end_date, calendar = trades.create_calendar()
        tickers_df = trades.create_tickers_df()

        # Store new base calendar
        calendar_storage = get_storage(tb_name = "calendar", tb_dict=self.table_config, db_path=self.db_path)
        calendar_storage.save(calendar)

        # Update Ticker_dim and create FX Pair
        tickers_storage = get_storage(tb_name = "tickers_dim", tb_dict=self.table_config, db_path=self.db_path)
        tickers = LoadFinancials(storage=tickers_storage,source=tickers_df)

        tickers.update_tickerdim()
        fx_pair = tickers.create_fxpair()
        
        # Relationship Dictionary
        self.relation_dict = {"tickers_df":tickers_df,
                "fx_pair":fx_pair} 


    def update_local_data(self):
        
        # Update yfinance data
        for table_name, table_configs in self.yf_table_config.items():
            print(table_name)
            table_storage = get_storage(tb_name=table_name, tb_dict=self.yf_table_config, db_path=self.db_path)

            dependent = table_configs["dependent"]
            dependent_data = self.relation_dict.get(dependent)

            
            print(f"File:\n\t{table_name}\n\nList:\n\t{dependent_data}\n")
            updater = LoadFinancials(storage = table_storage, source = dependent_data, start = self.start_date, end = self.end_date)

            updater.set_date()
            updater.precision_dl_worker()
            updater.add_newdata()


    def transform_data(self):

        table_collector = {}
        for table_name, content in self.table_config.items():
            
            storage = get_storage(tb_name = table_name, tb_dict=self.table_config, db_path=self.db_path)
            temp_df = LoadFinancials(storage=storage).local_data
            table_collector[table_name] = temp_df
                    

        editor = PrepareFinancials(table_collector)
        editor.cumulate_calendar()
        editor.combine_data() 
        editor.clean_data()
        editor.aggregate_data()


        output_storage = get_storage(tb_name = "output", tb_dict=self.table_config, db_path=self.db_path)
        output_storage.save(editor.ticker_year)
        print({"ticker_year":editor.ticker_year, "ticker_total":editor.ticker_total, "all_data":editor.merged_data})
        return {"ticker_year":editor.ticker_year, "ticker_total":editor.ticker_total, "all_data":editor.merged_data}

# - Start
if __name__ == "__main__":
    
    print(f"---------- Program Start ----------\n")
    
    argus = Argus()
    argus.init_local_data()
    argus.update_local_data()
    argus.transform_data()


    print("---------- Program End ----------")