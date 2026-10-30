# 项目专用环境

与 [`environments/`](../environments/) 中的通用组分开存放。当某组无法与通用框架环境共用时，在此锁定。

当前已准备：

| 目录 | 原因 |
| --- | --- |
| [`07b_gpflow_tf_py310/`](07b_gpflow_tf_py310/) | GPflow 需要 numpy&lt;2 以及 TF 2.16 + TFP 0.24 + tf-keras 2.16。不能装进 `07_tensorflow_cpu_py310`（TF 2.21 / numpy 2.x）。 |

未来按 `../project_dependency_supplement_guide_cn.md` 为**单个** Release 新增目录，例如 `project_specific/<release_id>/`。不要升级并覆盖上述基础锁定。
