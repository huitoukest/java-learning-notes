---
title: "j2ee,jsp,servlet文件下载服务器端"
date: "2015-07-01 16:49:07"
categories: ["java EE SSHM"]
tags: ["服务器", "servlet", "j2ee"]
---

1.getOutputStream() has already been called for this response

报错的原因:

使用tomcat容器调用response.getOutputStream()方法的时候只能够写二进制文件.

但调用requonse.getWriter()方法时，则只能够在前台打印文本文件.

所以:

如果在jsp页面:

```html
outPutStream.flush();
outPutStream.close();
outPutStream=null;
response.flushBuffer();
out.clear();
out = pageContext.pushBody();
```

这里out和pageContext是jsp的内置对象;

如果在后台:

如果使用response.getWrter,那么前面只能用response.setContentType("text/html");

如果想用二进制流的方式输出,那么就不都够使用response.setContentType("text/html");

如果是想传输文件,推荐:

response.setContentType("application/x-msdownload;charset=utf-8");

同时为了防止乱码,response.setCharacterEncoding("utf-8");   

filename = URLEncoder.encode(filename, "utf-8");  

**文件下载的代码:**

```html
public void getDownLoadBook() throws IOException{
	response.setCharacterEncoding("utf-8");
	String filepath=request.getSession().getServletContext().getRealPath("\\") + "upload\\books\\";
	//通过前台bookId,从数据库中取出文件保存的信息
Book book=this.getBookService().getBook(bookId);
if(book==null)
	{       response.setContentType("text/html");
		PrintWriter writer=response.getWriter();	
		writer.write("<html><body>");
		writer.write("此电子书不存在!");
		writer.write("</body></html>");
		writer.flush();
		writer.close();
		return;
	}
	String filename=book.getSaveName()+"";
	java.io.File file = new java.io.File(filepath + filename);
	if (!file.exists()) {
	         response.setContentType("text/html");
	         PrintWriter writer=response.getWriter();
	         writer.write("<html><body>");
		 writer.write("文件不存在!<br/>"+file.getAbsolutePath()+book.getOriginalName()+"不见了!");
		 writer.write("</body></html>");
		 writer.flush();
		 writer.close();
		 return;
		}
	response.setContentType("application/x-msdownload;charset=utf-8");
	response.setCharacterEncoding("utf-8");
	response.setContentLength((int) file.length());
	filename=book.getOriginalName();
	//编码文件名,防止乱码
	filename = URLEncoder.encode(filename, "utf-8");
	response.setHeader("Content-Disposition", "attachment; filename=" +filename);
	//得到输出流
javax.servlet.ServletOutputStream out = response.getOutputStream();
	// 读取文件流
	java.io.FileInputStream fileInputStream = new java.io.FileInputStream(file);
	// 下载文件, 设置响应头和下载保存的文件名
	filename=book.getOriginalName();
	if (filename != null && filename.length() > 0) {
	if (fileInputStream != null) {
	int filelen = fileInputStream.available();
	文件太大时内存不能一次读出,要循环
	int i=4096;
	   do{
	      byte a[] = new byte[4096];
	      i=fileInputStream.read(a);
	      out.write(a, 0, i);
	     }while(i>=4096);
	}
	fileInputStream.close();
	out.flush();
	out.close();
		}	 
}
```
