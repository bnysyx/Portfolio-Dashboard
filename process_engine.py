import yfinance as yf
import pandas as pd
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import sys


class LoadFinancials:

    def __init__(self, 
                 storage, 
                 source = "", 
                 start = None,
                 end = None
                 ):
                
        self.storage = storage
        self.source = source
    
        if start is None:
            self.start = datetime.now().replace(year=datetime.now().year - 1).strftime("%Y-%m-%d")
        else:
            self.start = start

        self.end = end
        self.local_data = self.storage.load()



    def create_calendar(self):

        start_date = self.local_data["Date"].min() - pd.Timedelta(days=5)
        end_date = pd.Timestamp.today()

        calendar = pd.date_range(start=start_date, end=end_date, freq="D")
        calendar = pd.DataFrame({"Date":calendar})

        calendar["Date"] = pd.to_datetime(calendar["Date"], errors="coerce")

        return start_date,end_date, calendar



    def create_tickers_df(self):                

        # Transform transactional data
        self.local_data.loc[self.local_data["Action"] == "Sell", "Shares"] *= -1
        self.local_data["Position"] = self.local_data.groupby("Ticker")["Shares"].cumsum()

        # Create start & end date for each ticker
        start_date = self.local_data[self.local_data["Position"] > 0].groupby(["Ticker"])["Date"].min()
        end_date = self.local_data[self.local_data["Position"] == 0].groupby(["Ticker"])["Date"].max()

        # Reconnect ticker data with inline start / end date
        self.source = pd.merge(
            start_date, end_date, on="Ticker", how="left", suffixes=("_start","_end")
        )
        self.source.reset_index(inplace=True)
        self.source["Date_end"] = self.source["Date_end"].fillna(pd.Timestamp.today().normalize())

        if self.source.empty:
            print(f"No tickers loaded. List is empty.\n")
        else:
            print(f"Tickers successfully loaded:\n{self.source}\n")
        
        return self.source
    



    def update_tickerdim(self):
        ticker_list = set(self.source["Ticker"])
        
        if self.local_data.empty or "Ticker" not in self.local_data.columns:
            self.local_data = pd.DataFrame(columns=["Ticker","Currency"])
            tickers_df = set()
        else:
            tickers_df = set(self.local_data["Ticker"].unique())

        missing_tickers = ticker_list.difference(tickers_df)

        if missing_tickers:
            print(f"Missing Ticker(s) detected: {missing_tickers}\n")

            df_missing = pd.DataFrame({"Ticker":list(missing_tickers)})
            self.local_data = pd.concat([self.local_data,df_missing], ignore_index=True)
            print("Missing Ticker(s) successfully added.\n")

        missing_ccy_idx = self.local_data["Currency"].isna()
        if missing_ccy_idx.any():
            print(f"Missing Currencies detected.\n")
            
            self.missing_ccy = self.local_data.loc[missing_ccy_idx,"Ticker"].tolist()
            new_ccy = self.load_newccy()
            print(f"Currencies successfully loaded:\n{new_ccy}\n")

            self.local_data.loc[missing_ccy_idx,"Currency"] = self.local_data.loc[missing_ccy_idx,"Ticker"].map(new_ccy)
            
            self.storage.save(self.local_data)




    def load_newccy(self):
        new_ccy = {}

        for t in self.missing_ccy:
            ticker_obj = yf.Ticker(t)
            new_ccy[t] = ticker_obj.info.get("currency","NaN")
            time.sleep(1)
        
        return new_ccy
    



    def create_fxpair(self):
        currency_list = self.local_data["Currency"].dropna().drop_duplicates()
        currency_list = currency_list[currency_list != "EUR"]

        fx_series = "EUR" + currency_list + "=X"
        fx_pair = fx_series.to_frame(name="Ticker")
        fx_pair["Date_start"] = self.source["Date_start"].min()
        fx_pair["Date_end"] = self.source["Date_end"].max()
        print(f"FX Pairs identified in the data set:\n{fx_pair}\n")

        return fx_pair
    



    def precision_dl_worker(self):
        self.new_data = []

        with ThreadPoolExecutor(max_workers=5) as executor: 
            future_to_ticker = {
                executor.submit(self.fetch_yfdata, ticker, start, end): ticker
                for ticker, start, end in zip(
                    self.source["Ticker"],
                    self.source["Date_start"],
                    self.source["Date_end"]
                )
            }

        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                df = future.result()
                if not df.empty:
                    self.new_data.append(df)
                    print(f"Succesfully downloaded {ticker}")
            except Exception as exc:
                print(f"{ticker} generated exception: {exc}")
            
        if self.new_data:
            self.new_data = pd.concat(self.new_data, ignore_index=True)
            if "Date" in self.new_data.columns: self.new_data["Date"] = pd.to_datetime(self.new_data["Date"], errors="coerce")




    def fetch_yfdata(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        # print(ticker,start_date, end_date)
        stock = yf.Ticker(ticker)
        df = stock.history(start = start_date, end = end_date)

        df.reset_index(inplace=True)
        df["Ticker"] = ticker
        
        df["Date"] = df["Date"].dt.date

        return df



    def add_newdata(self):

        if self.new_data.empty:
            print("No new Data found.")
        else:
            all_data = pd.concat([self.local_data,self.new_data], axis = 0, ignore_index=True)
            all_data.dropna(subset=["Close"], inplace=True)
            all_data.drop_duplicates(
                subset=["Date","Ticker"],
                keep="last",
                inplace = True
            )
            all_data = all_data.reset_index(drop=True)
            self.local_data = all_data
        self.storage.save(self.local_data)




    def set_date(self):
        print(self.local_data)
        if not self.local_data.empty:
            last_date = self.local_data["Date"].max() + pd.Timedelta(days=1)
            self.start = last_date.strftime("%Y-%m-%d")
            print(f"Last entry successfully identified as {last_date}.\n")
        else:
            print(f"No historical information identified.\n")
        
        print(f"Data will be updated between\n\t {self.start} \n\t {self.end}\n")       



    def load_newdata(self):
        online_data = yf.download(
            tickers=self.source, 
            start=self.start, 
            end=self.end,
            actions=True,
            auto_adjust=False,
            )
        time.sleep(1)

        self.new_data = online_data.stack(level=1, future_stack=True)
        self.new_data = self.new_data.reset_index()

        print(f"New Data loaded:\n{self.new_data.head()}\n")

    









class PrepareFinancials:

    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.multi_calendar = None
        self.merged_data = None

        self.ticker_year = None
        self.ticker_total = None



    def cumulate_calendar(self):
        self.raw_data["stock_transactions"].loc[self.raw_data["stock_transactions"]["Action"] == "Sell", "Shares"] *= -1
        self.raw_data["stock_transactions"]["Position"] = self.raw_data["stock_transactions"].groupby("Ticker")["Shares"].cumsum()
        print(self.raw_data["stock_transactions"])

        cartesian_calendar = pd.MultiIndex.from_product([self.raw_data["calendar"]["Date"],self.raw_data["tickers_dim"]["Ticker"]],names=["Date","Ticker"])
        

        self.multi_calendar = cartesian_calendar.to_frame(index = False)
        self.multi_calendar = pd.merge(
            left = self.multi_calendar,
            right = self.raw_data["stock_transactions"][["Date","Ticker","Shares","Position"]],
            on = ["Date","Ticker"],
            how = "left"
        )
        self.multi_calendar["Position"] = self.multi_calendar.groupby("Ticker")["Position"].ffill()
        self.multi_calendar.fillna({"Shares":0,"Position":0}, inplace=True)



    def combine_data(self):

        # Stocks & Ticker_dim
        self.merged_data = pd.merge(
            left = self.raw_data["stock_data"], 
            right = self.raw_data["tickers_dim"], 
            on="Ticker", 
            how="left"
        )
        

        # Merged with FX Rates
        self.raw_data["fx_data"]["Currency"] = self.raw_data["fx_data"]["Ticker"].str[3:6]
        self.merged_data = pd.merge(
            left = self.merged_data,
            right = self.raw_data["fx_data"][["Date","Currency","Close"]],
            on=["Date","Currency"],
            how="left",
            suffixes=("_stock","_fx")
        )

        # Merged with Shares & Positions
        self.merged_data = pd.merge(
            left = self.merged_data,
            right = self.multi_calendar,
            on=["Date","Ticker"],
            how="left"
        )


    def clean_data(self):
        # Stock Price to EUR
        self.merged_data["Current Price (EUR)"] = self.merged_data["Close_stock"] / self.merged_data["Close_fx"]
        self.merged_data.loc[self.merged_data["Currency"] == "EUR","Current Price (EUR)"] = self.merged_data["Close_stock"]
        
        # Dividends to EUR
        self.merged_data["Dividends_EUR"] = self.merged_data["Dividends"] / self.merged_data["Close_fx"]
        self.merged_data.loc[self.merged_data["Currency"] == "EUR","Dividends_EUR"] = self.merged_data["Dividends"]

        # Create Year
        self.merged_data["Year"] = self.merged_data["Date"].dt.year

        # Shift Position by t-1
        self.merged_data["Yesterdays Position"] = self.merged_data.groupby("Ticker")["Position"].shift(1)

        # Price Change
        self.merged_data["Price Change"] = self.merged_data.groupby("Ticker")["Current Price (EUR)"].diff()

        # Aggregated P/L
        self.merged_data["Aggregated P/L"] = self.merged_data["Yesterdays Position"] * self.merged_data["Price Change"]

        # Value
        self.merged_data["Position Value"] = self.merged_data["Current Price (EUR)"] * self.merged_data["Position"]
        self.merged_data["Dividend Payout"] = self.merged_data["Dividends_EUR"] * self.merged_data["Position"]

        # Drop irrelevant columns
        self.merged_data = self.merged_data[['Date','Ticker','Currency','Position','Current Price (EUR)','Year','Aggregated P/L','Position Value', 'Dividend Payout']]


    def aggregate_data(self):
        
        self.ticker_year = self.merged_data.groupby(["Ticker","Year"]).agg({
            "Dividend Payout":"sum",
            "Aggregated P/L":"sum",
            "Position Value":"last",
            "Current Price (EUR)":"last"
        })
        self.ticker_total = self.merged_data.groupby(["Ticker"]).agg({
            "Dividend Payout":"sum",
            "Aggregated P/L":"sum",
            "Position Value":"last",
            "Current Price (EUR)":"last"
        })
