-- @Name: query-fuzzy
-- @Depends: optional
-- @Flags: group
-- @Description: Fuzzy query
-- @Score: 1

SELECT CUSTOMER.C_NAME, CUSTOMER.C_ACCTBAL FROM CUSTOMER WHERE CUSTOMER.C_NAME LIKE '%#00%123_';

