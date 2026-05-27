"""
Database connection management with pooling and error handling
"""
import mysql.connector
from mysql.connector import pooling, Error
from config import Config
import logging

logger = logging.getLogger(__name__)

# Connection pool
connection_pool = None


def init_db_pool():
    """Initialize the database connection pool
    
    Should be called once at application startup
    """
    global connection_pool
    
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name=Config.DB_POOL_NAME,
            pool_size=Config.DB_POOL_SIZE,
            pool_reset_session=Config.DB_POOL_RESET_SESSION,
            **Config.get_db_config()
        )
        logger.info(f"Database pool initialized: {Config.DB_HOST}:{Config.DB_PORT}")
        return True
    except Error as e:
        logger.error(f"Failed to initialize database pool: {e}")
        return False


def get_db_connection():
    """Get a connection from the pool
    
    Returns:
        mysql.connector.connection_cext.CMySQLConnection or None if pool not initialized
    """
    if connection_pool is None:
        if not init_db_pool():
            return None
    
    try:
        return connection_pool.get_connection()
    except Error as e:
        logger.error(f"Failed to get database connection: {e}")
        return None


def get_db_cursor(dictionary=True):
    """Get a cursor with automatic connection management
    
    Args:
        dictionary: If True, return cursor with dictionary=True
        
    Returns:
        tuple: (connection, cursor) or (None, None) if failed
    """
    conn = get_db_connection()
    if conn is None:
        return None, None
    
    try:
        cursor = conn.cursor(dictionary=dictionary)
        return conn, cursor
    except Error as e:
        logger.error(f"Failed to create cursor: {e}")
        if conn:
            conn.close()
        return None, None


def close_cursor(cursor, connection):
    """Safely close cursor and connection
    
    Args:
        cursor: mysql.connector cursor
        connection: mysql.connector connection
    """
    if cursor:
        try:
            cursor.close()
        except Error as e:
            logger.error(f"Error closing cursor: {e}")
    
    if connection:
        try:
            connection.close()
        except Error as e:
            logger.error(f"Error closing connection: {e}")


def execute_query(query, params=None, dictionary=True, fetch_one=False):
    """Execute a query and return results
    
    Args:
        query: SQL query string
        params: Query parameters (for parameterized queries)
        dictionary: If True, return dict results
        fetch_one: If True, return single result instead of list
        
    Returns:
        Query results or None if failed
    """
    conn, cursor = get_db_cursor(dictionary=dictionary)
    if cursor is None:
        return None
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch_one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
        
        conn.commit()
        return result
    except Error as e:
        logger.error(f"Query execution error: {e}\nQuery: {query}")
        if conn:
            conn.rollback()
        return None
    finally:
        close_cursor(cursor, conn)


def execute_procedure(procedure_name, args=None):
    """Call a stored procedure
    
    Args:
        procedure_name: Name of the procedure
        args: List of arguments for the procedure
        
    Returns:
        Procedure results or None if failed
    """
    conn, cursor = get_db_cursor(dictionary=True)
    if cursor is None:
        return None
    
    try:
        if args:
            cursor.callproc(procedure_name, args)
        else:
            cursor.callproc(procedure_name)
        
        result = None
        if cursor.description:
            result = cursor.fetchall()
        
        conn.commit()
        return result
    except Error as e:
        logger.error(f"Procedure execution error: {e}\nProcedure: {procedure_name}")
        if conn:
            conn.rollback()
        return None
    finally:
        close_cursor(cursor, conn)


def get_insert_id(conn):
    """Get the last inserted ID
    
    Args:
        conn: mysql.connector connection
        
    Returns:
        Last insert ID or None
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT LAST_INSERT_ID() as id")
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
    except Error as e:
        logger.error(f"Error getting insert ID: {e}")
        return None


class DatabaseContextManager:
    """Context manager for database connections
    
    Usage:
        with DatabaseContextManager() as (conn, cursor):
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()
    """
    
    def __init__(self, dictionary=True):
        self.dictionary = dictionary
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        self.conn, self.cursor = get_db_cursor(dictionary=self.dictionary)
        return self.conn, self.cursor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if self.conn:
                self.conn.rollback()
        else:
            if self.conn:
                self.conn.commit()
        
        close_cursor(self.cursor, self.conn)
