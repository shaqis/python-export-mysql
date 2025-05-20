import mysql.connector
import csv
import os
import argparse
import re
from datetime import datetime
from configparser import ConfigParser

def read_config(config_file='config.ini'):
    """Read database configuration from file."""
    config = ConfigParser()
    config.read(config_file)
    return {
        'host': config.get('database', 'host'),
        'database': config.get('database', 'database'),
        'user': config.get('database', 'user'),
        'password': config.get('database', 'password'),
        'port': config.getint('database', 'port', fallback=3306)
    }

def connect_to_database(db_config):
    """Connect to MySQL database."""
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as error:
        print(f"Error connecting to MySQL database: {error}")
        exit(1)

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

def export_table_to_csv(connection, table_name, output_dir='.'):
    """Export a MySQL table to a CSV file."""
    cursor = connection.cursor()
    
    try:
        # Get column names
        cursor.execute(f"DESCRIBE {table_name}")
        columns = [column[0] for column in cursor.fetchall()]
        
        # Get data
        cursor.execute(f"SELECT * FROM {table_name}")
        data = cursor.fetchall()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Format filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f"{table_name}_{timestamp}.csv")
        
        # Write to CSV
        with open(output_file, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(columns)
            csv_writer.writerows(data)
        
        print(f"Successfully exported {len(data)} rows from {table_name} to {output_file}")
        return output_file
    
    except mysql.connector.Error as error:
        print(f"Error exporting table {table_name}: {error}")
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
    
    args = parser.parse_args()
    
    if not (args.table or args.all_tables or args.pattern):
        parser.error("You must specify either --table, --all-tables, or --pattern")
    
    try:
        db_config = read_config(args.config)
        connection = connect_to_database(db_config)
        
        tables_to_export = []
        
        if args.all_tables:
            tables_to_export = get_all_tables(connection)
        elif args.pattern:
            all_tables = get_all_tables(connection)
            tables_to_export = filter_tables(all_tables, args.pattern)
        elif args.table:
            tables_to_export = [table.strip() for table in args.table.split(',')]
        
        if not tables_to_export:
            print("No tables found to export")
            return
        
        print(f"Preparing to export {len(tables_to_export)} tables: {', '.join(tables_to_export)}")
        
        exported_files = []
        for table in tables_to_export:
            output_file = export_table_to_csv(connection, table, args.output)
            if output_file:
                exported_files.append(output_file)
        
        print(f"Export complete. {len(exported_files)} tables were exported successfully.")
        
        connection.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
