# Tmux 终端复用器使用指南

> 作者：[阮一峰](https://www.ruanyifeng.com)  
> 日期：[2019年10月21日](https://www.ruanyifeng.com/blog/2019/10/)

## 简介

Tmux 是一个强大的终端复用器（terminal multiplexer），它让开发者能够在单个终端窗口中同时管理多个会话。通过 Tmux，你可以：

- 在单个窗口中运行多个终端会话
- 在断开连接后保持会话运行
- 随时重新连接到已有会话
- 与团队成员实时共享终端会话
- 灵活地分割窗口进行多任务操作

这些特性使 Tmux 成为提升开发效率的必备工具。本文将详细介绍 Tmux 的使用方法。

## 一、Tmux 是什么？

### 1.1 会话与进程

在命令行环境中，我们通常通过终端窗口（terminal window，简称"窗口"）与计算机进行交互。这种交互过程被称为"会话"（session）。

会话的一个关键特性是：窗口与其内部运行的进程是紧密关联的。当窗口打开时，会话开始；当窗口关闭时，会话结束，其中的所有进程也会随之终止，无论它们是否完成运行。

这种情况在远程操作时尤为明显。例如，当你通过 SSH 连接到远程服务器并执行命令时，如果网络突然断开，再次连接后将无法恢复之前的操作状态。这是因为之前的 SSH 会话已经终止，其中的进程也随之消失。

为了解决这个问题，我们需要一种机制来实现会话与窗口的"解绑"：即使窗口关闭，会话也能继续在后台运行，并在需要时重新连接到其他窗口。

### 1.2 Tmux 的作用

Tmux 就是这样一个强大的终端复用器，它能够将会话与窗口完全分离，提供以下核心功能：

1. **多会话管理**：在单个窗口中同时运行多个会话，方便同时处理多个任务。
2. **会话持久化**：支持新窗口随时接入已存在的会话，确保工作不会因窗口关闭而中断。
3. **会话共享**：允许多个窗口同时连接到同一个会话，实现团队协作和实时共享。
4. **灵活布局**：支持窗口的垂直和水平拆分，提供更灵活的工作空间管理。

虽然 GNU Screen 也能提供类似功能，但 Tmux 在易用性、功能丰富度和性能方面都更胜一筹。

## 二、基本用法

### 2.1 安装

Tmux 需要手动安装，以下是各系统的安装命令：

```bash
# Ubuntu 或 Debian
sudo apt-get install tmux

# CentOS 或 Fedora
sudo yum install tmux

# Mac
brew install tmux
```

### 2.2 启动与退出

安装完成后，可以通过以下命令启动 Tmux：

```bash
tmux
```

执行上述命令后，将启动一个 Tmux 窗口。窗口底部会显示状态栏，其中：
- 左侧显示当前窗口的编号和名称
- 右侧显示系统信息（如时间、日期等）

要退出 Tmux 窗口，可以使用以下任一方式：
1. 按下 `Ctrl+d` 组合键
2. 在命令行中输入 `exit` 命令

```bash
exit
```

### 2.3 前缀键

Tmux 的所有快捷键都需要通过前缀键（Prefix Key）来触发。默认的前缀键是 `Ctrl+b`，这意味着在执行任何 Tmux 快捷键之前，都需要先按下这个组合键。

例如，要查看帮助信息，需要：
1. 先按下 `Ctrl+b`
2. 再按下 `?` 键
3. 查看完帮助后，按 `q` 或 `ESC` 键退出

## 三、会话管理

### 3.1 新建会话

Tmux 会自动为每个新会话分配一个数字编号（从 0 开始）。虽然可以通过编号来管理会话，但使用有意义的名称会让会话管理更加直观和高效。

```bash
tmux new -s <session-name>
```

### 3.2 分离会话

在 Tmux 窗口中，按下 `Ctrl+b d` 或者输入 `tmux detach` 命令，就会将当前会话与窗口分离。

```bash
tmux detach
```

执行后，就会退出当前 Tmux 窗口，但是会话和里面的进程仍然在后台运行。

查看当前所有的 Tmux 会话：

```bash
tmux ls
# 或
tmux list-session
```

### 3.3 接入会话

`tmux attach` 命令用于重新接入某个已存在的会话：

```bash
# 使用会话编号
tmux attach -t 0

# 使用会话名称
tmux attach -t <session-name>
```

### 3.4 杀死会话

`tmux kill-session` 命令用于杀死某个会话：

```bash
# 使用会话编号
tmux kill-session -t 0

# 使用会话名称
tmux kill-session -t <session-name>
```

### 3.5 切换会话

`tmux switch` 命令用于切换会话：

```bash
# 使用会话编号
tmux switch -t 0

# 使用会话名称
tmux switch -t <session-name>
```

### 3.6 重命名会话

`tmux rename-session` 命令用于重命名会话：

```bash
tmux rename-session -t 0 <new-name>
```

### 3.7 会话快捷键

常用会话快捷键：

- `Ctrl+b d`：分离当前会话
- `Ctrl+b s`：列出所有会话
- `Ctrl+b $`：重命名当前会话

## 四、最简操作流程

Tmux 的最简操作流程：

1. 新建会话：`tmux new -s my_session`
2. 在 Tmux 窗口运行所需的程序
3. 按下快捷键 `Ctrl+b d` 将会话分离
4. 下次使用时，重新连接到会话：`tmux attach-session -t my_session`

## 五、窗格操作

Tmux 可以将窗口分成多个窗格（pane），每个窗格运行不同的命令。以下命令都是在 Tmux 窗口中执行。

### 5.1 划分窗格

`tmux split-window` 命令用来划分窗格：

```bash
# 划分上下两个窗格
tmux split-window

# 划分左右两个窗格
tmux split-window -h
```

### 5.2 移动光标

`tmux select-pane` 命令用来移动光标位置：

```bash
# 光标切换到上方窗格
tmux select-pane -U

# 光标切换到下方窗格
tmux select-pane -D

# 光标切换到左边窗格
tmux select-pane -L

# 光标切换到右边窗格
tmux select-pane -R
```

### 5.3 交换窗格位置

`tmux swap-pane` 命令用来交换窗格位置：

```bash
# 当前窗格上移
tmux swap-pane -U

# 当前窗格下移
tmux swap-pane -D
```

### 5.4 窗格快捷键

常用窗格操作快捷键：

- `Ctrl+b %`：划分左右两个窗格
- `Ctrl+b "`：划分上下两个窗格
- `Ctrl+b <arrow key>`：光标切换到其他窗格
- `Ctrl+b ;`：光标切换到上一个窗格
- `Ctrl+b o`：光标切换到下一个窗格
- `Ctrl+b {`：当前窗格与上一个窗格交换位置
- `Ctrl+b }`：当前窗格与下一个窗格交换位置
- `Ctrl+b Ctrl+o`：所有窗格向前移动一个位置
- `Ctrl+b Alt+o`：所有窗格向后移动一个位置
- `Ctrl+b x`：关闭当前窗格
- `Ctrl+b !`：将当前窗格拆分为一个独立窗口
- `Ctrl+b z`：当前窗格全屏显示，再使用一次会变回原来大小
- `Ctrl+b Ctrl+<arrow key>`：按箭头方向调整窗格大小
- `Ctrl+b q`：显示窗格编号

## 六、窗口管理

除了将一个窗口划分成多个窗格，Tmux 也允许新建多个窗口。

### 6.1 新建窗口

`tmux new-window` 命令用来创建新窗口：

```bash
tmux new-window
# 新建一个指定名称的窗口
tmux new-window -n <window-name>
```

### 6.2 切换窗口

`tmux select-window` 命令用来切换窗口：

```bash
# 切换到指定编号的窗口
tmux select-window -t <window-number>

# 切换到指定名称的窗口
tmux select-window -t <window-name>
```

### 6.3 重命名窗口

`tmux rename-window` 命令用于为当前窗口起名（或重命名）：

```bash
tmux rename-window <new-name>
```

### 6.4 窗口快捷键

常用窗口操作快捷键：

- `Ctrl+b c`：创建一个新窗口
- `Ctrl+b p`：切换到上一个窗口
- `Ctrl+b n`：切换到下一个窗口
- `Ctrl+b <number>`：切换到指定编号的窗口
- `Ctrl+b w`：从列表中选择窗口
- `Ctrl+b ,`：窗口重命名

## 七、其他命令

一些其他有用的命令：

```bash
# 列出所有快捷键，及其对应的 Tmux 命令
tmux list-keys

# 列出所有 Tmux 命令及其参数
tmux list-commands

# 列出当前所有 Tmux 会话的信息
tmux info

# 重新加载当前的 Tmux 配置
tmux source-file ~/.tmux.conf
```

## 八、参考链接

- [A Quick and Easy Guide to tmux](https://www.hamvocke.com/blog/a-quick-and-easy-guide-to-tmux/)
- [Tactical tmux: The 10 Most Important Commands](https://danielmiessler.com/study/tmux/)
- [Getting started with Tmux](https://linuxize.com/post/getting-started-with-tmux/)

