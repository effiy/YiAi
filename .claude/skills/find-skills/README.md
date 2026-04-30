# find-skills 快速索引

`find-skills` 在 `.claude/skills/` 下发现并推荐可用技能。真源在 `SKILL.md`。

## 快速开始

```bash
/find-skills <任务描述> [关键词1,关键词2,...]
```

## 使用原则

1. 只返回 `.claude/skills/` 下真实存在的技能目录名，禁止编造
2. 返回的技能名必须与目录名完全一致
3. 找不到匹配时输出"未找到合适技能"