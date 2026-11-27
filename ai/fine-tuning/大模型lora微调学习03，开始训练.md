大模型lora微调学习03，开始训练

一次性训练一个数据集，不要混合跑。在激活Python虚拟环境后开始。

如果有非思考模式，则优先使用： template: qwen3_nothink

# 编写命令文件

由于命令的选项非常多，所以建议编写单独的yaml配置文件，然后命令中通过读取配置文件来执行。

当前你也可以通过传统的 --参数 值这一套传递。

这里创建 /mnt/d/opt/lora_learn/configs/lora_text2sql.yaml 文件

```yaml
### ============================================================
### 任务一：text-to-sql（自然语言问题 -> SQL）LoRA 微调配置
### 框架：LLaMA-Factory v0.9.5
### 硬件目标：纯 CPU（无 NVIDIA 显卡），fp32 精度
### 启动命令：llamafactory-cli train configs/lora_text2sql.yaml
### ============================================================

### model 模型
# 使用本地已下载好的模型目录（WSL 路径），避免训练时联网
model_name_or_path: /mnt/d/opt/lora_learn/models/Qwen3-0.6B
trust_remote_code: true

### method 训练方法
stage: sft                      # sft = 监督微调
do_train: true #仅有训练的时候设置为true，其他时候为false 比如 导出/合并 LoRA 权重
finetuning_type: lora           # 只训练 LoRA 适配器，不碰原模型权重
lora_rank: 8                    # LoRA 秩，越大可学习能力越强、参数越多（常用 8/16/32）
lora_alpha: 32                  # LoRA 缩放系数，一般是 rank 的 2~4 倍
lora_dropout: 0.05 #训练时，LoRA 支路的输入向量里每个元素有 5% 的概率被置零
lora_target: all                # 对所有线性层加 LoRA（q/k/v/o + mlp）
# 说明：CPU 上 lora_target: all 依然可行，因为只训练少量适配器参数

### dataset 数据集
dataset: text2sql_train         # 对应 data/lf/dataset_info.json 里的键名
eval_dataset: text2sql_val      # 验证集，用于观察是否过拟合
dataset_dir: /mnt/d/opt/lora_learn/data/lf
template: qwen3_nothink         # 关键：不输出 <think> 思考过程，保证 SQL 干净
cutoff_len: 512                 # 序列最大长度；CPU 上不宜过大，512 对本任务够用
max_samples: 576                # 使用训练集全部 576 条
preprocessing_num_workers: 2    # CPU 机器别开太多进程，2 即可
dataloader_num_workers: 2

### output 输出
output_dir: /mnt/d/opt/lora_learn/outputs/lora_text2sql
logging_steps: 5                # 每 5 步打印一次日志，方便观察
save_steps: 100                 # 每 100 步存一次检查点
save_total_limit: 2             # 最多保留 2 个检查点，省磁盘
plot_loss: true                 # 训练结束画 loss 曲线图
overwrite_output_dir: true      # 重跑时覆盖旧结果（想要续训改成 false）
report_to: none                 # 不上报 wandb 等外部平台

### train 训练超参（CPU 专用设置）
per_device_train_batch_size: 1  # CPU 内存虽大但算力有限，batch=1 起步
gradient_accumulation_steps: 8  # 累积 8 步等效 batch=8，稳定训练
learning_rate: 1.0e-4           # LoRA 常用学习率
num_train_epochs: 3.0           # 训练 3 轮
lr_scheduler_type: cosine
warmup_ratio: 0.1
weight_decay: 0.0
optim: adamw_torch              # CPU 用 torch 原生优化器（不要用 8bit 量化优化器）
bf16: false                     # CPU 不支持 bf16，务必 false（官方样例是 true，那是 GPU 用法）
fp16: false                     # CPU 不支持 fp16
gradient_checkpointing: false   # CPU 上关掉，避免额外计算开销
ddp_timeout: 180000000

### eval 验证
per_device_eval_batch_size: 1
eval_strategy: steps
eval_steps: 100

```

## 参数说明

### lora_dropout

| **取值**          | **适用场景**                            |
| :-------------- | :---------------------------------- |
| `0.0`           | 数据量大（万级以上）、只训 1\~2 epoch。官方很多示例就是 0 |
| \*\*`0.05`\*\*​ | **最常用的默认档**，小到中等数据量的稳妥选择            |
| `0.1`           | 数据少（几百到几千条）、容易过拟合、或 rank 较大         |
| `> 0.1`         | 很少用。再大容易欠拟合，LoRA 本来就参数少，压太狠学不动      |

### lora_rank

lora_alpha

## 常见取值组合

| `lora_rank` | `lora_alpha` | `α/r` | 说明                |
| :---------- | :----------- | :---- | :---------------- |
| 8           | 8            | 1     | 保守，更新幅度小          |
| 8           | 16           | 2     | **最经典搭配**，官方默认档   |
| 16          | 32           | 2     | rank 翻倍，比值不变      |
| 64          | 16           | 0.25  | 大 rank 小缩放，稳定但学得慢 |
| 64          | 128          | 2     | 大 rank 标准配        |
| 8           | 32           | 4     | 激进，学习率要相应调小       |

**主流区间是 `α/r ∈ [1, 2]`。**

​ 超过 4 容易训崩，低于 0.5 基本学不动。

### learning_rate 学习速率

| **场景**             | **推荐 lr**                      |
| :----------------- | :----------------------------- |
| LoRA SFT（数据万级以内）   | \*\*`1e-4 ~ 2e-4`\*\*​         |
| LoRA SFT（数据十万级）    | `5e-5 ~ 1e-4`                  |
| LoRA + 大 rank（64+） | `5e-5 ~ 1e-4`（rank 大要保守）       |
| LoRA DPO / 偏好对齐    | `5e-6 ~ 5e-5`（**比 SFT 小一个量级**） |
| Full 全参微调          | `1e-5 ~ 2e-5`                  |
| Freeze 部分层         | `1e-5 ~ 5e-5`                  |
| 预训练（PT）            | `1e-5 ~ 5e-5`                  |

**偏好对齐阶段 lr 必须显著降低**

这是高频翻车点：DPO 用 `1e-4` 训，模型会迅速崩坏，表现为 chosen/rejected 的 reward 差距先涨后崩。

经验法则：**有效 batch 翻倍，lr 大致乘 `√2` 或翻倍**（线性缩放 / 平方根缩放两种流派）。

所以看到别人 `lr=2e-4` 效果好，先确认他的 batch 是不是你的两倍。

看训练日志的 loss 曲线：

| 现象                  | 诊断     | 处理             |
| :------------------ | :----- | :------------- |
| loss 平稳下降，后期趋缓      | 合适     | 不动             |
| loss 前几步剧烈震荡、出现 nan | 太大     | 降 2\~5 倍       |
| loss 几乎不动、一直高位      | 太小     | 提 2\~5 倍       |
| loss 前期降得快、后期突然反弹   | 太大或过拟合 | 先降 lr，再看 epoch |
| loss 降到很低但验证集变差     | 过拟合    | 降 epoch 或加正则   |

### num_train_epochs 同一批数据过几遍

* oRA 参数少，**欠拟合比过拟合更常见**，需要多过几遍
* 但超过 3\~5 轮，小数据集上很快就开始死记硬背
* 官方示例几乎清一色 `3.0`，是经过大量实践验证的稳妥起点

**按数据量推荐**

| 训练样本数         | 推荐 epochs                 |
| :------------ | :------------------------ |
| < 500         | `5 ~ 10`（数据太少，多过几遍，但要配早停） |
| 500 \~ 5000   | `3 ~ 5`                   |
| 5000 \~ 50000 | `2 ~ 3`                   |
| > 50000       | `1 ~ 2`                   |
| 预训练语料         | `1`（通常就一遍）                |
| DPO / 偏好对齐    | `1 ~ 2`（**偏好数据极易过拟合**）    |

**核心直觉**：数据越少，越需要多轮；数据越多，一轮就够。

**偏好对齐为什么要少**

DPO 这类方法对数据分布很敏感，多训几轮模型会过度拟合 chosen 的措辞风格，导致：

* 输出变得生硬、模板化
* 通用能力退化（alignment tax）
* reward 差距虚高但实际效果变差

所以 `stage: dpo` 时 `num_train_epochs` 通常压到 `1.0 ~ 2.0`。

# 执行命令

```shell
llamafactory-cli train configs/lora_text2sql.yaml
```

即可开始训练；

输出的信息大致如下：

```shell
[INFO|trainer.py:1469] 2026-11-26 21:17:31,873 >> ***** Running training *****
[INFO|trainer.py:1470] 2026-11-26 21:17:31,874 >>   Num examples = 576
[INFO|trainer.py:1471] 2026-11-26 21:17:31,874 >>   Num Epochs = 3
[INFO|trainer.py:1472] 2026-11-26 21:17:31,874 >>   Num update steps per epoch = 72
[INFO|trainer.py:1473] 2026-11-26 21:17:31,874 >>   Instantaneous batch size per device = 1
[INFO|trainer.py:1476] 2026-11-26 21:17:31,874 >>   Total train batch size (w. parallel, distributed & accumulation) = 8
[INFO|trainer.py:1477] 2026-11-26 21:17:31,874 >>   Gradient Accumulation steps = 8
[INFO|trainer.py:1478] 2026-11-26 21:17:31,874 >>   Total optimization steps = 216
[INFO|trainer.py:1479] 2026-11-26 21:17:31,878 >>   Number of trainable parameters = 5,046,272
{'loss': '2.968', 'grad_norm': '21.16', 'learning_rate': '1.818e-05', 'epoch': '0.06944'}
{'loss': '1.967', 'grad_norm': '13.77', 'learning_rate': '4.091e-05', 'epoch': '0.1389'}
....
{'loss': '0.007491', 'grad_norm': '1.864', 'learning_rate': '7.685e-05', 'epoch': '1.181'}
{'loss': '0.002275', 'grad_norm': '0.01122', 'learning_rate': '7.335e-05', 'epoch': '1.25'}
 44%|███████████████████████████████████▎                                             | 94/216 [16:14<20:51, 10.26s/it]
```

## 日志怎么看

### loss（训练交叉熵）

含义：该 logging_steps 区间内所有 batch 的平均交叉熵损失。衡量模型对训练样本的拟合程度。
注意：这是训练集​ loss，不是验证集。它只说明"背得多熟"，不说明"泛化多好"。下列是经验值说明。

| **数值范围**      | **含义**                   | **判断**                  |
| :------------ | :----------------------- | :---------------------- |
| `> 5.0`       | 模型完全没在学，或数据/模板严重错配       | ❌ 立刻停，查 `template`、数据格式 |
| `3.0 ~ 5.0`   | 训练刚起步（warmup 期常见），或学习率过小 | ⚠️ 看后续是否下降              |
| `1.5 ~ 3.0`   | 早期正常区间，模型在适应任务           | ✅ 正常                    |
| `0.8 ~ 1.5`   | 中期正常区间                   | ✅ 正常                    |
| `0.4 ~ 0.8`   | 后期正常收敛区间，**这是理想终点**​     | ✅ 健康                    |
| `0.2 ~ 0.4`   | 拟合较充分，数据量小时可能出现          | ⚠️ 开始留意验证集              |
| `0.05 ~ 0.2`  | 拟合过度，大概率开始背题             | ⚠️ 需要验证集确认              |
| `0.01 ~ 0.05` | **明显过拟合**，模型在记忆训练样本      | ❌ 该停了                   |
| `< 0.01`      | **严重过拟合**，梯度基本消失         | ❌ 训练已无意义                |
| `nan` / `inf` | 数值爆炸，lr 太大或数据有脏样本        | ❌ 立刻停                   |

不同场景的合理终点会变

| 场景                     | 健康 loss 终点                        |
| :--------------------- | :-------------------------------- |
| LoRA SFT（通用指令）         | `0.4 ~ 0.8`                       |
| LoRA SFT（格式化任务，如分类/抽取） | `0.1 ~ 0.5`                       |
| Full 全参微调              | `0.3 ~ 0.6`                       |
| 预训练（PT）                | `1.5 ~ 2.5`（本来就高，正常）              |
| DPO / 偏好对齐             | `0.3 ~ 0.7`（看 `pref_beta`，绝对值意义弱） |
| KTO                    | `0.4 ~ 0.8`                       |

**关键**：loss 的绝对值没有跨任务可比性。判断好坏永远要**结合验证集 loss 和实际推理效果**，不能只看这个数字。

### grad_norm（梯度范数）

含义：更新前所有可训练参数梯度的全局 L2 范数。反映"当前还有多少学习信号"。

&#x20;对 LoRA 来说，统计的是 `A`、`B` 两个矩阵的梯度。

| 数值范围         | 含义                | 判断          |
| :----------- | :---------------- | :---------- |
| `> 100`      | 梯度爆炸，lr 太大或数据异常   | ❌ 危险，会出 nan |
| `30 ~ 100`   | 偏大，训练初期或大 lr 时可见  | ⚠️ 观察是否快速回落 |
| `10 ~ 30`    | 训练初期正常区间          | ✅ 正常        |
| `1 ~ 10`     | **中后期健康区间**，最理想   | ✅ 正常        |
| `0.1 ~ 1`    | 收敛后期，学习信号减弱       | ⚠️ 接近尾声     |
| `0.01 ~ 0.1` | 梯度接近消失，几乎学不动了     | ⚠️ 该考虑停     |
| `< 0.01`     | 梯度消失，训练实质停滞       | ❌ 无意义       |
| `0`          | 参数完全冻结或 lr 已衰减到 0 | ❌ 检查配置      |
| `nan`        | 数值溢出              | ❌ 立刻停       |

几个特殊现象：

| 现象          | 含义                             |
| :---------- | :----------------------------- |
| 突然从 5 跳到 50 | 遇到异常 batch，数据里有脏样本或超长样本        |
| 周期性尖峰       | 数据按类别排序了，类别分布不均匀，缺乏 shuffle    |
| 一直很小（< 0.1） | lr 太小，或 `lora_target` 设错没挂上模块  |
| 一直是 0       | LoRA 参数没被正确注入，检查 `lora_target` |

### learning_rate（当前实际学习率）

含义：当前这一步优化器实际使用的 lr，**已经包含 warmup 和调度器的结果**，不是你在 yaml 里写的那个目标值。

| 数值范围（LoRA SFT） | 含义                       | 判断          |
| :------------- | :----------------------- | :---------- |
| `0`（前几步）       | warmup 刚开始，lr 从 0 线性爬升   | ✅ 正常        |
| `1e-6 ~ 1e-5`  | warmup 早期                | ✅ 正常        |
| `5e-5 ~ 2e-4`  | **LoRA 的合理工作区间**​        | ✅ 正常        |
| `> 5e-4`       | 偏大，容易震荡                  | ⚠️ 查是否设错    |
| `> 1e-3`       | 过大，几乎必崩                  | ❌ 检查配置      |
| 全程恒定不变         | 调度器设成了 `constant` 或没生效   | ⚠️ 确认是否符合预期 |
| 后期不衰减          | `lr_scheduler_type` 配置问题 | ⚠️ 检查       |

**按 stage 分**：

| 阶段                 | 合理 lr 区间      |
| :----------------- | :------------ |
| LoRA SFT           | `5e-5 ~ 2e-4` |
| Full SFT           | `1e-5 ~ 2e-5` |
| DPO / ORPO / SimPO | `5e-6 ~ 5e-5` |
| PPO                | `1e-6 ~ 1e-5` |
| 预训练                | `1e-5 ~ 5e-5` |

### epoch（已过数据遍数）

含义：当前已消耗的训练数据量，折算成"完整过几遍"。小数表示进度。

| 数值          | 含义                 |
| :---------- | :----------------- |
| `0 ~ 0.1`   | warmup 期，模型刚开始适应   |
| `0.1 ~ 0.5` | 快速下降期，loss 降幅最大    |
| `0.5 ~ 1.0` | 主要收敛期              |
| `1.0 ~ 2.0` | 精调期，**过拟合常在此段开始**​ |
| `> 2.0`     | 高风险过拟合区（小数据集上尤其）   |
| `> 3.0`     | 除非数据量很大，否则基本在背题    |

最后： 邮寄地址转换的命令和配置类似，这里不再重复展示。

# 训练中断了怎么办

## 怎么自动停止？

训练已经达到效果，或者过拟合了，需要手动停止。

### 前台运行（终端里直接敲的命令）

**按 `Ctrl + C`**

* 第一次按：训练循环收到 `KeyboardInterrupt`，**当前 step 结束后**中断，会尝试保存一个 checkpoint（取决于版本和配置）
* 如果卡住不动，再按一次 `Ctrl + C` 强制退出
* 连按三次会直接 kill，可能留下不完整的 checkpoint 文件

**注意**：LLaMA-Factory 基于 Transformers `Trainer`，`Ctrl+C` 会走 `Trainer.train()` 的异常处理，通常会：

1. 停掉 dataloader
2. 保存当前状态到 `output_dir/checkpoint-xxx`
3. 打印中断信息后退出

所以**优先用 `Ctrl+C`，别急着 `kill -9`**。

### 后台运行（`nohup` / `tmux` / `screen`）

手动找pid触发停止

```
# 找进程
ps aux | grep llamafactory-cli

# 优雅停止（发 SIGTERM，等同 Ctrl+C）
kill <PID>
```

查找彻底：

```shell
# 先看全貌
ps aux | grep -E "torchrun|deepspeed|llamafactory"

# 按进程组杀（推荐）
pkill -f "llamafactory-cli train"

# 如果还有残留的 python 训练进程
ps aux | grep python | grep train
kill <PID>
```

注意：如果是 nvidia 显卡还要查找显卡是否释放了，没有的话需要手动处理。

### 手动恢复训练

* LLaMA-Factory 会存 checkpoint。重跑时把对应 yaml 里的 `overwrite_output_dir: true` 改为 `false`，并设置 `resume_from_checkpoint: 上次checkpoint路径`，可从断点继续。

- 或者从头重来（数据量不大，CPU 也就几十分钟）。

怎么查看终止前的训练情况？

* 在配置的输出目录中，trainer_log.jsonl 是之前训练的进度日志
* checkpoint-xxx，是第x step保存的训练数据

chckpoint 中的文件说明：

```textplan
checkpoint-100/                          共 11 个文件，约 70MB（text2sql）
│
│  === 第一组：核心，推理/合并/部署都依赖，永远别删 ===
├── adapter_model.safetensors   20MB     [核心] LoRA 权重本体，学到的全部"知识"就在这一个文件里；
│                                        删了等于没训练，无法恢复（除非重训）
├── adapter_config.json         1.1KB    [核心] r=8、alpha=32、target_modules、基座路径；
│                                        框架靠它知道把权重接到基座的哪些层上，删了权重加载失败
│
│  === 第二组：推理需要，做对比/合并时要带上 ===
├── chat_template.jinja         4.1KB    [推理需要] qwen3_nothink 的对话模板，规定消息怎么拼接；
│                                        删了推理时格式可能错乱；若你用脚本里 apply_chat_template 则不必单独带
├── tokenizer.json              11MB     [推理需要] 分词器词表，文本转 token id；删了无法编码输入
├── tokenizer_config.json       720B     [推理需要] 分词器配置（特殊token、padding）；删了分词器可能报错
│
│  === 第三组：仅"从断点续训"时需要，不续训就删 ===
├── trainer_state.json          4.6KB    [可删·除非续训] 训练状态：停在哪步、epoch、完整 loss 历史；
│                                        我查进度读的就是它；不续训可删，但建议留着做实验记录
├── training_args.bin           5.4KB    [可删·除非续训] 训练超参的二进制序列化，续训时还原当时配置
├── optimizer.pt                39MB     [可删·除非续训] AdamW 优化器状态（动量等），占整个 checkpoint 一半以上；
│                                        不打算续训就删它，立刻省 39MB
├── scheduler.pt                1.1KB    [可删·除非续训] 学习率调度器状态，续训时接着算 lr
└── rng_state.pth               14KB     [可删·除非续训] 随机数状态，续训时保证数据打乱顺序接得上

│
│  === 无关紧要，可随手删 ===
└── README.md                   5.2KB    [可删] 自动生成的模型卡片模板，内容几乎全是 [More Information Needed] 占位符，无任何实际作用

【删除决策速查】
- 只想拿去推理/合并：保留前 5 个（约 31MB），删掉第三组 + README，省 39MB
- 想从断点接着训：11 个全部保留，一个都不能删
- 已合并成完整模型、LoRA 也不用留：整个 checkpoint 目录可删（但先确认 outputs/merged_* 已生成）

```
