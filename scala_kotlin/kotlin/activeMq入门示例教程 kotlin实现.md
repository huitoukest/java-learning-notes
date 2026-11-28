---
title: "activeMq入门示例教程  kotlin实现"
date: "2018-04-06 09:33:07"
categories: ["消息通信"]
tags: ["JSM", "activeMq", "入门教程", "kotlin"]
---

# 简介
activeMq是一个实现了JMS的开源消息框架。

## 快速安装
官方网站：http://activemq.apache.org/

- 运行ActiveMQ服务
下载，解压缩 ，以apache-activemq-5.11.1为例：
将apache-activemq-5.11.1-bin.zip解压缩，我们可以看到它的整体目录结构：
 - bin存放的是脚本文件
 - conf存放的是基本配置文件
 - data存放的是日志文件
 - docs存放的是说明文档
 - examples存放的是简单的实例
 - lib存放的是activemq所需jar包
 - webapps用于存放项目的目录
进入bin目录，在window下运行activemq.bat start即可以启动。
其运行使用的默认端口有：
8161是web后台管理系统，在浏览器输入http://localhost:8161，使用默认admin admin登陆。
61616是 tcp 服务端口，用于开发使用。

- 检测
windows下使用如下命令检测是否启动tcp服务成功
```kotlin
C:\Documents and Settings\Administrator>netstat -an|find "61616"
TCP 0.0.0.0:61616 0.0.0.0:0 LISTENING
```
- 注意
在window下，最新版本启动的是 wrapper.exe 文件，位于bin的win64目录下

# 入门示例

## 工具类
```kotlin
import org.apache.activemq.ActiveMQConnection
import org.apache.activemq.ActiveMQConnectionFactory
import javax.jms.Connection
import javax.jms.ConnectionFactory

object ActiveMqUtils {
    //默认连接用户名
    private val USERNAME = ActiveMQConnection.DEFAULT_USER
    //默认连接密码
    private val PASSWORD = ActiveMQConnection.DEFAULT_PASSWORD
    //默认连接地址
    private val BROKEURL = ActiveMQConnection.DEFAULT_BROKER_URL


    private val connectionFactory: ConnectionFactory

    init {
        connectionFactory = ActiveMQConnectionFactory(USERNAME, PASSWORD,BROKEURL)
    }

    fun getConn(isAutoStart:Boolean = false):Connection{
        //获取连接
        val connection = connectionFactory.createConnection()
        if(isAutoStart){
            connection.start()
        }
        return connection
    }
    fun doInSession(doSomeThing : () -> Unit,conn:Connection?,isAutoCloseConn:Boolean = false){
        try {
            doSomeThing()
        }catch (e :Exception){
            e.printStackTrace()
        }finally {
            if(isAutoCloseConn){
                closeConn(conn)
            }
        }
    }
    fun closeConn(conn:Connection?){
        try {
            if(null != conn ){
                conn.close()
            }
        } catch (e :Exception){
            e.printStackTrace()
        }
    }
}

```

## 消息生产者
```kotlin
import javax.jms.*

fun main(args: Array<String>){
    JMSProducer.initCommonSender()
    JMSProducer.initTopicSender()
}

object JMSProducer {
     //发送的消息数量
     val SENDNUM = 5

    fun initCommonSender(){
        var connection: Connection = ActiveMqUtils.getConn(true)
        //创建session,事务模式
        val session = connection.createSession(true, Session.AUTO_ACKNOWLEDGE)
        ActiveMqUtils.doInSession({
            //创建一个名为HelloWorld123的队列
            val destination = session.createQueue("HelloWorld123")
            //创建消息生产者
            val messageProducer = session.createProducer(destination)
            messageProducer.setDeliveryMode(DeliveryMode.PERSISTENT)//持久化消息时需要设置
            sendMessage(session,messageProducer,DeliveryMode.PERSISTENT,"HelloWorld123")
            session.commit()
            messageProducer.close()
        } ,connection,true)
    }

    fun initTopicSender() {

        var connection: Connection = ActiveMqUtils.getConn(true)
        //创建session,事务模式
        val session = connection.createSession(true, Session.AUTO_ACKNOWLEDGE)
        ActiveMqUtils.doInSession({
            //创建一个名为HelloWorld123的队列
            val destination = session.createTopic("topic1")
            //创建消息生产者
            val messageProducer = session.createProducer(destination)
            messageProducer.setDeliveryMode(DeliveryMode.PERSISTENT)//持久化消息时需要设置
            sendMessage(session, messageProducer, DeliveryMode.PERSISTENT,"topic1")
            session.commit() //在session commit之后，客户端会“在同一批次中”收到这些消息，而不是发送一条接收一条
            messageProducer.close()
        }, connection, true)
    }
    /**
     * 发送消息
     * @param session
     * @param messageProducer
     */
    fun sendMessage(session:Session, messageProducer: MessageProducer, deliveryMode:Int,title:String){
        for( i in 0 until  JMSProducer.SENDNUM ) { //创建一条文本消息
            val msg = title + "  " + java.util.Date().toString()+" ActiveMQ 发送消息" + i
            val message = session.createTextMessage(msg)
            System.out.println(msg)

            //持久化的消息发送,messageProducer.send(Message message, int deliveryMode, int priority, long timeToLive)
            //timeToLive=0,表示永不过期，这里设置过期时间为1天。
            //通过消息生产者发出消息
            messageProducer.send(message, deliveryMode, 1,3600 * 1000 * 24)
            Thread.sleep(1500)
        }
    }
}

```

## 消息消费者
```kotlin
import javax.jms.*

fun main(args:Array<String>){

    Thread({
        JMSConsumer.receivedTopic()
    }).start()
    JMSConsumer.receivedQueue() //同步接收会阻塞线程，所以将异步topic方法放在前面
}

object JMSConsumer {
    /**
     * Queue普通的发送和接收
     */
    fun receivedQueue(){
        var connection: Connection = ActiveMqUtils.getConn(true)
        //创建session,事务模式
        val session = connection.createSession(true, Session.AUTO_ACKNOWLEDGE)
        ActiveMqUtils.doInSession({
            //创建一个名为HelloWorld123的队列
            val destination = session.createQueue("HelloWorld123");
            //创建消息消费者
            val messageConsumer = session.createConsumer(destination);
            while (true) {
                //当没有消息的时候，此方法会阻塞，知道有消息达到，或者达到超时时间。
                val textMessage = messageConsumer.receive(15000)
                //达到超时时间后会 textMessage == null成立，这时候表示已经没有消息达到，队列空闲，则session提交
                if(textMessage != null){
                    textMessage as TextMessage
                    System.out.println("HelloWorld123收到的消息:" + textMessage.getText())
                }else {
                    //如果没有commit，那么下次启动时，仍然会收到上次没有commit的消息
                    session.commit()
                    messageConsumer.close()
                    break
                }
            }
        } ,connection,true)
    }

    /**
     * topic的发送和接收
     */
    fun receivedTopic(){
        var connection: Connection = ActiveMqUtils.getConn(false)
        val clientID = "123123123"
        //持久化的时候需要设置唯一的客户端id,先传入连接的客服端唯一识别码,然后启动连接
        connection.setClientID(clientID)
        connection.start()
        //创建session,createSession中paramA 取值有 : true or false 表示是否支持事务,paramA设置为true时：paramB的值忽略
        //paramB 取值有:Session.AUTO_ACKNOWLEDGE，Session.CLIENT_ACKNOWLEDGE，DUPS_OK_ACKNOWLEDGE，SESSION_TRANSACTED
        //Session.AUTO_ACKNOWLEDGE为自动确认，客户端发送和接收消息不需要做额外的工作。
        //Session.CLIENT_ACKNOWLEDGE为客户端确认。客户端接收到消息后，必须调用javax.jms.Message的acknowledge方法。jms服务器才会删除消息。
        //DUPS_OK_ACKNOWLEDGE允许副本的确认模式。一旦接收方应用程序的方法调用从处理消息处返回，会话对象就会确认消息的接收；而且允许重复确认。在需要考虑资源使用时，这种模式非常有效。
        //创建session,事务模式
        val session = connection.createSession(true, Session.AUTO_ACKNOWLEDGE)
        ActiveMqUtils.doInSession({
            //创建一个名为topic1的topic
            val destination =  session.createTopic("topic1")
            //创建消息消费者
            val messageConsumer = session.createDurableSubscriber(destination,"topic1")
            //异步方式读取消息
            messageConsumer.setMessageListener {
                it as TextMessage
                System.out.println("topic1收到的消息:" + it.text);
                session.commit()
            }
        } ,connection,false)
    }
}

```

## 输出结果
消费者：
```text
HelloWorld123收到的消息:HelloWorld123 Wed Apr 04 15:50:28 CST 2018 ActiveMQ 发送消息0
HelloWorld123收到的消息:HelloWorld123 Wed Apr 04 15:50:29 CST 2018 ActiveMQ 发送消息1
HelloWorld123收到的消息:HelloWorld123 Wed Apr 04 15:50:30 CST 2018 ActiveMQ 发送消息2
HelloWorld123收到的消息:HelloWorld123 Wed Apr 04 15:50:31 CST 2018 ActiveMQ 发送消息3
HelloWorld123收到的消息:HelloWorld123 Wed Apr 04 15:50:32 CST 2018 ActiveMQ 发送消息4
topic1收到的消息:topic1 Wed Apr 04 15:50:33 CST 2018 ActiveMQ 发送消息0
topic1收到的消息:topic1 Wed Apr 04 15:50:34 CST 2018 ActiveMQ 发送消息1
topic1收到的消息:topic1 Wed Apr 04 15:50:35 CST 2018 ActiveMQ 发送消息2
topic1收到的消息:topic1 Wed Apr 04 15:50:36 CST 2018 ActiveMQ 发送消息3
topic1收到的消息:topic1 Wed Apr 04 15:50:37 CST 2018 ActiveMQ 发送消息4
```

生产者：
```text
HelloWorld123 Wed Apr 04 15:50:28 CST 2018 ActiveMQ 发送消息0
HelloWorld123 Wed Apr 04 15:50:29 CST 2018 ActiveMQ 发送消息1
HelloWorld123 Wed Apr 04 15:50:30 CST 2018 ActiveMQ 发送消息2
HelloWorld123 Wed Apr 04 15:50:31 CST 2018 ActiveMQ 发送消息3
HelloWorld123 Wed Apr 04 15:50:32 CST 2018 ActiveMQ 发送消息4
 INFO | Successfully connected to tcp://localhost:61616
topic1 Wed Apr 04 15:50:33 CST 2018 ActiveMQ 发送消息0
topic1 Wed Apr 04 15:50:34 CST 2018 ActiveMQ 发送消息1
topic1 Wed Apr 04 15:50:35 CST 2018 ActiveMQ 发送消息2
topic1 Wed Apr 04 15:50:36 CST 2018 ActiveMQ 发送消息3
topic1 Wed Apr 04 15:50:37 CST 2018 ActiveMQ 发送消息4
```

## 注意
如果先启动消费者，后启动生产者，那么
这里的 receivedQueue中设置的超时时间是15秒，那么在15内没有发送消息的话就会超时。
所以如果启动消费者15秒后仍然没有收到生产者的消息，那么这一次消费者将不会再收到消息。
同步的接收消息有这个问题，异步的不存在这个问题。
