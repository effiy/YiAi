## 会话管理命令表

| 功能           | 命令                                                              | 快捷键         | 说明                                     |
| -------------- | ----------------------------------------------------------------- | -------------- | ---------------------------------------- |
| 新建会话       | `tmux new -s <session-name>`                                      | `Ctrl+b :new`  | 创建一个指定名称的新会话                 |
| 分离会话       | `tmux detach`                                                     | `Ctrl+b d`     | 将当前会话与窗口分离，会话在后台继续运行 |
| 列出会话       | `tmux ls` 或 `tmux list-session`                                  | `Ctrl+b s`     | 显示当前所有的 Tmux 会话                 |
| 接入会话       | `tmux attach -t 0` 或 `tmux attach -t <session-name>`             | `Ctrl+b a`     | 重新连接到指定的会话                     |
| 杀死会话       | `tmux kill-session -t 0` 或 `tmux kill-session -t <session-name>` | `Ctrl+b x`     | 终止指定的会话                           |
| 切换会话       | `tmux switch -t 0` 或 `tmux switch -t <session-name>`             | `Ctrl+b (`/`)` | 在不同会话之间切换(前一个/后一个)        |
| 重命名会话     | `tmux rename-session -t 0 <new-name>`                             | `Ctrl+b $`     | 为指定会话设置新名称                     |
| 临时全屏       | `tmux resize-pane -Z`                                             | `Ctrl+b z`     | 将当前窗格临时全屏显示                   |
| 显示时间       | -                                                                 | `Ctrl+b t`     | 在当前窗格显示时间                       |
| 锁定会话       | -                                                                 | `Ctrl+b :`     | 锁定当前会话                             |
| 创建窗口       | `tmux new-window -n <window-name>`                                | `Ctrl+b c`     | 创建一个新窗口                           |
| 列出窗口       | -                                                                 | `Ctrl+b w`     | 显示所有窗口列表                         |
| 搜索窗口       | -                                                                 | `Ctrl+b f`     | 在所有窗口中搜索关键词                   |
| 同步窗格       | `tmux set-window-option synchronize-panes on/off`                 | -              | 开启/关闭窗格同步模式                    |
| 保存历史       | `tmux capture-pane -S - -E - -b buffer-name`                      | -              | 将窗格历史保存到缓冲区                   |
| 列出所有快捷键 | `tmux list-keys`                                                  | -              | 显示所有快捷键及对应命令                 |
| 列出所有命令   | `tmux list-commands`                                              | -              | 显示所有 Tmux 命令及参数                 |
| 显示会话信息   | `tmux info`                                                       | -              | 显示当前会话的详细信息                   |
| 重载配置文件   | `tmux source-file ~/.tmux.conf`                                   | -              | 重新加载指定的配置文件                   |

## 窗格管理命令表

| 功能               | 命令                             | 快捷键                    | 说明                         |
| ------------------ | -------------------------------- | ------------------------- | ---------------------------- |
| 划分上下窗格       | `tmux split-window`              | `Ctrl+b "`                | 将当前窗格分为上下两个       |
| 划分左右窗格       | `tmux split-window -h`           | `Ctrl+b %`                | 将当前窗格分为左右两个       |
| 关闭当前窗格       | -                                | `Ctrl+b x`                | 关闭当前所在的窗格           |
| 将窗格拆为独立窗口 | -                                | `Ctrl+b !`                | 将当前窗格拆分为一个独立窗口 |
| 显示窗格编号       | -                                | `Ctrl+b q`                | 短暂显示窗格编号             |
| 窗格全屏显示       | -                                | `Ctrl+b z`                | 当前窗格全屏/恢复原状        |
| 切换到上方窗格     | `tmux select-pane -U`            | `Ctrl+b ↑`                | 光标移到上方窗格             |
| 切换到下方窗格     | `tmux select-pane -D`            | `Ctrl+b ↓`                | 光标移到下方窗格             |
| 切换到左边窗格     | `tmux select-pane -L`            | `Ctrl+b ←`                | 光标移到左边窗格             |
| 切换到右边窗格     | `tmux select-pane -R`            | `Ctrl+b →`                | 光标移到右边窗格             |
| 切换到上一个窗格   | -                                | `Ctrl+b ;`                | 光标切换到上一个使用的窗格   |
| 切换到下一个窗格   | -                                | `Ctrl+b o`                | 光标切换到下一个窗格         |
| 当前窗格上移       | `tmux swap-pane -U`              | `Ctrl+b {`                | 当前窗格与上一个窗格交换位置 |
| 当前窗格下移       | `tmux swap-pane -D`              | `Ctrl+b }`                | 当前窗格与下一个窗格交换位置 |
| 所有窗格向前移动   | -                                | `Ctrl+b Ctrl+o`           | 所有窗格位置向前轮换         |
| 所有窗格向后移动   | -                                | `Ctrl+b Alt+o`            | 所有窗格位置向后轮换         |
| 调整窗格大小       | -                                | `Ctrl+b Ctrl+<arrow key>` | 按箭头方向调整当前窗格大小   |
| 创建新窗口         | `tmux new-window`                | `Ctrl+b c`                | 创建一个新窗口               |
| 创建命名窗口       | `tmux new-window -n <name>`      | -                         | 创建一个指定名称的新窗口     |
| 切换到上一窗口     | -                                | `Ctrl+b p`                | 切换到上一个窗口             |
| 切换到下一窗口     | -                                | `Ctrl+b n`                | 切换到下一个窗口             |
| 切换到指定窗口     | `tmux select-window -t <number>` | `Ctrl+b <number>`         | 切换到指定编号的窗口         |
| 切换到指定名称窗口 | `tmux select-window -t <name>`   | -                         | 切换到指定名称的窗口         |
| 窗口列表选择       | -                                | `Ctrl+b w`                | 显示窗口列表供选择           |
| 重命名窗口         | `tmux rename-window <new-name>`  | `Ctrl+b ,`                | 为当前窗口重命名             |
