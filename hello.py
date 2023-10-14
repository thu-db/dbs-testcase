ans = [
    # 1-system.sql
    "DATABASES",
    "",
    "",
    "",
    """
DATABASES
DB
DB1
DB2
""".strip(),
    "",
    "",
    "",
    """
DATABASES
DB
DB1
DB2
DB3
""".strip(),
    "",
    """
DATABASES
DB
DB2
DB3
""".strip(),
    # 2-table.sql
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    """
Field,Type,Null,Default
L_ORDERKEY,INT,NO,NULL
L_PARTKEY,INT,NO,NULL
L_SUPPKEY,INT,NO,NULL
L_LINENUMBER,INT,NO,NULL
L_QUANTITY,FLOAT,YES,NULL
L_EXTENDEDPRICE,FLOAT,YES,NULL
L_DISCOUNT,FLOAT,YES,NULL
L_TAX,FLOAT,YES,NULL
L_RETURNFLAG,VARCHAR(1),YES,NULL
L_LINESTATUS,VARCHAR(1),YES,NULL
L_SHIPINSTRUCT,VARCHAR(25),YES,NULL
L_SHIPMODE,VARCHAR(10),YES,NULL
L_COMMENT,VARCHAR(44),YES,NULL

PRIMARY KEY (L_PARTKEY, L_SUPPKEY);
FOREIGN KEY (L_ORDERKEY) REFERENCES ORDERS(O_ORDERKEY);
FOREIGN KEY (L_PARTKEY,L_SUPPKEY) REFERENCES PARTSUPP(PS_PARTKEY,PS_SUPPKEY);
    """.strip(),
    """
TABLES
PART
REGION
NATION
SUPPLIER
CUSTOMER
PARTSUPP
ORDERS
LINEITEM
    """.strip(),
    "",
    "",
    "",
    """
TABLES
TBL
TBL2
""".strip(),
    """
Field,Type,Null,Default
a,INT,NO,NULL
b,VARCHAR(16),NO,NULL
c,FLOAT,NO,NULL
""".strip(),
    "",
    """
TABLES
TBL
""".strip(),
]
if __name__ == "__main__":
    # print("start", file=sys.stderr, flush=True)
    for e in ans:
        input()
        if e:
            print(e)
        print("@done")
    input()
        
