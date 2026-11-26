LLaMAFactory数据主板

# LLaMA-Factory数据格式

## alpaca 格式

alpaca 格式适用于 单轮指令微调、预训练、偏好数据、KTO

格式为平铺字段：instruction/input/output

```json
[
  {
    "instruction": "人类指令（必填）",
    "input": "人类输入（选填）",
    "output": "模型回答（必填）",
    "system": "系统提示词（选填）",
    "history": [ //（选填）
      ["第一轮指令", "第一轮回答"],
      ["第二轮指令", "第二轮回答"]
    ]
  }
]
```

拼接逻辑：`instruction + "\n" + input` 合成用户侧输入，**history 里的回答也会参与 loss**。单轮就把 `history` 去掉。

LlamaFactory下的 /data/dataset_info.json 是 数据集注册表（也叫数据集索引/清单）。

它是「数据集名字 → 文件在哪 + 怎么解析」的映射表，训练时你只能通过这里的名字来引用数据，框架不会自动扫描目录。

如果有图片，相关格式示例：

```json
[
  {
    "instruction": "<image>这张图里是什么动物？",
    "input": "",
    "output": "是一只猫。",
    "history": [
      ["它是什么颜色的？", "橘色。"],
      ["<image>那这张呢？", "也是一只猫，白色。"]
    ],
    "images": ["mllm_demo_data/1.jpg", "mllm_demo_data/2.jpg"]
  }
]
```

## sharegpt 格式

ShareGPT 是 LLaMA-Factory 里**专门用来表达"多轮对话 + 多角色"**的样本结构。Alpaca 是扁平的 `instruction/input/output`，ShareGPT 则是一条 `conversations` 列表，每一轮是一个 `{from, value}` 对象

数据示例：

```json
[
  {
    "conversations": [
      {"from": "human", "value": "你好，我出生于1990年5月15日，我今天几岁？"},
      {"from": "gpt",   "value": "你今天36岁了。"}
    ],
    "system": "你是一个贴心的助手",
    "tools":  "[{\"name\": \"calculate_age\", \"description\": \"根据出生日期计算年龄\"}]"
  }
]
```

如果有图片的格式示例：

```json

[
  {
    "conversations": [
      {"from": "human",         "value": "<image>识别这张图里的物体并查询价格"},
      {"from": "function_call", "value": "{\"name\": \"search_price\", \"arguments\": {\"object\": \"cat\"}}"},
      {"from": "observation",   "value": "{\"price\": 99}"},
      {"from": "gpt",           "value": "图里是一只猫，参考价格 99 元。"}
    ],
    "tools": "[{\"name\": \"search_price\", \"description\": \"查询物体价格\"}]",
    "images": ["mllm_demo_data/1.jpg"]
  }
]

```

# dataset_info 数据格式说明

```json
{
  // 用法：训练时 --dataset <下面某个 key>，可逗号分隔多个：--dataset a,b,c
  // 路径：file_name 相对于 --dataset_dir（默认就是 data/ 目录）
  
  // 【1】最简写法：只给 file_name
  //   默认 formatting = alpaca
  //   默认 columns = instruction / input / output / system / history
  "demo_minimal": {
    "file_name": "demo.json"
    // 文件内容：
    // [{"instruction": "1+1=?", "input": "", "output": "2"}]
  },
  // 【2】Alpaca 完整写法（单轮 / 多轮 SFT）
  //   columns 方向：key = 框架标准字段，value = 你文件里实际的列名
  //   想用默认列名就可以整段省略 columns
  "demo_alpaca_full": {
    "file_name": "mydata/sft.jsonl",     // 可带子目录；支持 .json/.jsonl/.csv/.parquet/.arrow
    "formatting": "alpaca",              // 显式声明，等价于默认值
    "columns": {
      "prompt": "question",              // 默认 "instruction"
      "query": "context",                // 默认 "input"，可省略
      "response": "answer",              // 默认 "output"
      "system": "sys",                   // 默认 "system"，可省略
      "history": "hist"                  // 默认 "history"，二维数组 [[q1,a1],[q2,a2]]
    }
    // 文件内容：
    // {"question": "你好", "context": "", "answer": "你好！",
    //  "sys": "你是一个助手", "hist": [["在吗", "在的"]]}
  },

  // 【3】Alpaca + 偏好数据（DPO / ORPO / SimPO / RM / PPO）
  //   关键：ranking 必须为 true，否则 chosen/rejected 不会被当成偏好对
  "demo_dpo": {
    "file_name": "mydata/dpo.json",
    "formatting": "alpaca",
    "ranking": true,                     // ← 偏好数据必须开
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output",              // 可留空
      "chosen": "chosen",                // 默认 "chosen"，训练ai选择好
      "rejected": "rejected",            // 默认 "rejected"，远离坏的
      "system": "system",
      "history": "history"
    }
    // 文件内容：
    // {"instruction": "推荐一部电影", "input": "",
    //  "chosen": "《肖申克的救赎》", "rejected": "不知道"}
  },

  // 【4】Alpaca + KTO
  //   多一列布尔标签，标记该样本是好（true）还是坏（false）
  // --------------------------------------------------------------------------
  "demo_kto": {
    "file_name": "mydata/kto.json",
    "formatting": "alpaca",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output",
      "kto_tag": "label"                 // 默认 "kto_tag"，值为 true / false
    }
  },
  // 【5】ShareGPT 完整写法（多轮对话 / 工具调用）
  //   核心是 conversations 列表，每项 {from, value}
  //   角色位置约束：human/observation 在奇数位，gpt/function_call 在偶数位
  // --------------------------------------------------------------------------
  "demo_sharegpt": {
    "file_name": "mydata/sharegpt.json",
    "formatting": "sharegpt",            // ← 必须显式写
    "columns": {
      "messages": "conversations",       // 默认 "conversations"
      "system": "system",                // 默认 "system"，也可作为 conversations 里的 system 项
      "tools": "tools",                  // 默认 "tools"，工具描述（JSON 字符串）
      "images": "images",                // 多模态：图片路径列表
      "videos": "videos",                // 多模态：视频路径列表
      "audios": "audios"                 // 多模态：音频路径列表
    },
    "tags": {                            // 改写角色/内容键名，全部可选
      "role_tag": "from",                // 默认 "from"
      "content_tag": "value",            // 默认 "value"
      "user_tag": "human",               // 默认 "human"
      "assistant_tag": "gpt",            // 默认 "gpt"
      "observation_tag": "observation",  // 默认 "observation"
      "function_tag": "function_call",   // 默认 "function_call"
      "system_tag": "system"             // 默认 "system"
    }
    // 文件内容：
    // {"system": "你是一个助手",
    //  "conversations": [
    //    {"from": "human", "value": "<image>这是什么"},
    //    {"from": "gpt", "value": "一只猫"}
    //  ],
    //  "images": ["data/mllm/1.jpg"]}
  },
  // 【6】OpenAI / messages 风格
  //   注意：formatting 的合法值只有 "alpaca" 和 "sharegpt" 两个，
  //        没有 "openai"。所谓 OpenAI 格式 = sharegpt + tags 改键名。
  // --------------------------------------------------------------------------
  "demo_openai_style": {
    "file_name": "mydata/openai.jsonl",
    "formatting": "sharegpt",            // ← 仍然是 sharegpt
    "columns": {
      "messages": "messages"             // 列名叫 messages
    },
    "tags": {
      "role_tag": "role",                // from  → role
      "content_tag": "content",          // value → content
      "user_tag": "user",                // human → user
      "assistant_tag": "assistant",      // gpt   → assistant
      "system_tag": "system"
    }
    // 文件内容：
    // {"messages": [
    //   {"role": "system",    "content": "你是一个助手"},
    //   {"role": "user",      "content": "你好"},
    //   {"role": "assistant", "content": "你好！"}
    // ]}
  },

  // 【7】ShareGPT 承载偏好数据
  //   chosen / rejected 各是一段完整的 conversations 列表
  // --------------------------------------------------------------------------
  "demo_sharegpt_dpo": {
    "file_name": "mydata/dpo_sharegpt.json",
    "formatting": "sharegpt",
    "ranking": true,                     // ← 必须开
    "columns": {
      "messages": "conversations",
      "chosen": "chosen",                // 每项是 [{"from":..., "value":...}, ...]
      "rejected": "rejected",
      "system": "system"
    }
  },

  // 【8】预训练（PT）—— 纯文本，无标注
  // --------------------------------------------------------------------------
  "demo_pretrain": {
    "file_name": "mydata/corpus.jsonl",
    "formatting": "alpaca",
    "columns": {
      "prompt": "text"                   // ← 关键：把 prompt 映射到 text 列
    }
    // 文件内容：{"text": "一大段未标注语料……"}
  },
  // 【9】从 HuggingFace Hub 加载
  //   hf_hub_url 优先级高于 file_name，二者一般只写一个
  // --------------------------------------------------------------------------
  "demo_hf": {
    "hf_hub_url": "lmsys/lmsys-chat-1m",
    "subset": "default",                 // 数据集的子集名（config name）
    "split": "train",                    // 默认 "train"
    "folder": "",                        // 仓库内的子目录
    "num_samples": 5000,                 // 只取前 N 条，调试时很好用
    "formatting": "sharegpt",
    "columns": {
      "messages": "conversation"
    },
    "tags": {
      "role_tag": "role",
      "content_tag": "content",
      "user_tag": "user",
      "assistant_tag": "assistant"
    }
  },
  // 【10】从 ModelScope 加载（国内网络友好）
  // --------------------------------------------------------------------------
  "demo_ms": {
    "ms_hub_url": "AI-ModelScope/alpaca-gpt4-data-zh",
    "subset": "default",
    "split": "train",
    "formatting": "alpaca",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  },
  // 【11】自定义解析脚本 script_url
  //   指向 data/ 下的 .py 文件，需遵循 HuggingFace datasets 的
  //   script 规范（实现 _info / _split_generators / _generate_examples）。
  //   适合：数据要现场解码、拼接、清洗，json/csv 描述不了的情况。
  // --------------------------------------------------------------------------
  "demo_script": {
    "script_url": "my_loader.py",        // 相对 data/ 目录
    "subset": "default",
    "split": "train",
    "formatting": "alpaca",
    "columns": {
      "prompt": "instruction",
      "response": "output"
    }
  },
  // 【12】多文件目录 / 多模态
  //   file_name 可以指向目录，框架会拼接目录下所有数据文件
  // --------------------------------------------------------------------------
  "demo_mllm": {
    "file_name": "mllm_demo_data",       // 目录
    "formatting": "sharegpt",
    "columns": {
      "messages": "conversations",
      "images": "images"                 // 数量必须与文本里的 <image> 占位符个数一致
    },
    "tags": {
      "role_tag": "from",
      "content_tag": "value",
      "user_tag": "human",
      "assistant_tag": "gpt"
    }
  }
  // ⚠️ 最后一条后面不能有逗号（真实 JSON 里）
}
```

# 数据集的说明

数据是最重要的，数据绝对了训练的效果上限。

1. 一半来说lora为小规模训练，为了防止过拟合，训练的数据集在1k\~2k条左右，训练次数建议为1次数，且最好小于4次。
2. 训练数据能覆盖正常、好的、坏的、实际业务中产生的最好
3. 数据怎么来

   * 人工准备，质量高，效果好
   * 开源数据集
   * 模型生成+人工检查

     * 使用能力更强的模型根据多种要求生成各种训练数据，人工检查处理提高质量

# 当前准备

这里展示的为单个数据情况，数据集中是一个完整的json数组，有多条数据。

text2sql数据集格式示例：

```json
{
  "instruction": "你是一个 SQL 专家。请根据下面的数据库表结构，把自然语言问题转换成一条正确的 SQL 查询语句。只输出 SQL，不要解释。\n\n数据库：学生成绩库\n表结构：\n表 students(...)...",
  "input": "查询年龄大于 18 岁的女生姓名和分数",
  "output": "SELECT name, score FROM students WHERE age > 18 AND gender = '女';"
}
```

快递信息提取数据集格式：

```json
{
    "instruction": "你是一个信息抽取助手。请从下面的快递邮寄信息中，提取指定字段，并只输出一个合法的 JSON 对象，不要输出任何解释文字。\nJSON 必须包含且只包含这些字段：receiver, phone, province, city, district, address, sender, sender_phone, postcode, note。\n如果原文没有提到某个字段，该字段的值填空字符串 \"\"。",
    "input": "快递面单信息如下：收件人 林伟，收件电话 13810536558，收件地址 湖北省武汉市武昌区花园路373号19幢114室，邮编 604959；寄件人 林洋，寄件电话 19964052999。",
    "output": "{\"receiver\": \"林伟\", \"phone\": \"13810536558\", \"province\": \"湖北省\", \"city\": \"武汉市\", \"district\": \"武昌区\", \"address\": \"花园路373号19幢114室\", \"sender\": \"林洋\", \"sender_phone\": \"19964052999\", \"postcode\": \"604959\", \"note\": \"\"}"
  }
```



dataset中的配置(建议自身训练和验证的配置与数据放大单独的文件夹中，我们这里都是放到同一个文件夹下）：

```json
{
  "text2sql_train": {
    "file_name": "text2sql_train.json",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  },
  "text2sql_val": {
    "file_name": "text2sql_val.json",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  },
  "express_train": {
    "file_name": "express_train.json",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  },
  "express_val": {
    "file_name": "express_val.json",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  }
}

```

## 格式检查

执行脚本:

```shell
cd /mnt/d/opt/lora_learn
python3 - <<'PY'
import json, pathlib
for f in ["text2sql_train","text2sql_val","express_train","express_val"]:
    p = pathlib.Path("data/lf")/(f+".json")
    d = json.load(open(p, encoding="utf-8"))
    assert all(set(x)=={"instruction","input","output"} for x in d), f
    print(f, len(d), "条，格式 OK")
PY
```

结果：

```shell
text2sql_train 576 条，格式 OK
text2sql_val 64 条，格式 OK
express_train 540 条，格式 OK
express_val 60 条，格式 OK
```
