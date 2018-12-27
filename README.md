# 大藏经古籍数字化平台

[![Build Status](https://travis-ci.org/tripitakas/dzj-html.svg?branch=tornado)](https://travis-ci.org/tripitakas/dzj-html)

## 前端改版

- 参考[前端模板语法][templates]修改网页代码，主要使用`{% if/for %}`、`{{ py_expr }}`。
  
  常用变量见 `controller/base.py render()` 和相应的响应Handler中的参数。

- 使用 `{% include %}` 提取公共网页部分，例如 `_base_css.html`、`_base_js.html`、`_base_meta.html`。

- 可调用 `getApi`、`postApi` 函数调用后端接口，执行操作和填充页面数据。

- 可使用 `showError`、`showSuccess`、`decodeJSON` 等常用函数进行消息显示和数据转换。

## 安装

本平台需要 Python 3.6+/2.7、MySQL 5.5+/MariaDB 10.3+、MongoDB，请参考下面的说明安装和部署。

- [INSTALL-linux.md](doc/INSTALL-linux.md)
- [INSTALL-mac.md](doc/INSTALL-mac.md)
- [INSTALL-win.md](doc/INSTALL-win.md)

## 测试

本项目可采用测试驱动开发(TDD)模式实现后端接口：

```
pip install -r tests/requirements.txt
mysql -u root -e 'create database if not exists tripitaka_test;'
mysql -u root tripitaka_test < model/init.sql;
python tests/add_pages.py --json_path=tests/data --db_name=tripitaka_test
python run_tests.py 或选中测试用例文件调试
```

在 `tests` 下编写测试用例，然后在 `controller.views` 或 `controller.api` 中实现后端接口。

使用 `add_pages.py` 批量添加页面切分数据，可改变参数为实际页面的路径。

## 参考资料

- [Bootstrap 3 中文文档](https://v3.bootcss.com)
- [Tornado 官方文档中文版](https://tornado-zh.readthedocs.io/zh/latest/)
- [Tornado 前端模板语法][templates]
- [Introduction to Tornado 中文版](http://demo.pythoner.com/itt2zh/)
- [MongoDB 数据库开发](http://demo.pythoner.com/itt2zh/ch4.html)

[templates]: https://tornado-zh.readthedocs.io/zh/latest/guide/templates.html
