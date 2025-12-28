import os
from pathlib import Path
import sys
from sqlalchemy.orm import Session
from sqlalchemy import text

sys.path.insert(0, os.getcwd())

from db.session import get_db


class ViewManager:
    def __init__(self, db: Session, views_folder: str):
        self.views_folder = Path(views_folder)
        self.db = db

        self.view_path = self.views_folder / "views"
        self.materialized_view_path = self.views_folder / "materialized"

        self.views = self.__get_views(self.view_path)
        self.materialized_views = self.__get_views(self.materialized_view_path)

    def __get_views(self, path: Path):
        return [file.stem for file in path.iterdir() if file.is_file()]

    def create_views(self):
        for view_name in self.views:
            self.__create_view(
                view_name,
                self.__get_sql_query(folder=self.view_path, view_name=view_name),
            )

        for view_name in self.materialized_views:
            self.__create_materialized_view(
                view_name,
                self.__get_sql_query(
                    folder=self.materialized_view_path, view_name=view_name
                ),
            )

    def resresh_views(self):
        for view_name in self.materialized_views:
            self.__refresh_materialized_view(view_name)

    def __get_sql_query(self, folder: Path, view_name: str) -> str:
        with open(folder / f"{view_name}.sql", "r") as file:
            return file.read()

    def __create_view(self, view_name: str, query: str):
        sql = f"""
        CREATE OR REPLACE VIEW {view_name} AS
        {query}
        """
        self.db.execute(text(sql))
        self.db.commit()

    def __create_materialized_view(self, view_name: str, query: str):
        sql = f"""
        CREATE MATERIALIZED VIEW IF NOT EXISTS {view_name} AS
        {query}
        """
        self.db.execute(text(sql))
        self.db.commit()

    def __refresh_materialized_view(self, view_name: str):
        self.db.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}"))
        self.db.commit()


if __name__ == "__main__":
    vm = ViewManager(
        db=next(get_db()),
        views_folder=r"F:\itmo\courses\data-engeneering\ticket-price-monitoring-tg-bot\airflow\aggregation_layers\golden_views",
    )

    vm.create_views()
    vm.resresh_views()
