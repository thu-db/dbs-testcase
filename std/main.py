from argparse import ArgumentParser
import re

import mysql.connector
from mysql.connector.cursor import MySQLCursor

from judger.testcase import TestPoint

show_databases_re = re.compile("^SHOW\s+DATABASES")
mysql_databases = set(["information_schema", "mysql",
                       "performance_schema", "sys"])
desc_re = re.compile("^DESC\s")


def process_results(cur: MySQLCursor, sql: str, headers, data):
    flags = TestPoint.generate_flags(sql)
    if sql.startswith("SHOW"):
        if "DATABASE" in sql.upper():
            headers = "DATABASES",
            data = [e for e in data if e[0] not in mysql_databases]
        elif "TABLES" in sql.upper():
            headers = "TABLES",
        else:
            print("Unknown sql", sql)
            exit(-1)
    elif flags.is_desc:
        table_name = sql.split()[1].replace(";", "")
        cur.execute(f"SHOW INDEXES IN {table_name}")
        pass
    return headers, data


def run_sql(cur: MySQLCursor, sql: str):
    cur.execute(sql)
    if not cur.with_rows:
        return
    headers, data = process_results(cur, sql, cur.column_names, cur.fetchall())
    print(*headers, sep=',')
    for row in data:
        print(*row, sep=',')


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("-u", "--user", required=True)
    parser.add_argument("-p", "--password", required=True)
    parser.add_argument("--clear", action="store_true")
    parser.add_argument("host")
    return parser.parse_args()


def clear(cur: MySQLCursor):
    cur.execute("SHOW DATABASES")
    dbs = [e[0] for e in cur.fetchall()]
    dbs = [db for db in dbs if db not in mysql_databases]
    for db in dbs:
        cur.execute(f"DROP DATABASE {db}")


def main():
    conn = mysql.connector.connect(
        user=args.user,
        password=args.password,
        host=args.host,
        buffered=True,
        autocommit=True,
    )
    cur = conn.cursor()
    if args.clear:
        clear(cur)
    else:
        while True:
            sql = input().strip()
            if sql == "exit":
                break
            if not sql.endswith(";"):
                continue
            run_sql(cur, sql)
            print("@done")
    cur.close()
    conn.close()


if __name__ == "__main__":
    args = parse_args()
    main()
