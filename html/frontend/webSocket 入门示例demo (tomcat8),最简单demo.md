---
title: "webSocket 入门示例demo (tomcat8),最简单demo"
date: "2016-05-18 09:12:36"
categories: ["java EE SSHM"]
tags: ["webSocke", "tomcat8", "demo"]
---

# 1.新建web工程，配置xml文件

工程名称：webSocketDemo

web.xml文件配置：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<web-app xmlns="http://xmlns.jcp.org/xml/ns/javaee"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://xmlns.jcp.org/xml/ns/javaee
http://xmlns.jcp.org/xml/ns/javaee/web-app_3_1.xsd"
version="3.1"
metadata-complete="true">
<description>webSocketDemo</description>
<display-name>webSocketDemo</display-name>
<welcome-file-list>
<welcome-file>index.html</welcome-file>
<welcome-file>index.xhtml</welcome-file>
<welcome-file>index.htm</welcome-file>
<welcome-file>index.jsp</welcome-file>
</welcome-file-list>

</web-app>
```

# 2.编写jsp页面

```javascript
<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%
	String path = request.getContextPath();
	String socPath="ws://"+request.getServerName()+":"+request.getServerPort()+path+"/";
%>
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<title>websocketIndex</title>
<script type="text/javascript">
var wsuri = "<%=socPath%>getServer1";
var ws = null;
function startWebSocket() {
if ('WebSocket' in window)
ws = new WebSocket(wsuri);
else if ('MozWebSocket' in window)
ws = new MozWebSocket(wsuri);
else
	console.error("not support WebSocket!");
ws.onmessage = function(evt) {
alert(evt.data);
console.info(evt);
};

ws.onclose = function(evt) {

alert("close");
console.info(evt);
};

ws.onopen = function(evt) {
alert("open");
console.info(evt);
};
};

function init(){
	startWebSocket();
};
init();
```

```html
function sendMsg(){     	
ws.send(document.getElementById('writeMsg').value);
}
</script>
</head>
<body>
<input type="text" id="writeMsg"/> 
<input type="button" value="sendSmgToServer" onclick="sendMsg()"/>
<br>
<span>
wait 8 second,server will send you a msg!
</span>
</body>
</html>
```

# 3.编写webSocket服务端

    @ServerEndpoint("/getServer")
    public class SocketServer{

    	@OnOpen
    	public void onOpen(Session session) {
    		 final RemoteEndpoint.Basic basic =  session.getBasicRemote();  		  
    	        System.out.println("pathParams:"+session.getPathParameters());  
    	        System.out.println("requestParams"+session.getRequestParameterMap());  
    	    	try {
    				basic.sendText("open success on server");
    			} catch (IOException e) {
    				e.printStackTrace();
    			}
    	    	Thread t1=new Thread(new Runnable() {

    				@Override
    				public void run() {
    					try {
    						Thread.currentThread();
    						Thread.sleep(8000);
    						basic.sendText("server get you a msg: what your name?");
    					} catch (InterruptedException e) {
    						e.printStackTrace();
    					} catch (IOException e) {
    						e.printStackTrace();
    					}
    				}
    			});
    	    	t1.start();
    	}	
    	/**
    	 * 收到客户端消息时触发
    	 * @param relationId
    	 * @param userCode
    	 * @param message
    	 * @return
    	*/
    	@OnMessage
    	 public String onMessage(Session session,String message) {
    		 System.out.println("pathParams:"+session.getPathParameters());  
             System.out.println("requestParams"+session.getRequestParameterMap());  
    		return	"Got you msg !"+message;
    	}

    	/**
    	 * 异常时触发
    	 * @param relationId
    	 * @param userCode
    	 * @param session
    	*/
    	@OnError
    	 public void onError(Throwable throwable,Session session) {
    		 System.out.println("pathParams:"+session.getPathParameters());  
    	     System.out.println("requestParams"+session.getRequestParameterMap());  
    	     System.out.print("onError"+throwable.toString());
    	}

    	/**
    	 * 关闭连接时触发
    	 * @param relationId
    	 * @param userCode
    	 * @param session
    	*/

```java
	@OnClose
	 public void onClose(Session session) {
		 System.out.println("pathParams:"+session.getPathParameters());  
	        System.out.println("requestParams"+session.getRequestParameterMap());  
		 System.out.print("onClose ");
	}		
}
```

# 4.发布到tomc8及以上版本的服务器

**注意：采用支持Html5的浏览器浏览网页**
