from fastapi import FastAPI, Query # type: ignore
import json

app = FastAPI()

"""
使用示例:

GET 请求:
curl -X GET "http://localhost:8000/?module_name=modules.crawler&method_name=main&params=%7B%22url%22%3A%22https%3A%2F%2Fwww.qbitai.com%2F%22%2C%22min_title_length%22%3A24%7D"

POST 请求:
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "modules.crawler",
    "method_name": "main", 
    "params": {
      "url": "https://www.qbitai.com/",
      "min_title_length": 24
    }
  }'
"""
@app.get("/")
@app.post("/")
def read_module_to_execute(
    module_name: str = "modules.crawler",
    method_name: str = "main",
    params: str = Query(default='{"url": "https://www.qbitai.com/", "min_title_length": 24}')
):
    import importlib
    import asyncio
    
    # 将字符串转换为字典
    params_dict = json.loads(params)
    
    module = importlib.import_module(module_name)
    main_func = getattr(module, method_name)
    return asyncio.run(main_func(params_dict))

if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run(
        "server:app",
        reload=True
    )

