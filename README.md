# Bubbles

一款关于泡泡、种子与海底旅程的小型冒险解谜游戏。

你将操控一颗承载生命种子的泡泡，在海底关卡中穿过尖刺、墙体、气泡喷口与污染区域，收集资源并安全抵达叶片。泡泡数量与种子数量会共同影响浮力，如何释放种子、分裂泡泡、保存足够的生命力，是通关的关键。

## 启动游戏

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

## 操作方式

- `A` / `D` 或方向键左 / 右：水平移动
- `W` 或方向键上：向下释放一颗种子
- `S` 或方向键下：向上分裂一个泡泡
- `R`：重新开始当前关卡
- `Esc`：暂停游戏

## 游戏目标

- 从起始叶片出发，抵达目标叶片完成关卡。
- 收集野生种子和自由泡泡，调整自己的浮力与生存能力。
- 避开尖刺和危险区域，泡泡破裂后需要重新尝试。
- 通关关卡会推进地图进度，并记录你的星级表现。
- 收集足够的种子后，可以解锁新的海域分支。

祝你在海底慢慢漂，别把自己戳破。
