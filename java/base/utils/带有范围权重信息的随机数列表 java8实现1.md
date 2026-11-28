---
title: "带有范围权重信息的随机数列表  java8实现1"
date: "2018-03-05 21:44:05"
categories: ["j2se"]
tags: ["随机数", "权重", "列表", "红包算法"]
---

# 简介

注意： 第二种优化的实现方式见 http://blog.csdn.net/huitoukest/article/details/79474767

我们常常用到随机数，也经常用到随机数列表。比如常见的抽奖，微信/支付宝红包等。
而带有权重信息的随机数列表：是让列表中不同范围的数据具有不同的权重信息，使之在此范围内
产生的随机数的平均值符合此权重比值的数的概率最大。（看不懂的可以看示例说明）
比如：已知一个网站的访问量平均每天是10万，已知早上0点 - 9点的访问了占平均访问量是全天平均访问量的20% ， 10 - 19点的平均访问量是全天的30%，20-21点是50%。
那么我们可以产生一个在上诉三个范围内，产生一个权重2:10:5 的随机数列表来模拟网站的访问情况。

## 程序扩展
**微信和支付宝和红包往往具有正态分布的特点**，即中间值的红包最多，  
特别小的和特别大的红包很少，**红包的值的总和是确定的**。
如果需要产生这样的带有随机数数量信息的，在本示例中推荐如下两种方法：
1. 重写shuffleData方法，此方法中是真正的对数据进行了随机操作。
2. 产生三个不带有权重信息的随机数列表。比如：
 - 第一个列表，产生数量为10，总和是100的最小值6，最大值15的10个红包；
 - 第二个列表，产生数量为60，总和是200的最小值3，最大值5的80个红包；
 - 第三个列表，产生数量为10，总和是20的最小值1，最大值3的20个红包；
最后将三个列表放到一个列表中，就产生了一个数量是80，总和是320元的，较大概率基本符合正态分布
的红包列表。然后打乱数据即可使用。

# 实现

## 思路
为了保证产生的随机数的数量与总和与指定的数据相同。本示例中实现采用如下思路，  
测试用例中也这样测试：
1. 产生指定数量400个的，指定总数10000，最小值是1，最大值是100的随机数。
2. 产生一个指定大小的列表，将计算并处理填充平均数到列表中。
3. 根据最大最小值计算打乱数据的次数x，通过x次调用shuffleData来打乱数据 。  
如果不需要产生带有范围权重信息的数据，那么这个随机数列表已经可以拿来使用。
4. 对权重信息按照索引排序，填充其中漏掉的索引，并限制最大和最小索引。
5. 对4中权重信息按照权重值进行排序，对3中产生的列表复制并排序，并根据权重值产生
符合权重比值概率的索引，用此索引在3排序好的列表的随机数从取值，并存储到map中。
6. 对5中权重信息按照索引进行排序，并从map中取出随机数据添加到一个新建的列表中。
7. 对6中新建的列表按照权重信息，将每一个权重范围内的数据进行打乱。
8.  最后7中的列表即带有权重信息的列表数据

上诉实现的好处是产生的数量和总和是固定的，我们要做的是将数据打乱和加入权重信息。
还有一种思路：即产生随机数据的时候就加入权重信息，优点是不用打乱数据，缺点是需要控制  
数据的总和以及范围内的比值是否符合权重信息。

## 实现代码
```java
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class RandomListUtil {
    private static final double minPositiveValue = 1.0E-308;

    public static RandomRangeWeight getDefaultRandomRangeWeight(int startIndex,int endIndex) {
        RandomRangeWeight weightTmp  = new RandomRangeWeight();
        weightTmp.setStartIndex(startIndex);
        weightTmp.setEndIndex(endIndex);
        weightTmp.setWeightValue(RandomRangeWeight.DEFAULT_WEIGHT_VALUE);
        return weightTmp;
    }
    
    /**
     * 对权重信息进行重新排序，和数据填充;
     * @param randomRangeWeights
     * @return
     * @throws IOException 
     * @throws ClassNotFoundException 
     */
    private static List<RandomRangeWeight> refactorRandomRangeWeight(int listSize, RandomRangeWeight... randomRangeWeights) throws ClassNotFoundException, IOException{
        List<RandomRangeWeight> list = new ArrayList<>();
        if(listSize <=0 ) {
            return list;
        }
        if(null != randomRangeWeights && randomRangeWeights.length > 0) {
        RandomRangeWeight[] rangeWeights = new RandomRangeWeight[0];
        if(randomRangeWeights != null) {
            rangeWeights = new RandomRangeWeight[randomRangeWeights.length];
            deepCopyArray(randomRangeWeights,rangeWeights);
        }
            Arrays.sort(rangeWeights,new Comparator<RandomRangeWeight>(){
             @Override
             public int compare(RandomRangeWeight a, RandomRangeWeight b) {
                        if(b.getStartIndex() > a.getEndIndex()) {
                            return 1;
                        }else if(a.getStartIndex() > b.getEndIndex()) {
                            return  -1;
                        }//按照索引降序排序
                        return 0;
             }});
            for(int  i = 0; i <  rangeWeights.length ;i ++) {//初始化最大最小索引值
                RandomRangeWeight rangeWeight = rangeWeights[i];
                if(rangeWeight.getStartIndex() < 0 ) {
                    rangeWeight.setStartIndex(0);
                }
                if(rangeWeight.getEndIndex() >= listSize) {
                    rangeWeight.setEndIndex(listSize - 1);
                }
            }
             for(int  i = 0; i <  rangeWeights.length ;i ++) {//数据填充
                 RandomRangeWeight rangeWeight = rangeWeights[i];
                 if(i == 0 && rangeWeight.getEndIndex() < listSize -1) {
                     RandomRangeWeight weightTmp = getDefaultRandomRangeWeight(rangeWeight.getEndIndex() + 1,listSize -1);
                     list.add(weightTmp);
                 }
                 if(i == rangeWeights.length - 1 && rangeWeight.getStartIndex() > 0) {
                     RandomRangeWeight weightTmp = getDefaultRandomRangeWeight(0,rangeWeight.getStartIndex() -1);
                     list.add(weightTmp);
                 }
                 int startIndex;
                 int endIndex =  rangeWeight.getStartIndex() -1;
                     startIndex =  endIndex;             
                 if(i + 1 < rangeWeights.length) {
                     startIndex = rangeWeights[i + 1].getEndIndex() + 1;
                 }
                 if(startIndex > 0 && endIndex < listSize - 1 && startIndex <= endIndex) {
                     RandomRangeWeight weightTmp = getDefaultRandomRangeWeight(startIndex,endIndex);
                     list.add(weightTmp);
                 }
                 if(rangeWeight.getWeightValue() == 1) {
                     list.add(rangeWeight);
                 }
             }
             //将填充的数据进行打乱操作
             for(int  i = 0; i < list.size() ; i++ ) {
                 int random = (int) getRandomValue(0, list.size() - 1);
                 if(random == i) {
                     continue;
                 }
                 RandomRangeWeight tmp = list.get(i);
                 list.set(i, list.get(random));
                 list.set(random, tmp);
             }
             Arrays.sort(rangeWeights,new Comparator<RandomRangeWeight>(){
                 @Override
                 public int compare(RandomRangeWeight a, RandomRangeWeight b) {
                            //按照权重升序排序
                            return a.getWeightValue() - b.getWeightValue();
                 }});
             //填充排序后的数据
             for(int  i = 0; i <  rangeWeights.length ;i ++) {
                 RandomRangeWeight rangeWeight = rangeWeights[i];
                 if(rangeWeight.getWeightValue() != RandomRangeWeight.DEFAULT_WEIGHT_VALUE) {
                     list.add(0, rangeWeight);
                 }
             }
        }
        return list;
    }
   
    /**
     * 得到指定范围内的随机数列表，不带权重信息
     * @param minValue 最小值，如果为空，默认0
     * @param maxValue 最大值，如果为空，默认最大值是和
     * @param listSize 随机数数量
     * @param totalValue 总数
     * @return
     * @throws IOException 
     * @throws ClassNotFoundException 
     */
    public static List<Integer> getRandomList(Integer minValue,Integer maxValue,int listSize,Integer totalValue) throws ClassNotFoundException, IOException{
        return getRandomWeightList(minValue,maxValue,listSize,totalValue);
    }
    
   /**
    * 得到指定范围内的随机数列表
    * @param minValue 最小值，如果为空，默认0
    * @param maxValue 最大值，如果为空，默认最大值是和
    * @param listSize 随机数数量
    * @param totalValue 总数
    * @param randomType 产生带有权重的随机数的产生方式
    * @param randomRangeWeights 
    * @return
 * @throws IOException 
 * @throws ClassNotFoundException 
    */
    public static List<Integer> getRandomWeightList(Integer minValue,Integer maxValue,int listSize,Integer totalValue,RandomRangeWeight... randomRangeWeights) throws ClassNotFoundException, IOException {
        List<Integer> list = new ArrayList<>(listSize);
        if(null == minValue) {
            minValue = 0;
        }
        if(null == maxValue) {
            maxValue = totalValue;
        }
        if(minValue > maxValue) {
            int tmp = minValue;
            minValue = maxValue;
            maxValue = tmp;
        }
        double avgTotal = totalValue / listSize;
        if(avgTotal > maxValue) {
            String errorMsg = "can not product data in range " + minValue + "-" + maxValue 
                    + ",maxValue must greate than or equals  totalValue/listSize:" + avgTotal;
            throw new RuntimeException(errorMsg);
        }else if(avgTotal < minValue) {
            String errorMsg = "can not product data in range " + minValue + "-" + maxValue 
                    + ",minValue must less than or equals  totalValue/listSize:" + avgTotal;
            throw new RuntimeException(errorMsg);
        }
        int avgTotleInteger = (int) avgTotal;
        int reSetValueSIze = totalValue - avgTotleInteger * listSize;//需要计算值的数量;
        for(int i = 0,j = 0;i < listSize;i++,j++) {//数据填充
            if(j < reSetValueSIze) {//数据重新填充
                list.add(i, avgTotleInteger + 1);
            }else {
                list.add(i, avgTotleInteger);
            }
        }    
        int shuffleCount =  (int) ((maxValue - minValue ) / avgTotal + 1) ; //数据打乱的次数
        for(int i = 0; i < shuffleCount + 1 ; i++) {
            shuffleData(list,minValue,maxValue);
        }
       if(randomRangeWeights != null && randomRangeWeights.length > 0) {
           list = getRangeWeightList(list,randomRangeWeights);
       } 
       return list;
    }
    
    /**
     * 通过指定数据的范围权重randomRangeWeights，对list处理，生成带有权重范围分布的数据
     * @param list
     * @param randomRangeWeights
     * @return
     * @throws IOException 
     * @throws ClassNotFoundException 
     */
    @SuppressWarnings("unchecked")
    public static List<Integer> getRangeWeightList(List<Integer> list,RandomRangeWeight... randomRangeWeights) throws ClassNotFoundException, IOException{
        if(null == randomRangeWeights || randomRangeWeights.length <=0) {
            return list;
        }
        int weightTotal = 0;
        int weightCount = 0;
        for(RandomRangeWeight randomRangeWeight : randomRangeWeights) {
            if(randomRangeWeight.getWeightValue() > 0) {
                weightTotal  += randomRangeWeight.getWeightValue();
                weightCount ++;
            }
        }
        double avgWeight = 0;
        if(weightTotal > 0) {
            avgWeight = weightTotal / weightCount;
        }else {
            return list;
        }
       List<Integer> listTmp = (List<Integer>) deepCopy(list);
       Collections.sort(listTmp);
       List<RandomRangeWeight> rangeWeightList = refactorRandomRangeWeight(list.size(),randomRangeWeights);
       List<Integer> randomValueList = null;
       randomValueList = getRandomValueListByCycleRangeWeight(list,rangeWeightList,avgWeight);
       return randomValueList;
    }
   
    /**
     * 
     * @param sourceList
     * @param rangeWeightList 默认按照权重值降序排列
     * @param avgWeight
     * @return
     * @throws ClassNotFoundException
     * @throws IOException
     */
    @SuppressWarnings("unchecked")
    private static List<Integer> getRandomValueListByCycleRangeWeight(List<Integer> sourceList,List<RandomRangeWeight> rangeWeightList,double avgWeight) throws ClassNotFoundException, IOException{
        List<Integer> listTmp = (List<Integer>) deepCopy(sourceList);
        Collections.sort(listTmp);
        List<Integer> randomValueList = new ArrayList<>(sourceList.size());
        Map<String,List<Integer>> weightItemListMap = new HashMap<>();
        int listSize = listTmp.size();
        for(int i = 0;i < rangeWeightList.size() ; i ++) {
            RandomRangeWeight randomRangeWeight = rangeWeightList.get(i);
            String mapKey = randomRangeWeight.getStartIndex() + "_" + randomRangeWeight.getEndIndex();
            if(weightItemListMap.get(mapKey) == null) {
                weightItemListMap.put(mapKey, new ArrayList<Integer>());
            }
            List<Integer> itemList = weightItemListMap.get(mapKey);
            for(int j = randomRangeWeight.getStartIndex() ; j <=  randomRangeWeight.getEndIndex() ; j++ ) {
                
                int getIndex = 0;
                int getValue = 0;
                if(randomRangeWeight.getWeightValue() <= 0) {
                    getIndex = 0;
                }else {
                   getIndex = (int)((Math.random() * listSize + minPositiveValue) * randomRangeWeight.getWeightValue() / avgWeight );
                }
                if(getIndex >= listTmp.size()) {
                    getIndex = listTmp.size() - 1;
                }
                try {
                    getValue = listTmp.get(getIndex);
                }catch (Exception e) {
                    e.printStackTrace();
                }
                listTmp.remove(getIndex);
                itemList.add(getValue);
                
            }
        }
        List<RandomRangeWeight> rangeSortedWeightList = (List<RandomRangeWeight>) deepCopy(rangeWeightList);
        Collections.sort(rangeSortedWeightList,new Comparator<RandomRangeWeight>(){
            @Override
            public int compare(RandomRangeWeight a, RandomRangeWeight b) {
                       if(b.getStartIndex() > a.getEndIndex()) {
                           return - 1;
                       }else if(a.getStartIndex() > b.getEndIndex()) {
                           return  1;
                       }//按照索引升序排序
                       return 0;
            }});
        for(RandomRangeWeight randomRangeWeight : rangeSortedWeightList) {
            List<Integer> tmpList = weightItemListMap.get(randomRangeWeight.getStartIndex() + "_" + randomRangeWeight.getEndIndex());
            //System.out.println(randomRangeWeight.getStartIndex() + "_" + randomRangeWeight.getEndIndex() + ":" + tmpList.stream().reduce(0,(a,b)->a+b));
            randomValueList.addAll(tmpList);
        }
        shuffleRangeWeightData(randomValueList, rangeSortedWeightList);
        return randomValueList;
    }
    
    
   private static <T> void deepCopyArray(T[] src,T[] dest) {
       if(null != src) {
           System.arraycopy(src, 0, dest, 0, src.length);
       }else {
           dest = null;
       }
   }
    
   private static Object deepCopy(Object src) throws IOException, ClassNotFoundException{          
        ByteArrayOutputStream byteOut = new ByteArrayOutputStream();             
        ObjectOutputStream out = new ObjectOutputStream(byteOut);             
        out.writeObject(src);                   
        ByteArrayInputStream byteIn = new ByteArrayInputStream(byteOut.toByteArray());             
        ObjectInputStream in =new ObjectInputStream(byteIn);             
        return in.readObject();   
   }  
    
    
    private static void shuffleRangeWeightData(List<Integer> list,List<RandomRangeWeight> randomRangeWeights) {
        if(randomRangeWeights != null && !randomRangeWeights.isEmpty()) {
            for(RandomRangeWeight randomRangeWeight : randomRangeWeights) {
                int startIndex = Math.min(randomRangeWeight.getStartIndex(), list.size() - 1) ;
                int endIndex = Math.min(randomRangeWeight.getEndIndex(), list.size() - 1) ;
                for(int  i = startIndex ; i <= endIndex  ; i++) {
                    int tmpIndex = (int) getRandomValue(startIndex, endIndex);
                    int tmpA = list.get(i);
                    int tmpB = list.get(tmpIndex);
                    list.set(i, tmpB);
                    list.set(tmpIndex, tmpA);
                }
            }
        }
    }
    
    /**
     * 对list中的数据进行随机打乱
     * @param list
     * @param minValue
     * @param maxValue
     */
    public static void shuffleData(List<Integer> list,int minValue,int maxValue) {
        int listSize = list.size();
        for(int i = 0;i < listSize;i++) {
            int exChangeIndex = (int)(Math.random() *  listSize);
            if(exChangeIndex == i) {
                continue;
            }
            double randomValue = getRandomValue(minValue,maxValue);
            int tmpSum = list.get(i) + list.get(exChangeIndex);
            int valueA = (int) (tmpSum - randomValue);
            int valueB = tmpSum - valueA;
            if(valueA < valueB) {
                int tmpValue = valueA;
                valueA = valueB;
                valueB = tmpValue;
            }
            if(valueA > maxValue) {
                valueA = maxValue;
                valueB = tmpSum - valueA;
            }else if(valueB < minValue) {
                valueB = minValue;
                valueA = tmpSum - valueB;
            }
            double randonmValue = Math.random() + minPositiveValue;
            if(randonmValue > 0.5) {
                list.set(i, valueA);
                list.set(exChangeIndex,valueB);
            }else {
                list.set(exChangeIndex, valueA);
                list.set(i,valueB);
            }
        }
    }
    
    /*private static int getWeightValue(int index,RandomRangeWeight... randomRangeWeights) {
        
        List<RandomRangeWeight> list = null;
        if(null !=  randomRangeWeights) {
            list = Arrays.asList(randomRangeWeights);
        }
        return getWeightValue(index,list);
    }*/
    
    /*private static int getWeightValue(int index,List<RandomRangeWeight> randomRangeWeights) {
        if(null != randomRangeWeights) {
            for(RandomRangeWeight randomRangeWeight : randomRangeWeights) {
                if(randomRangeWeight.getStartIndex() <= index && index <= randomRangeWeight.getEndIndex()) {
                    return randomRangeWeight.getWeightValue();
                }
            }
        }
        return RandomRangeWeight.DEFAULT_WEIGHT_VALUE;
    }*/
    
    
    
    /**
     * 
     * @param minValue
     * @param maxValue
     * @param coefficient
     * @return
     */
    public static double getRandomValue(double minValue,double maxValue) {
        double value = Math.random() * (maxValue - minValue) + minPositiveValue;
        value = value + minValue;
        if(value < minValue) {
            value = minValue;
        }else if(value > maxValue) {
            value = maxValue;
        }
        return value;
    }
}

/**
 * 权重值weightValue小于等于0的数据，将直接按照最小权重计算;
 * @author huitoukest
 *
 */
public class RandomRangeWeight implements java.io.Serializable{
    private static final long serialVersionUID = 1L;
    public  static final int DEFAULT_WEIGHT_VALUE = 1;
    private int startIndex;
    private int endIndex;
    private int weightValue;
    
    
    public RandomRangeWeight() {}
    
    public RandomRangeWeight(int startIndex, int endIndex, int weightValue) {
        super();
        this.startIndex = startIndex;
        this.endIndex = endIndex;
        this.weightValue = weightValue;
    }
    public int getStartIndex() {
        return startIndex;
    }
    public void setStartIndex(int startIndex) {
        this.startIndex = startIndex;
    }
    public int getEndIndex() {
        return endIndex;
    }
    public void setEndIndex(int endIndex) {
        this.endIndex = endIndex;
    }
    public int getWeightValue() {
        return weightValue;
    }
    public void setWeightValue(int weightValue) {
        this.weightValue = weightValue;
    }
}

```

## 测试类

```java
public class RandomTest {
    
    @Test
    public void randomListTest() throws ClassNotFoundException, IOException {
        RandomRangeWeight[] randomArray = new RandomRangeWeight[]{
                new RandomRangeWeight(0,99,10),
                new RandomRangeWeight(100,199,5),
                new RandomRangeWeight(200,299,2),
                new RandomRangeWeight(300,400,20),
        };
        List<Integer> list =  RandomListUtil.getRandomList(1,100,400,10000);
        System.out.println("list size " + list.size() + " ,sum:" + list.stream().reduce(0,(a,b)->a+b));
        int count = 0;
        int sum = 0;
        int avgIndexCount = 100;
        list.forEach(item->System.out.print(item + ","));
        System.out.println();
        for(int  i = 0; i< list.size();i++) {
            count ++ ;
            sum += list.get(i);
            if(count == avgIndexCount) {
                System.out.print( (double)sum / count + "," );
                count = 0;
                sum = 0; 
            }  
        }
        list =  RandomListUtil.getRandomWeightList(1,100,400,10000,randomArray);
        System.out.println("list size " + list.size() + " ,sum:" + list.stream().reduce(0,(a,b)->a+b));
        count = 0;
        sum = 0;
        list.forEach(item->System.out.print(item + ","));
        System.out.println();
        for(int  i = 0; i< list.size();i++) {
            count ++ ;
            sum += list.get(i);
            if(count == avgIndexCount) {
                System.out.print( (double)sum / count + "," );
                count = 0;
                sum = 0; 
            }  
        }
        
    }
}
```

## 结果示例
```java
list size 400 ,sum:10000
25.68,25.59,19.38,29.27,list size 400 ,sum:10000
26.77,17.98,5.35,49.9,
```
结果示例说明：
第一行：列表数量，总和
第二行：不带权重信息的四个范围内的数据平均值。
第三行：带有权重信息的四个范围内的数据平均值。

注意：基于java8实现
