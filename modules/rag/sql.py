import sqlite3, os
import pandas as pd # type: ignore
from typing import List, Dict, Any, Optional
from haystack import component, Pipeline # type: ignore
from haystack.dataclasses import ChatMessage # type: ignore
from haystack.components.builders import ChatPromptBuilder # type: ignore
from haystack_integrations.components.generators.ollama import OllamaChatGenerator # type: ignore
import re

@component
class SQLQueryExtractor:
    """从LLM回复中提取SQL查询的组件"""
    
    @component.output_types(queries=List[str])
    def run(self, replies: List[ChatMessage]):
        queries = []
        for reply in replies:
            # 使用text属性获取内容
            content = reply.text if hasattr(reply, 'text') and reply.text else str(reply.content)
            if not isinstance(content, str):
                content = str(content)
            
            # 提取SQL查询，使用更精确的正则表达式
            extracted_query = self._extract_sql_query(content)
            if extracted_query:
                queries.append(extracted_query)
            else:
                # 如果没有找到SQL查询，返回原始内容用于调试
                queries.append(f"未找到SQL查询: {content.strip()}")
        
        return {"queries": queries}
    
    def _extract_sql_query(self, content: str) -> Optional[str]:
        """提取SQL查询的辅助方法"""
        # 清理内容，移除思考标签和代码块标记
        cleaned_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        cleaned_content = re.sub(r'```(?:sql)?', '', cleaned_content)
        cleaned_content = cleaned_content.strip()
        
        # 使用正则表达式匹配SELECT语句
        sql_pattern = r'(?i)(SELECT\s+.*?)(?:;|\Z)'
        match = re.search(sql_pattern, cleaned_content, re.DOTALL)
        
        if match:
            sql_query = match.group(1).strip()
            # 清理换行符和多余空格
            sql_query = ' '.join(sql_query.split())
            return sql_query + ';' if not sql_query.endswith(';') else sql_query
        
        return None

@component
class SQLQuery:
    """执行SQL查询的组件"""
    
    def __init__(self, sql_database: str):
        self.database_path = sql_database
        self.connection = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """初始化数据库连接"""
        try:
            self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
            # 设置行工厂以获得更好的结果格式
            self.connection.row_factory = sqlite3.Row
        except Exception as e:
            raise Exception(f"无法连接到数据库 {self.database_path}: {str(e)}")

    @component.output_types(results=List[str], queries=List[str])
    def run(self, queries: List[str]):
        results = []
        executed_queries = []
        
        for query in queries:
            try:
                # 验证查询是否为有效的SELECT语句
                if self._is_valid_sql_query(query):
                    result = self._execute_query(query)
                    results.append(result)
                    executed_queries.append(query)
                else:
                    error_msg = f"无效的SQL查询或包含错误: {query}"
                    results.append(error_msg)
                    executed_queries.append(query)
            except Exception as e:
                error_msg = f"SQL执行错误: {str(e)} | 查询: {query}"
                results.append(error_msg)
                executed_queries.append(query)
        
        return {"results": results, "queries": executed_queries}
    
    def _is_valid_sql_query(self, query: str) -> bool:
        """验证SQL查询是否有效"""
        query = query.strip()
        # 基本验证：必须以SELECT开头且包含FROM
        if not query.upper().startswith('SELECT'):
            return False
        
        # 安全检查：禁止危险操作
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in query.upper():
                return False
        
        return True
    
    def _execute_query(self, query: str) -> str:
        """执行SQL查询并返回格式化结果"""
        try:
            df = pd.read_sql_query(query, self.connection)
            
            if df.empty:
                return "查询结果为空"
            
            # 格式化结果，限制显示行数以避免输出过长
            max_rows = 50
            if len(df) > max_rows:
                result_str = f"查询返回 {len(df)} 行数据，显示前 {max_rows} 行:\n"
                result_str += df.head(max_rows).to_string(index=False)
                result_str += f"\n... (还有 {len(df) - max_rows} 行)"
            else:
                result_str = f"查询返回 {len(df)} 行数据:\n"
                result_str += df.to_string(index=False)
            
            return result_str
            
        except Exception as e:
            raise Exception(f"执行查询时出错: {str(e)}")
    
    def __del__(self):
        """清理数据库连接"""
        if self.connection:
            self.connection.close()

# 优化的提示模板
template = [
    ChatMessage.from_user("""你是一个SQL专家。请为以下问题生成一个准确的SQL查询。

问题: {{question}}
表名: absenteeism
表列: {{columns}}

要求:
1. 只返回SQL查询语句，不要包含任何解释
2. 确保语法正确
3. 使用标准SQL语法
4. 以分号结束查询

SQL查询:""")
]

def create_sql_pipeline() -> Pipeline:
    """创建优化的SQL查询管道"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "qwq")
    prompt = ChatPromptBuilder(
        template=template, 
        required_variables=["question", "columns"]
    )
    llm =  OllamaChatGenerator(
        model=ollama_model, 
        url=ollama_url,
        generation_kwargs={"temperature": 0.1}  # 降低温度以获得更一致的结果
    )
    
    # 验证数据库文件是否存在
    db_path = 'absenteeism.db'
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"数据库文件 {db_path} 不存在")

    sql_pipeline = Pipeline()
    sql_pipeline.add_component("prompt", prompt)
    sql_pipeline.add_component("llm",llm)
    sql_pipeline.add_component("sql_extractor", SQLQueryExtractor())
    sql_pipeline.add_component("sql_querier", SQLQuery(db_path))

    # 连接组件
    sql_pipeline.connect("prompt.prompt", "llm.messages")
    sql_pipeline.connect("llm.replies", "sql_extractor.replies")
    sql_pipeline.connect("sql_extractor.queries", "sql_querier.queries")

    return sql_pipeline

async def main(params: Dict[str, Any]) -> List[Dict[str, str]]:
    """运行SQL查询管道的主函数"""
    question = params.get("question", "有多少行数据?")
    columns = params.get("columns", "ID, Reason_for_absence, Month_of_absence, Day_of_the_week, Seasons, Transportation_expense, Distance_from_Residence_to_Work, Service_time, Age, Work_load_Average_day_, Hit_target, Disciplinary_failure, Education, Son, Social_drinker, Social_smoker, Pet, Weight, Height, Body_mass_index, Absenteeism_time_in_hours")
    
    try:
        pipeline = create_sql_pipeline()
        result = pipeline.run({
            "prompt": {
                "question": question,
                "columns": columns
            }
        })
        
        # 提取结果
        if result.get("sql_querier", {}).get("results"):
            return [{"result": result["sql_querier"]["results"][0]}]
        else:
            return [{"result": "没有返回结果"}]
            
    except Exception as e:
        return [{"result": f"执行错误: {str(e)}"}]

if __name__ == "__main__":
    try:
        sql_pipeline = create_sql_pipeline()
        
        # 尝试绘制管道图
        try:
            sql_pipeline.draw("sql_pipeline.png")
            print("管道图已保存为 sql_pipeline.png")
        except Exception as e:
            print(f"无法绘制管道图: {e}")
        
        # 执行测试查询
        test_question = "On which days of the week does the average absenteeism time exceed 4 hours?"
        test_columns = "ID, Reason_for_absence, Month_of_absence, Day_of_the_week, Seasons, Transportation_expense, Distance_from_Residence_to_Work, Service_time, Age, Work_load_Average_day_, Hit_target, Disciplinary_failure, Education, Son, Social_drinker, Social_smoker, Pet, Weight, Height, Body_mass_index, Absenteeism_time_in_hours"
        
        print(f"执行测试查询: {test_question}")
        result = sql_pipeline.run({
            "prompt": {
                "question": test_question,
                "columns": test_columns
            }
        })
        
        print("执行结果:")
        print(result["sql_querier"]["results"][0])
        
    except Exception as e:
        print(f"程序执行错误: {str(e)}")

