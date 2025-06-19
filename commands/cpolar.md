## 命令说明表

| 功能类型     | 命令                                            | 说明                           |
| ------------ | ----------------------------------------------- | ------------------------------ |
| HTTP 服务    | `cpolar http 80`                                | 启动 HTTP 服务，端口 80        |
| TCP 服务     | `cpolar tcp 22`                                 | 启动 TCP 服务，端口 22         |
| HTTPS 服务   | `cpolar https 443`                              | 启动 HTTPS 服务，端口 443      |
| 自定义域名   | `cpolar http 80 --domain=your-domain.cpolar.cn` | 设置自定义域名，方便记忆和访问 |
| 多端口映射   | `cpolar http 80,443,8080`                       | 同时映射多个端口               |
| 访问密码     | `cpolar http 80 --auth="username:password"`     | 设置访问密码，增加安全性       |
| 查看版本信息 | `cpolar version`                                | 查看当前版本信息               |
| 查看所有隧道 | `cpolar list`                                   | 查看所有活动的隧道             |
| 查看服务状态 | `cpolar status`                                 | 查看当前服务运行状态           |
| 停止服务     | `cpolar stop`                                   | 停止所有运行中的服务           |
