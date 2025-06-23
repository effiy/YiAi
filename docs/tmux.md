# Tmux 终端复用器使用指南

> 作者：[阮一峰](https://www.ruanyifeng.com)  
> 日期：[2019 年 10 月 21 日](https://www.ruanyifeng.com/blog/2019/10/)

## 背景

### 会话与进程

在命令行环境中，我们通常通过终端窗口（terminal window，简称"窗口"）与计算机进行交互。这种交互过程被称为"会话"（session）。

会话的一个关键特性是：窗口与其内部运行的进程是紧密关联的。

当窗口打开时，会话开始；

当窗口关闭时，会话结束，其中的所有进程也会随之终止，无论它们是否完成运行。

这种情况在远程操作时尤为明显。例如，当你通过 SSH 连接到远程服务器并执行命令时，如果网络突然断开，再次连接后将无法恢复之前的操作状态。这是因为之前的 SSH 会话已经终止，其中的进程也随之消失。

**为了解决这个问题，我们需要一种机制来实现会话与窗口的"解绑"：即使窗口关闭，会话也能继续在后台运行，并在需要时重新连接到其他窗口。**

## 认知

### Tmux 的作用

Tmux 就是这样一个强大的终端复用器，它能够将会话与窗口完全分离，提供以下核心功能：

1. **多会话管理**：在单个窗口中同时运行多个会话，方便同时处理多个任务。
2. **会话持久化**：支持新窗口随时接入已存在的会话，确保工作不会因窗口关闭而中断。
3. **会话共享**：允许多个窗口同时连接到同一个会话，实现团队协作和实时共享。
4. **灵活布局**：支持窗口的垂直和水平拆分，提供更灵活的工作空间管理。

虽然 GNU Screen 也能提供类似功能，但 Tmux 在易用性、功能丰富度和性能方面都更胜一筹。

## 设计

### 前缀键

Tmux 的所有快捷键都需要通过前缀键（Prefix Key）来触发。默认的前缀键是 `Ctrl+b`，这意味着在执行任何 Tmux 快捷键之前，都需要先按下这个组合键。

例如，要查看帮助信息，需要：

1. 先按下 `Ctrl+b`
2. 再按下 `?` 键
3. 查看完帮助后，按 `q` 或 `ESC` 键退出

## 实践

### 启动与退出

启动 Tmux 的命令：

```bash
tmux
```

执行上述命令后，将启动一个 Tmux 窗口。窗口底部会显示状态栏，其中：

- 左侧显示当前窗口的编号和名称
- 右侧显示系统信息（如时间、日期等）

要退出 Tmux 窗口，可以使用以下任一方式：

1. 按下 `Ctrl+d` 组合键
2. 在命令行中输入 `exit` 命令

### Tmux 的最简操作流程：

1. 新建会话：`tmux new -s my_session`
2. 在 Tmux 窗口运行所需的程序
3. 按下快捷键 `Ctrl+b d` 将会话分离
4. 下次使用时，重新连接到会话：`tmux attach-session -t my_session`

## 八、参考链接

- [A Quick and Easy Guide to tmux](https://www.hamvocke.com/blog/a-quick-and-easy-guide-to-tmux/)
- [Tactical tmux: The 10 Most Important Commands](https://danielmiessler.com/study/tmux/)
- [Getting started with Tmux](https://linuxize.com/post/getting-started-with-tmux/)
