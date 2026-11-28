大模型微调，模型量化

需要的软件有

| Python       | 装一个 Windows 版（121MB 的 torch 就够）       |
| ------------ | ---------------------------------------------- |
| torch 下载量 | **121MB**（PyPI 上的 Windows 包就是纯 CPU 版） |
| llama.cpp    | 解压即用，**没有动态库问题**                   |

# 量化知识

**一句话**：量化就是把权重从 16 位浮点降低，比如压成 4 位整数存。

**怎么压的**：把一行权重按 32 个数分一组，每组算一个缩放系数，32 个数各压成 4 位。原来 32 个数占 512 位，现在占 144 位，压缩到 28%。

**为什么叫 Q4_K\_M**：

- `K`：按块（block）分组量化，比老的 Q4_0 精度高；
- `M`：Medium，一种**混合配方**——不是所有层都压 4 位。

`llama-quantize` 实际干的事：

| 层                            | 用什么精度     | 为什么                           |
| ----------------------------- | -------------- | -------------------------------- |
| 大部分 attn / ffn 权重        | `q4_K`（4 位） | 主体，压得最狠                   |
| `attn_v`、`ffn_down` 等敏感层 | `q6_K`（6 位） | 对误差敏感，多留 2 位            |
| 词表 embedding / 输出头       | `q6_K`         | 压太狠伤语义                     |
| 各种 norm                     | 保持 `f32`     | 只有几百个数，压了不省空间还掉点 |

所以 Q4_K_M 的平均位宽是 **5.24 bit** 而不是 4——这不是算错，是混合配方的结果。文件名写 Q4，指主体是 4 位。

> 记住这一句就够：**Q4_K_M = 该 4 的 4，该 6 的 6，norm 不动**。这就是它比 Q4_0 好用的原因。

# win 系统下

本地模型以 Qwen3-0.6B 为例子。

在同一级目录下安装好python环境

```shell
uv python install 3.13
uv venv --python 3.13 
```

ps：为了放置新对话中执行py虚拟环境未激活，建议直接 .venv\Scripts\python.exe 方式执行py脚本。

## llama.cpp 相关文件准备

**下载llama.cpp编译好的软件**

```shell
https://ghproxy.net/https://github.com/ggml-org/llama.cpp/releases/download/b12810/llama-b12810-bin-win-cpu-x64.zip
```

llama-b12810-bin-win-cpu-x64.zip 手动解压到未来 convert_hf_to_gguf.py 的同级目录的 bin目录中方便后续使用。

**下载llama源码包**，为的是里面的转换脚本

```text
https://ghproxy.net/https://github.com/ggml-org/llama.cpp/archive/refs/tags/b12810.tar.gz
```

或者从源直接下 [https://github.com/ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp)

由于我们不需要全部文件，而是极少的一部分，所以这里**通过一个py脚本来下载必须的**(笔者使用ai编写的脚本，也读者自行根据最新版本情况让ai编写脚本来下载即可)。

[download_llama_convert_min.py](script/download_llama_convert_min.py)

然后开始安装 torch，这里选择的是cpu版本（convert_hf_to_gguf.py同级目录下安装相关依赖）

```shell
uv pip install --torch-backend=cpu torch
```

安装其余的相关依赖（convert_hf_to_gguf.py同级目录下安装相关依赖）

```shell
uv pip install transformers tokenizers safetensors numpy tqdm protobuf pyyaml sentencepiece
```

也可以使用国内镜像加速

```shell
uv pip install torch `
  --index-url https://download.pytorch.org/whl/cpu `
  --index-strategy unsafe-best-match `
  --extra-index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

检测环境是否准备好了

```shell
.venv\Scripts\python.exe -c "import sys,torch,numpy,transformers; print(sys.version.split()[0], torch.__version__, numpy.__version__, transformers.__version__)"
#正常情况下会输出各个版本
3.13.16 2.15.0+cpu 2.5.5 5.24.1
```



### 执行导出

步骤

```text
HF 权重(safetensors)
   │  convert_hf_to_gguf.py --outtype bf16
   ▼
Qwen3-0.6B-BF16.gguf        ← 高精度「母版」，约 1.2GB
   │  llama.exe quantize ... Q4_K_M
   ▼
Qwen3-0.6B-Q4_K_M.gguf      ← 你要的最终文件，约 400MB
```



### 导出为bf16.gguf文件

进入 convert_hf_to_gguf.py 所在文件夹

```shell
uv run convert_hf_to_gguf.py ../Qwen3-0.6B --outfile ../Qwen3-0.6B-BF16.gguf --outtype bf16
```

注意：输出文件的 Qwen3-0.6B-BF16.gguf 的相关父级文件夹必须提前创建好，这里不会自动创建

### 量化为Q4_K_M文件

检查量化软件的可用性 ，exe的路径为 llama-b12810-bin-win-cpu-x64.zip 解压的文件。

```shell
./bin/llama-quantize.exe --help
```

会显示支持的量化参数，部分显示如下

```text
allowed quantization types
-----------------------------------------------------------------------------

  40  or  Q1_0    :  1.125 bpw quantization
  41  or  Q2_0    :  2.25 bpw quantization (group 64)
   2  or  Q4_0    :  4.34G, +0.4685 ppl @ Llama-3-8B
   3  or  Q4_1    :  4.78G, +0.4511 ppl @ Llama-3-8B
  38  or  MXFP4_MOE :  MXFP4 MoE
   8  or  Q5_0    :  5.21G, +0.1316 ppl @ Llama-3-8B
   9  or  Q5_1    :  5.65G, +0.1062 ppl @ Llama-3-8B
  19  or  IQ2_XXS :  2.06 bpw quantization
  20  or  IQ2_XS  :  2.31 bpw quantization
  28  or  IQ2_S   :  2.5  bpw quantization
  29  or  IQ2_M   :  2.7  bpw quantization
  24  or  IQ1_S   :  1.56 bpw quantization
  31  or  IQ1_M   :  1.75 bpw quantization
  36  or  TQ1_0   :  1.69 bpw ternarization
  37  or  TQ2_0   :  2.06 bpw ternarization
  10  or  Q2_K    :  2.96G, +3.5199 ppl @ Llama-3-8B
  21  or  Q2_K_S  :  2.96G, +3.1836 ppl @ Llama-3-8B
  23  or  IQ3_XXS :  3.06 bpw quantization
  26  or  IQ3_S   :  3.44 bpw quantization
  27  or  IQ3_M   :  3.66 bpw quantization mix
  12  or  Q3_K    : alias for Q3_K_M
  22  or  IQ3_XS  :  3.3 bpw quantization
  11  or  Q3_K_S  :  3.41G, +1.6321 ppl @ Llama-3-8B
  12  or  Q3_K_M  :  3.74G, +0.6569 ppl @ Llama-3-8B
  13  or  Q3_K_L  :  4.03G, +0.5562 ppl @ Llama-3-8B
  25  or  IQ4_NL  :  4.50 bpw non-linear quantization
  30  or  IQ4_XS  :  4.25 bpw non-linear quantization
  15  or  Q4_K    : alias for Q4_K_M
  14  or  Q4_K_S  :  4.37G, +0.2689 ppl @ Llama-3-8B
  15  or  Q4_K_M  :  4.58G, +0.1754 ppl @ Llama-3-8B
  17  or  Q5_K    : alias for Q5_K_M
  16  or  Q5_K_S  :  5.21G, +0.1049 ppl @ Llama-3-8B
  17  or  Q5_K_M  :  5.33G, +0.0569 ppl @ Llama-3-8B
  18  or  Q6_K    :  6.14G, +0.0217 ppl @ Llama-3-8B
   7  or  Q8_0    :  7.96G, +0.0026 ppl @ Llama-3-8B
   1  or  F16     : 14.00G, +0.0020 ppl @ Mistral-7B
  32  or  BF16    : 14.00G, -0.0050 ppl @ Mistral-7B
   0  or  F32     : 26.00G              @ 7B
          COPY    : only copy tensors, no quantizing
```

量化导出命令

```shell
./bin/llama-quantize.exe ../Qwen3-0.6B-BF16.gguf ../Qwen3-0.6B-Q4_K_M.gguf Q4_K_M
```

作用：以 f16 GGUF 为输入，按 `Q4_K_M` 混合精度写出最终量化模型；目标文件已存在会被覆盖。

实测在本机笔记本上执行，纯cpu量化，1.4G原有gguf模型 -> 487M的量化gguf文件 大约几秒即可完成。

## 验证与运行

通过脚本验证导出的量化模型，gguf-py 同级目录执行，Qwen3-0.6B-Q4_K_M.gguf 为量化模型路径

```shell
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'./gguf-py'); from gguf import GGUFReader; r=GGUFReader('../Qwen3-0.6B-Q4_K_M.gguf'); print(str(r.get_field('general.architecture').contents()), int(r.get_field('general.file_type').contents()), len(r.tensors))"
```

输出

```text
qwen3 15 311
```

说明

```text
qwen3   15   311
 ↑       ↑     ↑
架构名  量化类型码  张量条目数
```

### 加载并推理（llama-cli）

**单轮**

```shell
./bin/llama-cli.exe -m ../Qwen3-0.6B-Q4_K_M.gguf --reasoning-budget 0 -p "你好，请介绍一下你自己" -n 64 -st
```

PS

如果本地已经安装了 Llama-GUI，可以

控制台响应

```text
PS D:\tmp\llm\llamacpp> ./bin/llama-cli.exe -m ../Qwen3-0.6B-Q4_K_M.gguf --reasoning-budget 0 -p "你好，请介绍一下你自己" -n 64 -st


Loading model...

▄▄ ▄▄
██ ██
██ ██  ▀▀█▄ ███▄███▄  ▀▀█▄    ▄████ ████▄ ████▄
██ ██ ▄█▀██ ██ ██ ██ ▄█▀██    ██    ██ ██ ██ ██
██ ██ ▀█▄██ ██ ██ ██ ▀█▄██ ██ ▀████ ████▀ ████▀
                                    ██    ██
                                    ▀▀    ▀▀

build      : b12810-ca123ba76
model      : ../Qwen3-0.6B-Q4_K_M.gguf
ftype      : Q4_K - Medium
modalities : text

available commands:
  /exit or Ctrl+C     stop or exit
  /regen              regenerate the last response
  /clear              clear the chat history
  /read <file>        add a text file
  /glob <pattern>     add text files using globbing pattern



> 你好，请介绍一下你自己
好的，用户问“你好，请介绍一下你自己”，我需要先回应他的问候，然后介绍自己。首先，用户可能对我的身份感兴趣，所以应该简要说明我的身份，比如“我是一个AI助手”。接着，要确认用户是否需要帮助，这样用户会觉得被重视。同时

[ Prompt: 318.0 t/s | Generation: 99.0 t/s ]


Exiting...
```

非思考模式的连续对话

```shell
./bin/llama-cli.exe -m ../Qwen3-0.6B-Q4_K_M.gguf --reasoning-budget 0 -p "你是小助手" --chat-template-kwargs '{"enable_thinking": false}' -n 640
```

更多启动相关参数在单独的大模型部署文章中介绍。

### lora的运行和量化

准备文件，之前训练好的或者checkpoint备份的lora文件，这两个是必须的，先放到文件夹中 lora 中。

```text
adapter_config.json	1.1 KB	LoRA 结构：r=8、alpha=32、7 个 target modules	✅ 必需（HF 加载 + GGUF 转换）
adapter_model.safetensors	20.2 MB	LoRA 权重本体	✅ 必需
```

在convert_hf_to_gguf.py 所在目录安装

```shell
.venv\Scripts\python.exe -m pip install peft
```

可以直接和原模型加载一起运行,以下为示例脚本，根据实际情况调整

```shell
# 保存为 run_lora_hf.py，用 llamacpp\.venv 跑
# lora 中就是 adapter_config.json 和 adapter_model.safetensors 文件
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_dir = r"D:\tmp\llm\Qwen3-0.6B"
lora_dir = r"D:\tmp\llm\lora"

# tokenizer 必须用 base 目录（checkpoint 的 tokenizer_config 没有 chat_template）
tok = AutoTokenizer.from_pretrained(base_dir)
model = AutoModelForCausalLM.from_pretrained(base_dir, dtype="auto")
model = PeftModel.from_pretrained(model, lora_dir).eval()

msgs = [{"role": "user", "content": "你好，请介绍一下你自己"}]
text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True,
                               enable_thinking=False)   # 训练若是思考模式则去掉这句
ids = tok(text, return_tensors="pt")
out = model.generate(**ids, max_new_tokens=1024, do_sample=True,
                     temperature=0.7, top_p=0.8)
print(tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True))
```

注意：

- transformers 5.24.1 用 dtype="auto"；旧版写 torch_dtype="auto"。
- 这是 CPU 推理，0.6B 约几 token/s，够冒烟验证。
- 不需要把 LoRA 合并进 base，PeftModel 运行时自动叠加。

控制台输出

```text
Loading weights: 100%|██████████████████████████████████████████████████████████████| 311/311 [00:00<00:00, 717.18it/s]
你好！我是你的虚拟助手，可以帮你解答问题、提供帮助或者分享知识。有什么我可以帮你的吗？😊
```



#### lora转为gguf

需要下载 convert_lora_to_gguf.py 文件，放到之前的 convert_hf_to_gguf.py 所在目录

```shell
curl.exe -L -o llamacpp\convert_lora_to_gguf.py https://raw.githubusercontent.com/ggml-org/llama.cpp/master/convert_lora_to_gguf.py
```

走镜像地址更快：[https://cdn.jsdelivr.net/gh/ggml-org/llama.cpp@master/convert_lora_to_gguf.py](https://cdn.jsdelivr.net/gh/ggml-org/llama.cpp@master/convert_lora_to_gguf.py)

然后在此目录下执行命令将原有格式转为f16的gguf格式

```shell
.venv\Scripts\python.exe ./convert_lora_to_gguf.py  --base ../Qwen3-0.6B --outtype f16  --outfile ../checkpoint-100-f16.gguf  ../lora
```

**注意：**

- \--base 必须指向本地 Qwen3-0.6B基座模型，否则会尝试联网/找不到目录。
- \--outtype 默认是 f32（40 MB），显式写 f16 得到约 20 MB；想要更小可 q8_0（约 10 MB）。
  - \--**outtype 不是量化档位**。它在这个脚本里**只是个"输出浮点存储类型"的标记**，跟 llama-quantize 里的 Q4_K_M / Q8_0 完全是两套概念
- 预期日志：Using model architecture: qwen3 → Model successfully exported to ...。
- 转换只用 torch/transformers/safetensors（venv 已有），不需要装 peft。

**保存精度**

LoRA 训练出来的 A/B 两个低秩小矩阵，**常见保存精度是 bf16 或 fp16**，且因为本身一般只有几十M，所以也不量化，同时量化后效果也不好。



**是否基座模型和lora进度需要一致？**

可以不一致：量化精度

llama.cpp 现在的 LoRA 是运行时相加（Wx + B(Ax)），不是预先把 BA 折进 W。所以：基座是 Q4_K_M / Q8_0 / Q6_K 都行，适配器保持 f16 全精度

#### lora的gguf运行

一次性控制台对话

```shell
./bin/llama-cli.exe -m ../outputq4/Qwen3-0.6B-Q4_K_M.gguf     --lora ../Qwen3-0.6B-lora_f16.gguf --jinja --chat-template-kwargs '{"enable_thinking": false}' -p "你是qwen小助手" -n 256 -st   
```

服务方式运行

```shell
./bin/llama-server.exe -m ../outputq4/Qwen3-0.6B-Q4_K_M.gguf     --lora ../Qwen3-0.6B-lora_f16.gguf --jinja --chat-template-kwargs '{"enable_thinking": false}' --host 127.0.0.1 --port 8081 -c 2048
```

通过浏览器访问 http://127.0.0.1:8081 会出现一个对话界面



# linux下的处理

## 环境准备

建立一个llamacpp文件用来存放相关必须数据，进入这个文件夹后执行；

下载转换必须的脚本等相关数据

```shell
../.venv/bin/python3.13 download_llama_convert_min.py
```

安装必须的一些依赖(这里选择的是cpu版本，如果是有显卡的话可以选择安装完版本，不加后面的index-url的cpu版本即可)

```shell
uv pip install "torch==2.15.0" --index-url https://download.pytorch.org/whl/cpu
uv pip install "transformers==5.24.1" "numpy==2.5.5" "safetensors==0.8.0"
```

或者使用其他源加速

```shell
uv pip install torch torchvision torchaudio \
  --index-url https://mirrors.aliyun.com/pytorch-wheels/cpu
uv pip install torch torchvision torchaudio \
  --index-url https://mirrors.aliyun.com/pytorch-wheels/cpu \
  --extra-index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

验证：

```shell
../.venv/bin/python -c "import torch, transformers, numpy, safetensors; print(torch.__version__, transformers.__version__, numpy.__version__, safetensors.__version__)"
```

注意：gguf 不用装，转换脚本会自动加载 llamacpp/gguf-py



同样下载lora的转换脚本

```shell
curl -LO https://cdn.jsdelivr.net/gh/ggml-org/llama.cpp@b12810/convert_lora_
to_gguf.py
```

llama-quantize 文件准备

Release 主页（手动挑包）\
https://github.com/ggml-org/llama.cpp/releases/latest

进页面后拉到 Assets，找名字形如 llama-bXXXXX-bin-ubuntu-x64.tar.gz 的包，那就是 Linux x86_64 的 CPU 预编译版 。

或者官方在 latest release 里放了一个 `nightly-tag.txt`，里面是当前构建号，可以拼出直链

```shell
LLAMA_BUILD=$(curl -sL https://github.com/ggml-org/llama.cpp/releases/latest/download/nightly-tag.txt)

# 2. 下载 Linux x64 CPU 包
curl -LO "https://github.com/ggml-org/llama.cpp/releases/download/${LLAMA_BUILD}/llama-${LLAMA_BUILD}-bin-ubuntu-x64.tar.gz"
```

当前最新的下载

```shell
curl -LO "https://github.com/ggml-org/llama.cpp/releases/download/b12810/llama-b12810-bin-ubuntu-x64.tar.gz"
```

或者使用一些加速地址

```shell
curl -fLO https://gh-proxy.org/https://github.com/ggml-org/llama.cpp/releases/download/b12810/llama-b12810-bin-ubuntu-x64.tar.gz
```

## 转换与运行

### 模型HF -> f16 GGUF

转换原始模型为f16的gguf格式，几分钟内执行完毕

```shell
uv run convert_hf_to_gguf.py ../models/Qwen3-0.6B \
  --outtype f16 \
  --outfile ./Qwen3-0.6B-f16.gguf
```

### f16 -> Q4_K_M（约 484 MB）

解压llamabin文件

```shell
mkdir llamabin
huito@pc:/mnt/d/opt/lora_learn/llamacpp$ tar -xzvf llama-b12810-bin-ubuntu-x64.tar.gz -C llamabin
```

执行

```shell
./llamabin/llama-b12810/llama-quantize \
  ./Qwen3-0.6B-f16.gguf \
  ./Qwen3-0.6B-Q4_K_M.gguf \
  Q4_K_M
./llamabin/llama-b12810/llama-quantize: error while loading shared libraries: libgomp.so.1: cannot open shared object file: No such file or directory
```

报错

```shell
./llamabin/llama-b12810/llama-quantize: error while loading shared libraries: libgomp.so.1: cannot open shared object file: No such file or directory
```

安装报错提示的相关依赖

```shell
sudo apt-get update && sudo apt-get install -y libgomp1
```

然后重新执行，大约二十多秒完成

```shell
./llamabin/llama-b12810/llama-quantize \
  ./Qwen3-0.6B-f16.gguf \
  ./Qwen3-0.6B-Q4_K_M.gguf \
  Q4_K_M
```

验证导出

```shell
uv run python -c "
import sys
sys.path.insert(0, 'gguf-py')
from gguf import GGUFReader
r = GGUFReader('./Qwen3-0.6B-Q4_K_M.gguf')
print(r.get_field('general.architecture').contents(),
      int(r.get_field('general.file_type').contents()),
      len(r.tensors))
"
```

期望输出

```text
qwen3 15 311
```

### 导出 LoRA 为 GGUF

```shell
uv run python convert_lora_to_gguf.py \
  --base ../models/Qwen3-0.6B \
  --outtype f16 \
  --outfile ./Qwen3-0.6B-lora-f16.gguf \
  ../outputs/lora_text2sql/checkpoint-100
```

预期日志 Using model architecture: qwen3 → Model successfully exported，产物约 20 MB。\
可选更小：--outtype q8_0（约 10 MB）。\
注意默认是 f32（约 40 MB），必须显式 f16。

## 运行Lora+量化模型

运行这些和win上一样，**单次对话测试**

```shell
./llamabin/llama-b12810/llama-cli \
  -m ./Qwen3-0.6B-Q4_K_M.gguf \
  --lora ./Qwen3-0.6B-lora-f16.gguf \
  --jinja --chat-template-kwargs '{"enable_thinking": false}' \
  -p "你好，请介绍一下你自己" -n 128 -st
```

**server模式运行**

```shell
./llamabin/llama-b12810/llama-server \
-m ./Qwen3-0.6B-Q4_K_M.gguf \
\--lora ./Qwen3-0.6B-lora-f16.gguf \
\--jinja --chat-template-kwargs '{"enable_thinking": false}' \
\--host 0.0.0.0 --port 8080 -c 2048
```

web界面：[http://127.0.0.1:8080](http://127.0.0.1:8080)

对话接口：

```shell
curl -sS http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3","messages":[{"role":"user","content":"你好"}],"max_tokens":128}'
```

# 更多概念

| 概念    | 一句话解释                                                         |
| ------- | ------------------------------------------------------------------ |
| HF 权重 | HuggingFace 仓库里的 `.safetensors`/`config.json`/tokenizer 等文件 |
| GGUF    | llama.cpp 的模型容器格式，把权重、词表、元数据打包成单文件         |
| f16     | 16 位浮点，转换中间态，精度高但体积大                              |

内存不足可用 `--use-temp-file` 或量化时降 `--max-buffer-size`

## 依赖表（版本为本文 venv 实测）

| 包名            | 本文实测版本 | 从零安装命令（参考）                                                                         | 为什么需要                                                                 | 缺失时典型报错                                                             |
| --------------- | ------------ | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| torch           | 2.15.0+cpu   | `python -m pip install "torch==2.15.0+cpu" --index-url https://download.pytorch.org/whl/cpu` | HF 模型加载 / 张量运算                                                     | `ModuleNotFoundError: No module named 'torch'`；脚本预检直接打印该安装命令 |
| numpy           | 2.5.5        | `python -m pip install "numpy==2.5.5"`                                                       | 数组与权重转换基础依赖                                                     | `ModuleNotFoundError: No module named 'numpy'`                             |
| transformers    | 5.24.1       | `python -m pip install "transformers==5.24.1"`                                               | 读取 Qwen3 配置/权重映射；5.x 本文转换成功                                 | `ModuleNotFoundError: No module named 'transformers'`，或架构不被识别      |
| sentencepiece   | 0.2.3        | `python -m pip install "sentencepiece==0.2.3"`                                               | 词表/分词器相关转换                                                        | `ImportError: cannot import name ... sentencepiece`                        |
| safetensors     | 0.8.0        | `python -m pip install "safetensors==0.8.0"`                                                 | 读取 `model.safetensors`（日志 `indexing model part 'model.safetensors'`） | `cannot import name 'safe_open'` / 无法索引权重分片                        |
| protobuf        | 7.36.2       | `python -m pip install "protobuf==7.36.2"`                                                   | GGUF/tokenizer 序列化辅助                                                  | `TypeError: Descriptors cannot be created directly`（版本过旧时）          |
| pyyaml          | 6.0.4        | `python -m pip install "pyyaml==6.0.4"`                                                      | 读取模型 YAML 配置                                                         | `ModuleNotFoundError: No module named 'yaml'`                              |
| tqdm            | 4.70.1       | `python -m pip install "tqdm==4.70.1"`                                                       | 转换/写出进度条（日志 `Writing: 100%`）                                    | 缺失不致命，进度条消失                                                     |
| huggingface-hub | 2.5.0        | 随 `transformers` 自动安装                                                                   | HF 仓库/文件解析                                                           | `LocalModelNotFoundError` 或无法解析 repo id                               |
| tokenizers      | 0.23.3       | 随 `transformers` 自动安装                                                                   | 词表编码                                                                   | 词表写出阶段报错                                                           |

> `gguf` **不在 pip 包列表里**（`importlib.metadata.version('gguf')` 抛 `PackageNotFoundError`）：
> 本文通过 `sys.path.insert(0, 'llamacpp/gguf-py')` 直接使用本地源码

- **为什么不要直接 `pip install -r requirements-convert_hf_to_gguf.txt`**：它会按 pin 覆盖当前 venv——Python 3.13 (<3.15) 会把 torch 从 `2.15.0+cpu` 降到 `2.11.0`（触发大体积 wheel 下载），把 transformers 从 `5.24.1` 降到 `4.57.6`，把 protobuf 从 `7.36.2` 降到 `<5`；还会额外 pip 安装 `gguf`，与本地 `gguf-py` 源码路径产生重复来源。**本文实际做法**：未降级、未补装任何包，遇到缺失的手动补上。
