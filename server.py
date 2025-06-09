import sys, os, json
from fastapi import FastAPI, Query # type: ignore

# 禁用 Python 字节码缓存
sys.dont_write_bytecode = True

# 确保子进程也不生成 __pycache__
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# 创建FastAPI应用实例
app = FastAPI()

"""
使用示例:

GET 请求:
http://localhost:8000/?module_name=modules.crawler.crawler&method_name=main&params={"url":"https://www.qbitai.com/","min_title_length":24}
http://localhost:8000/?module_name=modules.database.mongoDB&method_name=insert_one&params={"cname":"test_collection","document":{"name": "张三", "age": 30, "email": "zhangsan@example.com"}}
http://localhost:8000/?module_name=modules.database.mongoDB&method_name=find_one&params={"cname":"test_collection","query":{"name": "张三"}}

命令行示例:
curl -X GET "http://localhost:8000/?module_name=modules.crawler.crawler&method_name=main&params=%7B%22url%22%3A%22https%3A%2F%2Fwww.qbitai.com%2F%22%2C%22min_title_length%22%3A24%7D"

POST 请求:
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "modules.crawler.crawler",
    "method_name": "main", 
    "params": {
      "url": "https://www.qbitai.com/",
      "min_title_length": 24
    }
  }'

浏览器直接访问(默认参数):
http://localhost:8000/
"""
# 同时支持GET和POST两种HTTP请求方法的路由
@app.get("/")
@app.post("/")
def read_module_to_execute(
    # 设置默认模块名为modules.crawler
    module_name: str = "modules.crawler.crawler",
    # 设置默认方法名为main
    method_name: str = "main",
    # 使用Query参数处理params，默认值为爬取启智AI网站且最小标题长度为24
    params: str = Query(default='{"url": "https://www.qbitai.com/", "min_title_length": 24}')
):
    # 导入动态加载模块所需的库
    import importlib
    # 导入异步支持库
    import asyncio
    
    # 将字符串转换为字典
    params_dict = json.loads(params)
    
    # 动态导入指定的模块
    module = importlib.import_module(module_name)
    # 从模块中获取指定的方法
    main_func = getattr(module, method_name)
    # 异步执行获取的方法，并传入参数字典，返回执行结果
    return asyncio.run(main_func(params_dict))

# 当直接运行此脚本时执行以下代码
if __name__ == "__main__":
    # 导入uvicorn服务器
    import uvicorn # type: ignore
    # 启动uvicorn服务器，运行FastAPI应用
    uvicorn.run(
        "server:app",  # 指定应用模块路径
        reload=True    # 启用热重载，便于开发调试
    )
