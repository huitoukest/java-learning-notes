---
title: "带有范围权重信息的随机数列表   java8实现 2"
date: "2018-03-07 17:59:34"
categories: ["j2se"]
tags: ["随机数", "范围", "权重", "红包算法"]
---

# 说明
其定义可以参考http://blog.csdn.net/huitoukest/article/details/79449076
主要是使产生的随机数在一个列表中的几个范围内的平均值符合给的的权重比值。
在此文实现中，对权重值过大的情况进行了处理，通过自动降低权重值的方法来使之产生出符合
最大值和最小值的随机数。

## 思路
和RandomListUtil中的填充数据->随机数据->排序->按照权重取值->打乱权重范围内的随机值不同。
RandomListUtil2中的实现思路如下：
->    计算带有数量信息的权重比值
->    通过比值计算出每个范围内的随机总数
->   生成每个范围内的随机数
-->  将生成的多个列表合并为一个
相对于 RandomListUtil1 中的实现而言，其范围内的数据的平均数的权重信息将会更加稳定，同时步奏更少。

# 实现

## 工具类

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
import java.util.IntSummaryStatistics;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
/**
 * 
 * @author huitoukest
 * 和RandomListUtil中的填充数据->随机数据->排序->按照权重取值->打乱权重范围内的随机值不同。
 * RandomListUtil2的思路是计算带有数量信息的权重比值-> 通过比值计算出每个范围内的随机总数->生成每个范围内的随机数
 *  -->将生成的多个列表合并为一个;
 * 
 */
public class RandomListUtil2 {
    private static final double minPositiveValue = 1.0E-308;

    public static void main(String[] args) {
        RangeWeightData rwData = new RangeWeightData();
        rwData.setCount(10);
        rwData.setTotal(100);
        List<Integer> getRandomList = getRandomList(1, 15, 10,100);
        getRandomList.forEach(item->System.out.println(item + ","));
    }
    
    public static RandomRangeWeight getDefaultRandomRangeWeight(int startIndex,int endIndex) {
        RandomRangeWeight weightTmp  = new RandomRangeWeight();
        weightTmp.setStartIndex(startIndex);
        weightTmp.setEndIndex(endIndex);
        weightTmp.setWeightValue(RandomRangeWeight.DEFAULT_WEIGHT_VALUE);
        return weightTmp;
    }
    
    /**
     * 对权重信息进行数据填充;
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
             for(int  i = 0; i <  rangeWeights.length ;i ++) {//填充默认权重数据
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
             //填充排序后的数据
             for(int  i = 0; i <  rangeWeights.length ;i ++) {
                 RandomRangeWeight rangeWeight = rangeWeights[i];
                 if(rangeWeight.getWeightValue() != RandomRangeWeight.DEFAULT_WEIGHT_VALUE) {
                     list.add(rangeWeight);
                 }
             }
        }
        return list;
    }
   
    /**
    * 通过权重和列表的总和
    * @param totalValue
    * @param randomRangeWeights
    * @return 和权重列表索引对应的每一个部分的数据总和,优先满足最小值要求。
     * @throws IOException 
     * @throws ClassNotFoundException 
    */
    @SuppressWarnings("unchecked")
    private static List<RangeWeightData> getRangeSumValue(Integer minValue,Integer maxValue,int listSize,int totalValue,  List<RandomRangeWeight> randomRangeWeights) throws ClassNotFoundException, IOException{
        if(null == randomRangeWeights) {
            return null;
        }
        List<RangeWeightData> rangeSumDataList = new ArrayList<>(randomRangeWeights.size());
        if(randomRangeWeights.isEmpty()) {
            return rangeSumDataList;
        }
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
        //处理权重数据，如果按照最大权重的比例算出来的结果的平均数大于最大值，则将其余所有的权重值进行加1操作，
        //以此缓慢降低最大权重的比值，知道其算出的结果小于最大值。
        
        /**
         * 用来装处理后的权重数据
         */
        List<RandomRangeWeight> handleRangeWeightList = (List<RandomRangeWeight>) deepCopy(randomRangeWeights);
        handleRangeWeightList.forEach(item->{
            if(item.getStartIndex() > item.getEndIndex()) {
                int tmpValue = item.getStartIndex();
                item.setStartIndex(item.getEndIndex());
                item.setEndIndex(tmpValue);
            }
            if(item.getStartIndex() < 0) {
                item.setStartIndex(0);
            }
            if(item.getEndIndex() >= listSize) {
                item.setEndIndex(listSize - 1);
            }
        });//处理无效索引
        boolean re = true;
        IntSummaryStatistics intSummaryStatistics = null;
        while(re) {
            intSummaryStatistics = handleRangeWeightList.stream().mapToInt(item->item.getWeightValue()).summaryStatistics();
            int maxWeightValue = intSummaryStatistics.getMax();
            //如果计算出的最大权重范围内的平均值比最大值还大,那么使最大权重值减去1。
            re =  intSummaryStatistics.getSum()  * maxWeightValue > maxValue * intSummaryStatistics.getCount() * intSummaryStatistics.getAverage();            
            if(re) {
                handleRangeWeightList.stream()
                                     .filter(item -> item.getWeightValue() >= maxWeightValue)
                                     .forEach(item -> item.setWeightValue(item.getWeightValue() - 1 ));
            }
        }
        final double weightAvg = intSummaryStatistics.getAverage();
        //得到每一个权重数据内的数据总和
        rangeSumDataList = handleRangeWeightList
                             .stream()
                             .map(item-> {
                                 RangeWeightData rangeWeightData = new RangeWeightData();
                                 rangeWeightData.setRandomRangeWeight(item);
                                 rangeWeightData.setCount((item.getEndIndex() - item.getStartIndex() + 1));
                                 int sumValue = (int)(avgTotal * item.getWeightValue() * rangeWeightData.getCount() / weightAvg);
                                 rangeWeightData.setTotal(sumValue);
                                 return rangeWeightData;
                              })
                             .collect(Collectors.toList());
        int rangeSum = rangeSumDataList.stream().mapToInt(item->item.getTotal()).sum();
        int reSetValueSIze = totalValue - rangeSum;//需要计算值的数量;
        int j = 0;
        while(j < reSetValueSIze) {
            for(int i = 0;i < rangeSumDataList.size() && j < reSetValueSIze;i++) {//数据填充
                RangeWeightData rwd = rangeSumDataList.get(i);
                if(rwd.getCount() * maxValue > rwd.getTotal() + 1) {
                    rwd.setTotal(rwd.getTotal() + 1);
                    j++;
                }
            }
        }       
       return rangeSumDataList; 
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
    public static List<Integer> getRandomList(Integer minValue,Integer maxValue,int listSize,int  totalValue){
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
            int shuffleCount =  (int) ((maxValue - minValue ) / avgTotal)  ; //数据打乱的次数
            if(shuffleCount == 0) {
                shuffleCount = 1;
            }
            for(int i = 0; i < shuffleCount + 1 ; i++) {
                shuffleData(list,minValue,maxValue);
            }
            return list;
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
        List<Integer> list = null;
        
        if(randomRangeWeights == null || randomRangeWeights.length <= 0) {          
           list = getRandomList(minValue,maxValue,listSize,totalValue);
        }else {
            List<RandomRangeWeight> randomRangeWeightList  = Arrays.asList(randomRangeWeights);
            List<RangeWeightData> rwList= getRangeSumValue(minValue, maxValue, listSize, totalValue,randomRangeWeightList);
            Collections.sort(rwList,new Comparator<RangeWeightData>(){
                @Override
                public int compare(RangeWeightData a, RangeWeightData b) {
                           if(b.getRandomRangeWeight().getStartIndex() > a.getRandomRangeWeight().getEndIndex()) {
                               return -1;
                           }else if(a.getRandomRangeWeight().getStartIndex() > b.getRandomRangeWeight().getEndIndex()) {
                               return  1;
                           }//按照索引升序排序
                           return 0;
                }});
            list = new ArrayList<>();
            List<Integer> tmp  = null;
            for(RangeWeightData rw : rwList ) {
                tmp = getRandomList(minValue,maxValue,rw.getCount(),rw.getTotal());
                list.addAll(tmp);
            }
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
    
    /**
     * 在指定的范围内交换打乱数据
     * @param list
     * @param randomRangeWeights
     */
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
     * 对list中的数据进行随机和打乱
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
    
    /**
     * 的到指定范围内的一个随机数
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
```

## bean

```java
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

/**
 * 存储计算后的范围/权重数据
 * @author huitoukest
 *
 */
public class RangeWeightData {
    private int count = 0;
    private int total = 0;
    private RandomRangeWeight randomRangeWeight;
    public int getCount() {
        return count;
    }
    public void setCount(int count) {
        this.count = count;
    }
    public int getTotal() {
        return total;
    }
    public void setTotal(int total) {
        this.total = total;
    }
    public RandomRangeWeight getRandomRangeWeight() {
        return randomRangeWeight;
    }
    public void setRandomRangeWeight(RandomRangeWeight randomRangeWeight) {
        this.randomRangeWeight = randomRangeWeight;
    } 
}

```

## 测试类

```java
public class RandomTest {
    @Test
    public void randomListTest2() throws ClassNotFoundException, IOException {
        RandomRangeWeight[] randomArray = new RandomRangeWeight[]{
                new RandomRangeWeight(0,99,10),
                new RandomRangeWeight(100,199,5),
                new RandomRangeWeight(200,299,2),
                new RandomRangeWeight(300,400,200),
        };
        List<Integer> list =  RandomListUtil2.getRandomList(1,100,400,10000);
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
        list =  RandomListUtil2.getRandomWeightList(1,100,400,10000,randomArray);
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

## 结果

```java
list size 400 ,sum:10000
1,1,70,76,52,83,1,43,5,25,31,47,20,人工省略...
27.9,21.99,20.45,29.66,list size 400 ,sum:10000
3,1,7,1,1,34,11,1,26,13,1,1,1,1,35,人工省略...
8.55,4.28,1.7,85.47,
```
