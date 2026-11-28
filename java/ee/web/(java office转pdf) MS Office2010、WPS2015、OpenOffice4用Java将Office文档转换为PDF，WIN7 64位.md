---
title: "(java office转pdf) MS Office2010、WPS2015、OpenOffice4用Java将Office文档转换为PDF，WIN7 64位系统"
date: "2016-05-11 15:18:01"
categories: ["java EE SSHM"]
tags: ["ms office", "openoffice", "WPS2015", "PDF"]
---

2023的更多选择：

1\. documents4j ，现有框架和本文原理类似。

2\. docx4j 基于解析文档xml内容来转换。

手动搭建方式：

1.前言

MS Office2010是可以的，理论上2007版本也可以，博主没试过；

Wps2015是可以的，理论上Wps2016也能用，Wps理论上还兼容MS Office的相关代码，有时间的可以试试；

Wps和Ms Office都需要导入jacob-1.18.jar包，以及将jacob-1.18-x64.dll或者jacob-1.18-x64.dll放置到jdk的bin目录（或者windows的System32/SysWoW64目录下）

而OpenOffice需要导入jodconverter-2.2.1.jar等相关包；

相关包的下载链接，包含实现代码：<http://download.csdn.net/detail/huitoukest/9506740>

包中的代码可能没有捕获NoClassDefFoundError异常和，建议使用者自行捕获；

2.MS Office2010

核心代码如下：

    private static final int wdFormatPDF = 17;
    	private static final int xlTypePDF = 0;
    	private static final int ppSaveAsPDF = 32;
    	//private static final int msoTrue = -1;
    	//private static final int msofalse = 0;
    	/**
    	 * @return 操作成功与否的提示信息. 如果返回 -1, 表示找不到源文件, 或url.properties配置错误; 如果返回 0,
    	 *         则表示操作成功; 返回1, 则表示转换失败
    	 */

```java
	@Override
	public int officeToPdf(OfficeToPDFInfo officeToPDFInfo) {
		String sourceFile=officeToPDFInfo.sourceUrl;
		String destFile=officeToPDFInfo.destUrl;
			File inputFile = new File(sourceFile);
			if (!inputFile.exists()) {
				return -1;// 找不到源文件, 则返回-1
			}
			// 如果目标路径不存在, 则新建该路径
			File outputFile = new File(destFile);
			if (!outputFile.getParentFile().exists()) {
				outputFile.getParentFile().mkdirs();
			}
			String extentionName=FileUtils.getFileExtension(sourceFile);
			if(extentionName.equalsIgnoreCase("ppt")||extentionName.equalsIgnoreCase("pptx"))
			{
				ppt2pdf(officeToPDFInfo.sourceUrl,officeToPDFInfo.destUrl);
			}else if(extentionName.equalsIgnoreCase("doc")||extentionName.equalsIgnoreCase("docx")){
				doc2pdf(officeToPDFInfo.sourceUrl,officeToPDFInfo.destUrl);
			}else if(extentionName.equalsIgnoreCase("xls")||extentionName.equalsIgnoreCase("xlsx")){
				excel2PDF(officeToPDFInfo.sourceUrl,officeToPDFInfo.destUrl);
			}	
			return 0;
	}

	protected static boolean doc2pdf(String srcFilePath, String pdfFilePath) {  
ActiveXComponent app = null;  
Dispatch doc = null;  
try {  
ComThread.InitSTA();  
app = new ActiveXComponent("Word.Application");  
app.setProperty("Visible", false);  
Dispatch docs = app.getProperty("Documents").toDispatch();  
doc = Dispatch.invoke(docs, "Open", Dispatch.Method,  
new Object[] { srcFilePath,   
new Variant(false),   
new Variant(true),//是否只读  
new Variant(false),   
new Variant("pwd") },  
new int[1]).toDispatch();  
// Dispatch.put(doc, "Compatibility", false);  //兼容性检查,为特定值false不正确  
Dispatch.put(doc, "RemovePersonalInformation", false);  
Dispatch.call(doc, "ExportAsFixedFormat", pdfFilePath,wdFormatPDF); // word保存为pdf格式宏，值为17
return true; // set flag true;  
}finally {  
if (doc != null) {  
Dispatch.call(doc, "Close", false);  
}  
if (app != null) {  
app.invoke("Quit", 0);  
}  
ComThread.Release();  
}  
}

	protected static boolean ppt2pdf(String srcFilePath, String pdfFilePath) {  
ActiveXComponent app = null;  
Dispatch ppt = null;  
try {  
ComThread.InitSTA();  
app = new ActiveXComponent("PowerPoint.Application");  
Dispatch ppts = app.getProperty("Presentations").toDispatch();  

// 因POWER.EXE的发布规则为同步，所以设置为同步发布  
ppt = Dispatch.call(ppts, "Open", srcFilePath, true,// ReadOnly  
true,// Untitled指定文件是否有标题  
false// WithWindow指定文件是否可见  
).toDispatch();  
Dispatch.call(ppt, "SaveAs", pdfFilePath, ppSaveAsPDF); //ppSaveAsPDF为特定值32    
return true; // set flag true;  
}finally {  
if (ppt != null) {  
Dispatch.call(ppt, "Close");  
}  
if (app != null) {  
app.invoke("Quit");  
}  
ComThread.Release();  
}
} 
	 public static boolean excel2PDF(String inputFile,String pdfFile){
	     ActiveXComponent app=null;
	     Dispatch excel =null;
		 try{
	        ComThread.InitSTA();  
	        app = new ActiveXComponent("Excel.Application");
	        app.setProperty("Visible", false);
	        Dispatch excels = app.getProperty("Workbooks").toDispatch();
	        excel = Dispatch.call(excels,"Open",inputFile, false,true).toDispatch();
	        Dispatch.call(excel,"ExportAsFixedFormat", xlTypePDF,pdfFile);
	        return true;
	    }finally{
	    	  if (excel!= null) {
	    		  Dispatch.call(excel, "Close");  
}  
if (app != null) {  
app.invoke("Quit");  
}
ComThread.Release();  
	    }	         
	    }
```

2.Wps 2015

核心代码如下：

    public final static String WORDSERVER_STRING="KWPS.Application";
    	public final static String PPTSERVER_STRING="KWPP.Application";
    	public final static String EXECLSERVER_STRING="KET.Application";
    	private static final int wdFormatPDF = 17;
    	private static final int xlTypePDF = 0;
    	private static final int ppSaveAsPDF = 32;

    	/**
    	 * @return 操作成功与否的提示信息. 如果返回 -1, 表示找不到源文件, 或url.properties配置错误; 如果返回 0,
    	 *         则表示操作成功; 返回1, 则表示转换失败
    	 */

```java
	@Override
	public int officeToPdf(OfficeToPDFInfo officeToPDFInfo) {
		String sourceFile=officeToPDFInfo.sourceUrl;
		String destFile=officeToPDFInfo.destUrl;
			File inputFile = new File(sourceFile);
			if (!inputFile.exists()) {
				return -1;// 找不到源文件, 则返回-1
			}
			// 如果目标路径不存在, 则新建该路径
			File outputFile = new File(destFile);
			if (!outputFile.getParentFile().exists()) {
				outputFile.getParentFile().mkdirs();
			}
			String extentionName=FileUtils.getFileExtension(sourceFile);
			if(extentionName.equalsIgnoreCase("ppt")||extentionName.equalsIgnoreCase("pptx")||extentionName.equalsIgnoreCase("wpt"))
			{
				ppt2pdf(officeToPDFInfo.sourceUrl,officeToPDFInfo.destUrl);
			}else if(extentionName.equalsIgnoreCase("doc")||extentionName.equalsIgnoreCase("docx")||extentionName.equalsIgnoreCase("wps")){
				doc2pdf(officeToPDFInfo.sourceUrl,officeToPDFInfo.destUrl);
			}else if(extentionName.equalsIgnoreCase("xls")||extentionName.equalsIgnoreCase("xlsx")||extentionName.equalsIgnoreCase("et")){
				excel2PDF(officeToPDFInfo.sourceUrl,officeToPDFInfo.destUrl);
			}	
			return 0;
	}
	protected static boolean doc2pdf(String srcFilePath, String pdfFilePath) {  
		 ActiveXComponent pptActiveXComponent=null; 
		 ActiveXComponent workbook = null; 
		try {
	 ComThread.InitSTA();//初始化COM线程  
pptActiveXComponent = new ActiveXComponent(WORDSERVER_STRING);//初始化exe程序  
Variant[] openParams=new Variant[]{
		new Variant(srcFilePath),//filePath
		new Variant(true),
		new Variant(true)//readOnley
};
workbook = pptActiveXComponent.invokeGetComponent("Documents").invokeGetComponent
		("Open",openParams);
workbook.invoke("SaveAs",new Variant(pdfFilePath),new Variant(wdFormatPDF));                
return true;
		}finally{
	 if(workbook!=null)
	 {
		 workbook.invoke("Close"); 
		 workbook.safeRelease(); 
	 }
	 if(pptActiveXComponent!=null)
	 {  		
		 pptActiveXComponent.invoke("Quit"); 
		 pptActiveXComponent.safeRelease();
	 }
	 ComThread.Release();  
}
}

	protected static boolean ppt2pdf(String srcFilePath, String pdfFilePath) {
		 ActiveXComponent pptActiveXComponent=null; 
		 ActiveXComponent workbook = null;  
	     boolean readonly = true;
		try {
	 ComThread.InitSTA();//初始化COM线程  
pptActiveXComponent = new ActiveXComponent(PPTSERVER_STRING);//初始化exe程序  
workbook = pptActiveXComponent.invokeGetComponent("Presentations").invokeGetComponent
		("Open",new Variant(srcFilePath),new Variant(readonly));
workbook.invoke("SaveAs",new Variant(pdfFilePath),new Variant(ppSaveAsPDF));                
return true;
		}finally{
	 if(workbook!=null)
	 {
		 workbook.invoke("Close"); 
		 workbook.safeRelease(); 
	 }
	 if(pptActiveXComponent!=null)
	 {  		
		 pptActiveXComponent.invoke("Quit"); 
		 pptActiveXComponent.safeRelease();
	 }
	 ComThread.Release();  
}
} 
	 public static boolean excel2PDF(String srcFilePath,String pdfFilePath){
		ActiveXComponent et = null; 
	    Dispatch workbooks = null;  
	    Dispatch workbook = null;  
	         ComThread.InitSTA();//初始化COM线程  
	         //ComThread.InitSTA(true);  
	         try {  
	             et = new ActiveXComponent(EXECLSERVER_STRING);//初始化et.exe程序  
	             et.setProperty("Visible", new Variant(false));  
	             workbooks = et.getProperty("Workbooks").toDispatch();  
	             //workbook = Dispatch.call(workbooks, "Open", filename).toDispatch();//这一句也可以的  
	             workbook = Dispatch.invoke(workbooks,"Open",Dispatch.Method,new Object[]{srcFilePath,0,true},new int[1]).toDispatch();   
	             //Dispatch.invoke(workbook,"SaveAs",Dispatch.Method,new Object[]{pdfFilePath,xlTypePDF},new int[1]);
	             Dispatch.call(workbook,"ExportAsFixedFormat",new Object[]{xlTypePDF,pdfFilePath});
	             return true;
	         }finally{
	        	 if(workbook!=null)
	        	 {
	        		 Dispatch.call(workbook,"Close");
	        		 workbook.safeRelease(); 
	        	 }
	        	 if(et!=null)
	        	 {  		
	        		 et.invoke("Quit"); 
	        		 et.safeRelease();
	        	 }
	        	 ComThread.Release();  
	         }
	 }
```

3.OpenOffice4.X

    public int officeToPdf(OfficeToPDFInfo officeToPDFInfo) throws IOException {
    		String sourceFile=officeToPDFInfo.sourceUrl;
    		String destFile=officeToPDFInfo.destUrl;
    		String OpenOffice_HOME=officeToPDFInfo.openOfficeHOME;
    			File inputFile = new File(sourceFile);
    			if (!inputFile.exists()) {
    				return -1;// 找不到源文件, 则返回-1
    			}

    			// 如果目标路径不存在, 则新建该路径
    			File outputFile = new File(destFile);
    			if (!outputFile.getParentFile().exists()) {
    				outputFile.getParentFile().mkdirs();
    			}

    			//= "D:\\Program Files\\OpenOffice.org 3";//这里是OpenOffice的安装目录, 在我的项目中,为了便于拓展接口,没有直接写成这个样子,但是这样是绝对没问题的
    			// 如果从文件中读取的URL地址最后一个字符不是 '\'，则添加'\'
    			if (OpenOffice_HOME.charAt(OpenOffice_HOME.length() - 1) != '\\') {
    				OpenOffice_HOME += "\\";
    			}
    			// 启动OpenOffice的服务
    			String command = OpenOffice_HOME
    					+ "program\\soffice.exe -headless -accept=\"socket,host=127.0.0.1,port=8100;urp;StarOffice.ServiceManager\" -nofirststartwizard";
    			Process pro = Runtime.getRuntime().exec(command);

```java
			// connect to an OpenOffice.org instance running on port 8100
			OpenOfficeConnection connection = new SocketOpenOfficeConnection(
					"127.0.0.1", 8100);
			connection.connect();
			// convert
			DocumentConverter converter = new OpenOfficeDocumentConverter(connection);
			//DocumentConverter converter = new StreamOpenOfficeDocumentConverter(connection); 

			converter.convert(inputFile, outputFile);
			// close the connection
			connection.disconnect();
			// 关闭OpenOffice服务的进程
			pro.destroy();
			return 0;
	}
```
