# -*- coding: utf-8 -*-
"""
Created on 2022/04/15
@author: schengatto@gmail.com
"""
import logging
import os

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logger = logging.getLogger()


class PostgresSqlConnector:
    def __init__(self):
        self._db_host = os.getenv("DB_HOST")
        self._db_port = os.getenv("DB_PORT")
        self._db_name = os.getenv("DB_NAME")
        if self.connect_to_database():
            logger.info('Connected with database successfully')

    def connect_to_database(self):
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        if self._db_host is None or self._db_port is None or self._db_name is None or DB_USER is None or DB_PASSWORD is None:
            raise Exception("Invalid database settings")
        conn = psycopg2.connect(
            host=self._db_host,
            port=self._db_port,
            database=self._db_name,
            user=DB_USER,
            password=DB_PASSWORD)
        return conn

    def create_database(self, create_: str):
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        conn = psycopg2.connect(
            host=self._db_host,
            port=self._db_port,
            database='postgres',
            user=DB_USER,
            password=DB_PASSWORD)

        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()  # create cursor object

        # TODO security fix
        # Use the psycopg2.sql module instead of string concatenation
        # in order to avoid sql injection attacks.
        # cursor.execute(sql.SQL("CREATE DATABASE {}").format(
        #     sql.Identifier(self.db_name))
        # )

        cursor.execute(create_)  # execute query
        conn.commit()  # commit query to database
        logger.info(f'Table have been created successfully! {cursor}')
        self.close(conn, cursor=cursor)

    # function to read from database
    def read(self, read_, mapping=None):
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(read_)
        result = []
        for row in cursor:
            if mapping is None:
                result.append(row)
            else:
                result.append(mapping(row))
        return result

    # function to create in projects database
    def create(self, create_: str):
        conn = self.connect_to_database()
        cursor = conn.cursor()  # create cursor object
        cursor.execute(create_)  # execute query
        conn.commit()  # commit query to database
        logger.info(f'Table have been created successfully! {cursor}')
        self.close(conn, cursor=cursor)

    # function to insert in projects database
    def insert(self, insert_: str):
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(insert_)
        conn.commit()
        logger.info(f'Records have been successfully inserted! {cursor}')
        self.close(conn, cursor=cursor)

    # function to update table
    def update(self, update_: str):
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(update_)
        conn.commit()
        logger.info(f'Records have been successfully updated! {cursor}')
        self.close(conn, cursor=cursor)

    # function to delete in projects database
    def delete(self, delete_: str):
        conn = self.connect_to_database()
        cursor = conn.cursor()
        cursor.execute(delete_)
        conn.commit()
        logger.info(f'Records have been successfully deleted! {cursor}')
        self.close(conn, cursor=cursor)

    # function to create pandas dataframe
    def create_pandas_df(self, sql_query: str):
        conn = self.connect_to_database()
        table = pd.read_sql_query(sql_query, conn)
        self.close(conn)
        return table

    # close the cursor and connection to the server
    def close(self, conn, cursor=None):
        if cursor is not None:
            cursor.close()
        conn.close()
