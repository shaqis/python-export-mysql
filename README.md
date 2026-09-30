# MySQL to CSV Exporter

A Python utility for exporting MySQL tables to CSV files.

## Setup

Requires Python 3.

1. Create and activate a virtual environment (recommended; required on systems
   where pip reports `externally-managed-environment`):
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your database connection by editing `config.ini`:
   ```ini
   [database]
   host = localhost
   database = your_database
   user = your_username
   password = your_password
   port = 3306
   ```

   Credentials can also be supplied via environment variables, which override
   `config.ini`: `MYSQL_HOST`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`,
   `MYSQL_PORT`. Avoid committing real passwords to `config.ini`.

## Usage

You must specify one of `--table`, `--all-tables` or `--pattern`.

```bash
# Export a single table
python mysql_to_csv.py --table users

# Export several tables (comma separated)
python mysql_to_csv.py --table "users,orders,products"

# Export every table in the database
python mysql_to_csv.py --all-tables

# Export tables whose name matches a regex
python mysql_to_csv.py --pattern "user_.*"

# Custom config file and output directory
python mysql_to_csv.py --table users --config production.ini --output exports/users

# CSV that opens correctly in Excel (UTF-8 with BOM)
python mysql_to_csv.py --table users --encoding utf-8-sig
```

## Parameters

| Option | Description |
| --- | --- |
| `--table` | Table name(s) to export, comma separated. Names are checked against the database; unknown tables are reported and skipped. |
| `--all-tables` | Export all tables in the database. |
| `--pattern` | Regex matched against table names. |
| `--config` | Path to the configuration file (default: `config.ini`). |
| `--output` | Directory for the CSV files (default: `output`). |
| `--encoding` | CSV file encoding (default: `utf-8`). |

## Output

Each table is written to `<output>/<table>_<YYYYMMDD_HHMMSS>.csv`, for example
`output/customers_20230715_120530.csv`. The first row contains the column names.
Rows are streamed in batches, so large tables do not need to fit in memory.

The script exits with a non-zero status if any table could not be exported.
