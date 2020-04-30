import pandas as pd
import pyodbc
import re 
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

#строка соединения с сервером
sql_conn = pyodbc.connect('Driver={SQL Server Native Client 11.0};Server=(localdb)\MSSQLLocalDB;Database=vvDataExp2;\
Trusted_Connection=yes') 
cursor = sql_conn.cursor()

##выборка чеков перкрестка и пятерочки
query = "SELECT distinct name FROM [dbo].[items01] where inn in ('7825706086','7728029110','7715277300') \
and name like N'%молок%'"
#and name like N'%чудо%'

#таблица замен
query3 = "SELECT [oldval], [newval] FROM [dbo].[items08] "
df3 = pd.read_sql(query3, sql_conn)

#товар из чеков
df = pd.read_sql(query, sql_conn)
#df['name2'] = ""
df['bzmzh'] = ""
df['size'] = ""
df['product'] = ""
df['product2'] = ""
df['temp1'] = ""
df['temp2'] = ""
df['temp3'] = ""
df['name3'] = ""
df['rank'] = 0
df['percent'] = ""
df['brand'] = ""
df['category'] = ""


for index,row in df.iterrows():
    var1 = row['name']
    
    #меняем подстроки по таблице
    for index3,row3 in df3.iterrows():
        var1 = var1.replace(row3['oldval'], row3['newval'])
    
    #убираем код в начале
    var1 = var1.replace(': ',':')
    var1 = var1[var1.find(' ') + 1:len(var1)]
    
    df.at[index, 'temp3'] = var1
    
    #БЗМЖ 
    if var1.find('БЗМЖ') >=0:
        df.at[index, 'bzmzh'] = 'БЗМЖ'
        var1 = var1.replace('БЗМЖ', '')
    
    #вычисляем размер
    var2 = re.search(r'\d+((\.|\,|x|X|х|Х)?)\d*([а-я]|[А-Я])*$', var1)
    if var2:
        var3 = var2.start()
        var16 = var1[var3:var2.end()]
       
        var1 = var1[0:var3]
        #берем только число
        var23 = re.search(r'\d+((\.|\,|x|X|х|Х)?)\d*',var16)
        var22 = var16[var23.start():var23.end()]
        df.at[index, "size"] = var16

  
    #первое русское слово + заглавная букво и до следующей заглавной буквы - название
    var5 = re.search(r'[А-Я]([а-я]+)', var1)
    if var5:
        var6 = var5.start()
    else:
        var6 = 0
    
    
    var7 = re.search(r'[А-Я][А-Я]|[A-Z][A-Z]', var1[var6:len(var1)])
    if var7:
        var8 = var7.start()
    else:
        var8 = 0
    
    if var8 == 0:
        var8 = len(var1)
       
    var9 = var1[var6:var8 + var6]
    if var9.rstrip() != '':
        df.at[index, 'product2'] = re.compile(r'[а-я]+|[a-z]+').findall(var9.lower())[0] 
    var1 = var1.replace(var9,'')
    
    #часть перед первым руссским словом
    var10 = ''
    var15 = ''
    if var6 > 0:
        var10 = var1[0:var6].rstrip()
        
        var1 = var1.replace(var10,'')
    
    #ищем в остатке фразу с большими буквами
    var11 = re.search(r'[А-Я]|[A-Z]', var1)
    if var11:
        var12 = var11.start()
        #смотрим далее русскую маленькую
        var13 = re.search(r'[а-я]|\d', var1)
        if var13:
            var14 = var13.start()
        else:
            var14 = len(var1)
        var15 = var1[var12:var14]
        
        var1 = var1.replace(var15,'')
      
    #если первой фразы с большими нет - ставим вторую
    if var10 == '':
        var10 = var15
        var15= ''
    
    var10 = var10.lower().lstrip()
    df.at[index, 'temp1'] = var10
    #df.at[index, 'temp2'] = 
    
  
    #остаток добавляем к продукту
    var9 += " " + var1 + " " +  var15.lower()
    
    df.at[index, 'product'] = var9 
    
     
    ##выборка из эталонной базы
    query2 = "SELECT  *  FROM [vvDataExp2].[dbo].[vItems07] \
    where PROD_COUNT = N'" + var22 + "'"
        
    
    #первое словов в бренде 
    var19 = re.compile(r'[а-я]+|[a-z]+').findall(var10)
    if len(var19) > 0:
        query2 += " and [PROD_NAME2] like N'%" + var19[0] + "%'"
       
    #первое словов в названии
    var21 = re.compile(r'[а-я]+|[a-z]+').findall(var9.lower())
    query2 += " and [name] like N'" + var21[0] + "%'"  
    #второе
    if len(var21)>1:
        query2 += " and [name] like N'%" + var21[1] + "%'"
    #третье
    #if len(var21)>2:
       #query2 += " and [name] like N'%" + var21[2] + "%'"
    
    
    #определяем % жирности
    var17 = re.search(r'\d(.*)%', var9)
    if var17:
        var18 = var9[var17.start():var17.end()].replace(',','.')
        df.at[index, 'percent'] = var18
        query2 += " and name like '%" + var18 + "%'"
    
    #товар из эталонной базы
    df2 = pd.read_sql(query2, sql_conn)
    df2['rank'] = 0
    
    #поиск по эталонам
    for index2,row2 in df2.iterrows():
        df2.at[index2, 'rank'] = fuzz.partial_ratio(var9, row2['name'])
    
    for index2,row2 in df2[df2['rank'] == df2['rank'].max()].head(1).iterrows():
        df.at[index, 'name3'] = row2['name']
        df.at[index, 'rank'] = row2['rank']
        df.at[index, 'brand'] = row2['PROD_NAME']
        df.at[index, 'category'] = row2['PROD_GCPCL_BRICK']
        
    



print (len(df[df['rank'] > 0].index))
print (len(df[df['rank'] == 0].index))

df.to_excel('output.xlsx')
df[df['rank'] == 0].sort_values('temp1').tail(60)   