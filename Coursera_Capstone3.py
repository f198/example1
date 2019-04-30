
# coding: utf-8

# In[1]:


import pandas as pd
get_ipython().system(u'pip install beautifulsoup4')
get_ipython().system(u'pip install lxml')
get_ipython().system(u'pip install requests')


# In[2]:


from bs4 import BeautifulSoup
import requests


# In[3]:


path = requests.get('https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M', timeout = 5)


# In[4]:


soup = BeautifulSoup(path.text, "lxml")


# In[5]:


match = soup.find('div', class_='mw-parser-output')


# This code looks for the titles of the table

# In[7]:


word = []

for th in match.table.tbody.tr.find_all('th'):
    c = th.text
    word.append(c)
    


word = list(map(str.strip,word))

print(word)



# This code looks for the body of the table, all the elements

# In[8]:


content = []
for td in match.table.tbody.find_all('td'):
   
    d = td.text
    content.append(d)
    
    
PC = content[0::3]
BH = content[1::3]
ND = content[2::3]

PC = list(map(str.strip,PC))
BH = list(map(str.strip,BH))
ND = list(map(str.strip,ND))


df = pd.DataFrame([PC,BH,ND]).transpose()



df.head(5)


# In[9]:


df.columns = word


# In[10]:


df.head()


# This eliminates the Boroughs that are not assigned

# In[27]:



df = df[(df['Borough'] != 'Not assigned')]

df


# This will give the same name of the Borough to the Neighbourhoods that are not assigned

# In[83]:



df.loc[df['Neighbourhood'] == 'Not assigned','Neighbourhood'] = df[(df['Neighbourhood'] == 'Not assigned')]['Borough']


# In[96]:


A = df.groupby(['Postcode','Borough'])['Neighbourhood'].apply(list)
A.columns = word
A.head(5)


# In[98]:


Toronto_Neighbourhoods = pd.DataFrame(A)
Toronto_Neighbourhoods.head(5)


# In[101]:


Toronto_Neighbourhoods.shape

