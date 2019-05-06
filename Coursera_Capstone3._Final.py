
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

# In[6]:


word = []

for th in match.table.tbody.tr.find_all('th'):
    c = th.text
    word.append(c)
    


word = list(map(str.strip,word))

print(word)



# This code looks for the body of the table, all the elements

# In[7]:


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


# In[8]:


df.columns = word


# In[9]:


df.head()


# This eliminates the Boroughs that are not assigned

# In[10]:



df = df[(df['Borough'] != 'Not assigned')]

df.head()


# This will give the same name of the Borough to the Neighbourhoods that are not assigned

# In[11]:



df.loc[df['Neighbourhood'] == 'Not assigned','Neighbourhood'] = df[(df['Neighbourhood'] == 'Not assigned')]['Borough']


# In[12]:


A = df.groupby(['Postcode','Borough'], as_index = False, sort = False).agg(','.join)
A.columns = word
A.head(5)


# In[13]:


Toronto_Neighbourhoods = pd.DataFrame(A)
Toronto_Neighbourhoods.head(5)


# In[14]:


Toronto_Neighbourhoods.shape


# That was the first part

# I will use geopy instead of geocoder because I ony got 'Nones'

# In[15]:


get_ipython().system(u'conda install geopy')


# In[16]:


from geopy.geocoders import Nominatim


# In[17]:


Lati = []
Long = []
h = 0

for i in Toronto_Neighbourhoods['Postcode']:
    try:
        geolocator = Nominatim(user_agent="specify_your_app_name_here")
        location = geolocator.geocode('{}, Toronto, Ontario'.format(Toronto_Neighbourhoods.iloc[h,2].split(',')[0]))
    
    
        lo = location.longitude
        la = location.latitude
        
        Lati.append(la)
        Long.append(lo)
        h = h+1
    except:
        location = geolocator.geocode('{}, Toronto, Ontario'.format(Toronto_Neighbourhoods.iloc[h,1]))
        lo = location.longitude
        la = location.latitude
        Lati.append(la)
        Long.append(lo)
        h = h+1
     




# In[18]:



Newdf = pd.DataFrame(Toronto_Neighbourhoods)



# In[19]:


Newdf['Latitude'] = Lati
Newdf['Longitude'] = Long

Newdf.head()


# That was the second part

# In[21]:


import numpy as np

get_ipython().system(u"conda install -c conda-forge geopy --yes # uncomment this line if you haven't completed the Foursquare API lab")
from geopy.geocoders import Nominatim # convert an address into latitude and longitude values

import matplotlib.cm as cm
import matplotlib.colors as colors

# import k-means from clustering stage
from sklearn.cluster import KMeans

get_ipython().system(u"conda install -c conda-forge folium=0.5.0 --yes # uncomment this line if you haven't completed the Foursquare API lab")
import folium # map rendering library

print('Libraries imported.')


# Get the latitude and longitude of Toronto

# In[22]:


location = geolocator.geocode('Toronto, Ontario')
TorLat = location.latitude
TorLon = location.longitude


# In[23]:


neighborhoods = Newdf


# Create a map

# In[24]:


map_Toronto = folium.Map(location=[TorLat, TorLon], zoom_start=10)

# add markers to map
for lat, lng, borough, neighborhood in zip(neighborhoods['Latitude'], neighborhoods['Longitude'], neighborhoods['Borough'], neighborhoods['Neighbourhood']):
    label = '{}, {}'.format(neighborhood, borough)
    label = folium.Popup(label, parse_html=True)
    folium.CircleMarker(
        [lat, lng],
        radius=5,
        popup=label,
        color='blue',
        fill=True,
        fill_color='#3186cc',
        fill_opacity=0.7,
        parse_html=False).add_to(map_Toronto)  
    
map_Toronto


# Getting Foursquare Data

# In[26]:


CLIENT_ID = '0NUBJCL1AELPHGX0CQMAAQLIFLIYQC20MXMICWTY3FEETYOG' # your Foursquare ID
CLIENT_SECRET = 'XEBGQOZAEUS1BCEJZR1QGKL1HTY3CBE0ULULWMRB02BNOAZK' # your Foursquare Secret
VERSION = '20180605' # Foursquare API version



# In[28]:


LIMIT = 100 # limit of number of venues returned by Foursquare API

radius = 500 # define radius

# create URL
url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
    CLIENT_ID, 
    CLIENT_SECRET, 
    VERSION, 
    TorLat, 
    TorLon, 
    radius, 
    LIMIT)
url # display URL


# In[29]:


results = requests.get(url).json()
results


# In[30]:


# function that extracts the category of the venue
def get_category_type(row):
    try:
        categories_list = row['categories']
    except:
        categories_list = row['venue.categories']
        
    if len(categories_list) == 0:
        return None
    else:
        return categories_list[0]['name']


# In[32]:


import json
from pandas.io.json import json_normalize 


# In[33]:


venues = results['response']['groups'][0]['items']
    
nearby_venues = json_normalize(venues) # flatten JSON

# filter columns
filtered_columns = ['venue.name', 'venue.categories', 'venue.location.lat', 'venue.location.lng']
nearby_venues =nearby_venues.loc[:, filtered_columns]

# filter the category for each row
nearby_venues['venue.categories'] = nearby_venues.apply(get_category_type, axis=1)

# clean columns
nearby_venues.columns = [col.split(".")[-1] for col in nearby_venues.columns]

nearby_venues.head()


# In[34]:


print('{} venues were returned by Foursquare.'.format(nearby_venues.shape[0]))


# In[35]:


def getNearbyVenues(names, latitudes, longitudes, radius=500):
    
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
            
        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']
        
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood', 
                  'Neighborhood Latitude', 
                  'Neighborhood Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    
    return(nearby_venues)


# In[37]:


Toronto_venues = getNearbyVenues(names=neighborhoods['Neighbourhood'],
                                   latitudes=neighborhoods['Latitude'],
                                   longitudes=neighborhoods['Longitude']
                                  )




# In[39]:


print(Toronto_venues.shape)
Toronto_venues.head()


# In[40]:


Toronto_venues.groupby('Neighborhood').count()


# In[41]:


print('There are {} uniques categories.'.format(len(Toronto_venues['Venue Category'].unique())))


# In[43]:


#Analise each neighborhood

# one hot encoding
Toronto_onehot = pd.get_dummies(Toronto_venues[['Venue Category']], prefix="", prefix_sep="")

# add neighborhood column back to dataframe
Toronto_onehot['Neighborhood'] = Toronto_venues['Neighborhood'] 

# move neighborhood column to the first column
fixed_columns = [Toronto_onehot.columns[-1]] + list(Toronto_onehot.columns[:-1])
Toronto_onehot = Toronto_onehot[fixed_columns]

Toronto_onehot.head()


# In[45]:


#Group by neighborhood and see the frequency

Toronto_grouped = Toronto_onehot.groupby('Neighborhood').mean().reset_index()
Toronto_grouped


# In[51]:




def return_most_common_venues(row, num_top_venues):
    row_categories = row.iloc[1:]
    row_categories_sorted = row_categories.sort_values(ascending=False)
    
    return row_categories_sorted.index.values[0:num_top_venues]


# In[52]:


#10 most common venues per neghborhood

num_top_venues = 10

indicators = ['st', 'nd', 'rd']

# create columns according to number of top venues
columns = ['Neighborhood']
for ind in np.arange(num_top_venues):
    try:
        columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
    except:
        columns.append('{}th Most Common Venue'.format(ind+1))

# create a new dataframe
neighborhoods_venues_sorted = pd.DataFrame(columns=columns)
neighborhoods_venues_sorted['Neighborhood'] = Toronto_grouped['Neighborhood']

for ind in np.arange(Toronto_grouped.shape[0]):
    neighborhoods_venues_sorted.iloc[ind, 1:] = return_most_common_venues(Toronto_grouped.iloc[ind, :], num_top_venues)

neighborhoods_venues_sorted.head()


# Now clusters by K-Means

# In[53]:


#Cluster with k-means

# set number of clusters
kclusters = 5

Toronto_grouped_clustering = Toronto_grouped.drop('Neighborhood', 1)

# run k-means clustering
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(Toronto_grouped_clustering)

# check cluster labels generated for each row in the dataframe
kmeans.labels_[0:10] 


# In[58]:


#Data frame with venues
# add clustering labels
#neighborhoods_venues_sorted.insert(0, 'Cluster Labels', kmeans.labels_)

Toronto_merged = neighborhoods

# merge toronto_grouped with toronto_data to add latitude/longitude for each neighborhood
Toronto_merged = Toronto_merged.join(neighborhoods_venues_sorted.set_index('Neighborhood'), on='Neighbourhood')

Toronto_merged.head() # check the last columns!


# In[59]:


#Visualize the clusters

# create map
map_clusters = folium.Map(location=[TorLat, TorLon], zoom_start=11)

# set color scheme for the clusters
x = np.arange(kclusters)
ys = [i + x + (i*x)**2 for i in range(kclusters)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# add markers to the map
markers_colors = []
for lat, lon, poi, cluster in zip(Toronto_merged['Latitude'], Toronto_merged['Longitude'], Toronto_merged['Neighbourhood'], Toronto_merged['Cluster Labels']):
    label = folium.Popup(str(poi) + ' Cluster ' + str(cluster), parse_html=True)
    folium.CircleMarker(
        [lat, lon],
        radius=5,
        popup=label,
        color=rainbow[cluster-1],
        fill=True,
        fill_color=rainbow[cluster-1],
        fill_opacity=0.7).add_to(map_clusters)
       
map_clusters


# In[60]:


#Examine each cluster

Toronto_merged.loc[Toronto_merged['Cluster Labels'] == 0, Toronto_merged.columns[[1] + list(range(5, Toronto_merged.shape[1]))]]


# This cluster seems to be focused on convenience and grocery stores

# In[61]:


Toronto_merged.loc[Toronto_merged['Cluster Labels'] == 1, Toronto_merged.columns[[1] + list(range(5, Toronto_merged.shape[1]))]]


# The above cluster seems to have restaurants, pharmacies and parks.

# In[62]:


Toronto_merged.loc[Toronto_merged['Cluster Labels'] == 2, Toronto_merged.columns[[1] + list(range(5, Toronto_merged.shape[1]))]]


# The above segment is more focused on sports, fields, gyms, yoga and parks.

# In[63]:


Toronto_merged.loc[Toronto_merged['Cluster Labels'] == 3, Toronto_merged.columns[[1] + list(range(5, Toronto_merged.shape[1]))]]


# The above segment is strong in cafes

# In[64]:


Toronto_merged.loc[Toronto_merged['Cluster Labels'] == 4, Toronto_merged.columns[[1] + list(range(5, Toronto_merged.shape[1]))]]


# This segment is mainly art, yoga and exhibits

# The End
