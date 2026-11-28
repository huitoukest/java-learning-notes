---
title: "rabbitMq 入门示例demo kotlin语言实现 default ,direct,topic,fanout模式"
date: "2018-04-04 17:59:26"
categories: ["消息通信"]
tags: ["rabbitmq", "kotlin", "消息发送", "入门教程"]
---

# 简介
rabbitMq是一个消息框架，企业中使用较多，这里示例 default ,direct,topic,fanout模式下的消息发送和接收代码。

# 实现

## maven依赖
```kotlin
<dependencies>
        <dependency>
            <groupId>com.rabbitmq</groupId>
            <artifactId>amqp-client</artifactId>
            <version>5.2.0</version>
        </dependency>
        <dependency>
            <groupId>log4j</groupId>
            <artifactId>log4j</artifactId>
            <version>1.2.17</version>
        </dependency>
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-api</artifactId>
            <version>1.7.22</version>
        </dependency>
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-simple</artifactId>
            <version>1.7.22</version>
        </dependency>
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-log4j12</artifactId>
            <version>1.7.22</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
```

## 工具类
```kotlin
object ChannelUtils {
    fun getChannelInstance(connectionDescription: String): Channel {
        try {
            val connectionFactory = getConnectionFactory()
            val connection = connectionFactory.newConnection(connectionDescription)
            return connection.createChannel()
        } catch (e: Exception) {
            throw RuntimeException("获取Channel连接失败")
        }

    }

    private fun getConnectionFactory(): ConnectionFactory {
        val connectionFactory = ConnectionFactory()

        // 配置连接信息
        connectionFactory.host = "127.0.0.1"
        connectionFactory.port = 5672
        connectionFactory.virtualHost = "/"
        connectionFactory.username = "guest"
        connectionFactory.password = "guest"

        // 网络异常自动连接恢复
        connectionFactory.isAutomaticRecoveryEnabled = true
        // 每10秒尝试重试连接一次
        connectionFactory.setNetworkRecoveryInterval(10000)

        // 设置ConnectionFactory属性信息
        val connectionFactoryPropertiesMap = HashMap<String,Any>()
        connectionFactoryPropertiesMap.put("myProps", "any value")
        connectionFactory.clientProperties = connectionFactoryPropertiesMap

        return connectionFactory
    }
}
```

## 消息发送者
```kotlin
import com.rabbitmq.client.*
import java.nio.charset.Charset
import java.util.HashMap
import com.rabbitmq.client.AMQP

fun main(args : Array<String>){
    val ra = RabbitSender();
    ra.sendMsg()
    ra.closeConnection()
}

class RabbitSender {
    companion object {
        //默认是使用guest账户，5672端口
        val factory = ConnectionFactory()
        val conn:Connection
        init {
            factory.setHost("localhost")
            conn = factory.newConnection()
        }
    }
    fun sendMsg() {
        sendDrectDefault()
        sendDirect()
        sendFanout()
        sendTopic()
    }

    /**
     * 服务器能给我们提供一个 non-durable(不持久化的), exclusive(单独的), autodelete(随着消费者的消亡自动删除的),random(随机命名)的一个队列.
     * String queueName = channel.queueDeclare().getQueue()
     *
     * 直连的方式,指定队列的发送和接收
     * 本质上所有的消息发送都要送往exchange（可以没有队列，但不能没有交换机，没有队列时消息直接被丢弃）。
     * RabbitMQ提供了一种直接向Queue发送消息的快捷方法：直接使用未命名的exchange，不用绑定routing_key，直接用它指定队列名。
     * 不创建交换机，但仍然能够发送消息到队列中。因为我们使用了命名为空字符串("")默认的交换机。
     */
    private  fun sendDrectDefault(){
        val QUEUE_NAME = "fruits default"
        //指定队列,队列只会在它不存在的时候创建，多次声明并不会重复创建。信息的内容是字节数组，也就意味着你可以传递任何数据。
        val channel = conn.createChannel()
        // durable = false 是否持久化, exclusive = false 是否排外：只能创建一个conn连接, autoDelete = false 是否自动删除, arguments = null
        channel.queueDeclare(QUEUE_NAME, false, false , false ,null)
        val payload = "Hello , world!"
        //往队列中发出一条消息,basicPublish的第一个参数是转发器exchange的名称,这里采用的是默认的转发器""
        channel.basicPublish("",QUEUE_NAME,null, payload.toByteArray(Charset.forName("UTF-8")))
        this.closeChannel(channel)

    }

    /**
     * 单个指定队列的发送和接收,只有完全匹配才会接收到消息,
     * 消息的额发送实际上是发送给交换机的，由交换机自动匹配队列，通过消息队列投递消息给消费者。
     */
    fun sendDirect(){
        val exchangeName = "test_exchange_direct"
        val message = "test exchange direct"
        val channel = conn.createChannel()
        val routing_key="direct01"//匹配路由键值
        //声明交换器类型direct
        // 声明交换机 (交换机名, 交换机类型, 是否持久化, 是否自动删除, 是否是内部交换机, 交换机属性)
        channel.exchangeDeclare(exchangeName, BuiltinExchangeType.DIRECT, true, false, false, HashMap<String,Any>())
        // 设置消息属性 发布消息 (交换机名, Routing key, 可靠消息相关属性 后续会介绍, 消息属性, 消息体)
        val basicProperties = AMQP.BasicProperties().builder().deliveryMode(2).contentType("UTF-8").build()
        //发送一条消息
        channel.basicPublish(exchangeName,routing_key,basicProperties,message.toByteArray(Charset.forName("UTF-8")))
        //this.closeChannel(channel)
    }

    /**
     * 绑定多个队列的发送和接收,Fanout即广播模式
     * Fanout : 扇形交换机它把消息发送给它所知道的所有队列
     */
    fun sendFanout(){
        val exchangeName = "test_exchange_fanout"
        val message = "test exchange fanout"
        val channel = conn.createChannel()
        //声明交换器Exchange
        channel.exchangeDeclare(exchangeName,BuiltinExchangeType.FANOUT)
        channel.basicPublish(exchangeName,"",null,message.toByteArray(Charset.forName("UTF-8")))
        this.closeChannel(channel)
    }

    /** Topic Exchange,只有匹配此routing_key规则的消息会被接收
     */
    private fun sendTopic(){
        val exchangeName = "test_exchange_topic"
        val message = "test exchange topic"
        val channel = conn.createChannel()
        val routing_key="topic.direct"//匹配路由键值
        //声明交换器类型direct
        channel.exchangeDeclare(exchangeName,BuiltinExchangeType.TOPIC)

        var basicProperties:AMQP.BasicProperties? = null //deliveryMode = 2,数据持久化
        basicProperties =  AMQP.BasicProperties().builder().deliveryMode(2).contentType("UTF-8").build()

        channel.basicPublish(exchangeName,routing_key,basicProperties,message.toByteArray(Charset.forName("UTF-8")))
        this.closeChannel(channel)
    }

    /**
     *关闭频道
     */
    fun closeChannel(channel: Channel){
        channel.close()
    }
    /**
     *关闭连接
     */
    fun closeConnection(){
        conn.close()
    }
}
```

## 消息接收者
```kotlin
import com.rabbitmq.client.*
import java.nio.charset.Charset
import java.util.*

fun main(args : Array<String>){
    val ra = RabbitReceiver()
    ra.reMsg()
}
class MyConsumer(channel: Channel) : DefaultConsumer(channel) {

    override fun handleDelivery(consumerTag: String?, envelope: Envelope?, properties: AMQP.BasicProperties?, body: ByteArray?) {
        val routingKey: String? = envelope?.routingKey
        val contentType: String? = properties?.contentType
        val deliveryTag: Long? = envelope?.deliveryTag
        // (process the message components here ...)
        val message = String(body!!, Charset.forName("UTF-8"))
        //channel.basicAck(deliveryTag, false) //手动关闭channel,手动返回
        println("routingKey:$routingKey,contentType:$contentType,deliveryTag:$deliveryTag,message:$message")
    }
}

class RabbitReceiver {

    fun reMsg() {

        reDirectDefault()
        reDirectDefault()
        receiveDirect()
        receiveDirect()

        receiveFanout()
        receiveFanout()

        receiveTopic()
    }
    
    fun reDirectDefault(){
        val QUEUE_NAME = "fruits default"
        val channel = ChannelUtils.getChannelInstance("re")
        //声明队列，主要为了防止消息接收者先运行此程序，队列还不存在时创建队列。
        channel.queueDeclare(QUEUE_NAME,false,false,false,null)
        //传递参数为prefetchCount = 1。
        //这样告诉RabbitMQ不要在同一时间给一个消费者超过一条消息。换句话说，只有在消费者空闲的时候会发送下一条信息。
        val prefetchCount = 1;
        channel.basicQos(prefetchCount);
        //var consumer = new QueueingConsumer(channel)
        val consumer = MyConsumer(channel)
        channel.basicConsume(QUEUE_NAME,true,consumer)
    }

    /**
     *derect的消息接收方式
     */
    fun receiveDirect(){
        val QUEUE_NAME= "fruitsDirect" + Random().nextInt()
        val EXCHANGE_NAME = "test_exchange_direct"
        val routing_key = "direct01";//匹配路由键值
        val routing_key2 = "direct02";//匹配路由键值

        val channel = ChannelUtils.getChannelInstance("receiveDirect")
        //定义队列
        channel.queueDeclare(QUEUE_NAME, true, false, false, null)
        // 声明交换机 (交换机名, 交换机类型, 是否持久化, 是否自动删除, 是否是内部交换机, 交换机属性)
        channel.exchangeDeclare(QUEUE_NAME, BuiltinExchangeType.DIRECT, true, false, false, HashMap())//绑定队列到交换器

        channel.queueBind(QUEUE_NAME, EXCHANGE_NAME,routing_key, HashMap())
        //绑定队列到交换器,这里指挥匹配绑定的这两种路由键值
        channel.queueBind(QUEUE_NAME, EXCHANGE_NAME,routing_key2)
        //统一时刻服务器只会发一条消息给消费者;
        channel.basicQos(1)
        //定义队列的消费者
        val consumer = MyConsumer(channel)
        // 消费者订阅消息 监听如上声明的队列 (队列名, 是否自动应答(与消息可靠有关 后续会介绍), 消费者标签, 消费者)
        channel.basicConsume(QUEUE_NAME, true, "receiveDirect", consumer)
    }


    fun receiveFanout(){
        val title = "receiveFanout";
        val QUEUE_NAME= title + Random().nextInt()
        val EXCHANGE_NAME = "test_exchange_fanout"
        val routing_key="routing_key_fanout";//匹配路由键值,这里的键值是除开null之外的任意字符串，都会被fanout给匹配到

        val channel = ChannelUtils.getChannelInstance(title)
        //定义队列
        channel.queueDeclare(QUEUE_NAME, true, false, false, null)
        // 声明交换机 (交换机名, 交换机类型, 是否持久化, 是否自动删除, 是否是内部交换机, 交换机属性);
        channel.exchangeDeclare(QUEUE_NAME, BuiltinExchangeType.FANOUT, true, false, false, HashMap())//绑定队列到交换器
        channel.queueBind(QUEUE_NAME, EXCHANGE_NAME,routing_key, HashMap());
        //统一时刻服务器只会发一条消息给消费者
        channel.basicQos(1)
        //定义队列的消费者
        val consumer = MyConsumer(channel)
        // 消费者订阅消息 监听如上声明的队列 (队列名, 是否自动应答(与消息可靠有关 后续会介绍), 消费者标签, 消费者)
        channel.basicConsume(QUEUE_NAME, true, title, consumer)
    }

    /**
     *topic的消息接收方式
     * 将路由键和某模式进行匹配。此时队列需要绑定要一个模式上。符号“#”匹配一个或多个词，符号“*”匹配不多不少一个词。
     * 因此“audit.#”能够匹配到“audit.irs.corporate”，但是“audit.*” 只会匹配到“audit.irs”。
     */
    fun receiveTopic(){
        //队列和绑定交换器中的消息都会接收到
        val QUEUE_NAME ="test_topic" + java.util.Random().nextInt()
        val EXCHANGE_NAME = "test_exchange_topic";

        val channel = ChannelUtils.getChannelInstance("test_topic_re")
        channel.exchangeDeclare(EXCHANGE_NAME,BuiltinExchangeType.TOPIC)

        val  declareOk = channel.queueDeclare(QUEUE_NAME, false, false, false, null)

        // 将队列Binding到交换机上 (队列名, 交换机名, Routing key, 绑定属性)
        channel.queueBind(declareOk.queue, EXCHANGE_NAME,"#.direct", HashMap<String,Any>())

        //绑定队列到交换器,这里指挥匹配绑定的这两种路由键值
        channel.queueBind(QUEUE_NAME, EXCHANGE_NAME,"#topic")

        //统一时刻服务器只会发一条消息给消费者
        channel.basicQos(1)
        //定义队列的消费者
        val consumer = MyConsumer(channel)
        //监听队列，手动返回完成
        channel.basicConsume(QUEUE_NAME, true, consumer)
    }

}
```

# 输出结果
运行消息接受者之后运行消息发送者：结果如下：

```kotlin
routingKey:fruits default,contentType:null,deliveryTag:1,message:Hello , world!
routingKey:direct01,contentType:UTF-8,deliveryTag:1,message:test exchange direct
routingKey:direct01,contentType:UTF-8,deliveryTag:1,message:test exchange direct
routingKey:,contentType:null,deliveryTag:1,message:test exchange fanout
routingKey:,contentType:null,deliveryTag:1,message:test exchange fanout
routingKey:topic.direct,contentType:UTF-8,deliveryTag:1,message:test exchange topic
```
