---
title: "人民币大小写转换 java 实现"
date: "2017-10-12 17:28:31"
categories: ["j2se"]
tags: ["java", "大小写", "转换", "人民币"]
---

参考:http://blog.csdn.net/guaishushu1ss/article/details/76757405

对匹配的金额大小,转换规则做了部分修改

工具类:

    public class CurrencyUtil {
    	/**
    	 * 转换为中国人民币大写字符串,精确到分
    	 * @param money 传入小写数字字符串
    	 * @return
    	 * @throws Exception
    	 */

```java
	public static String toChinaUpper(String money) throws Exception {
		boolean lessZero = false;
		if(money.startsWith("-")) {
			money = money.substring(1);
			lessZero = true;
		}

		if (!money.matches("^[0-9]*$|^0+\\.[0-9]+$|^[1-9]+[0-9]*$|^[1-9]+[0-9]*.[0-9]+$")) {
			throw new Exception("钱数格式错误！");
		}
		String[] part = money.split("\\.");
		String integerData = part[0];
		String decimalData = part.length > 1 ? part[1] : "";
		//替换前置0
		if(integerData.matches("^0+$"))
		{
			integerData = "0";
		}else if(integerData.matches("^0+(\\d+)$")){
			integerData = integerData.replaceAll("^0+(\\d+)$", "$1");
		}		

		StringBuffer integer = new StringBuffer();
		for (int i = 0; i < integerData.length(); i++) {
			char perchar = integerData.charAt(i);
			integer.append(upperNumber(perchar));
			integer.append(upperNumber(integerData.length() - i - 1));
		}
		StringBuffer decimal = new StringBuffer();
		if (part.length > 1 && !"00".equals(decimalData)) {
			int length = decimalData.length() >= 2 ? 2 : decimalData.length();
			for (int i = 0; i < length; i++) {
				char perchar = decimalData.charAt(i);
				decimal.append(upperNumber(perchar));
				if (i == 0)
					decimal.append('角');
				if (i == 1)
					decimal.append('分');
			}
		}
		String result = integer.toString() + decimal.toString();
		result = dispose(result);
		if(lessZero && !"零圆整".equals(result)) {
			result = "负" + result;
		}
		return result;
	}

	private static char upperNumber(char number) {
		switch (number) {
		case '0':
			return '零';
		case '1':
			return '壹';
		case '2':
			return '贰';
		case '3':
			return '叁';
		case '4':
			return '肆';
		case '5':
			return '伍';
		case '6':
			return '陆';
		case '7':
			return '柒';
		case '8':
			return '捌';
		case '9':
			return '玖';
		}
		return '0';
	}

	private static char upperNumber(int index) {
		int realIndex =  index  % 9;
		if(index > 8) {//亿过后进入回归,之后是拾,佰...
			realIndex =  (index - 9) % 8;
			realIndex = realIndex + 1;
		}
		switch (realIndex) {
		case 0:
			return '圆';
		case 1:
			return '拾';
		case 2:
			return '佰';
		case 3:
			return '仟';
		case 4:
			return '万';
		case 5:
			return '拾';
		case 6:
			return '佰';
		case 7:
			return '仟';
		case 8:
			return '亿';
		}
		return '0';
	}

	private static String dispose(String result) {
		result = result.replaceAll("0", "");//处理
		result = result.replaceAll("零仟零佰零拾|零仟零佰|零佰零拾|零仟|零佰|零拾", "零");
		result = result.replaceAll("零+", "零").replace("零亿", "亿");
		result = result.matches("^.*亿零万[^零]仟.*$") ? result.replace("零万", "零") : result.replace("零万", "万");	
		result = result.replace("亿万", "亿");
		//处理小数
		result = result.replace("零角", "零").replace("零分", "");	
		result = result.replaceAll("(^[零圆]*)(.+$)", "$2");	
		result = result.replaceAll("(^.*)([零]+圆)(.+$)", "$1圆零$3");

		//处理整数单位
		result = result.replaceAll("圆零角零分|圆零角$|圆$|^零$|圆零$|零圆$", "圆整");
		result = result.replaceAll("^圆整$", "零圆整");
		result = result.replaceAll("零+", "零");
		result = result.replaceAll("(^.*)(圆[零]+$)", "$1圆整");

		return result;
	}
}
```

测试类:

```java
public class CurrencyUtilTest {
	@Test
public void test(){
try {
	Assert.assertEquals(CurrencyUtil.toChinaUpper("0"),"零圆整");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("000000000000"),"零圆整");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("0.00"),"零圆整");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("0.03"),"叁分");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("0.43"),"肆角叁分");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("0000.43"),"肆角叁分");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("10000.43"),"壹万圆零肆角叁分");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("000000000000.000"),"零圆整");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("421.0"),"肆佰贰拾壹圆整");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("421.0000"),"肆佰贰拾壹圆整");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("215224635421.00"),"贰仟壹佰伍拾贰亿贰仟肆佰陆拾叁万伍仟肆佰贰拾壹圆整");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("215224635421.53"),"贰仟壹佰伍拾贰亿贰仟肆佰陆拾叁万伍仟肆佰贰拾壹圆伍角叁分");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("215224635421.03"),     "贰仟壹佰伍拾贰亿贰仟肆佰陆拾叁万伍仟肆佰贰拾壹圆零叁分");
	Assert.assertEquals(CurrencyUtil.toChinaUpper("2463215224635421.03"),"贰仟肆佰陆拾叁万贰仟壹佰伍拾贰亿贰仟肆佰陆拾叁万伍仟肆佰贰拾壹圆零叁分");
Assert.assertEquals(CurrencyUtil.toChinaUpper("1"),"壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("10"),"壹拾圆整");
Assert.assertEquals(CurrencyUtils.toChinaUpper("10.01"),"壹拾圆零壹分");
Assert.assertEquals(CurrencyUtils.toChinaUpper("10000100.01"),"壹仟万零壹佰圆零壹分");
Assert.assertEquals(CurrencyUtil.toChinaUpper("20.7"),"贰拾圆零柒角");
Assert.assertEquals(CurrencyUtil.toChinaUpper("10.70"),"壹拾圆零柒角");
Assert.assertEquals(CurrencyUtil.toChinaUpper("18.5"),"壹拾捌圆伍角");
Assert.assertEquals(CurrencyUtil.toChinaUpper("200.5"),"贰佰圆零伍角");
Assert.assertEquals(CurrencyUtil.toChinaUpper("2000"),"贰仟圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("50000"),"伍万圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("500000"),"伍拾万圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5000000"),"伍佰万圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("50000000"),"伍仟万圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("500000000"),"伍亿圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5000000000"),"伍拾亿圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5000000001"),"伍拾亿零壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5000000021"),"伍拾亿零贰拾壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5000000421"),"伍拾亿零肆佰贰拾壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5000005421"),"伍拾亿零伍仟肆佰贰拾壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5000035421"),"伍拾亿零叁万伍仟肆佰贰拾壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5000635421"),"伍拾亿零陆拾叁万伍仟肆佰贰拾壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5004635421"),"伍拾亿零肆佰陆拾叁万伍仟肆佰贰拾壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5024635421"),"伍拾亿贰仟肆佰陆拾叁万伍仟肆佰贰拾壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5224635421"),"伍拾贰亿贰仟肆佰陆拾叁万伍仟肆佰贰拾壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("15224635421"),"壹佰伍拾贰亿贰仟肆佰陆拾叁万伍仟肆佰贰拾壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("215224635421"),"贰仟壹佰伍拾贰亿贰仟肆佰陆拾叁万伍仟肆佰贰拾壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("500021"),"伍拾万零贰拾壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5000821"),"伍佰万零捌佰贰拾壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("5050006501"),"伍拾亿伍仟万陆仟伍佰零壹圆整");
Assert.assertEquals(CurrencyUtil.toChinaUpper("550300001"),"伍亿伍仟零叁拾万零壹圆整");
} catch (Exception e) {
e.printStackTrace();
}
}
}
```

附上转换的一些规则:

```text
人民币常识
人民币金额中文大写汉字主要包括：零、壹、贰、叁、肆、伍、陆、柒、捌、玖、拾、佰、仟、万、亿。
人民币（缩写为RMB）是我国大陆地区的法定货币，尽管每个人几乎天天都要接触到人民币或者支票，但是人民币大写如何写是困扰很多人的问题。
尽管生活中看起来极其熟悉而又简单的东西，但发现其实并不会写。人民币在ISO 4217简称为CNY（China Yuan），常用简写为RMB（Ren Min Bi）；人民币货币的符号是“ ￥”（'Y'+'='），读音为“YUAN”。
人民币按照材料的自然属性划分，有金属币（亦称硬币）、纸币（亦称钞票）。无论纸币、硬币均等价流通，至今已发行了五套人民币。
人民币大写规范介绍
银行、单位和个人填写的各种票据和结算凭证是办理支付结算和现金收付的重要依据，直接关系到支付结算的准确、及时和安全。票据和结算凭证是银行、单位和个人凭以记载账务的会计凭证，是记载经济业务和明确经济责任的一种书面证明。因此，填写票据和结算凭证必须做到标准化、规范化、要素齐全、数字正确、字迹清晰、不错漏、不潦草、防止涂改。
中文大写金额数字应用正楷或行书填写，如壹、贰、叁、肆、伍、陆、柒、捌、玖、拾、佰、仟、万、亿、元、角、分、零、整(正)等字样，不得用一、二(两)、三、四、五、六、七、八、九、十、毛、另(或0)填写，不得自造简化字。如果金额数字书写中使用繁体字，如贰、陆、亿、万、圆的，也应受理。 
人民币大写的正确写法还应注意以下几项：
一、中文大写金额数字到“元”为止的，在“元”之后、应写“整”(或“正”)字；在“角”之后，可以不写“整”(或“正”)字；大写金额数字有“分”的，“分”后面不写“整”(或“正”)字。
二、中文大写金额数字前应标明“人民币”字样，大写金额数字应紧接“人民币”字样填写，不得留有空白。大写金额数字前未印“人民币”字样的，应加填“人民币”三字，在票据和结算凭证大写金额栏内不得预印固定的“仟、佰、拾、万、仟、佰、拾、元、角、分”字样。
三、阿拉伯数字小写金额数字中有“0”时，中文大写应按照汉语语言规律、金额数字构成和防止涂改的要求进行书写。
四、阿拉伯小写金额数字前面均应填写人民币符号“￥”，阿拉伯小写金额数字要认真填写，不得连写分辨不清。
五、票据的出票日期必须使用中文大写，为防止变造票据的出票日期，在填写月、日时、月为壹、贰和壹拾的，日为壹至玖和壹拾、贰拾和叁拾的，应在其前加“零”，日为拾壹至拾玖的应在其前加“壹”，如1月15日应写成零壹月壹拾伍日，再如10月20日应写成零壹拾月零贰拾日。
六、票据出票日期使用小写填写的，银行不予受理；大写日期未按要求规范填写的，银行可予受理，但由此造成损失的由出票人自行承担。
```
