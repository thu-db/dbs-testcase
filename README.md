# DBS-Testcase

## 数据说明

注意，由于评测器的设计问题，测例有一些需要考虑的约定：

1. 使用 `ORDER BY` 时，应该将排序字段也输出到结果中，否则评测器会因为无法判定该部分的有序性而直接视为结果正确。例如 `SELECT name FROM T ORDER BY id`，评测器得到的参考答案和用户输出都只有一列 `name`，那么评测器只能认为所有行的 `id` 都是一样的，用户以任意顺序输出均为正确。
2. 主外键的创建不应该与显式索引有冲突，否则很难规定 DESC 的显示内容。
3. 插入的数据中最好不要包含 `@` 符号，如果包含最好不要是字符串的第一个字符，如果是则绝不能有查询使得 `@` 出现在行首，否则这会被评测器识别为输出内容结束的标志。

## 标程说明

附带了 `std/main.py` 作为借用 MySQL 跑测例的标程，附带的第三方库放在 `std/requirements.txt` 中，注意它用了 `judger` 中的一个工具函数，所以需要手动设置 `PYTHONPATH` 来解决 `import` 路径问题，参考运行方法如下（Windows 的 CMD 中将 `export` 改为 `set` 即可）：

```
export PYTHONPATH=.
python std/main.py [other_arguments...]
```

## TODO

以下是优先级不高，可能在将来学期完成的内容：

- 用 `logger` 库重构输出
