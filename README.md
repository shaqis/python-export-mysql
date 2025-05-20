# MySQL to CSV Exporter

A Python utility for exporting MySQL tables to CSV files.

## Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Configure your database connection:
   Edit `config.ini` with your MySQL database credentials.

## Usage

Basic usage:
```
python mysql_to_csv.py --table your_table_name
```

Additional options:
```
python mysql_to_csv.py --table your_table_name --config path/to/config.ini --output path/to/output/dir
```

## Parameters

- `--table`: (Required) The name of the table to export
- `--config`: (Optional) Path to configuration file (default: config.ini)
- `--output`: (Optional) Directory to save CSV files (default: ./output)

## Example

```
python mysql_to_csv.py --table customers --output data/exports
```

This will create a timestamped CSV file like `data/exports/customers_20230715_120530.csv`
