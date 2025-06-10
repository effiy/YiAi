# 深度解析 Agent 实现，定制自己的 Manus

> 作者：阿里云开发者  
> 日期：[2025 年 04 月 25 日](https://mp.weixin.qq.com/s/rX3J1f8V_-dvBYn1MAl1dg)

## 背景

Manus 核心能力就是基于 LLM 的**自主任务分解与执行**。他有两个明显的特点，值得学习：

1. 通过工程化能力（任务调度、工具整合）将 AI Agent 从概念落地为大众产品，满足了大家对 AI "自主解决问题" 的深层期待。

2. 准确抓住行业热点，成为 2025 年 AI 领域的现象级话题，精准抓住"国产 AI"标签与行业热点，邀请码机制（限量发放）制造稀缺性，创始人通过简洁演示快速传递产品价值。

为了让读者对 Agent 能够有系统的认识，同时也可以对 Agent 的认识完成一次祛魅的过程，本篇文章结构为：

1. **认识**：对 AI Agent 相关的一些组成进行原理性解释
2. **设计**：基于 OpenManus 构建自己的 MyManus，落地和验证认识中的一些概念和原理
3. **实验**：基于 MyManus 进行验证，对当前的 Agent 存在的问题有个直观的感受
4. **改进**：结合前面的实验以及 Agent 当下的问题，探讨未来的方向和改进方案

## 认识

结合 Agent 相关的几篇关键文章和论文，梳理下基于 LLM 的 AI Agent 的设计模式以及一些原理性的概念。ATA 上关于 LLM 和 Agent 的原理性的优质文章太多，这里主要涉及 Manus 或 OpenManus 用到的部分。

### AI Agent 正在重新定义软件服务

#### 你只需要告诉我你要什么，不要告诉我怎么做

AI Agent 将使软件架构的范式从面向过程迁移到面向目标，就像传统面向过程的工作流和 K8S 的声明式设计模式一样。当然这两种解决的问题是不一样的：K8s 通过定义期望状态而非具体步骤来管理集群，降低集群状态管理的复杂度，确保集群的稳定性和容错性。Agent 之前，传统的软件架构只能解决有限范围的任务，而基于 Agent 的架构可以解决无限域的任务，实现真正意义上的个性化服务。

![ProAgent: From Robotic Process Automation to Agentic Process Automation](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwoXHZIhTzIodFjTO89Mq2xXG6leCvmVjTJGkVdYAhkLIwbohlsopC37w/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

我们可以从 Manus 的官方网站看到，Manus 宣称可以做如下的事情，并提供了相当丰富的案例：

- **数据分析**：分析店铺销售数据，制定改进策略等
- **教育**：互动课程，学习资源收集，宇宙探索等
- **生活**：保险策略对比，租赁合同分析，旅行计划等
- **效率**：合同审查，简历筛选，网站 SEO 优化等
- **研究**：财报分析，政策研究

#### AI Agent 的核心要素

不同的机构或团队对 Agent 的架构模块划分略有差异，但基本上包含了以下四个核心要素：

- **感知**：接收和处理外部信息
- **记忆**：存储和管理历史信息
- **规划**：制定和执行任务计划
- **行动**：执行具体操作

此外，部分团队还涉及以下特色模块：

- **定义**：管理 Agent 角色特性
- **学习**：预训练、小样本学习
- **认知与意识**：思考、整体认知

![AI Agent架构模块](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwo0ssKpzHcgbbzic8Qcia7ye10nfWtkicAuDsUA3TpqLaYA67aWdQDD53AA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

<div style="text-align: center;margin: -16px 0 16px 0;">_内容来源：华泰证券研究所_</div>

Lilian Weng（翁荔）的《LLM Powered Autonomous Agents》这篇博客被广泛认为是"AI Agent 领域最权威的结构化综述之一"，为开发者提供了技术框架参考。作者将 AI Agent 定义为"规划 + 记忆 + 工具调用"的组合，强调 LLM 作为系统的核心控制器：

- **规划（Planning）**：任务分解、子任务生成及自我反思
- **记忆（Memory）**：长期记忆存储与上下文管理，用于处理复杂任务
- **工具使用（Tool Usage）**：通过 API 或外部工具增强 Agent 的能力（如搜索、文件操作，代码执行等）

![LLM Powered Autonomous Agents架构](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwo6o6of9ib6Yy5Yib7rgTvWOrYnkWPiagN641dQSUbs7EQzCpUNbkOJ8kVw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

## 设计

接下来围绕 Agent 几个核心要素进行设计，会先简单介绍一些基本的原理，然后基于 OpenManus 做二次设计或者展示其原来的实现。

### LLM

在这之前概括下 LLM 的一些基本的原理，关于 LLM 的原理性文章已经很多了，这里只对 LLM 的推理原理做个简单回顾。

当下的 LLM 的核心依然是基于神经网络，相比传统的神经网络 CNN/RNN 等，Transformer 架构通过自注意力机制允许模型直接计算任意两个位置之间的关系，从而更高效捕捉长距离依赖，使得 LLM 有更强大的多层叠加能力。Transformer 的并行计算能力（如自注意力的矩阵运算）同时加速了训练速度，支持更大的模型规模。另外通过多层非线性激活函数（如 ReLU、GeLU）可学习更加复杂模式，随着参数规模和训练数据增加，LLM 会突现传统神经网络难以实现的能力（如逻辑推理、代码生成），LLM 具备了涌现能力！（也许这就是量变产生了质变吧）

LLM 的推理简单理解为是一个"模式匹配 + 概率计算"的过程，通过 Transformer 架构和自回归生成，基于海量文本学习到的统计规律，逐步生成符合语言习惯的输出。其效果依赖于训练数据的质量、模型规模以及生成策略的选择。每一步生成都依赖于已生成的上下文，即通过已知的前序词预测下一个词，当前 LLM 具备上下文学习（In-Context Learning）能力，LLM 通过 Prompt 中提供的示例或指令，无需参数更新即可适应新任务，依然是在于利用模型的模式匹配能力和统计规律，Transformer 架构中，Prompt 的 token 位置靠前，权重更高，对后续生成的影响更大。

LLM 的涌现能力使其具备复杂任务处理能力，但同时也因训练数据的噪声和统计生成特性，容易产生幻觉。RAG 通过引入外部知识减少幻觉，SFT 微调通过高质量数据优化输出，Agent 通过工具调用增强交互能力。这些方法可在一定程度上缓解幻觉，增强可解释性，但可解释性仍受限于 LLM 的黑箱特性。Agent 设计中，Prompt 是核心组件之一，所有的设计都是围绕构建和管理 Prompt，需结合工具调用、记忆管理等模块设计。为适应不同任务，Prompt 需精细化设计并管理多个版本。

### Memory

前面了解到，LLM 本质上就是一个具有数十亿到千亿级别参数的无状态函数，比如可以这样：

![LLM无状态函数示意图](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwoJTlvvM05gdlaP9pevC0vSMq7ib9BbkJo8Jk7mB356SvicYJ5U27GucLg/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

LLM 就像一个失忆的绝世高手一样，虽然没有记忆，但可以武功还在，LLM 回复完全基于输入的提示（prompt）和训练数据中的模式，通常我们所说的记忆是指的是用户输入提示，分为短期记忆和长期记忆。

LLM 的"短期记忆"通常依赖于其上下文窗口（最大 Token 限制），通过在输入中包含当前对话或任务的相关信息来维持连贯性。LLM 的一些生产参数比如 Temperature，Top-P 可以影响其基于上下文生成文本内容。Temperature 主要是影响生成的确定性，是通过控制 Temperature 实现生成内容的准确性与创造性二者之间的权衡。Top-P 主要是发散程度，在聚焦和多样性之间的平衡。

长期记忆依赖于外部组件，虽然 LLM 的预训练参数"存储"了知识，通常已经过时，特定领域的知识，需外部技术（如 RAG）补充长期依赖关系。短期记忆也可以转变为长期记忆，这个对 Agent 的自主进化很有帮助。

我们设计一个简单的短期记忆模块，记录推理和外部感知的结果信息，每次调用 LLM 时都会带上（受限于 LLM 的最大 Token），这样 LLM 就会在每次推理时"记住"之前的推理过程，以及外部工具感知的结论。相当于：每次你问问题，都要讲一遍前面的交流内容。定义 Memory 类，记录每次的 Message 内容。

```python
class Memory(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    max_messages: int = Field(default=100)
```

以下是 Memory 内容例子

```python
{
  "messages": [
    {
      "role": "user",
      "content": "\n        CURRENT PLAN STATUS:\n        Plan: QuickSort Implementation Plan (ID: plan_1742277313)\n==========================================================\n\nSteps:\n1. [→] {'step_name': 'Research and understand the QuickSort algorithm', 'status': 'in_progress', 'notes': ''}\n2. ...",
      "tool_calls": null,
      "name": null,
      "tool_call_id": null
    },
    {
      "role": "user",
      "content": "You can interact with the computer using PythonExecute, save important content and information files through FileSaver, open browsers with BrowserUseTool, and retrieve information using GoogleSearch.\n\nPythonExecute: ...",
      "tool_calls": null,
      "name": null,
      "tool_call_id": null
    },
    {
      "role": "assistant",
      "content": "",
      "tool_calls": [
        {
          "id": "call_294a4ff7396f4c91813990",
          "type": "function",
          "function": {
            "name": "google_search",
            "arguments": "{\"query\": \"QuickSort algorithm explained\"}"
          }
        }
      ],
      "name": null,
      "tool_call_id": null
    },
    {
      "role": "tool",
      "content": "Observed output of cmd `google_search` executed:\n['https://www.w3schools.com/dsa/dsa_algo_quicksort.php']...",
      "tool_calls": null,
      "name": "google_search",
      "tool_call_id": "call_294a4ff7396f4c91813990"
    },
    {
      "role": "user",
      "content": "You can interact with the computer using PythonExecute...",
      "tool_calls": null,
      "name": null,
      "tool_call_id": null
    },
    {
      "role": "assistant",
      "content": "I have researched the QuickSort algorithm using a Google search. Here are some resources that can help us understand how it works...",
      "tool_calls": null,
      "name": null,
      "tool_call_id": null
    }
  ]
}
```

### Tools

人类创造、修改和利用外部物体来做超出人类身体和认知极限的事情，为 LLM 配备外部工具可以显著扩展模型功能和应用场景。

Agent 的工具调用，实际上是借助 LLM 的能力，LLM 需要先理解工具的功能和参数格式。

![Tool Learning with Large Language Models: A Survey](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwoczCtsdTjvYfRGCEqNuLcw0YRBTsQh7QAzmpBfe97HbCJEkicgD0VpKA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

上图可以简单概括为：

1. 你有一系列工具，同时有比较详细的说明书。你拿着说明书找 LLM 问一个 LLM 自身推理无法（准确）完成的问题，比如：今天几号，天气怎么样，当前数据库内容是什么。这些预训练的 LLM 是无法感知到的，需要借助外部工具。

2. LLM 会从你的工具说明书列表中选工具，准确地告诉你你应该用哪个工具，同时把输入参数也给你（基于说明书描述）。

3. 你拿到后调用工具，获取感知信息，然后再把结果信息给到 LLM。

4. LLM 判断输出结果，并继续回答你之前的问题。

### Planning

#### 1. Planning 的核心组件

Lilian Weng 在其博文中将 Planning 分为四个关键子模块：

- **Reflection（反思）**：评估执行结果并调整策略
- **Self-critics（自我批评）**：对决策进行自我评估
- **Chain of thoughts（思维链）**：通过连续推理解决问题
- **Subgoal decomposition（子目标分解）**：将复杂任务拆分为可管理的子任务

Planning 的核心是将任务分解为可执行的步骤，并根据反馈不断优化计划。例如，通过子目标分解将大任务拆解为小任务，通过反思评估结果并调整策略。

#### 2. Planning 的实现方式

目前有多种实现 Agent Planning 能力的方法：

1. **Reason + Act（ReAct）**：推理-行动-反馈循环
2. **Plan-and-Solve（PS）**：规划-执行模式
3. **Tree of Thoughts（ToT）**：多方案并行思考
   - 示例提示词："生成 3 种不同预算方案，总预算不超过 10 万元，并列出每个方案的子任务"
4. **基于角色的多 Agent（MetaGPT）**：多智能体协作

#### 3. ReAct 模式详解

ReAct 通过 LLM 交替执行推理和行动，实现了推理与外界感知的协同：

- **推理**：帮助模型推断、跟踪和更新行动计划，处理异常
- **行动**：与外部资源（如知识库或环境）交互，获取额外信息

![ReAct: Synergizing Reasoning and Acting in Language Models](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwod8f38I7wPw7ahR1w5sjP2kfT2ib3rQEO82uHQv2P3RSNibqGZTENdQYw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

#### 4. ReActAgent 流程设计

ReActAgent 实现了重复的 Thought-Action-Observation 循环，其退出机制有两种：

1. **最大步数限制**：当执行步骤超过预设的最大步数时退出
2. **终止工具调用**：当 LLM 调用终止工具时退出循环
   - 终止工具描述："When you have finished all the tasks, call this tool to end the work"

![ReActAgent 流程](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwoWNZNEqWib1r7d7sFEqnzbbdoV0CgZbvEkvxZFLL322aHKWla8dw8C5w/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

设计 ReAct 抽象类，由主体的 Agent 继承， 包含 llm 和 memory，同时有 think 和 act 两个阶段的操作，think 通过调用 LLM 进行推理， act 主要是调用工具获取额外的信息。 通过 step 串联， step 由 Agent 重复调用，每次都会通过 LLM 的推理判断是否需要调用工具。

```python
class ReActAgent(BaseModel, ABC):
    name: str = Field(..., description="Unique name of the agent")
    description: Optional[str] = Field(None, description="Optional agent description")
    # Prompts
    system_prompt: Optional[str] = Field(
        None, description="System-level instruction prompt"
    )
    next_step_prompt: Optional[str] = Field(
        None, description="Prompt for determining next action"
    )
    # Dependencies
    llm: LLM = Field(default_factory=LLM, description="Language model instance")
    memory: Memory = Field(default_factory=Memory, description="Agent's memory store")

    @abstractmethod
    async def think(self) -> bool:
        """Process current state and decide next action"""

    @abstractmethod
    async def act(self) -> str:
        """Execute decided actions"""

    async def step(self) -> str:
        """Execute a single step: think and act.
            Thought: ...
            Action: ...
            Observation: ...
            ... (Repeated many times)
        """
        should_act = await self.think()
        # 判断是否使用工具
        if not should_act:
            return "Thinking complete - no action needed"
        return await self.act()
```

**`Plan-and-Solve`**

Chain-of-Thought（CoT）使 LLMs 能够明确地生成推理步骤并提高它们在推理任务中的准确性。比如 Zero-short-CoT 将目标问题陈述结合"让我们逐步思考"这样的提示词，作为 LLM 的输入。这是一种隐式生成推理链，具有一定的模糊性，存在语义理解错误，无法生成合理的计划等问题。

Plan-and-Solve 是一种改进的 CoT 提示方法，通过显式分解任务为子目标并分步执行，提升复杂任务的推理能力。Plan-and-Solve 将传统的"黑箱"推理操作，进一步转化为结构化流程，使得 Agent 的可解释性增强，而且还可以动态调整和反思。是 Agent 实现 Planning 能力的很好的技术支撑。

![Plan-and-Solve流程图](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwogX2R35icI0LicObT1583jqOLicY99icfjAqLOVEmr6onlzPnWic64Er32uw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

**`参考 Plan-and-Solve 论文设计 Planner`**

![Planner 设计图](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwo0xe7aQnVwlBYyNc6QvgAcrHVx89smGqrOou9ZicNLAlL96bloamjpqQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

## Agent 实现

我们已经完成了 Agent 的核心模块实现，包括：

- Memory
- Tools
- Planning

目前还缺少 LLM 模型调用部分。值得庆幸的是，目前各大云厂商和模型部署工具（如 Ollama、vLLM 等）都兼容 OpenAI 的 API 接口，这在一定程度上实现了统一。

### MyManus 项目

基于 OpenManus 项目，我们开发了 MyManus。为了便于理解和后续扩展，我们做了以下改进：

1. **依赖关系优化**

   - 简化了 Tools、ReActAgent、Planning 之间的依赖关系
   - 保持与 OpenManus 工具的完全兼容性

2. **Planning 实现优化**

   - 简化了 Planning 实现
   - 移除了多 Plan 调度逻辑
   - 暂时移除了多 Agent 支持（计划后续添加）
   - 注：最新版 OpenManus 已将 PlanningAgent 移除，Planning 功能移至 flow 中

3. **新增功能**
   - **EventListenerManager**：用于跟踪核心模块间的协同事件，优化 WebUI 展示
   - **数据开发工具**：
     - **DatabaseTool**：支持数据库执行和查询操作，用于验证 Agent 的数据处理能力
     - **Jupyter Notebook Client**：支持远程执行 Python 代码和指令，可用于管理敏感密钥信息

### 整体架构设计

![整体架构图](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwoFcIB8cZUK59M7WGzuGFJ7xbaU0FdJoDeRNntoBCiaHPIIFiagdAlDDqA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

### Prompt

到这里， 你会发现前面的 Memory，Tools，Planning 每一部分，其实都是在解决最核心的问题：如何在正确阶段构建最佳的 Prompt，印证了 LLM 部分描述提示词的重要性。 所以 Prompt 非常重要， 如果你发现 Agent 效果不好， 可以先从优化提示词开始。

系统的提示词，某种程度上决定了 LLM 对 Agent 的特质和能力判断， 比如借助 LLM 生成计划，如果没有设计系统的提示词，LLM 根据用户的输入，会生成完全无关的计划，思考的域越大，效果会越差。 Openmanus 里面的计划系统提示词，就很明确地告知 LLM 的如何执行计划，如何使用工具等。

每一步的提示词，决定 LLM 如何使用工具， 比如我希望 LLM 优先使用 RemoteJupyterClient，可以重点强调其作用，尤其是加了 You Can also use pip install packages when package not found 这一句，LLM 可以生成 pip 命令，自动安装包。

Planning

```
PLANNING_SYSTEM_PROMPT = """
You are an expert Planning Agent tasked with solving problems efficiently through structured plans.
Your job is:
1. Analyze requests to understand the task scope
2. Create a clear, actionable plan that makes meaningful progress with the `planning` tool
3. Execute steps using available tools as needed
4. Track progress and adapt plans when necessary
5. Use `finish` to conclude immediately when the task is complete


Available tools will vary by task but may include:
- `planning`: Create, update, and track plans (commands: create, update, mark_step, etc.)
- `finish`: End the task when complete
Break tasks into logical steps with clear outcomes. Avoid excessive detail or sub-steps.
Think about dependencies and verification methods.
Know when to conclude - don't continue thinking once objectives are met.
"""
```

ManusAgent

```
SYSTEM_PROMPT = "You are OpenManus, an all-capable AI assistant, aimed at solving any task presented by the user. You have various tools at your disposal that you can call upon to efficiently complete complex requests. Whether it's programming, information retrieval, file processing, or web browsing, you can handle it all."

NEXT_STEP_PROMPT = """You can interact with the computer using PythonExecute, save important content and information files through FileSaver, open browsers with BrowserUseTool, execute python code with RemoteJupyterClient and retrieve information using GoogleSearch.

PythonExecute: Execute Python code to interact with the computer system, when RemoteJupyterClient not work, try use this.

RemoteJupyterClient: Execute Python code on a remote Jupyter Server to data processing, automation tasks, etc. You Can also use pip install packages when package not found.

FileSaver: Save files locally, such as txt, py, html, etc.

BrowserUseTool: Open, browse, and use web browsers.If you open a local HTML file, you must provide the absolute path to the file.

GoogleSearch: Perform web information retrieval

Terminate: End the current interaction when the task is complete or when you can do nothing.

Based on user needs, proactively select the most appropriate tool or combination of tools. For complex tasks, you can break down the problem and use different tools step by step to solve it. After using each tool, clearly explain the execution results and suggest the next steps.

Always maintain a helpful, informative tone throughout the interaction. If you encounter any limitations or need more details, clearly communicate this to the user before terminating.
"""
```

tools

```
SYSTEM_PROMPT = "You are an agent that can execute tool calls"

NEXT_STEP_PROMPT = (
    "If you want to stop interaction, use `terminate` tool/function call."
)
```

## 实验

### 实验验证

为了验证前面实现的 Agent 系统，我们进行了以下场景的实验。所有实验都通过 WebUI 进行观察，Planning 和 ReAct Agent 均使用 qwen-max-latest 作为底层 LLM。

#### 实验一：快速排序实现（无计划模式）

**实验过程：**

- Agent 快速生成了排序算法实现
- 直接给出结果并等待下一步指示
- 由于缺乏额外指令，LLM 虽然热情但无法感知具体需求
- 最终仅使用 JupyterClient 验证了代码正确性

**实验截图：**

![实验一截图](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJoEbAbAwrosBuT1ASJPq2H6p0ABm9lnUwGhG8DlSvmg79vp6yccfmobVERgpdicsqBO3PmPcdw09w/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

#### 实验二：快速排序实现（有计划模式）

**实验过程：**

- Planning Agent 将任务拆分为 9 个具体步骤
- 总用时约 6 分钟
- 综合运用多个工具：
  - Google Search：搜索算法实现参考
  - PythonExecutor：本地代码执行
  - JupyterClient：远程代码运行
  - FileSave：保存代码和报告
- 最终成果：
  - 完整的快速排序实现代码
  - 详细的性能测试报告
  - 增强了代码的可解释性

**实验截图：**

![实验二截图](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJoEbAbAwrosBuT1ASJPq2HWdM8n1YY4TEBAkFfiaiby0O4aJZtdTQRB7KrFGgYwMI8HJ0Pq1wcA7CA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

### 实验三：销售数据分析（无计划模式）

**实验目标：**
分析 2009 年销售额最高的销售代理

**实验过程：**

- LLM 自主规划并执行了以下步骤：
  1. 查看数据库表结构
  2. 分析相关数据表
  3. 执行 SQL 查询
- 最终成功得出正确结果

**实验结论：**
即使在无计划模式下，LLM 也展现出了良好的自主规划能力，能够独立完成数据分析任务。

**实验截图：**

![实验三截图](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJoEbAbAwrosBuT1ASJPq2H7g6cAz1qiaCicibcdYewqp0GNLOl6pYUiaVFewaIcd0NPzDeeH3FhQQ0mQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

### 实验四：杭州天气数据分析（有计划模式）

**实验目标：**
分析并可视化杭州最近 7 天的天气数据

**实验过程：**

1. **数据获取尝试**

   - LLM 尝试使用工具爬取结构化天气数据
   - 数据获取失败，调用了 Terminate 工具结束任务

2. **任务继续执行**

   - ReAct Agent 未将失败视为终止条件
   - Planning 继续执行后续步骤
   - LLM 出现幻觉，从历史数据中获取数据

3. **数据可视化实现**
   - LLM 充分利用 JupyterClient 工具
   - 编写并远程运行代码
   - 遇到包缺失时，通过 PIP 安装所需包
   - 成功创建新工具并完成可视化

**实验结论：**
展示了 Agent 系统在遇到障碍时的灵活性和创造性，能够通过工具扩展来解决问题。

**实验截图：**

![实验四截图](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJoEbAbAwrosBuT1ASJPq2H4mC3wlpNsjicUN0D6qlMkt8ApBGc1ANyia4tOicoPRbSRW0gghupsUC9w/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

```
# Action
🚀 Manus is about to execute 1 tools: [ChatCompletionMessageToolCall(id='call_6284438a03d74103b16fc7', function=Function(arguments='{"code":"import sys\\n!{sys.executable} -m pip install matplotlib"}', name='remote_jupyter'), type='function', index=0)]
# Using Tool
🔧 Activating tool: 'remote_jupyter' args:{'code': 'import sys\n!{sys.executable} -m pip install matplotlib'}
```

### 实验总结

通过以上实验，我们可以得出以下关键发现：

1. **ReAct 模式特点**

   - 对 LLM 依赖度高
   - 执行效率较高
   - 输出结果简洁直接

2. **Plan and Solve 模式特点**

   - 可解释性更强
   - 计划可能滞后于实际情况
   - 常导致 ReAct 在单个计划步骤内完成所有任务

3. **工具依赖问题**

   - Agent 对工具能力依赖度高
   - 需要设计"兜底逻辑"
   - 防止 LLM 产生幻觉

4. **技术限制**

   - 复杂任务可能超出 LLM 上下文限制
   - 影响任务连续性

5. **结果可靠性**
   - 执行结果不稳定
   - 代码/SQL 可能正确但结论错误

## 改进

### 自主化演进

#### 自我批判

通过实验观察，LLM 的规划能力能够帮助 Agent 更好地完成复杂任务。在任务规划方面，系统正在从基于规则和参数的规划能力逐步向基于环境的感知、实践反思和迭代进化方向发展。

ReActAgent 虽然具备一定的感知、反思和迭代能力，但在处理复杂任务时仍显不足，且可解释性低于 PS 模式。目前 Planning 存在两个主要问题：

1. 依据不足：LLM 容易出现幻觉，导致步骤过多，需要在执行计划前获取更多信息
2. 缺乏动态调整：计划执行过程中无法及时调整，需要具备动态改进计划的能力

#### 代码即为工具

在工具使用与选择方面，系统正在向多工具选择规划方向进化，甚至能够创造适用于 LLM 的工具。LLM 创造工具的能力主要依赖于其编码能力。例如，Manus 团队在讨论是否使用 MCP 时，受到 CodeAct 启发，将代码执行视为解决问题的工具而非目标，正如"太极生两仪，两仪生四象，四象生八卦"所阐述的哲学思想。

![自主化演进示意图](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwozu1icM9gdgnRvW8SbiaLjuibSoJ4GqSh9D1hjxTH2E8gNibqcIlHkib6s1g/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

<p align="center"><em>Executable Code Actions Elicit Better LLM Agents</em></p>

### 自我成长：Agent 经验积累与改进

#### 上下文长度限制与注意力问题

ReAct Agent 通过 Thought-Action-Observation 循环迭代完成任务。随着交互次数增加，上下文长度会显著增长。以 Qwen-Max 为例，其 32K 的上下文长度在处理复杂任务时仍显不足。长上下文不仅影响性能，还会导致 LLM 注意力分散，容易忽略中间信息。

![Lost in the Middle: How Language Models Use Long Contexts](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwoIfVLIR7SPYbVdRo2hrsEToRxjWTFicE0AUs9uoIkkbCnELCqia7V6YbQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

#### 记忆管理策略

Agent 需要高效的记忆管理机制，避免"回忆一生"的低效行为。建议：

1. 结合 RAG 技术构建长期记忆
2. 区分短期工作记忆和长期记忆
3. 基于用户行为优化记忆存储
4. 参考 MemGPT 和 Mem0 的设计思路

![Mem0 Memory Operations](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwoQv4DWnpoZ5FCicO5xv7n68AUQLrzUia72S0BSlKH4icXFN5fA1XCrTDrg/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

### Agent 评估与协作

#### 自我学习能力评测

Anthropic 建议：必须建立结果评估机制。推荐使用 StreamBench 项目进行评测。

![StreamBench](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwopWmicCGpCGibkvgCzL82A6OQjk25JN1mNj9s2aQbBXZr3CFb58AvueIA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

![ChatDev](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwoNAgoLCXcdFP6rPiae4tiaWeBrQKibYRQpaOyTbwmac4D4ouCGZTruY9hw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

#### 多智能体协作

吴恩达提出的四个 Agent 设计模式：

- Reflection
- Tool Use
- Planning
- Multi-Agent Collaboration

多智能体协作优势：

- 提高任务执行效率
- 实现复杂问题分解
- 优化上下文管理

挑战：

- 系统复杂度增加
- 需要解决协作机制
- 信息共享与隐私保护
- 多智能体学习问题

![Why Do Multi-Agent LLM Systems Fail?](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwozPsPnzHvia6hRU2Nicf1Cp7EP0pfqS2dhvHic7dSpSUgB65I3YGxtbvPQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

### 规划问题优化

针对 Planning 的局限性，Google 提出 PlanGEN 框架，包含三个核心组件：

1. 约束
2. 验证
3. 选择智能体

![PlanGEN Framework](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwowrmL8jbLHC1Cw1MYjt7ibvM17j2hwBTQMB9rWgFnck0QMgbzhMCjbvw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

### 协作涌现研究

参考论文《Scaling Large-Language-Model-based Multi-Agent Collaboration》(https://arxiv.org/abs/2406.07155)探讨了协作涌现现象，类比神经网络规模法则，研究增加智能体数量是否会产生新的能力涌现。

## MCP

![MCP架构图](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwowTZXaP0sQ2IHY0XHw10BZJ7PEKNwc4VyMd4kV43r8SyWSBUZsaUrxw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

### MCP 简介

MCP（Model Context Protocol）是由 Anthropic 公司提出的一种协议，其核心动机在于显著提升 AI 模型（如 Claude）与外部系统之间的交互能力。通过开源的方式，MCP 不仅鼓励社区共同参与和完善这一协议，还旨在推动 AI Agent 生态的发展。从技术角度来看，MCP 的设计并不复杂，但其真正的力量来自于共识——这种共识使得不同系统间的协作成为可能，并为开发者提供了一种标准化的解决方案。

借助 MCP，Agent 只需一次接入即可无缝适配多种工具和服务，从而大幅减少碎片化开发的重复劳动。MCP 让一个 Agent 能够连接整个世界，实现跨系统的无缝集成能力。如果想追踪 MCP 当前的发展动态及其生态状况，可以关注[awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)项目，这里汇聚了全球开发者对这一领域的最新探索与贡献。

![MCP架构设计](https://mmbiz.qpic.cn/mmbiz_png/Z6bicxIx5naJnZenEDVcrQTPhxVAGuSwo4ib5VtqSpI0IrPxyDS0jpGZmu91dPjcyPxQVxPmeyS0BAia3ByP83mVQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1)

### 架构设计优势

在架构设计上，MCP 将 Host（Client）与 Server 分离，工具由 Server 端调用，而 Server 端则负责统一管控这些工具的使用，并对外提供服务。这种设计模式提高了系统的灵活性和可扩展性，对于云服务提供商来说或者 Dify 这种 LLMOps 中间价产品，是利好的，主要体现在以下几个方面：

#### 1. 服务复用

MCP 通过标准化工具集成流程，云厂商无需再为每个客户或场景单独开发接口，客户也不需要定制开发，而是可以直接复用现有的成熟服务模块。在保证功能完整性的同时，也降低了维护成本。

#### 2. 一站式平台构建

依托 MCP 的标准化协议，云厂商能够快速搭建起"一站式"AI 服务平台。例如，通过可视化管理界面和低代码工作流配置工具，用户无需深入理解底层技术细节，便可轻松完成复杂的任务部署。

#### 3. 工具生态整合

在 MCP 的支持下，客户不仅可以享受云厂商提供的专属工具，还能自由利用开源生态中的丰富资源，如数据库、浏览器自动化工具等。这些工具通过 Agent 进行统一调用，形成了一套协同的工作体系。云厂商因此得以借助开源社区的力量，避免从零开始开发，从而帮助用户加速 AI 应用的落地进程，这是一种共生关系。

#### 4. 合规与安全性保障

通过在 MCP Server 端实施权限管理、审计机制以及沙箱环境的构建，能有效减少敏感数据暴露的风险。例如，在 MyManus 中引入 JupyterClient 时，就是希望为代码执行其设计了一个受控的沙箱环境，允许单租户拥有专属的环境变量设置。

## 争议与展望

也有反对使用 MCP 的声音，比如 LangChain 发起了讨论，并对 MCP 是否是昙花一现发起了投票，有 40%的人认为是个未来的标准，20%的认为是昙花一现。具体讨论可以看[MCP: Flash in the Pan or Future Standard?](https://blog.langchain.dev/mcp-fad-or-fixture/)。

当下不能过于神化任何 AI 相关东西，MCP 解决不了 LLM 很多时候无法正确地使用工具问题，但还是值得投入研究的，"人们总是高估一项科技所带来的短期效益，却又低估它的长期影响"。AI 最大的机会可能在于改变现有的业务流程和产品，专注特定的小规模的业务场景，深入解决具体问题，而不是追求建立大型平台。

## 结语

在深入研读大量人工智能领域的学术论文和技术文献后，我深刻认识到：只有将理论知识付诸实践，转化为具体的代码实现和文字记录，才能真正体会到大型语言模型（LLM）所展现的独特魅力。这种从理论到实践的过程，不仅加深了对技术的理解，更是一场深入的思想对话。

Agent 相关的研究领域仍有广阔的发展空间，希望本文能为读者带来一些启发。即使未能达到预期效果，写作本身也是一种自我沉淀和逻辑梳理的过程，这种收获同样令人欣慰。

### 参考文献

1. [Tool Learning with Large Language Models: A Survey](https://arxiv.org/abs/2405.17935)
2. [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
3. [Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models](https://arxiv.org/abs/2305.04091)
4. [ChatDev: Communicative Agents for Software Development](https://arxiv.org/abs/2307.07924)
5. [Scaling Large-Language-Model-based Multi-Agent Collaboration](https://arxiv.org/abs/2406.07155)
6. [PlanGEN: A Multi-Agent Framework for Generating Planning and Reasoning Trajectories for Complex Problem Solving](https://arxiv.org/abs/2502.16111)
7. [A Survey on the Memory Mechanism of Large Language Model based Agents]
8. [Lost in the Middle: How Language Models Use Long Contexts](https://cs.stanford.edu/~nfliu/papers/lost-in-the-middle.arxiv2023.pdf)
9. [LLM Agents Use Cases & Risks](https://www.holisticai.com/blog/llm-agents-use-cases-risks)
