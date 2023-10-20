-- @Name: index-schema
-- @Depends: query-data-a
-- @Flags: index
-- @Description: Schema alter for indexes
-- @Score: 4

USE DB;

SELECT * FROM TBL;

-- Check add index and show desc
ALTER TABLE TBL ADD INDEX idx_a(a);
DESC TBL;

SELECT * FROM TBL;
SELECT * FROM TBL WHERE a > 3;
SELECT * FROM TBL WHERE a = 3;
SELECT * FROM TBL WHERE a < 3 AND a > 4;
SELECT * FROM TBL WHERE a > 3 AND a < 4;

-- Check index with duplicated data
INSERT INTO TBL VALUES (2, '2', 2.0), (3, '3', 3.0), (4, '4', 4.0), (5, '5', 5.0), (6, '6', 6.0);
SELECT * FROM TBL WHERE a > 2 AND a < 6;


-- Check drop index
ALTER TABLE TBL DROP INDEX idx_a;
DESC TBL;
SELECT * FROM TBL WHERE a > 2 AND a < 6;

