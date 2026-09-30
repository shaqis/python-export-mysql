import mysql.connector
import csv
import os
import argparse
import re
import sys
from datetime import datetime
from configparser import ConfigParser

def read_config(config_file='config.ini'):
    """Read database configuration from file, overridable by MYSQL_* environment variables."""
    config = ConfigParser()
    config.read(config_file)

    def setting(key, env_name, fallback=None):
        value = os.environ.get(env_name)
        if value:
            return value
        return config.get('database', key, fallback=fallback)

    try:
        return {
            'host': setting('host', 'MYSQL_HOST'),
            'database': setting('database', 'MYSQL_DATABASE'),
            'user': setting('user', 'MYSQL_USER'),
            'password': setting('password', 'MYSQL_PASSWORD'),
            'port': int(setting('port', 'MYSQL_PORT', '3306')),
        }
    except ValueError as error:
        raise ValueError(f"Invalid database port: {error}")

def connect_to_database(db_config):
    """Connect to MySQL database."""
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as error:
        print(f"Error connecting to MySQL database: {error}", file=sys.stderr)
        sys.exit(1)

def get_all_tables(connection):
    """Get a list of all tables in the database."""
    cursor = connection.cursor()
    try:
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        return tables
    except mysql.connector.Error as error:
        print(f"Error retrieving tables: {error}")
        return []
    finally:
        cursor.close()

def filter_tables(tables, pattern=None):
    """Filter tables based on pattern."""
    if not pattern:
        return tables
    
    regex = re.compile(pattern)
    return [table for table in tables if regex.search(table)]

def quote_identifier(name):
    """Quote a table name with backticks so special characters are safe."""
    return "`" + name.replace("`", "``") + "`"

def export_table_to_csv(connection, table_name, output_dir='.', encoding='utf-8', batch_size=10000):
    """Export a MySQL table to a CSV file, streaming rows in batches."""
    cursor = connection.cursor()
    output_file = None

    try:
        cursor.execute(f"SELECT * FROM {quote_identifier(table_name)}")
        columns = [column[0] for column in cursor.description]

        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f"{table_name}_{timestamp}.csv")

        row_count = 0
        with open(output_file, 'w', newline='', encoding=encoding) as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(columns)
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                csv_writer.writerows(rows)
                row_count += len(rows)

        print(f"Successfully exported {row_count} rows from {table_name} to {output_file}")
        return output_file

    except (mysql.connector.Error, OSError) as error:
        print(f"Error exporting table {table_name}: {error}", file=sys.stderr)
        if output_file and os.path.exists(output_file):
            os.remove(output_file)
        return None
    finally:
        cursor.close()

def main():
    parser = argparse.ArgumentParser(description='Export MySQL tables to CSV')
    parser.add_argument('--table', help='Table name to export (can specify multiple tables with comma separation)')
    parser.add_argument('--all-tables', action='store_true', help='Export all tables from the database')
    parser.add_argument('--pattern', help='Regex pattern to match table names for export')
    parser.add_argument('--config', default='config.ini', help='Configuration file path')
    parser.add_argument('--output', default='output', help='Output directory for CSV files')
    parser.add_argument('--encoding', default='utf-8',
                        help="CSV file encoding (use 'utf-8-sig' if opening in Excel)")

    args = parser.parse_args()

    if not (args.table or args.all_tables or args.pattern):
        parser.error("You must specify either --table, --all-tables, or --pattern")

    connection = None
    try:
        db_config = read_config(args.config)
        connection = connect_to_database(db_config)

        available_tables = get_all_tables(connection)
        unknown = []

        if args.all_tables:
            tables_to_export = available_tables
        elif args.pattern:
            tables_to_export = filter_tables(available_tables, args.pattern)
        else:
            requested = [table.strip() for table in args.table.split(',') if table.strip()]
            unknown = [table for table in requested if table not in available_tables]
            if unknown:
                print(f"Table(s) not found in database: {', '.join(unknown)}", file=sys.stderr)
            tables_to_export = [table for table in requested if table in available_tables]

        if not tables_to_export:
            print("No tables found to export")
            return 1

        print(f"Preparing to export {len(tables_to_export)} tables: {', '.join(tables_to_export)}")

        exported_files = []
        for table in tables_to_export:
            output_file = export_table_to_csv(connection, table, args.output, args.encoding)
            if output_file:
                exported_files.append(output_file)

        print(f"Export complete. {len(exported_files)} of {len(tables_to_export)} tables were exported successfully.")
        return 0 if len(exported_files) == len(tables_to_export) and not unknown else 1
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        return 1
    finally:
        if connection is not None:
            connection.close()

if __name__ == "__main__":
    sys.exit(main())
