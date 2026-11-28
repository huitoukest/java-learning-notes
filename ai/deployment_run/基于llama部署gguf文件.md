# 基于 llama.cpp 部署 GGUF 模型（Windows / Linux）

> **基准版本**：llama.cpp **b12810 / 1.1.0-dev**（本机二进制 `version: 1.1.0-dev (build 12810, commit ca123ba76)`）。下文所有参数名、默认值、别名均以该版 `--help` 为准；老版本的印象值（如 `-c` 默认 4096、`--port` 默认 8080）不要再套用。
>
> **示例文件**：主模型 `Qwen3-0.6B-Q4_K_M.gguf`（约 484 MB），LoRA 适配器 `checkpoint-100-f16.gguf`（约 10 MB，text2sql）。两者都在 `D:\tmp\llm` 根目录。
>
> **实测边界**：本机只用 **Windows + CPU 包**实测过 `llama-cli` / `llama-bench` / `llama-server` / LoRA 加载；`--list-devices` 返回 `(none)`，无 GPU。**Linux、GPU/CUDA/Vulkan/ROCm、macOS、Ollama、Llama GUI 均为“未在本机实测”**，只给官方文档可核的命令与写法。吞吐数字只作“能跑”示例，不是性能结论。
>
> **与微调篇的衔接**：本文件只讲“部署与参数”。GGUF 的转换、量化、LoRA 产出一律见同目录上一层级 `ai/fine-tuning/` 下的六篇微调笔记，尤其 [大模型lora微调学习06，基于llamacpp的模型量化.md](../fine-tuning/大模型lora微调学习06，基于llamacpp的模型量化.md)；本文不重复转换流程，只做指针与部署侧补充。

---

## 0. 30 秒选路

先按目的选入口，再跳到对应章节。

| 我想做什么 | 用哪个入口 | 直接看 |
| --- | --- | --- |
| 本机命令行聊几句、单轮问一句 | `llama-cli` | [§2.1](#21-单次对话llama-cli)、[§2.2](#22-多轮单轮退出读文件) |
| 给应用提供 HTTP / OpenAI 兼容 API | `llama-server` | [§2.3](#23-起服务健康检查openai-兼容调用webui) |
| 在浏览器里点着聊（不装第三方软件） | `llama-server` 内置 Llama Chat | [§8.1](#81-内置-webuillama-chat) |
| 用图形启动器配置参数、管理模型 | 第三方 Llama GUI | [§8.2](#82-第三方-llama-gui可选) |
| 装好即用、自动管模型（不关心细粒度参数） | Ollama | [§9](#9-ollama-运行-gguf) |
| 榨干本机硬件、多卡/投机/高并发 | CLI 或 server + 性能参数 | [§3](#3-本地高性能运行) |
| 叠加微调出来的 LoRA | `--lora` / `--lora-scaled` | [§10](#10-lora-部署要点) |
| 报错了、端口连不上、输出乱码 | 排错表 | [§11](#11-排错表) |

> 路径约定先记住一条：**通用命令只写一份**（[§2](#2-通用启动命令windows--linux-同一份)），Windows / Linux / GPU / macOS 的差异各自单列，不重复整条命令。

---

## 1. 部署前：文件、入口、版本

### 1.1 目录与文件

| 用途 | 本机实际路径 | 文档通用段写法 |
| --- | --- | --- |
| 工作根目录 | `D:\tmp\llm` | `./`（即 cwd） |
| 主模型 | `D:\tmp\llm\Qwen3-0.6B-Q4_K_M.gguf` | `./Qwen3-0.6B-Q4_K_M.gguf` |
| LoRA 适配器 | `D:\tmp\llm\checkpoint-100-f16.gguf` | `./checkpoint-100-f16.gguf` |
| 二进制（Windows） | `D:\tmp\llm\llamacpp\bin\*.exe` | 裸命令名 `llama-cli` 等（假设 `bin` 在 PATH） |
| 二进制（Linux 示例） | `/opt/llama/llama-b12810/` | 同上 |

> 通用段一律用 `./Qwen3-0.6B-Q4_K_M.gguf` 且 cwd = 模型所在目录；平台段给出真实路径映射。

### 1.2 三个入口 + 统一入口 `llama.exe`

| 二进制 | 作用 | 注意 |
| --- | --- | --- |
| `llama-cli` | 单进程命令行对话/单轮推理 | 不对外提供 HTTP API |
| `llama-server` | OpenAI 兼容 REST 服务 + 内置 WebUI | 并发、连续批处理、`/health`、`/v1/chat/completions` |
| `llama-bench` | 基准测试 | 输出 pp/tg 表，用于选参数 |
| `llama.exe` | **v1.1.0 新统一入口（multitool）** | 子命令：`serve`、`cli`、`download`、`version`、`licenses`、`help` |

`llama.exe` 是新的统一入口，`llama serve` ≈ `llama-server`、`llama cli` ≈ `llama-cli`；旧二进制 `llama-server.exe` / `llama-cli.exe` 仍在 `bin/` 中且可独立运行。本机实测 `llama.exe serve --help` 与 `llama-server --help` 同构，`--port` 行同为 `9931`。本文示例以独立的 `llama-cli` / `llama-server` 为主，读者用统一入口时把命令名换成 `llama cli` / `llama serve` 即可。

### 1.3 一次能跑通的判断

部署前先用三条命令确认二进制与设备，别急着写业务命令。

```shell
llama-cli --version
llama-cli --list-devices
llama-cli --help
```

- `--version`：确认 `b12810` / `1.1.0-dev`，别拿旧版文档对参数（本机实测退出码 0）。
- `--list-devices`：打印可用后端设备；本机输出 `Available devices:\n  (none)`，说明 CPU 包没检测到 GPU。GPU 机器会列出设备名，再决定 `-ngl` / `-dev`。
- `--help`：本文参数速查（[§4](#4-参数速查通用)）只收部署常用项，全部参数以本版 help 为准；落盘办法见 [§12](#12-附版本与参数获取)。

---

## 2. 通用启动命令（Windows / Linux 同一份）

> **平台写法约定（先读这段）**：以下命令宿主为 **PowerShell 7 / bash**，命令用裸名（`llama-cli` / `llama-server` / `llama-bench`），假设 `bin` 目录已加入 PATH。续行：bash 用 `\`；PowerShell 7 用反引号（`` ` ``）或单行；cmd 用单行。下面通用块为可读性用 `\`，Windows 读者按此替换。JSON 一律用单引号包裹，避免 PowerShell 把双引号拆散。cwd = 模型所在目录，模型写作 `./Qwen3-0.6B-Q4_K_M.gguf`。平台差异只写在 [§5](#5-windows-差异)–[§7](#7-gpu--macos-差异)，这里不重复。

### 2.1 单次对话（llama-cli）

```shell
llama-cli -m ./Qwen3-0.6B-Q4_K_M.gguf \
  --reasoning-budget 0 \
  --chat-template-kwargs '{"enable_thinking": false}' \
  -p "你是小助手" -n 256 -st
```

- `-m`：主模型路径；`-p`：起始提示词；`-n 256`：单次最多生成 256 token（默认 `-1` 无限）。
- `-st`：单轮模式，答完即退出；不加则进入交互对话（本版默认交互，旧 `-cnv`/`-i` 已不在 help 中）。
- Qwen3 关思考**必须**用 `--chat-template-kwargs '{"enable_thinking": false}'`：实测仅传 `--reasoning-budget 0` 仍会输出思考段。两者一起给最稳。

### 2.2 多轮、单轮退出、读文件

```shell
# 交互多轮（本版默认行为，无需 -cnv / -i）
llama-cli -m ./Qwen3-0.6B-Q4_K_M.gguf

# 单轮退出
llama-cli -m ./Qwen3-0.6B-Q4_K_M.gguf \
  --chat-template-kwargs '{"enable_thinking": false}' \
  -p "用一句话介绍自己" -n 64 -st

# 从文件读提示词（UTF-8）
llama-cli -m ./Qwen3-0.6B-Q4_K_M.gguf -f ./prompt.txt -n 256 -st
```

### 2.3 起服务、健康检查、OpenAI 兼容调用、WebUI

```shell
llama-server -m ./Qwen3-0.6B-Q4_K_M.gguf \
  -c 4096 -np 4 -cb \
  --host 127.0.0.1 --port 9931 -a qwen3 \
  --reasoning-budget 0 --chat-template-kwargs '{"enable_thinking": false}'
```

- `--host` 默认 `127.0.0.1`（只本机），`--port` 默认 **9931**（不是老印象里的 8080）；对外改 `0.0.0.0`。
- `-np/--parallel` 默认 `-1`（auto），这里显式 `4` 个并发槽，也就是 llama-server 同一时刻能"同时接住"几个请求。；`-cb` 连续批处理默认 enabled，4 路可以拼成一个 batch 送进模型算，提高吞吐。如果大于配置的并发数，新的请求来到会排队等待。
- `-c 4096` 全服务一共 4096 token，会被 4 个槽均分，也就是每个对话1024个token，日志里看 `n_ctx_slot`（本机实测 `-c 2048 -np 4` → `n_ctx_slot = 512`）；**按日志为准**。
- 浏览器打开 `http://127.0.0.1:9931/` 即用内置 WebUI（[§8.1](#81-内置-webuillama-chat)）。

健康检查与调用：

```shell
curl http://127.0.0.1:9931/health
# {"status":"ok"} 就绪；加载中可能返回 503

curl http://127.0.0.1:9931/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3","messages":[{"role":"user","content":"你好"}],"max_tokens":256}'
```

> 设了 `--api-key` 时：`/health` 不带 key 仍 200；`/v1/chat/completions` 不带 key 返回 401，带 `Authorization: Bearer <key>` 返回 200（本机实测）。加载中 `/health` 可为 503。

### 2.4 基准测试（llama-bench）

```shell
llama-bench -m ./Qwen3-0.6B-Q4_K_M.gguf -p 512 -n 128 -r 3 -ngl 99 -fa on -t 8
```

- `-p 512`：提示长度；`-n 128`：生成长度；`-r 3`：重复次数（bench help 默认 5）；`-t 8`：线程数（bench 默认 8，本机物理核也是 8）。
- `-ngl 99` 是“足够大的数字”的旧写法，仍合法；默认已是 `-1`（bench 端）。`-fa on` 开 Flash Attention。
- 输出 `pp512`（提示处理）与 `tg128`（生成）两行 tok/s，用于对比参数改动是否有效（[§3.7](#37-压测与读数llama-bench)）。
  - **pp512**​ = 模型"**读题**"的速度：一次性把 512 个输入 token 并行算完（prefill / prompt processing）
  - **tg128**​ = 模型"**答题**"的速度：一个字一个字往外蹦 128 个 token（decode / text generation）

---

## 3. 本地高性能运行

### 3.1 调优顺序与判断依据

别一次改一堆参数，按这个顺序逐项加，每步看日志/读数再决定下一步：

1. **设备确认**：llama.exe cli `--list-devices` 看有没有 GPU；无 GPU 时 `-ngl` 怎么写都不报错，但谈不上加速。
2. **`-ngl` / `-fit`**：先 `-ngl all`（或旧数字 `99`）尽量卸载；显存不够让 `-fit on`（默认）自动收缩，或手动 `-fit`/`-fitt` 调余量。
   - 把模型所有可卸载的层全部搬进 GPU 显存里跑**，是 llama.cpp 里"全力开显卡"的开关。`-ngl` 全称 `--n-gpu-layers`（也写作 `--gpu-layers`），`all` 就是"能卸多少卸多少"。
   - -ngl auto（新版本默认）llama.cpp 按空闲显存自己算能卸几层
3. **`-c`**：按业务上下文设，**显式写**（默认 0 会取模型 40960，KV 账本见 [§3.8](#38-显存估算公式--qwen3-06b-实例)）。
4. **`-fa on`**：开 Flash Attention，长上下文更省显存/更快。**不影响模型质量和输出内容**（数学等价），只影响三件事：**显存占用、prefill 速度、长上下文/并发能不能跑得动**。对 decode 速度（tg）几乎没影响。
5. **KV 量化**：`-ctk q8_0 -ctv q8_0` 减半 KV 占用（非 f16 组合建议配 `-fa on`，缺内核会回退 f16 并告警，不是“必须”）。
   - -ctk 和 -ctv 是指定 KV Cache 用什么数值精度存储的两个参数，后面跟 q8_0 就是"把原本 16 位浮点存的缓存压成 8 位"，显存占用大约砍半。
   - KV Cache 是推理时"记住前文"的地方，每生成一个 token，所有层都要往里面追加一对 K/V 向量。它的体积随**上下文长度 × 层数 × KV 头数 × 头维度**线性增长，KV 显存 ≈ 2(K和V) × 层数 × KV头数 × 头维度 × 上下文长度 × 每元素字节数。
6. **`-b` / `-ub`**：批 2048 / 微批 512 是默认，显存紧就调小 `-ub`。
7. **`-np` / `-cb`**（server）：并发槽 + 连续批处理，注意上下文被均分。
8. **`-t` / `-tb`**：最后按物理核设线程（本机 8 物理核）。

**观察点**：启动日志 `offloaded N/N layers to GPU`；`/health` 200；`llama-bench` 的 `pp`/`tg`；`nvidia-smi` 看显存。下面六条示例（+ LoRA）按场景取用。

### 3.2 单卡 GPU：CLI 高性能

```shell
llama-cli -m ./Qwen3-0.6B-Q4_K_M.gguf \
  -ngl all -fa on -ctk q8_0 -ctv q8_0 \
  -c 8192 -b 2048 -ub 512 -t 8 -tb 8 \
  --reasoning-budget 0 --chat-template-kwargs '{"enable_thinking": false}' \
  -p "用三句话介绍你自己" -n 256 -st
```

### 3.3 单卡 GPU：server 高并发（API-only）

```shell
llama-server -m ./Qwen3-0.6B-Q4_K_M.gguf \
  -ngl all -fa on -ctk q8_0 -ctv q8_0 \
  -c 16384 -np 4 -cb -b 2048 -ub 512 -t 8 -tb 8 \
  --host 0.0.0.0 --port 8080 -a qwen3 \
  --api-key sk-local-123 --metrics --no-webui \
  --reasoning-budget 0 --chat-template-kwargs '{"enable_thinking": false}'
```

- `-np 4 -cb`：4 并发槽 + 连续批处理；`-c 16384` 按槽位均分（日志 `n_ctx_slot = 4096`，以实际日志为准）。这里显式用 8080，默认仍是 9931。
- `--api-key` 保护业务端点；`--no-webui` 关掉内置页（纯 API 部署）；`--metrics` 暴露 `/metrics`。
- `--host 0.0.0.0` 对外开放时务必带 `--api-key`，`/health` 仍是公开的，别裸奔到公网。
- 看 `/health` 200、`/metrics` 与并发槽日志。**GPU 项未在本机实测**。

### 3.4 多卡（layer / tensor split）

```shell
llama-server -m ./Qwen3-8B-Q4_K_M.gguf \
  -ngl all -sm layer -ts "3,1" -mg 0 -fa on \
  -c 16384 -np 2 --host 127.0.0.1 --port 8080
```

- `-sm layer`：按层切分（默认 `layer`）；`row` 按行切权重；`tensor` 实验性。`-ts "3,1"`：两卡权重按 3:1 分；`-mg 0`：主卡索引（默认 0）。
- 8B 文件需自备，本机只有 0.6B；本例给出命令形态，**未在本机实测**。看两张卡都分配到层、`nvidia-smi` 双卡显存。这里显式用 8080，默认仍是 9931。

### 3.5 投机解码

```shell
llama-cli -m ./Qwen3-8B-Q4_K_M.gguf \
  -md ./Qwen3-0.6B-Q4_K_M.gguf -ngld all \
  --spec-draft-n-max 8 --spec-draft-n-min 0 --spec-draft-p-min 0.5 \
  -ngl all -fa on -c 8192 -b 2048 -ub 512 \
  --chat-template-kwargs '{"enable_thinking": false}' \
  -p "用三句话介绍你自己" -n 256 -st
```

- `-md` 是 `--spec-draft-model` 的别名，草稿模型需与主模型同词表且更小（这里拿 0.6B 给 8B 当 draft）。`-ngld all` 草稿模型也全量卸载。
- `--spec-draft-n-max 8`（默认 3）每步草稿 token 数；`--spec-draft-p-min 0.5`（默认 0.00）最低接受概率；`--spec-draft-p-split`（默认 0.10）另有控制。
  - 每生成一步，**先让草稿连续猜 N 个 token**，然后**主模型一次并行验证这 N 个**
  - **和`-md`必须一起开**。草稿模型本身计算量小，如果留在 CPU，每步"草稿自回归猜 N 个"就会变成整条链路的瓶颈——主模型在 GPU 上干等 CPU 吐 token，加速比直接归零甚至倒亏 。
  - 显存账要算两份：主模型权重 + KV，草稿模型权重 + 草稿自己的 KV。0.6B 草稿额外开销大概 1GB 上下，一般不是问题
  - 反直觉的结果：**n-max 越小反而越快**。原因是草稿越往后猜越不准，被拒绝的后半段既烧了草稿的算力，又让主模型验证了一批注定作废的 token，净收益被吃光。推荐值为4左右。
- 旧 `-d/--draft/--draft-max`、`--p-split` **已移除**，别再写。看 draft 接受率与生成 t/s 是否提升；本例**未在本机实测**。

### 3.6 纯 CPU 高吞吐

```shell
llama-cli -m ./Qwen3-0.6B-Q4_K_M.gguf \
  -t 8 -tb 8 -b 2048 -ub 512 -c 8192 -fa on -ctk q8_0 -ctv q8_0 --prio 2 \
  --chat-template-kwargs '{"enable_thinking": false}' \
  -p "用三句话介绍你自己" -n 256 -st
```

- `-t/-tb 8` 设物理核数（本机 AMD 8845HS 8 物理核）；`--prio 2` 提进程优先级。
  - `--prio` llama 进程在操作系统里的优先级，-1最低，0为默认，3最高。
- 这组参数里 `-fa on -ctk/-ctv q8_0` 的组合本机实测可跑（Windows CPU 包也接受 `-fa on`，无 GPU 时 `-ngl all` 不报错）。

### 显存估算公式 + Qwen3-0.6B 实例

KV cache 每 token 的字节数（f16）：

```
KV/token ≈ 2 × layers × kv_heads × head_dim × bytes
Qwen3-0.6B（28 层、8 KV heads、head_dim 128、f16=2B）：
2 × 28 × 8 × 128 × 2B ≈ 112 KiB/token  →  8K ≈ 0.9 GiB (f16) / q8_0 ≈ 0.45 GiB
```

常见的kv内存占用情况（qwen3-0.6B）

| **上下文** | **f16** | **q8_0** | **q6** | **q5_1** | **q4_1** |
| ---------: | ------: | --------: | -----: | --------: | --------: |
|   **16K**​ |    1.75 |      0.93 |   0.72 |      0.66 |      0.55 |
|   **32K**​ |    3.50 |      1.86 |   1.44 |      1.31 |      1.09 |
|   **64K**​ |    7.00 |      3.72 |   2.87 |      2.63 |      2.19 |
|  **128K**​ |    14.0 |      7.45 |   5.75 |      5.25 |      4.38 |
|  **256K**​ |    28.0 |      14.9 |   11.5 |      10.5 |      8.75 |
|  **512K**​ |    56.0 |      29.8 |   23.0 |      21.0 |      17.5 |
|    **1M**​ |     112 |      59.5 |   46.0 |      42.0 |      35.0 |

**Qwen3-4B 的 KV 占用恒等于 0.6B 的 1.286 倍（多 28.57%）**

跟上下文长度、量化档位都无关。

原因很简单——KV 公式里只有 **层数、KV 头数、head_dim、bytes**​ 四个变量，两个模型的 KV 头数（都是 8）和 head_dim（都是 128）完全一样，唯一差别在层数：

| 模型       |    层数 | KV 头 | head_dim |
| ---------- | ------: | ----: | -------: |
| Qwen3-0.6B | **28**​ |     8 |      128 |
| Qwen3-4B   | **36**​ |     8 |      128 |

倍数 = 36 / 28 = **1.2857**

### 动态加载 LoRA（本机实测命令形态）

```shell
llama-cli -m ./Qwen3-0.6B-Q4_K_M.gguf --lora ./checkpoint-100-f16.gguf \
  --chat-template-kwargs '{"enable_thinking": false}' -p "你好，请介绍你自己" -n 64 -st
```

---

## 4. 参数速查（通用）

只收部署常用 + 易错项；参数名/默认值/别名以 b12810 help 为准。列：`参数（主/别名） | 默认值 | 取值 | 作用 | 备注`。带 server/cli 标记的是单端参数。

### 4.1 模型加载与 LoRA

| 参数 | 默认值 | 取值 | 作用 | 备注 |
| --- | --- | --- | --- | --- |
| `-m, --model FNAME` | 无 | GGUF 路径 | 指定主模型 | 必填 |
| `--spec-draft-model FNAME`(`-md`,`--model-draft`) | unused | GGUF 路径 | 投机草稿模型 | 见 §4.7 |
| `-hf, --hf-repo <u>/<m>[:q]`(`-hfr`) | unused | 仓库 ID | 从 HF 拉取 | quant 默认 `Q4_K_M` |
| `--lora FNAME` | 无 | 路径，逗号分隔 | 运行时叠加 LoRA | 见 §10 |
| `--lora-scaled FNAME:SCALE,...` | 无 | `路径:缩放` | 带缩放的 LoRA | scale=alpha/r |
| `-lm, --load-mode MODE` | `auto` | `auto`/`none`/`mmap`/`mlock`/`mmap+mlock`/`dio` | 统一控制 mmap/mlock | **取代** `--no-mmap`/`--mlock` |
| `--override-kv KEY=TYPE:VALUE,...` | 无 | int/float/bool/str | 覆盖模型元数据 | 超训练长度会乱码（推断） |
| `-dev, --device <d1,d2>` | 自动 | 设备列表；`none`=不卸载 | 指定卸载设备 | 彻底禁 GPU 用 `none` |
| `--list-devices` | — | 开关 | 列设备后退出 | 部署前先跑 |

### 4.2 上下文 / 批 / 缓存

| 参数 | 默认值 | 取值 | 作用 | 备注 |
| --- | --- | --- | --- | --- |
| `-c, --ctx-size N` | **0（取模型）** | token 数 | 上下文窗口 | 不是 4096；模型可能是 40960 |
| `-b, --batch-size N` | `2048` | token 数 | 逻辑最大批（预填充） | 显存紧调小 |
| `-ub, --ubatch-size N` | `512` | token 数 | 物理最大微批 | 无“≤-b”硬约束 |
| `-p, --prompt PROMPT` | 无 | 字符串 | 起始提示词 | **cli 专属** |
| `-f, --file FNAME` | none | 文件 | 从文件读提示词 | cli 专属 |
| `-r, --reverse-prompt` | 无 | 字符串 | 命中即停 | cli+server |
| `-e, --escape`(`--no-escape`) | `true` | 开关对 | 解析 `\n \r \t` | 默认已开 |
| `--in-prefix` / `--in-suffix` | **本版无** | — | — | help 未找到，属模板层能力 |

### 4.3 采样与输出约束

| 参数 | 默认值 | 取值 | 作用 | 备注 |
| --- | --- | --- | --- | --- |
| `-n, --predict N` | `-1` | token 数 | 单次最大生成数 | `-2` 语义 help 未写，别写成事实 |
| `-s, --seed SEED` | `-1`（随机） | 整数 | 随机种子 | 允许负数 |
| `--temp N`(`--temperature`) | `0.80` | 浮点 | 温度 | — |
| `--top-k N` | `40`（0 关闭） | 整数 | Top-K 采样 | — |
| `--top-p N` | `0.95`（1.0 关闭） | 浮点 | 核采样 | — |
| `--min-p N` | `0.05`（0 关闭） | 浮点 | 相对最小保留 | — |
| `--repeat-penalty N` | `1.00` | 浮点 | 重复惩罚 | — |
| `--repeat-last-n N` | `64`（**0 关闭**） | token 数 | 回看窗口 | 0 是关闭，不是“不限” |
| `--grammar GRAMMAR` | 无 | **GBNF 字符串** | 语法约束 | 文件用 `--grammar-file` |
| `--grammar-file FNAME` | 无 | 文件 | 从文件读语法 | — |
| `--json-schema SCHEMA`(`-j`) | 无 | **JSON 字符串** | JSON 约束 | 文件用 `-jf` |
| `--json-schema-file FILE`(`-jf`) | 无 | 文件 | 从文件读 schema | — |

> 更多采样参数与采样器链见落盘 help（§12.1）。

### 4.4 思考 / 模板（Qwen3 重点）

| 参数 | 默认值 | 取值 | 作用 | 备注 |
| --- | --- | --- | --- | --- |
| `--reasoning-budget N` | `-1` | -1/0/N | 思考 token 预算 | 仅设 `--reasoning-budget 0` 仍会思考 |
| `--reasoning-format F` | **`auto`** | `none`/`deepseek`/`deepseek-legacy` | 思考段输出格式 | auto 是默认值，不是列举值 |
| `-rea, --reasoning` | `auto` | on/off/auto | 思考总开关 | auto 从模板探测 |
| `--reasoning-effort L` | `default` | `default`/`minimal`/`low`/`medium`/`high`/`xhigh`/`max` | 思考力度档位 | 模板未实现会报错 |
| `--jinja`(`--no-jinja`) | **enabled** | 开关对 | Jinja 模板引擎 | 默认已开，无需显式加 |
| `--chat-template JINJA` | 取模型元数据 | 内置名/Jinja 串 | 指定聊天模板 | 文件形式 `--chat-template-file` |
| `--chat-template-kwargs S` | 无 | JSON 对象串 | 传模板变量 | `{"enable_thinking": false}` |

> Qwen3 关思考的正确姿势：`--reasoning-budget 0` **加** `--chat-template-kwargs '{"enable_thinking": false}'`。`/think`、`/no_think` 是模板软开关（追加在 prompt 末尾），不是命令行参数，别和本表混用。`-cnv`/`-i` 本版 help 未找到：默认就是交互，单轮用 `-st`。

### 4.5 CPU / GPU / 显存

| 参数 | 默认值 | 取值 | 作用 | 备注 |
| --- | --- | --- | --- | --- |
| `-t, --threads N` | `-1`（自动） | 整数 | 生成线程 | 设物理核数 |
| `-tb, --threads-batch N` | 同 `-t` | 整数 | 批线程 | — |
| `-ngl, --gpu-layers N` | **`auto`** | 整数/`auto`/`all` | 卸载层数 | `-ngl 0` ≠ 禁 GPU；禁 GPU 用 `--device none` |
| `-fa, --flash-attn` | `auto` | `on`/`off`/`auto` | Flash Attention | 三态，默认 auto |
| `-ctk, --cache-type-k T` | `f16` | 10 种（见下） | K cache 类型 | — |
| `-ctv, --cache-type-v T` | `f16` | 同上 | V cache 类型 | 非 f16 配 `-fa on`，缺内核回退告警 |
| `-sm, --split-mode` | **`layer`** | `none`/`layer`/`row`/`tensor` | 多卡切分 | `tensor` 实验性 |
| `-ts, --tensor-split N0,N1` | help 未标（bench `0`） | 比例如 `3,1` | 各卡权重比 | — |
| `-mg, --main-gpu INDEX` | `0` | 索引 | 主卡 | 与 `-sm` 联动 |
| `--prio N` | `0` | -1..3 | 进程优先级 | — |
| `-fit, --fit` | `on` | on/off | 自动适配显存 | 会调整未显式设的参数 |
| `-fitt, --fit-target MiB` | `1024` | MiB 列表 | 每卡保留余量 | — |
| `-fitc, --fit-ctx N` | `4096` | token 数 | fit 可设最小上下文 | — |

`-ctk`/`-ctv` 10 种取值：`f32,f16,bf16,f8_e4m3,q8_0,q4_0,q4_1,iq4_nl,q5_0,q5_1`。关于“V 量化必须开 FA”：**本版 help 无此硬约束**；官方 build.md 的 `GGML_CUDA_FA_QUANTS` 说未编译的组合会回退 f16 并告警，故写“建议配合 `-fa on`，缺内核回退告警”，不写“必须”。

### 4.6 server 专属

| 参数 | 默认值 | 取值 | 作用 | 备注 |
| --- | --- | --- | --- | --- |
| `--host HOST` | `127.0.0.1` | IP 列表/`.sock` | 监听地址 | `0.0.0.0` 对外 |
| `--port PORT` | **9931** | 端口 | 监听端口 | 不是 8080 |
| `-a, --alias STRING` | 无 | 逗号分隔 | API 对外模型名 | `model` 字段匹配 |
| `--api-key KEY` | `none` | 逗号分隔多把 | API 鉴权 | env `LLAMA_API_KEY`；文件形式 `--api-key-file` |
| `-to, --timeout N` | `3600` | 秒 | 读写超时 | — |
| `-np, --parallel N` | **`-1`（auto）** | 槽位数 | 并发槽位 | 完整名是 `--parallel`，不是 `--n-parallel`；cli 同名 `-np` 为 `1` |
| `-cb, --cont-batching` | **enabled** | 开关 | 连续批处理 | server 专属 |
| `-sps, --slot-prompt-similarity` | `0.10` | 浮点 | 槽位 prompt 复用 | — |
| `--metrics` | disabled | 开关 | `/metrics` | — |
| `--slots`(`--no-slots`) | enabled | 开关对 | 槽位监控端点 | — |
| `--threads-http N` | `-1` | 整数 | HTTP 线程 | server 专属 |
| `--ui`(`--webui`,`--no-ui`,`--no-webui`) | **enabled** | 开关组 | 内置 Llama Chat | `--ui` 主名，`--webui` 别名 |
| `--ui-config JSON` | 无 | JSON 串 | UI 默认设置 | 文件用 `--ui-config-file` |
| `--models-dir PATH` | disabled | 目录 | 多模型路由 | 触发路由模式（文档推断）；上限 `--models-max` 默认 4 |
| `--cors-origins ORIGINS` | `*` | Origin 列表 | CORS 允许来源 | **取代** `--cors`/`--cors-allow-origin` |
| `--ssl-key-file` / `--ssl-cert-file` | 无 | PEM 文件 | HTTPS | 需 OpenSSL 构建 |
| `--log-file FNAME` | 无 | 文件 | 日志落盘（全量日志加 `-v`） | cli+server |
| `--embedding`(`--embeddings`) | disabled | 开关 | embedding 用例 | server 专属 |
| `--pooling` | 取模型默认 | `none`/`mean`/`cls`/`last`/`rank` | 池化方式 | 常配 `--rerank` |

### 4.7 投机解码

| 参数 | 默认值 | 取值 | 作用 | 备注 |
| --- | --- | --- | --- | --- |
| `--spec-draft-model`(`-md`) | unused | GGUF 路径 | 草稿模型 | 同词表、更小 |
| `--spec-draft-ngl N`(`-ngld`) | `auto` | 数字/auto/all | 草稿卸载层数 | 别名 `--gpu-layers-draft` |
| `--spec-draft-n-max N` | `3` | 整数 | 每步草稿 token 数 | 取代旧 `-d` |
| `--spec-draft-p-min P` | `0.00` | 浮点 | 最低接受概率 | 别名 `--draft-p-min` |
| `--spec-draft-p-split P` | `0.10` | 浮点 | split 概率 | 别名 `--draft-p-split` |
| `--spec-type` | `none` | 逗号分隔算法 | 投机算法类型 | `draft-simple`/`draft-eagle3`/`ngram-*` 等 |
| `-d, --draft, --draft-max` | **已移除** | — | — | 替代：`--spec-draft-n-max` |
| `--draft-min, --draft-n-min` | **已移除** | — | — | 替代：`--spec-draft-n-min` |

### 4.8 版本差异 / 旧 → 新映射

| 旧写法 | b12810 写法 | 说明 |
| --- | --- | --- |
| `--no-mmap` | `-lm none` 或默认 `auto` | 独立开关本版无 |
| `--mlock` | `-lm mlock` / `-lm mmap+mlock` | 独立开关本版无 |
| `-d` / `--draft` / `--draft-max` | `--spec-draft-n-max`（默认 3） | 旧参数已移除 |
| `--p-split` | `--spec-draft-p-split`（默认 0.10，别名 `--draft-p-split`） | 数值一致，名字变 |
| `--n-parallel` | `-np` / `--parallel`（env `LLAMA_ARG_N_PARALLEL`） | `--n-parallel` 本版无 |
| `--cors` / `--cors-allow-origin` | `--cors-origins`（默认 `*`） | 旧写法本版无 |
| `--webui` | `--ui`（`--webui` 降为别名） | 默认 enabled |
| `--in-prefix` / `--in-suffix` | 无替代 | 属模板层能力 |
| `-cnv` / `-i` | 默认交互 + `-st` 单轮 | 本版 help 未找到 |
| `-ngl 99` | `-ngl all` 或默认 `auto` | 99 仍合法，只是数字写法 |
| `-n -2` 填满上下文 | 无据 | 本版 help 未写，勿写成事实 |
| `--port 8080`（老构建默认） | `--port 9931`（默认） | 8080 是历史版本推断 |

---

## 5. Windows 差异

### 5.1 包选择与解压布局

官方预编译包（GitHub Releases b12810，zip）：

| 包 | 后端 | 备注 |
| --- | --- | --- |
| `llama-b12810-bin-win-cpu-x64.zip` | CPU | 本机所用；另有 `cpu-arm64` |
| `llama-b12810-bin-win-cuda-12.4-x64.zip` | CUDA 12.4 | **需另下 cudart** |
| `llama-b12810-bin-win-cuda-13.5-x64.zip` | CUDA 13.5 | **需另下 cudart**（另有 arm64） |
| `llama-b12810-bin-win-vulkan-x64.zip` | Vulkan | 自包含，无 cudart（另有 arm64） |
| `llama-b12810-bin-win-rocm-10.0-x64.zip` | ROCm/HIP | — |
| `llama-b12810-bin-win-sycl-x64.zip` | SYCL（Intel GPU） | — |
| `llama-b12810-bin-win-openvino-2026.4.1-x64.zip` | OpenVINO | — |

Windows zip **解压后是扁平目录**：`D:\tmp\llm\llamacpp\bin` 下直接是 `llama-cli.exe`、`llama-server.exe`、`llama.exe`、`llama-bench.exe`、`llama.dll`、`ggml.dll`、`ggml-cpu-*.dll`、`libomp.dll` 等，没有额外顶层文件夹。

CUDA 主包**不含**运行库 DLL，需把同名 `cudart-llama-bin-win-cuda-12.4-x64.zip` / `cudart-llama-bin-win-cuda-13.5-x64.zip` 解压到同一目录。Vulkan/ROCm/SYCL/OpenVINO/CPU 包无独立运行库包。

### 5.2 路径、续行（cmd 单行）、引号、curl、编码

PowerShell 7 用反引号（`` ` ``）续行（[§2](#2-通用启动命令windows--linux-同一份) 的 `\` 是 bash 写法；PS7 请换成反引号）；**cmd 不支持 `\` 也不支持反引号**，写成单行：

```bat
.\llamacpp\bin\llama-cli.exe -m .\Qwen3-0.6B-Q4_K_M.gguf --reasoning-budget 0 --chat-template-kwargs "{\"enable_thinking\": false}" -p "你好" -n 64 -st
```

PS7 单行版用单引号包 JSON；多行用反引号续行。

- 裸命令名没在 PATH 时，Windows 用 `.\llamacpp\bin\llama-cli.exe`；cwd 在 `D:\tmp\llm` 时模型就是 `.\Qwen3-0.6B-Q4_K_M.gguf`。
- 引号：PowerShell 7 / bash 用单引号包 JSON（`{"enable_thinking": false}`）；cmd 下用双引号并转义内部双引号。
- `curl`：`curl.exe http://127.0.0.1:9931/health`（Windows 会把 `curl` 解析成 `Invoke-WebRequest` 别名，显式写 `.exe` 避免差异）。不要用 `curl` 根路径判断 WebUI，见 [§8.1](#81-内置-webuillama-chat)。
- 编码：控制台默认编码可能把中文提示符显示为 `?`，不影响退出码与推理；`-f` 读的提示词文件存成 UTF-8。

### 5.3 DLL / 运行库与 CUDA runtime

- CPU 包自带 `libomp.dll`（OpenMP 运行库）；按 CPU 指令集择优加载多份 `ggml-cpu-*.dll`（本机选中 `zen4`）。
- CUDA 包若报缺 DLL，按 [§5.1](#51-包选择与解压布局) 补 `cudart-llama-bin-win-cuda-*`。
- **GPU 项未在本机实测**：本机 `--list-devices` 为 `(none)`。

### 5.4 后台运行、端口、防火墙

```powershell
# 后台起 server（PS7），记录 PID 便于停止
$p = Start-Process .\llamacpp\bin\llama-server.exe -PassThru -WindowStyle Hidden -ArgumentList @(
  '-m','.\Qwen3-0.6B-Q4_K_M.gguf','-c','4096','-np','4','-cb','--host','127.0.0.1','--port','9931','--no-webui')
$p.Id   # 结束：Stop-Process -Id <PID>
```

- 端口用 `--port` 改（默认 9931）；本机冒烟可用 18080/18081/18086 避免冲突。
- `0.0.0.0` 对外时需在 Windows 防火墙放行端口，并务必带 `--api-key`。
- G4 收尾：按 PID 停服务并确认端口释放。

---

## 6. Linux 差异

### 6.1 包选择与解压（未在本机实测）

官方预编译包（tar.gz）：

| 包 | 后端 |
| --- | --- |
| `llama-b12810-bin-ubuntu-x64.tar.gz` | CPU（另有 arm64） |
| `llama-b12810-bin-ubuntu-cuda-12.8-x64.tar.gz` | CUDA 12.8（另有 13.5 / arm64） |
| `llama-b12810-bin-ubuntu-vulkan-x64.tar.gz` | Vulkan（另有 arm64） |
| `llama-b12810-bin-ubuntu-rocm-10.0-x64.tar.gz` | ROCm/HIP |
| `llama-b12810-bin-ubuntu-openvino-2026.4.1-x64.tar.gz` | OpenVINO |
| `llama-b12810-bin-ubuntu-sycl-fp16-x64.tar.gz` | SYCL |

Linux CUDA 同样需另下 `cudart-llama-b12810-bin-ubuntu-cuda-12.8-x64.tar.gz` 等运行库包。与 Windows 不同，**Linux tar 带顶层目录 `llama-b12810/`**：

```shell
mkdir -p /opt/llama
tar -xzvf llama-b12810-bin-ubuntu-x64.tar.gz -C /opt/llama
/opt/llama/llama-b12810/llama-cli --version
```

可执行文件**无 `.exe` 后缀**。

### 6.2 依赖（libgomp1、驱动、LD_LIBRARY_PATH）

- `libgomp1`：既有量化笔记在 Ubuntu 上跑 `llama-quantize` 报 `error while loading shared libraries: libgomp.so.1`；`sudo apt-get update && sudo apt-get install -y libgomp1` 解决。本版官方 build.md 未在预编译包章节硬性声明，故写“**可能需要**，按报错安装”。
- CUDA/ROCm 需先装对应驱动；Vulkan 需 ICD。
- `LD_LIBRARY_PATH`：若把 cudart 解压到别处，用 `export LD_LIBRARY_PATH=/opt/llama/llama-b12810:$LD_LIBRARY_PATH` 指过去。

### 6.3 shell 写法与权限

- [§2](#2-通用启动命令windows--linux-同一份) 的 `\` 续行在 bash 直接可用；cwd = 模型目录；模型写 `./Qwen3-0.6B-Q4_K_M.gguf`。
- 解压后二进制可能无执行位：`chmod +x /opt/llama/llama-b12810/llama-cli`。
- 通用命令假设 `bin` 在 PATH；未加时写 `/opt/llama/llama-b12810/llama-cli`。

### 6.4 systemd 服务化 + 日志 + 防火墙（未在本机实测）

```ini
# /etc/systemd/system/llama-server.service（示例）
[Unit]
Description=llama.cpp GGUF server (Qwen3-0.6B)
After=network.target

[Service]
User=llama
WorkingDirectory=/opt/llama
LimitNOFILE=65535
ExecStart=/opt/llama/llama-b12810/llama-server -m /opt/llama/Qwen3-0.6B-Q4_K_M.gguf -c 4096 -np 4 -cb --host 127.0.0.1 --port 9931 -a qwen3 --no-webui
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

> `User=llama` 需按实际服务用户调整（先创建该用户）；`After=network.target` + `[Install]` 缺一不可，否则 `systemctl enable` 会失败。

```shell
sudo systemctl daemon-reload
sudo systemctl enable --now llama-server
journalctl -u llama-server -f
```

- 日志：`--log-file /var/log/llama-server.log` 或 `journalctl`。
- 防火墙：`sudo ufw allow 9931/tcp`（仅对外需要）；对内的 `127.0.0.1` 不用放行。

---

## 7. GPU / macOS 差异

> 本节全部 **未在本机实测**（本机无 GPU、无 macOS）。只给官方可核的构建包与参数写法。

### 7.1 后端选择矩阵

| 平台/硬件 | 推荐包 | 后端 |
| --- | --- | --- |
| NVIDIA | win/linux `cuda-12.4` / `cuda-12.8`(+cudart) | CUDA |
| AMD | win/linux `rocm-10.0` | ROCm/HIP |
| Intel GPU | win `sycl` / `openvino` | SYCL / OpenVINO |
| 通用显卡 | win/linux `vulkan` | Vulkan（自包含） |
| Apple Silicon | `macos-arm64` | Metal |
| 无 GPU | `cpu` | CPU |

### 7.2 设备发现与选择

```shell
llama-cli --list-devices
llama-cli -m ./Qwen3-0.6B-Q4_K_M.gguf -dev CUDA0 -ngl all
```

- `--list-devices` 先确认设备名，`CUDA0` 需按 `--list-devices` 的实际设备名替换（本机无 GPU，未实测）；`-dev <dev1,dev2>` 指定卸载设备，`-dev none` 彻底禁用 GPU。
- `-ngl 0` **不等于完全禁用 GPU**（官方 build.md：GPU 仍可能加速部分计算）；要彻底禁用用 `--device none`。

### 7.3 多卡切分

`-sm {none,layer,row,tensor}`（默认 `layer`）、`-ts N0,N1`（比例如 `3,1`）、`-mg INDEX`（默认 0）。命令见 [§3.4](#34-多卡layer--tensor-split)。`tensor` 为实验性。

### 7.4 Flash Attention / KV cache 量化组合

`-fa {on,off,auto}`（默认 auto）+ `-ctk`/`-ctv`（默认 f16，10 种取值）。非 f16 的 K/V 组合依赖对应 FA 内核是否编译，缺内核会回退 f16 并告警——写“建议 `-fa on`”，不写“必须”。组合与账本见 [§3.8](#38-显存估算公式--qwen3-06b-实例)。

### 7.5 自动适配 `-fit` 与显存不足

`-fit on`（默认）会调整未显式设置的参数以适配显存；`-fitt`（默认 1024 MiB/卡）调保留余量，`-fitc`（默认 4096）调最小上下文。OOM 时：调小 `-c` → `-ctk q8_0 -ctv q8_0` → 减小 `-ub` → 减少 `-np` → `-fit on`。

### 7.6 macOS（未实测，4 类各一行）

| 类别 | 写法 |
| --- | --- |
| 包/解压 | `llama-b12810-bin-macos-arm64.tar.gz`（Intel 为 `x64`）解压；或 `brew install llama.cpp`；或 `curl -fsSL https://llama.app/install.sh \| sh` |
| 路径与 shell | 无 `.exe` 后缀；cwd = 模型目录，`./Qwen3-0.6B-Q4_K_M.gguf`；bash 用 `\` 续行 |
| 依赖 | Metal 默认启用，无需 cudart；Xcode Command Line Tools 供源码编译 |
| 服务化 | 用 launchd plist 或前台启动；`brew services` 仅在 formula 提供 service 时可用（未实测） |

---

## 8. GUI 使用

“GUI”在本语境有歧义，两种完全不同的东西，端口与定位不能混：**内置 WebUI = 9931（服务端自带页面）**，**第三方 Llama GUI = 5240（外部控制面板）**。

### 8.1 内置 WebUI（Llama Chat）

随 `llama-server` 提供，官方名为 **Llama Chat**。`--ui`/`--webui` 开关组默认 **enabled**，浏览器打开 `http://127.0.0.1:9931/`（与 API 同源同端口的根路径）即可用；`--no-webui` / `--no-ui` 关闭，保留 API。

- `--ui-config '{"temperature":0.7}'` 传 UI 默认设置；文件形式用 `--ui-config-file`。
- **不要用 curl 根路径判断 UI 可用性**：实测不带 `Accept-Encoding: gzip` 访问 `/` 返回 415（`gzip is not supported by this browser`）；带 `-H 'Accept-Encoding: gzip' --compressed` 返回 200。用浏览器或 `/health` 判断。
- Release 里的 `llama-b12810-ui.tar.gz` 是独立分发的静态资源包，不是“另一个 GUI 程序”，通常已内置在二进制包中。

### 8.2 第三方 Llama GUI（可选）

[thomas9120/LLama-GUI](https://github.com/thomas9120/LLama-GUI) 是**独立第三方启动器/控制面板**（GPL-3.0），不是 llama.cpp 官方组件。它自己下载并管理 bNNNN 二进制，把 `llama-server` 参数做成表单。

| 项 | 值 |
| --- | --- |
| 控制面板 | `http://127.0.0.1:5240`（**不是 9931**） |
| 前置 | Python 3.9+ |
| 安装（Win） | `irm https://raw.githubusercontent.com/thomas9120/LLama-GUI/main/online_installers/install-online.ps1 \| iex` |
| 安装（Linux/macOS） | `curl -fsSL https://raw.githubusercontent.com/thomas9120/LLama-GUI/main/online_installers/install-online.sh \| sh` |
| 手动 | `git clone https://github.com/thomas9120/LLama-GUI.git && cd LLama-GUI` 后按平台跑安装脚本 |
| 模型目录 | 默认 `models/`，可在 Configure → Models Folder 改指向已有模型库 |
| 默认参数 | 工具是 `llama-server`，`-fit on`，context `64000`（**GUI 自己的默认值，不是 llama.cpp 默认**） |

无内置鉴权，别暴露公网。可用 `LLAMA_GUI_HOST` / `LLAMA_GUI_PORT` 改监听。本任务不安装、不运行。

### 8.3 其它前端（指针）

Open WebUI 等前端通过 `http://host:9931/v1` 对接 `llama-server`（OpenAI 兼容层）；LM Studio 是独立运行时，不是 `llama-server` 前端。本文不展开。

---

## 9. Ollama 运行 GGUF

> 本任务**未安装/未运行 Ollama**；全部来自官方文档（docs.ollama.com，抓取 2026-11-28），只写有出处的内容。

### 9.1 与 llama.cpp 的关系

Ollama 官方 README 的 “Supported backends” 明确列出 **llama.cpp**；它直接吃 llama.cpp 转换/量化出的 GGUF，但**导入时不量化 GGUF**（先用 `llama-quantize` 备好文件）。

### 9.2 Modelfile 导入 GGUF（FROM）

```text
# Modelfile
FROM ./Qwen3-0.6B-Q4_K_M.gguf
PARAMETER num_ctx 8192
PARAMETER temperature 0.7
SYSTEM "你是小助手"
```

分片用通配符 `FROM /path/to/model-*.gguf`，或 Modelfile 里多个 `FROM`。`PARAMETER` 合法键：`num_ctx`、`temperature`、`top_k`、`top_p`、`min_p`、`repeat_penalty`、`repeat_last_n`、`seed`、`stop`、`num_predict`、`draft_num_predict`（命名与 llama.cpp 的 `-c`/`--temp` 不同）。

### 9.3 运行、API、模型管理

```shell
ollama create qwen3-local -f ./Modelfile
ollama run qwen3-local
ollama ps
ollama show --modelfile qwen3-local
ollama stop qwen3-local
```

- 原生 API：`http://localhost:11434/api`（`POST /api/chat`、`POST /api/generate`）。
- OpenAI 兼容：`http://localhost:11434/v1/chat/completions`。
- 端口 **11434**，与 llama-server 的 9931 是两套独立服务。

```shell
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3-local",
  "messages": [{"role":"user","content":"Why is the sky blue?"}],
  "stream": false
}'
```

### 9.4 LoRA / ADAPTER（官方当前未列，需实测）

当前官方 Modelfile Reference 指令表只有 `FROM`/`PARAMETER`/`TEMPLATE`/`SYSTEM`/`LICENSE`/`MESSAGE`/`REQUIRES`/`CAPABILITY`，**没有 `ADAPTER` 指令**。故 `ADAPTER ./lora-f16.gguf` 属“官方当前未列，需按版本实测”，**不写成官方支持**。llama.cpp 可用 `--lora` 动态叠加（见 [§10](#10-lora-部署要点)），Ollama 走 Modelfile → `create` 路径，本轮未确认是否等价。

### 9.5 常用环境变量表（以官方 FAQ 为准）

| 变量 | 默认值 | 作用 |
| --- | --- | --- |
| `OLLAMA_HOST` | `127.0.0.1:11434` | 绑定地址 |
| `OLLAMA_MODELS` | Linux `/usr/share/ollama/.ollama/models`；Win `C:\Users\%username%\.ollama\models` | 模型目录 |
| `OLLAMA_CONTEXT_LENGTH` | FAQ `4096`（context-length 页按 VRAM 分档：<24GiB→4k、24–48GiB→32k、≥48GiB→256k） | 上下文 |
| `OLLAMA_NUM_PARALLEL` | 未设时多数后端 `1` | 并行请求数（会使上下文按倍数增长） |
| `OLLAMA_MAX_LOADED_MODELS` | `3 × GPU 数`（CPU 为 3） | 同时加载上限 |
| `OLLAMA_MAX_QUEUE` | `512` | 排队上限，超出 503 |
| `OLLAMA_FLASH_ATTENTION` | 支持时自动 | `=1` 强制、`=0` 关 |
| `OLLAMA_KV_CACHE_TYPE` | `f16` | KV 量化（全局，非按模型） |
| `OLLAMA_KEEP_ALIVE` | `5 分钟` | 驻留时间 |
| `OLLAMA_ORIGINS` | 本地地址 | CORS 白名单 |
| `OLLAMA_NO_CLOUD` | 未设 | `=1` 关云功能 |

> `OLLAMA_GPU_OVERHEAD` 在官方 FAQ/GPU/API/README 中均 **NOT FOUND**，不要写成官方默认值。设置方式：Linux systemd `Environment="OLLAMA_HOST=..."`，Win 系统环境变量后重启。llama.cpp 侧命令行参数优先于 `LLAMA_ARG_*`；Ollama 以环境变量/Modelfile 为准。

### 9.6 与 llama-server 的能力边界

Ollama 适合“装好即用、自动管模型”；需要细粒度控制（投机类型、K/V 分类型、多模型路由、动态 LoRA）时，llama.cpp 原生 CLI/server 更合适。并发语义也不同：`OLLAMA_NUM_PARALLEL` 让单模型有效上下文倍增，llama-server 的 `-np` 是均分上下文。本轮未做性能对比。

---

## 10. LoRA 部署要点

### 10.1 PEFT 产物 vs GGUF 适配器

微调篇产出的 PEFT `adapter_model.safetensors` 需先转成 GGUF（流程见 [微调 06](../fine-tuning/大模型lora微调学习06，基于llamacpp的模型量化.md)，本文不重复）。部署侧拿到的是 `checkpoint-100-f16.gguf` 这类 f16 适配器。

### 10.2 运行时叠加：--lora / --lora-scaled

```shell
llama-cli -m ./Qwen3-0.6B-Q4_K_M.gguf \
  --lora ./checkpoint-100-f16.gguf \
  --chat-template-kwargs '{"enable_thinking": false}' \
  -p "你好，请介绍你自己" -n 64 -st
```

- 这条**本机实测可加载**（退出码 0，text2sql 适配器输出 SQL）。base 是 Q4_K_M、适配器 f16，证实“量化 base + f16 LoRA 运行时叠加”可行。
- 多个适配器用逗号分隔；`--lora-scaled FNAME:SCALE` 带自定义缩放，`scale = alpha/r`（与微调时的rank/alpha对应）。
- base 的量化精度与 LoRA 无关：换 Q4_K_M / Q8 不影响适配器加载方式。
- **Windows 冒号问题**：`--lora-scaled` 的 `路径:缩放` 在 Windows 盘符 `D:\...` 下冒号会被误解析；建议用相对路径 `./checkpoint-100-f16.gguf:4`（scale=alpha/r=32/8=4），或优先只用 `--lora`（本机实测路径无冒号问题）。
- server 另有 `--lora-init-without-apply`（默认 disabled），稍后经 `POST /lora-adapters` 应用，可做动态切换。

---

## 11. 排错表

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 能起服务但连不上 API | `--host` 只绑 `127.0.0.1` / 端口被占 | 改 `--host 0.0.0.0` / 换 `--port`；`netstat -ano \| findstr 9931` |
| `POST /v1/chat/completions` 401 | 设了 `--api-key` 但没带 | 加 `Authorization: Bearer <key>`；`/health` 不带 key 仍 200 |
| `/health` 返回 503 | 模型还在加载 | 等加载完成再请求 |
| 浏览器打不开 WebUI | `--no-webui` 关了 / curl 根路径 415 | 用浏览器开 `http://host:9931/`；别用 curl 判断 UI（需 gzip 头） |
| Windows 报缺 DLL | CUDA 包没装运行库 | 解压对应 `cudart-llama-bin-win-cuda-*` 到同目录 |
| Linux 报 `libgomp.so.1` 缺失 | 缺 OpenMP 运行库 | `sudo apt-get install -y libgomp1` |
| CUDA OOM / 显存不够 | `-c` 取模型 40960 / KV 太大 | 显式 `-c`；`-ctk/-ctv q8_0`；减 `-ub`/`-np`；`-fit on` |
| 输出乱码 | 超过训练长度 / 编码问题 | 减小 `-c` 到训练长度内；提示词文件存 UTF-8 |
| 生成为空或思考段去不掉 | Qwen3 只给了 `--reasoning-budget 0` | 加 `--chat-template-kwargs '{"enable_thinking": false}'` |
| 改参数后没变快 | 猜错瓶颈 | 用 `llama-bench` 单参数对比 pp/tg；看 `offloaded N/N layers` 日志 |
| 上下文不够用 | `-np` 均分了 `-c` | 减小 `-np` 或增大 `-c`，以日志 `n_ctx_slot` 为准 |
| 老文档参数名找不到 | 版本差异 | 查 [§4.8](#48-版本差异--旧--新映射)，用 b12810 写法 |

---

## 12. 附：版本与参数获取

### 12.1 help 落盘（以本机为准）

```powershell
# Windows / PowerShell（Linux/bash 去掉 .exe、把 *> 换成 > 2>&1）
.\llamacpp\bin\llama-cli.exe --help  *> .\help-cli.txt
.\llamacpp\bin\llama-server.exe --help *> .\help-server.txt
.\llamacpp\bin\llama-bench.exe --help *> .\help-bench.txt
.\llamacpp\bin\llama.exe help all       *> .\help-all.txt
```

`llama.exe help all` 列出统一入口的全部子命令帮助。本文参数速查（[§4](#4-参数速查通用)）只收约 75 行常用项，全量以落盘 help 为准。

### 12.2 关键 `LLAMA_ARG_*` 环境变量

help 中大量参数带 `LLAMA_ARG_*` 环境变量；`llama-server` README 明确“命令行参数优先于环境变量”。Docker 部署常用：

| 环境变量 | 对应参数 |
| --- | --- |
| `LLAMA_ARG_HOST` | `--host` |
| `LLAMA_ARG_PORT` | `--port` |
| `LLAMA_ARG_MODEL` | `-m` |
| `LLAMA_ARG_CTX_SIZE` | `-c` |
| `LLAMA_ARG_N_PARALLEL` | `-np` |
| `LLAMA_ARG_THINK` | `--reasoning-format` |
| `LLAMA_ARG_THINK_BUDGET` | `--reasoning-budget` |
| `LLAMA_API_KEY` | `--api-key` |

```shell
docker run -p 9931:9931 -v /path/to/models:/llama ghcr.io/ggml-org/llama.cpp:server \
  -m /llama/Qwen3-0.6B-Q4_K_M.gguf -c 4096 -np 4 -cb --host 0.0.0.0
```

