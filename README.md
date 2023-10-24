# DBS-Testcase

## 使用说明

用来本地评测的入口文件是 `runner.py`，使用时你理应在本文件夹下启动评测器，将你编译好的程序的相对路径或者绝对路径复制到下面的参数中，参考指令如下：

```bash
python3 runner.py -- /path/to/your/prog -f query data
```

部分测例会有 `flag` 标记，表明该测例只有给出 flag 后才会显式地启动该测例，上述例子中便启用了两个 flag，分别是 `query` 和 `data`，如果你不希望启用任何 flag，则可以不使用 `-f` 参数，或者提供无效参数如 `-f no_use`。

在 CI 评测时为了执行编译流程并解决难以找到自己可执行程序的路径的问题，另外编写了一个 `run-ci.py` 进行上层封装，它被期望在你自己的项目中运行，会读取你项目根目录下的 `testcase.yml` 配置文件并据此进行操作：
 
0. 验证 CI 文件没有被篡改
1. 以你的项目根目录为工作目录，根据配置文件 `compile` 段进行编译
2. 以 `dbs-testcase` 的根目录为工作目录，运行 `runner.py`，但是在启用你的程序时会将工作目录切换回你的项目根目录

例如你的项目在 `/path/to/student-repo`，本仓库的路径在 `/path/to/dbs-testcase`，那么如下是一个可能的运行`testcase.yml`配置

```yml
compile:
  commands: make

run:
  commands: ./bin/mydb
  flags:
    - no_use
```

然后你在 `/path/to/student-repo` 中执行 

```bash
python3 /path/to/dbs-testcase/run-ci.py
```

简单来说你不必研究 `run-ci.py` 的工作原理，你只需要记住在你自己项目的 `dbs-testcase.yml` 中的 `commands` 都是以你项目的根目录为参考即可。

## 数据说明

注意，由于评测器的设计问题，测例有一些需要考虑的约定：

1. 使用 `ORDER BY` 时，应该将排序字段也输出到结果中，否则评测器会因为无法判定该部分的有序性而直接视为结果正确。例如 `SELECT name FROM T ORDER BY id`，评测器得到的参考答案和用户输出都只有一列 `name`，那么评测器只能认为所有行的 `id` 都是一样的，用户以任意顺序输出均为正确。
2. 主外键的创建不应该与显式索引有冲突，否则很难规定 DESC 的显示内容。
3. 插入的数据中最好不要包含 `@` 符号，如果包含最好不要是字符串的第一个字符，如果是则绝不能有查询使得 `@` 出现在行首，否则这会被评测器识别为输出内容结束的标志。

## 标程说明

附带了 `std/main.py` 作为借用 MySQL 跑测例的标程，附带的第三方库放在 `std/requirements.txt` 中，可以用于生成答案，参考运行方式如下：

```bash
python runner.py --std -f [flags, ...] -- python std/main.py <args...>
```

## TODO

以下是优先级不高，可能在将来学期完成的内容：

- 用 `logger` 库重构输出
