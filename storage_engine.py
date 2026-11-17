from abc import ABC, abstractmethod
from sqlalchemy import create_engine
import pandas as pd



class StorageMethod(ABC):
    @abstractmethod
    def load(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def save(self, data: pd.DataFrame) -> None:
        pass


class CSVStorage(StorageMethod):
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self) -> pd.DataFrame:
        try:
            local_data = pd.read_csv(self.file_path, sep=",", index_col=0)
            if "Date" in local_data.columns: local_data["Date"] = pd.to_datetime(local_data["Date"], errors="coerce")
            return local_data 
        
        except FileNotFoundError:
            print(f"File not found at {self.file_path}. Returning empty Dataframe.")
            return pd.DataFrame()
        
    def save(self, data) -> None:
        data.to_csv(self.file_path, sep=",", index=True)
        print(f"Successfully saved data to {self.file_path}")



class SQLStorage(StorageMethod):
    def __init__(self, table_url, table_name):
        self.engine = create_engine(table_url)
        self.table_name = table_name

    def load(self) -> pd.DataFrame:
        try:
            query= f"SELECT * FROM {self.table_name}"
            return pd.read_sql(query, con=self.engine)
        
        except Exception as e:
            print(f"Failed to load from PostgreSQL: {e}")
            return pd.DataFrame()
        
    def save(self, data) -> None:
        data.to_sql(self.table_name, con=self.engine, if_exists="replace", index=True)
        print(f"Successfully saved data to table: {self.table_name}")




class XLSXStorage(StorageMethod):
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self) -> pd.DataFrame:
        try:
            local_data = pd.read_excel(self.file_path, index_col=0)
            if "Date" in local_data.columns: local_data["Date"] = pd.to_datetime(local_data["Date"], errors="coerce")
            return local_data 
        
        except FileNotFoundError:
            print(f"File not found at {self.file_path}. Returning empty Dataframe.")
            return pd.DataFrame()
        
    def save(self, data) -> None:
        data.to_excel(self.file_path, index=True)
        print(f"Successfully saved data to {self.file_path}")
#




def get_storage(tb_name, tb_dict, db_path="") -> StorageMethod:
    tb_type = tb_dict[tb_name]["tb_type"]

    if tb_type == "csv":
        return CSVStorage(file_path=f"data/{tb_name}.{tb_type}")
    elif tb_type == "sql":
        return SQLStorage(table_url=db_path, table_name=tb_name)
    elif tb_type == "xlsx":
        return XLSXStorage(file_path=f"data/{tb_name}.{tb_type}")
    else:
        raise ValueError("Unsupported storage type")


