---
title: "springboot amqp rabiitmq 使用fastjson自定义MessageConverter"
date: "2020-12-01 19:56:28"
categories: ["java EE SSHM", "消息通信"]
tags: ["MQ", "springboot", "amqp", "fastjson", "Converter"]
---

# 简介
支持byte[] 、CharSequence 两种类型直接传输 ，其余对象直接用fastjson转为json字符串传输 。
byte[] 一般用来传输文件 ， 而 CharSequence用来传输字符串效率更高。
# 代码
```java
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.serializer.SerializerFeature;
import org.springframework.amqp.core.Message;
import org.springframework.amqp.core.MessageProperties;
import org.springframework.amqp.support.converter.AbstractMessageConverter;
import org.springframework.amqp.support.converter.MessageConversionException;

import java.io.UnsupportedEncodingException;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

public class FastJsonMessageConverter extends AbstractMessageConverter {
    private static final String DEFAULT_CHARSET = "UTF-8";
    private static final Map<String, Function<Message,Object>> MSG_CONVERT_MAP = new HashMap<>();
    static {
        MSG_CONVERT_MAP.put(MessageProperties.CONTENT_TYPE_BYTES, message -> message.getBody());
        MSG_CONVERT_MAP.put(MessageProperties.CONTENT_TYPE_TEXT_PLAIN, message -> {
            try {
                return new String(message.getBody(), DEFAULT_CHARSET);
            } catch (UnsupportedEncodingException e) {
                throw new MessageConversionException(
                        "Failed to convert Message content", e);
            }
        });
        MSG_CONVERT_MAP.put(MessageProperties.CONTENT_TYPE_JSON, message -> {
            try {
                return JSON.parse(new String(message.getBody(), DEFAULT_CHARSET));
            } catch (UnsupportedEncodingException e) {
                throw new MessageConversionException(
                        "Failed to convert Message content", e);
            }
        });
    }
    
    public FastJsonMessageConverter() {
        super();
    }

    @Override
    public Object fromMessage(Message message)
            throws MessageConversionException {
        MessageProperties messageProperties = message.getMessageProperties();
        return MSG_CONVERT_MAP.get(messageProperties.getContentType()).apply(message);
    }

    @Override
    protected Message createMessage(Object objectToConvert,
                                    MessageProperties messageProperties)
            throws MessageConversionException {
        byte[] bytes = null;
        try {
            if (objectToConvert instanceof byte[]){
                messageProperties.setContentType(MessageProperties.CONTENT_TYPE_BYTES);
                bytes = (byte[]) objectToConvert;
            }else if(objectToConvert instanceof CharSequence){
                messageProperties.setContentType(MessageProperties.CONTENT_TYPE_TEXT_PLAIN);
                messageProperties.setContentEncoding(DEFAULT_CHARSET);
                bytes = objectToConvert.toString().getBytes(DEFAULT_CHARSET);
            }else {
                messageProperties.setContentType(MessageProperties.CONTENT_TYPE_JSON);
                String jsonString = JSON.toJSONString(objectToConvert, SerializerFeature.WriteClassName);
                bytes = jsonString.getBytes(DEFAULT_CHARSET);
            }
        } catch (UnsupportedEncodingException e) {
            throw new MessageConversionException(
                    "Failed to convert Message content", e);
        }
        if (bytes != null) {
            messageProperties.setContentLength(bytes.length);
        }
        return new Message(bytes, messageProperties);
    }

}
```

## 在spring boot中配置
配置rabbitMQ的消息转换器。

```java
import org.springframework.amqp.core.AcknowledgeMode;
import org.springframework.amqp.rabbit.annotation.EnableRabbit;
import org.springframework.amqp.rabbit.config.SimpleRabbitListenerContainerFactory;
import org.springframework.amqp.rabbit.connection.CachingConnectionFactory;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.annotation.PostConstruct;


@EnableRabbit
@Configuration
public class RabbitMQConfig {

    @Autowired
    private RabbitTemplate rabbitTemplate;

    @PostConstruct
    public void init(){
    	//设置发送时的消息转换器
        rabbitTemplate.setMessageConverter(new FastJsonMessageConverter());
    }

    /**
     * 配置接收的消息转换器
     * @return
     */
    @Bean
    public MessageConverter jsonMessageConverter() {
        return new FastJsonMessageConverter();
    }
```
