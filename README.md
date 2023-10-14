

注意，由于评测器的设计问题，测例有一些需要考虑的约定：

1. 使用 `ORDER BY` 时，应该将排序字段也输出到结果中，否则评测器会因为无法判定该部分的有序性而直接视为结果正确。例如 `SELECT name FROM T ORDER BY id`，评测器得到的参考答案和用户输出都只有一列 `name`，那么评测器只能认为所有行的 `id` 都是一样的，用户以任意顺序输出均为正确。