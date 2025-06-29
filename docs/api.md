## 使用示例

### GET 请求:

https://api.effiy.cn/module/?module_name=modules.crawler.crawler&method_name=main&params={"url":"https://www.qbitai.com/","min_title_length":24}

## insert_one

### GET 请求:

https://api.effiy.cn/module/?module_name=modules.database.mongoClient&method_name=insert_one&params={"cname":"test_collection","document":{"name": "张三", "age": 30, "email": "zhangsan@example.com"}}

### 参数说明:

- cname: 集合名称
- document: 要插入的文档

## find_one

### GET 请求:

https://api.effiy.cn/module/?module_name=modules.database.mongoClient&method_name=find_one&params={"cname":"test_collection","query":{"name": "张三"}}

### 参数说明:

- cname: 集合名称
- query: 查询条件
- projection: 指定返回的字段（可选）

## update_one

### GET 请求:

https://api.effiy.cn/module/?module_name=modules.database.mongoClient&method_name=update_one&params={"cname":"test_collection","query":{"name": "张三"},"update":{"age": 31, "updated": true}}

### 参数说明:

- cname: 集合名称
- query: 查询条件
- update: 更新内容

## find_one_and_update

### GET 请求:

https://api.effiy.cn/module/?module_name=modules.database.mongoClient&method_name=find_one_and_update&params={"cname":"test_collection","query":{"name": "张三"},"update":{"status": "active"},"return_document": true}

### 参数说明:

- cname: 集合名称
- query: 查询条件
- update: 更新内容
- return_document: 是否返回更新后的文档

## insert_many

### GET 请求:

https://api.effiy.cn/module/?module_name=modules.database.mongoClient&method_name=insert_many&params={"cname":"test_collection","documents":[{"name":"李四","age":25,"email":"lisi@example.com"},{"name":"王五","age":35,"email":"wangwu@example.com"}]}

### 参数说明:

- cname: 集合名称
- documents: 要插入的文档列表，每个文档是一个字典

## find_many

### GET 请求:

https://api.effiy.cn/module/?module_name=modules.database.mongoClient&method_name=find_many&params={"collection_name":"rss","filter_query":{},"sort_criteria":[]}

### 参数说明:

- collection_name: 集合名称
- filter_query: 查询条件，支持 MongoDB 查询操作符
- sort_criteria: 排序条件，格式为[["字段名", 1/-1]]，1 表示升序，-1 表示降序

## count_documents

### GET 请求:

https://api.effiy.cn/module/?module_name=modules.database.mongoClient&method_name=count_documents&params={"cname":"rss","query":{}}

## 参数说明:

- cname: 集合名称
- query: 查询条件，支持 MongoDB 查询操作符

## delete_many

### GET 请求:

https://api.effiy.cn/module/?module_name=modules.database.mongoClient&method_name=delete_many&params={"cname":"rss","query":{}}

### 参数说明:

- cname: 集合名称
- query: 查询条件，支持 MongoDB 查询操作符

## upsert

### GET 请求:

https://api.effiy.cn/module/?module_name=modules.database.mongoDB&method_name=upsert&params={"cname":"test_collection","document":{"name":"张三","age":31,"email":"zhangsan_new@example.com"},"query_fields":["name"]}

### 参数说明:

- cname: 集合名称
- document: 文档对象，包含查询条件和更新内容
- query_fields: 用作查询条件的字段名数组，默认为["name"]

## list_collections

### GET 请求:

https://api.effiy.cn/module/?module_name=modules.database.mongoClient&method_name=list_collections&params={}

## upsert_many

### GET 请求:

https://api.effiy.cn/module/?module_name=modules.database.mongoClient&method_name=upsert_many&params={"cname":"test_collection","documents":[],"query_fields":["title"]}

### 参数说明:

- cname: 集合名称
- documents: 文档列表，每个文档包含查询条件和更新内容
- query_fields: 用作查询条件的字段名数组，默认为["name"]
