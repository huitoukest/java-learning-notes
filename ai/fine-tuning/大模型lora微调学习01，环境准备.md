# 大模型微调学习01，环境准备

# 基本环境

* CPU AMD Ryzen 7 8845HS，8 核 16 线程

- 集成显卡 AMD Radeon 780M

* 内存 32 GB

- 操作系统 Windows 11 家庭版中文版，Build 26300

* 通过wsl2 ubuntu26 （只要是linux环境，比较新的系统版本均可）
  * 本地相关文件的目录：/mnt/d/opt/lora_learn&#x20;
* Python 、PyTorch、LLaMA-Factory、LoRA rank

# 模型选择与下载

Qwen/Qwen3-0.6B，实际上就是  Instruct 版，我们选择这个版本，1.4G左右

* Instruct 版 ，官方后训练（对齐）版本，推荐做 SFT（监督微调，Supervised Fine-Tuning）

- Qwen/Qwen3-0.6B-Base ，纯基座版 未经指令对齐，适合预训练/研究，不适合直接 SFT
- 打开页面： [https://hf-mirror.com](https://hf-mirror.com)， 点击 进入 Files and version，[https://hf-mirror.com/Qwen/Qwen3-0.6B/tree/main 进入具体的文件下载页面](https://hf-mirror.com/Qwen/Qwen3-0.6B/tree/main)
- 也可以直接用命令下载

```
export HF_ENDPOINT=https://hf-mirror.com
huggingface-cli download Qwen/Qwen3-0.6B --local-dir /mnt/d/opt/lora_learn/models/Qwen3-0.6B
```

下载后的qwen3-0.6b的文件列表大致如下：

```text
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---          2026/11/26    12:25           1570 .gitattributes
-a---          2026/11/26    12:25            726 config.json
-a---          2026/11/26    12:25            239 generation_config.json
-a---          2026/11/26    12:25          11343 LICENSE
-a---          2026/11/26    12:25        1671853 merges.txt
-a---          2026/11/26    12:31     1503300328 model.safetensors
-a---          2026/11/26    12:25          13965 README.md
-a---          2026/11/26    12:25           9732 tokenizer_config.json
-a---          2026/11/26    12:25       11422654 tokenizer.json
-a---          2026/11/26    12:25        2776833 vocab.json
```

* 此版本默认 是 BF16（bfloat16，16 位浮点），不是量化版

  * 也存在比如q8量化版的instruct版本，但是不能用于训练。通常是GGUF格式， 是 llama.cpp 生态的打包格式，它把量化权重、分词器、元数据全塞进一个文件，只有 llama.cpp / Ollama 这类推理引擎认识它。LLaMA-Factory 底层走的是 transformers + safetensors，**根本不认 GGUF 格式**，连加载这一步都过不去，更别提训练。

# python环境

## 通过conda安装python

选择国内清华镜像加速

```shell
wget https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh
```

或者官方源：[https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh](https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh)

执行安装：

```shell
bash Miniconda3-latest-Linux-x86_64.sh
```

交互：① 许可协议一路回车，出现 `Please answer 'yes' or 'no':` 输入 `yes`；② 安装路径提示直接回车用默认；③ 最后问是否初始化 conda，输入 `yes`。

查看是否安装成功：

```shell
conda --version
```

配置国内源：

```shell
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --set show_channel_urls yes
```

### 创建虚拟环境

```shell
conda create -n lora_learn python=3.13 -y
```

成功标志：末尾出现 `To activate this environment, use conda activate lora_learn`。

**激活**：

```
conda activate lora_learn
```

**成功标志**：提示符变成 `(lora_learn) 用户名@计算机名:~$`

> 以后每次新开 WSL 终端都要先执行这句。

**验证**：

```
python --version
```

**预期看到**：Python 3.13.x

**给 pip 换国内源**：

```
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

**验证**：`pip config list` 应显示 `global.index-url='https://pypi.tuna.tsinghua.edu.cn/simple'`

## 通过UV安装python（推荐）

安装

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

激活环境变量

```shell
source $HOME/.local/bin/env
```

查看版本判断是否成功：

```shell
>> uv --version
uv 0.13.10 (x86_64-unknown-linux-gnu)
```

### 环境配置

uv 自己管理 Python，不需要 conda。

**让 uv 下载 Python 3.13**：

```
uv python install 3.13
```

**预期看到**：下载 CPython 3.13.x 的进度，显示安装路径。 **验证**：`uv python list` 能看到 `cpython-3.13.x-linux-x86_64-gnu`。

**创建虚拟环境**：

```
cd /mnt/d/opt/lora_learn
uv venv --python 3.13 .venv
```

**预期看到**：`Using CPython 3.13.x`、`Creating virtual environment at: .venv`、`Activate with: source .venv/bin/activate`

**激活**：

```
source .venv/bin/activate
```

**成功标志**：提示符出现 `(.venv)`。

> 以后每次新开终端：`cd /mnt/d/opt/lora_learn && source .venv/bin/activate`。

**验证**：

```
python --version
```

**预期看到**：`Python 3.13.x`

> uv 默认走 PyPI 官方源，已很快。想换国内源可在 install 命令加 `--index-url https://pypi.tuna.tsinghua.edu.cn/simple`。

---

# 安装 PyTorch

PyTorch 是一个用 Python 写深度学习模型的框架，我们安装Python版本支持的PyTorch即可。后续我们只用uv来实现相关安装的部分。

在 /mnt/d/opt/lora_learn 下，安装cpu版本（根据自身机器硬件选择）：

```shell
uv pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 \
  --index-url https://download.pytorch.org/whl/cpu
```

验证：

```shell
python -c "import torch; print('torch版本:', torch.__version__); print('CUDA可用:', torch.cuda.is_available())"
```

预期输出：

```shell
torch版本: 2.6.0+cpu
CUDA可用: False
```

实际在wsl下可能报Waring，这个和win系统磁盘格式有关：

```shell
Installing wheels...                                                                        warning: Failed to hardlink files; falling back to full copy. This may lead to degraded performance.
         If the cache and target directories are on different filesystems, hardlinking may not be supported.
         If this is intentional, set `export UV_LINK_MODE=copy` or use `--link-mode=copy` to suppress this warning.
```

uv 装包时默认**硬链接**：wheel 缓存在 `~/.cache/uv/`，装的时候不复制内容，直接给 `site-packages` 建个硬链接，几乎零耗时零空间。

但这个项目在 **`/mnt/d/...`（Windows 盘挂载到 WSL）**，文件系统是 **DrvFs**，跟 ext4 之间**不支持硬链接**，于是 uv 只能退化成"完整复制"。不影响使用。

查看是否安装成功：

```shell
python -c "import torch, torchvision, torchaudio; print(torchvision.__version__, torchaudio.__version__)"
```

成功输出：

```shell
python   3.13.18
torch    2.6.0+cpu
tv/ta    0.21.0+cpu 2.6.0+cpu
cuda     False
threads  8
smoke    torch.Size([512, 512])
```

# LlamaFactory 的安装

之前名称为LLaMA-Factory，

[地址：https://github.com/hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory) ， 我这里下载版本 v0.9.5（2026-05-30 发布，最新稳定版）

直接git clone下载：

```shell
git clone --depth 1 --branch v0.9.5 https://github.com/hiyouga/LlamaFactory.git
```

也可以考虑使用国内的镜像：

```shell
git clone --depth 1 https://gitcode.com/gh_mirrors/ll/Llama-Factory.git LlamaFactory
cd LlamaFactory && git fetch --depth 1 origin tag v0.9.5 && git checkout v0.9.5
```

安装相关依赖：

```shell
cd /mnt/d/opt/lora_learn/LlamaFactory
uv pip install -e .
uv pip install -r requirements/metrics.txt
```

uv 会按 pyproject.toml 自动把 transformers 锁在 ≤5.6.0，不用你操心版本冲突。

验证：

```shell
llamafactory-cli version
```

## 预期输出（可能比较慢）

```shell
----------------------------------------------------------
| Welcome to LLaMA Factory, version 0.9.5                |
|                                                        |
| Project page: https://github.com/hiyouga/LLaMA-Factory |
----------------------------------------------------------
```



整体环境检查(建议编写为check_env.sh后续直接执行）：

```shell
#!/bin/bash
# ============================================================
# 环境自检脚本：在 WSL 里运行，确认训练前的软硬件条件
# 用法：cd /mnt/d/opt/lora_learn && bash scripts/check_env.sh
# ============================================================
set -e
echo "========== 1. 系统信息 =========="
uname -a
echo
echo "========== 2. CPU 与内存 =========="
lscpu | grep -E "Model name|CPU\(s\)|Thread|Core" | head -5
free -h
echo
echo "========== 3. Python 版本（要求 3.11+）==========="
python3 --version
echo
echo "========== 4. 磁盘空间（D 盘挂载点）==========="
df -h /mnt/d | tail -1
echo
echo "========== 5. 关键 Python 包 =========="
python3 - <<'PY'
import importlib.metadata as md
pkgs = ["torch", "transformers", "datasets", "accelerate", "peft", "trl", "llamafactory"]
for p in pkgs:
    try:
        print(f"  {p:15s} {md.version(p)}")
    except md.PackageNotFoundError:
        print(f"  {p:15s} [未安装]")
try:
    import torch
    print(f"\n  torch 版本: {torch.__version__}")
    print(f"  CUDA 可用: {torch.cuda.is_available()}  (本机预期为 False，正常)")
except Exception as e:
    print(f"  torch 导入失败: {e}")
PY
echo
echo "========== 6. 模型文件完整性 =========="
MODEL_DIR=/mnt/d/opt/lora_learn/models/Qwen3-0.6B
if [ -f "$MODEL_DIR/model.safetensors" ] && [ -f "$MODEL_DIR/config.json" ]; then
    ls -lh "$MODEL_DIR" | head -20
    echo "  [OK] 模型关键文件存在"
else
    echo "  [警告] 模型文件不完整，请先执行下载步骤"
fi
echo
echo "========== 7. LLaMA-Factory 命令 =========="
if command -v llamafactory-cli >/dev/null 2>&1; then
    llamafactory-cli version 2>/dev/null || echo "  llamafactory-cli 存在"
else
    echo "  [警告] llamafactory-cli 未找到，请确认已 pip install -e . 并激活虚拟环境"
fi
echo
echo "========== 自检结束 =========="

```
