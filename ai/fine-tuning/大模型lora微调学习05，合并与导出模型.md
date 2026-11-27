大模型lora微调，合并与导出

# 直接合并导出

说明：一般情况在生产环境可能存在多个lora+一个基座模型的情况，此时不会合并导出模型，而是根据业务动态匹配相应的lora动态加载。

```shell
llamafactory-cli export configs/export_text2sql.yaml
```

export_text2sql.yaml 的内容

```yaml
### LoRA 合并导出配置：把 text2sql 适配器合并进基座，得到一个可独立部署的模型
### 命令：llamafactory-cli export configs/export_text2sql.yaml
### 说明：合并后模型约 1.43GB，是「完整模型」；不合并则只有几十 MB 的适配器
model_name_or_path: /mnt/d/opt/lora_learn/models/Qwen3-0.6B
adapter_name_or_path: /mnt/d/opt/lora_learn/outputs/lora_text2sql/checkpoint-100
template: qwen3_nothink
finetuning_type: lora
export_dir: /mnt/d/opt/lora_learn/outputs/merged_text2sql
export_size: 2
export_device: cpu
export_legacy_format: false
```

## 更多导出配置

```yaml
### model（基础模型与适配器）
model_name_or_path: null                 # 默认: null（必填）；基座模型路径或 HF/ModelScope ID，必须未量化
adapter_name_or_path: null               # 默认: null；LoRA 适配器路径，逗号分隔可多适配器串行合并；与 export_quantization_bit 互斥
template: null                           # 默认: null；对话模板，必须与训练一致（qwen/llama3/qwen2_vl…）
finetuning_type: lora                    # 默认: lora；标注用，export 主要靠 adapter_name_or_path 推断
trust_remote_code: false                 # 默认: false；Qwen/GLM/VL 等自定义代码模型需设 true
model_revision: main                     # 默认: main；远端模型 branch/tag/commit
cache_dir: null                          # 默认: null；下载缓存目录，null 走 HF 默认缓存
use_fast_tokenizer: true                 # 默认: true；用 tokenizers 快分词
resize_vocab: false                      # 默认: false；是否按新增 token 调整 embedding
add_tokens: null                         # 默认: null；逗号分隔新增普通 token
add_special_tokens: null                 # 默认: null；逗号分隔新增特殊 token
low_cpu_mem_usage: true                  # 默认: true；低内存加载
rope_scaling: null                       # 默认: null；linear/dynamic/yarn/llama3 等长上下文缩放
flash_attn: auto                         # 默认: auto；auto/disabled/sdpa/fa2
infer_dtype: auto                        # 默认: auto；导出权重精度 auto/float16/bfloat16/float32
hf_hub_token: null                       # 默认: null；推 HF 用
ms_hub_token: null                       # 默认: null；推 ModelScope 用
om_hub_token: null                       # 默认: null；推 Modelers 用

### export（合并导出主开关）
export_dir: null                         # 默认: null（必填）；合并后完整模型输出目录
export_size: 1                           # 默认: 1（GB）；分片大小，大模型建议 2~5
export_device: cpu                       # 默认: cpu；cpu/auto，显存不够走 cpu，有卡可设 auto
export_legacy_format: false              # 默认: false；false=.safetensors（推荐），true=.bin 老格式
export_hub_model_id: null                # 默认: null；非空则导出后自动推到 HF/ModelScope 仓库

### quantization（合并后再量化，不能与 adapter_name_or_path 同次跑）
export_quantization_bit: null            # 默认: null；4 或 8，设了走 GPTQ/AWQ/bnb 后量化
export_quantization_dataset: null        # 默认: null；校准集 jsonl，GPTQ/AWQ 必填
export_quantization_nsamples: 128        # 默认: 128；校准样本数
quantization_method: gptq                # 默认: gptq；gptq/awq/bnb/aqlm/quanto/eetq/hqq/mxfp4

### 通用/推理侧（export 进程内加载用，不写进产物）
infer_backend: huggingface               # 默认: huggingface；huggingface/vllm/sglang
offload_folder: null                     # 默认: null；低显存卸载目录，null 不卸载
use_cache: true                          # 默认: true
print_param_status: false                # 默认: false；调试打印参数状态
```

# 配置说明

## adapter_name_or_path

支持写多个（逗号分隔或 YAML 列表），意思是把多个 LoRA 适配器按你给出的顺序，依次叠加合并到同一个基座上，不是“任选一个”，也不是“多适配器同时在线切换”。

- **顺序敏感**：`A,B` 和 `B,A` 数值上不完全等价（浮点累加顺序不同，且第二个 adapter 是作用在“已合并 A 的模型”上再算 ΔW）。
- **能力叠加但可能互相干扰**：比如 `sft,legal` 是“先通用对话再法律风格”，反过来可能把通用口吻冲掉。
- **rank/alpha/target_modules 要兼容**：多个 adapter 的 `target_modules` 不一致时，没覆盖到的层就只吃前一个的增量。
- **训练时不能这么用**：`llamafactory-cli train` 阶段传多个会直接报错 `only a single LoRA adapter is supported`，多 adapter 只用于 **export/merge 或 inference 合并**。
- **量化基座不支持多 adapter**：`quantization_bit` 或已是 4bit/8bit 模型时，传多个会报 `Quantized model only accepts a single adapter`，必须先 fp16 合完再量化。
- 什么时候真需要写多个
  - 分阶段训练：CPT LoRA → SFT LoRA → DPO LoRA，想一次性叠回基座
  - 多能力拼装：通用 SFT + 某领域小 LoRA
  - 做消融：`base+sft` vs `base+sft+domain` 各导一份对比
- 什么时候别写多个
  - 只是想“切换不同 LoRA 推理” → 用单 adapter 多次起服务，或 vLLM 多 adapter 热切，别在 export 里堆
  - 想做**权重平均（model soup）**​ → LLaMA-Factory 这个字段不是干这个的，得用 mergekit 之类
  - 量化导出那一步 → 只留一个路径，或先合完再二次 export 量化

## low_cpu_mem_usage

low_cpu_mem_usage 是 LLaMA-Factory / transformers 加载模型时的内存峰值优化开关，默认 True（LLaMA-Factory 里默认开，CLI 可用 --no_low_cpu_mem_usage 关掉）。\
**它到底做了什么？**\
传统 from_pretrained 加载流程是：

1\.
先按 config 在 CPU RAM 里建一个随机初始化的完整模型（占一份模型大小）

2\.
再把磁盘上的 safetensors/bin 权重整个读进 RAM（又占一份）

3\.
最后把权重 copy 进模型骨架 → 峰值 RAM ≈ 2 × 模型体积。7B bf16 就是 ~28GB，70B 直接 280GB，很多机器还没开始合并就被 OS kill。

开 low_cpu_mem_usage=True 后改成：

1\.
用 meta device​ 建空壳（只记 shape，不分配真实内存）

2\.
按分片（shard）从磁盘读权重，直接灌进最终位置

3\.
峰值 RAM 从 2× 降到 1× 模型体积 + 单个分片缓冲

**在 llamafactory-cli export 里的实际意义**\
•合并 LoRA 时：基座 + 适配器 + 中间态本来就要占内存，开这个能避免“加载基座那一刻就双份爆 RAM”。\
export_device: cpu​ 时尤其重要——合并全程在 CPU 跑，不开这个 13B/70B 很容易 OOM。\
•不影响导出结果：权重数值、分片方式、safetensors 格式都不变，只影响“加载那一步”的 RAM 曲线。\
不省显存：它只管 CPU RAM；要省显存得靠 export_device: cpu、量化、offload_folder。

**什么时候可以关**（--no_low_cpu_mem_usage）\
•小模型（≤1.5B）、内存充裕，想要加载稍快一点（老实现下 meta-device 逐分片灌权重比“一次性读+拷贝”略慢）\
某些自定义架构 / 老 bin 格式在 meta device 下初始化报错，关掉回退到传统路径能绕过\
调试时想看“未优化前的真实内存行为”\
**常见误解**\
❌ “开了它就能用 CPU 跑 70B 推理” → 错，它不卸载、不量化，只是加载不炸内存\
❌ “它和 device_map=auto 是一回事” → 错，前者管 RAM 峰值，后者管 CPU/GPU 切分\
❌ “export 完产物会变小” → 错，产物大小只由 infer_dtype / export_quantization_bit 决定

实践建议：export 阶段保持默认 true 别动；只有遇到 meta-device 初始化异常再临时 --no_low_cpu_mem_usage 试。

## rope_scaling

rope_scaling 是给位置编码做长上下文外推的开关，默认 null（不缩放，用模型原生上下文长度）。设了它，模型就能在超过训练长度的序列上保持位置关系不崩。\
**常见取值**\
•linear：把位置索引按比例压小，简单但长文本精度一般，适合小倍数扩展\
•dynamic：推理时按实际长度动态插值，短序列不受影响、长序列才缩放，比 linear 稳\
•yarn：NTK 感知 + 分段插值，长上下文效果较好，Qwen 系常用\
•llama3：Llama 3 专用的分段缩放方案，配 Llama 3 系列用\
•还有 longrope、mrope（多模态）等，按模型支持选\
**关键注意**\
•必须和训练时一致：微调时用了哪种缩放，export/推理就得配同一种，否则位置编码错位，输出会乱。\
•要带参数：一般写成 rope_scaling: {type: yarn, factor: 4.0} 这种形式，factor 是扩展倍数，不是只写个类型名。\
•不是万能：缩放只缓解位置外推，超太长仍会掉点；真要长上下文，训练阶段就得用长样本 + 对应缩放。\
•不改权重体积：只影响计算方式，导出产物大小不变。\
一句话：短任务别碰，默认 null；要长上下文就选和训练一致的 type + 合理 factor

## export_size

export_size 是合并导出时权重文件的分片大小，单位 GB，默认 1。它只决定产物切成几个文件，不改权重数值、不改总体积。\
它做什么\
导出时按这个大小把权重切分成多个 model-00001-of-000xx.safetensors 分片。\
例如 7B bf16 约 15GB：\
export_size: 1 → 约 15 个分片\
export_size: 5 → 约 3 个分片\
一句话：export_size 只管“切成几块”，只影响存储和传输，不影响精度和体积；

## flash_attn

flash_attn 是 LLaMA-Factory 里控制注意力后端的开关，默认 auto。它只影响“计算 attention 时用哪套 kernel”，不改变权重数值、不改变导出产物大小，但会影响加载/训练/推理的速度和显存。\
可选值（LLaMA-Factory 主线）\
•auto（默认）：让 transformers 自己挑。通常优先 SDPA，环境满足且模型支持时可能走 FA2。\
•sdpa：PyTorch 原生 scaled_dot_product_attention，零额外依赖，CPU/GPU 都能跑，底层自动 dispatch（在支持的 CUDA 上可能内部用 Flash kernel）。生产最稳的默认替代。\
•fa2：强制 FlashAttention-2，需要装 flash-attn 包 + Ampere 及以上 NVIDIA 卡（A100/4090/H100）。长序列下最快、显存最省。\
•disabled：强制走 eager（朴素 QK^T → softmax → ·V），最慢最占显存，但唯一能干净返回 attention weights，调试/导出 ONNX 时用。

（新版还有 fa3，目前主要 GPT-OSS 类模型走，普通 Qwen/Llama 用不到）

**在 export 阶段的实际意义**\
•合并 LoRA 本身不怎么吃 attention kernel，export 时这个参数影响很小，保持 auto 就行。\
•真正影响大的是 train / chat / api / vLLM 前加载：长上下文（≥4k）用 fa2 比 sdpa 再快一档、显存再低一截；没装 flash-attn 硬写 fa2 会报 ImportError。\
•三种后端数学等价，但 bf16 下累加顺序不同会有 ~1e-3 级数值抖动，不影响训练稳定性，但做严格复现实验时要固定同一个值。\
•某些模型有强制：Gemma-2 软帽要 fa2；Youtu-VL 不支持 sdpa 强制 eager；这些 LLaMA-Factory 会自动覆盖你写的值。

## infer_dtype

- 作用：决定**未量化权重**在导出/加载时用什么浮点容器存。
- 可选：`auto` / `float16` / `bfloat16` / `float32`
- `auto` 的推断逻辑：硬件支持 BF16 且模型 config 允许 → `bfloat16`；否则 CUDA/NPU 支持 FP16 → `float16`；再不行 → `float32`

简单来说，不量化时的配置，可选 fp16/bf16/fp32

## export_quantization_bit

- 作用：**是否把合并后的权重做训练后量化（PTQ）**，以及压到几 bit。
- 可选值（GPTQ 路径）：`2 / 3 / 4 / 8`；bnb 是 `4 / 8`；HQQ `1-6/8`；EETQ `8`
- 设了它 → 走 `export_quantization_method`（默认 gptq，也可 awq/bnb/hqq/eetq…）+ 必须给 `export_quantization_dataset` 校准集
- 影响：
  - 体积：4bit ≈ 原 fp16 的 1/4，8bit ≈ 1/2
  - 推理显存大幅下降，但**需要专用 kernel**（AutoGPTQ / ExLlama / vLLM-AWQ 等）
  - 有精度损失，数学/逻辑任务敏感
- **硬约束**：**不能和 `adapter_name_or_path` 同次跑**；必须“先 merge 出 fp16 完整模型 → 第二次 export 只带 `model_name_or_path=上一步 + export_quantization_bit=4 + 校准集`”

## use_cache

模型推理时是否启用 KV Cache​ 的开关，默认 True。它只影响生成阶段的计算方式，不改权重、不改产物。

推理保持 `True`（默认），训练和要完整 attention 的场景设 `False`；对 export 导出结果无影响。

## 验证导出模型

重新加载模型验证

```shell
python3 - <<'PY'
from transformers import AutoModelForCausalLM, AutoTokenizer
p = "/mnt/d/opt/lora_learn/outputs/merged_text2sql"
m = AutoModelForCausalLM.from_pretrained(p, device_map="cpu")
t = AutoTokenizer.from_pretrained(p)
print("合并模型加载成功，参数量约", round(sum(x.numel() for x in m.parameters())/1e8,2), "亿")
PY
```

输出

```text
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████████████████████████| 310/310 [00:00<00:00, 1127.86it/s]
合并模型加载成功，参数量约 5.96 亿
```

或者直接启动cli对话

```shell
llamafactory-cli chat --model_name_or_path outputs\merged_text2sql  \
  --template qwen3_nothink \
  --trust_remote_code true
```

## 为什么合并后的模型体积变小了

**合并后变小是因为冗余的 `lm_head` 副本被去重了，BF16 精度没变、参数没丢，是更干净的保存方式**

原因：

**下载的模型文件里就带着它**\
`models/Qwen3-0.6B/config.json` 里有一行：

```
"tie_word_embeddings": true
```

tie_word_embeddings = true  = 输入嵌入层和输出投影层共享同一份矩阵，直觉上：一个词"输入时的向量"和"输出时判断它该不该出现"，用的是同一个坐标系。好处是省一个 embedding 矩阵的参数（本例约 1.49 亿参数 = 296.75 MB）

这个配置会在合并的时候自动继承使用。

**tie=true = "这两个矩阵是同一个"，文件只需存一份；你的基座多存了一份，导出时去掉了**

**验证**

基座 `model.safetensors` 内部，两个张量**真实同时存在**（通过ai提供的脚本可以查询出来）：

| **张量**                    | **大小**  | **shape**       | **存储区间**           |
| :-------------------------- | :-------- | :-------------- | :--------------------- |
| `lm_head.weight`            | 296.75 MB | \[151936, 1024] | (0, 311164928)         |
| `model.embed_tokens.weight` | 296.75 MB | \[151936, 1024] | (311164928, 622329856) |
