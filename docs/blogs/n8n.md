# 深度解析n8n：开源工作流自动化平台

> 作者：YiAi
> 日期：2025年06月11日

![n8n 可视化界面示意图](https://img.notionusercontent.com/s3/prod-files-secure%2Fa60c81ff-618d-483a-b409-e9e387096f6f%2Fd1eba9d3-2cbd-44df-a544-8590273f2666%2F1941719976508_.jpeg/size/w=1163?exp=1749688839&sig=xQvYFomygf8FO2vcq8x1SXi35YQuqCZNw3Is93CggQY&id=867d3eda-3c87-48cf-a7b5-d73c868b0759&table=block)

## 背景

**[n8n](https://n8n.io/)** 是一个强大的开源工作流自动化平台，它允许用户通过可视化界面创建复杂的工作流程，实现不同应用程序和服务之间的自动化集成。作为一个开源项目，在 **[GitHub](https://github.com/n8n-io/n8n) 上获得了超过 106k 颗星，成为最受欢迎的工作流自动化工具之一。

## 认知

### 可视化工作流设计 - It works but why？

n8n 提供了一个直观的可视化界面，让用户可以通过拖拽方式创建工作流。每个工作流由节点（Nodes）组成，节点之间通过连接（Connections）建立数据流转关系。这种设计使得复杂的工作流程变得易于理解和维护。

### 分类逻辑 - 你应该先想清楚自己需要什么节点

n8n 的节点根据是否涉及外部服务和节点的自身作用可以有两个分类维度：
ㅤ
| 节点名称 | 触发节点（Triggers） | 执行节点（Actions） |
| :--- | :--- | :--- |
| 外部节点（需要依赖外部服务 API 的节点） | Gmail 收到新的邮件，触发工作流执行 | 通过 Gmail 写一封邮件并且发出去 |
| 自有节点（不依赖外部，或者基于标准协议） | 点击 Test Workflow 按钮，触发工作流执行 | 内建的逻辑节点，比如条件、判断、循环、数据处理等 |

**触发节点（Triggers）**  
- 触发节点可以作为工作流的第一个节点，相当于程序的“开始”。  
- 常见的触发方式包括：定时执行、接收聊天软件消息、界面按钮点击等。  
- **注意：一个工作流必须有明确的启动条件（Trigger），不会无缘无故自动运行。**

**执行节点（Actions）**  
- 执行节点不能作为工作流的第一个节点，必须由其他执行节点或触发节点触发。  
- 复杂的处理逻辑通常由执行节点完成。

---

基于上述分类，菜单中的节点类型可以这样理解：

| 节点类型         | 说明                                                         | 分类标签                   |
|------------------|--------------------------------------------------------------|----------------------------|
| Action in an app | 外部服务 API 封装节点，如 Google Sheets                      | 外部节点                   |
|                  | 市面上众多开放服务的节点                                     | 外部节点                   |
|                  | 每个外部服务节点分为【触发节点】和【执行节点】                |                            |
| 数据处理节点     | 用于数据过滤、转换                                           | 自有节点、执行节点         |
| Flow 节点        | 条件、循环、合并等逻辑操作                                   | 自有节点、执行节点         |
| Core 节点        | 代码节点                                                     | 自有节点、执行节点         |
| 人工智能节点     | 为 AI 打造的复合型节点，功能特殊                             | 特殊节点                   |
| 添加另一个触发器 | 增加新的触发节点                                             | 触发节点                   |
| 运行按钮         | 在 n8n 界面点击运行，触发程序                                | 自有节点                   |
| 外部 API 命令    | 如 Telegram 收到消息                                         | 外部节点                   |
| 定时任务         | 每天/每小时定时执行                                          | 自有节点                   |
| HTTP 请求触发    | 通过 HTTP 请求启动任务                                       | 自有节点                   |
| Workflow 触发    | 由其他工作流触发                                             | 自有节点                   |
| 聊天消息触发     | 聊天框消息触发（AI 对话类节点专用）                          | 特殊节点                   |
| 文件变更/Email   | 文件变更、邮件等事件                                         | 自有节点                   |

通过搜索和菜单分类，可以快速定位到所需的节点类型，提升工作流设计效率。

## 设计

### 常用的逻辑（条件、循环等）节点详细介绍

在 n8n 中，逻辑节点被归类在 Flow 类目下，也就是流程控制。它支持以下 9 种流程控制节点：

| 节点名称             | 说明                                                                                   |
|----------------------|----------------------------------------------------------------------------------------|
| Filter               | 过滤，从上游输入的一堆 items 里过滤掉不满足条件的。                                    |
| If                   | 判断，根据上游输入的数据判断给出 true 和 false 结果，并将数据流分叉成两个。            |
| Loop Over Items      | 循环，将上游输入的一堆 items 中的每一个，运行一遍 loop 中的部分，全部运行后打包输出。  |
| Merge                | 合并，将两个上游输出的数据合并成一个。                                                 |
| Compare Datasets     | 比较，将两个上游输出的数据进行比较，并决定在什么情况下用哪一个输出给下游。              |
| Execute Workflow     | 执行另一个 Workflow。                                                                 |
| Stop and Error       | 停止 Workflow 并输出错误。                                                            |
| Switch               | 路由，可理解为 If 的进阶版，根据上游输入的数据进行多重判断，分叉成多个数据流。         |
| Wait                 | 等待，运行到这里暂停一会儿，主要用于向第三方 API 发起请求时避免超过访问限制。           |


### **[企业微信群机器人配置说明](https://developer.work.weixin.qq.com/document/path/91770)**
```bash
curl 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=391185cd-b748-43a2-a9ec-2163183e3cd0' \
   -H 'Content-Type: application/json' \
   -d '
    {
      "msgtype": "markdown",
      "markdown": {
          "content": "实时新增用户反馈<font color=\"warning\">132例</font>，请相关同事注意。\n
          >类型:<font color=\"comment\">用户反馈</font>
          >普通用户反馈:<font color=\"comment\">117例</font>
          >VIP用户反馈:<font color=\"comment\">15例</font>"
      }
    }'
```

### **[如何给企业微信机器人发送消息？](https://www.bilibili.com/video/BV1pcL7z6EMv/?vd_source=9d10468e7f3b1477a6c14279b9a032a6)**
```json
{
  "name": "wechat-robot",
  "nodes": [
    {
      "parameters": {
        "method": "POST",
        "url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=391185cd-b748-43a2-a9ec-2163183e3cd0",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={\n  \"msgtype\": \"markdown\",\n  \"markdown\": {\n      \"content\": \"实时新增用户反馈<font color=\\\"warning\\\">132例</font>，\\n请相关同事注意。类型:<font color=\\\"comment\\\">用户反馈</font>普通用户反馈:<font color=\\\"comment\\\">117例</font>VIP用户反馈:<font color=\\\"comment\\\">15例</font>\"\n  }\n}",
        "options": {}
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [
        260,
        0
      ],
      "id": "9240dffb-75c1-401c-afc2-f2d87d332b47",
      "name": "HTTP Request"
    },
    {
      "parameters": {},
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [
        0,
        0
      ],
      "id": "f93c01f8-af81-4c20-b69a-a427ac981a45",
      "name": "When clicking ‘Execute workflow’"
    }
  ],
  "pinData": {},
  "connections": {
    "When clicking ‘Execute workflow’": {
      "main": [
        [
          {
            "node": "HTTP Request",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "active": false,
  "settings": {
    "executionOrder": "v1"
  },
  "versionId": "01a6410e-fe2b-4c97-9871-a12cd311d0aa",
  "meta": {
    "instanceId": "13c44c29821d820f58d01df6007919b772c3a53794ff8732958835f32562f1de"
  },
  "id": "l9pRLrrZsd5Qszou",
  "tags": []
}
```


### 参考文献

1. [n8n官方文档](https://docs.n8n.io/)
2. [n8n GitHub仓库](https://github.com/n8n-io/n8n)
3. [n8n社区论坛](https://community.n8n.io/)
4. [n8n博客](https://blog.n8n.io/)
5. [n8n 中文使用教程](https://n8n.akashio.com/)
6. [企业微信群机器人配置说明](https://developer.work.weixin.qq.com/document/path/91770)
7. [n8n 模板](https://n8n.io/workflows/)
8. [如何给企业微信机器人发送消息？](https://www.bilibili.com/video/BV1pcL7z6EMv/?vd_source=9d10468e7f3b1477a6c14279b9a032a6)
9. [Aggregate-聚合、Merge-合并、Summarize-汇总](https://xiangyugongzuoliu.com/n8n-aggregate-merge-summarize-guide-for-beginners/)
10. [零基础入门AI自动化](https://www.bilibili.com/video/BV14cPTecEwd/?spm_id_from=333.337.search-card.all.click&vd_source=9d10468e7f3b1477a6c14279b9a032a6)
11. [ComfyUI 终极效率革命：用N8N打通大语言模型，实现一键全自动AI绘画！](https://www.bilibili.com/video/BV17tMjzmEdf/)
