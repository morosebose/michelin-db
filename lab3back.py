'''
CIS 41B Spring 2023
Surajit A Bose
Lab 3 back end
'''

import requests
from bs4 import BeautifulSoup as bs
import json
import sqlite3

class Restaurants():
    '''
    Restaurants instance has one attribute, rest_dict
    rest_dict is a dictionary of dictionaries
        - Key : Restaurant Name
        - Value : A dictionary of restaurant data. Key, value pairs are
            - Website : URL of restaurant
            - City : Where restaurant is located
            - Price : Range from $ to $$$$$
            - Cuisine : Whether Mexican, French, etc.
            - Address : Street address of restaurant
    
    Restaurants has two class attributes:
        - ROOT_URL, root website that has subpages with restaurant data
        - FIRST, the first subpage to crawl for this data
    '''
    # TODO: Get the city part of the FIRST as an argument rather than hardcoding
    # TODO: Rewrite without OOP, use functions rather than methods
    
    ROOT_URL = 'https://guide.michelin.com'
    FIRST = '/us/en/california/cupertino/restaurants'
    
    def __init__(self) :
        '''Crawl the webpages and create the restaurants dictionary'''
        self.rest_dict = {}
        to_crawl = [Restaurants.FIRST]
        crawled = set()

        while to_crawl :
            elem = to_crawl.pop()
            crawled.add(elem)
            full_elem = Restaurants.ROOT_URL + elem
            page = requests.get(full_elem)
            soup = bs(page.content, 'lxml')
            pagination = soup.select('ul.pagination a')
            for link in pagination :
                if link['href'] not in crawled :
                    to_crawl.append((link['href']))
            main_section = 'section.section-main.search-results.search-listing-result'
            name_url = soup.select(f'{main_section} h3.card__menu-content--title.pl-text.pl-big a')
            loc = soup.select(f'{main_section} .card__menu-footer--location.flex-fill.pl-text')
            price_cuisine = soup.select(f'{main_section} .card__menu-footer--price.pl-text')
            
            for i in range(len(name_url)) :
                rest = name_url[i].text.strip()
                self.rest_dict[rest] = {}
                self.rest_dict[rest]['Website'] = Restaurants.ROOT_URL + name_url[i]['href']
                self.rest_dict[rest]['City'] = loc[i].text.strip()[: -5]
                pc = price_cuisine[i].text.split('·')
                self.rest_dict[rest]['Price'] = pc[0].strip()
                self.rest_dict[rest]['Cuisine'] = pc[1].strip()
                self.rest_dict[rest]['Address'] = self.getAddress(self.rest_dict[rest]['Website'])
                             
    def getAddress(self, url) :
        '''
        Helper function to extract the address of a restaurant from its url
        
        @param url website of restaurant
        @return address of restaurant
        '''
        page = requests.get(url)
        soup = bs(page.content, 'lxml')
        address = soup.find('li', class_ = 'restaurant-details__heading--address' )
        return address.text
  
    @property
    def data(self) :
        return self.rest_dict
    
    def write_data(self) :
        '''Write out data to JSON file'''
        with open ('rest_data.json', 'w') as fh :
            json.dump(self.data, fh, indent = 4)
            

class RestaurantsDB() :
    '''
    RestaurantsDB instance has one attribute, a database of restaurant info.
    The database has four tables:
        - Cities, for the cities where the restaurants are located
        - Costs, from $ to $$$$ for price range of a given restaurant
        - Cuisines, whether Ethiopian, Mexican, Indian, etc
        - Restaurants, all the restaurants with their name, url, address, etc
        
    RestaurantsDB has one class attribute, DEFAULT for the JSON file 
    from which the data is read in and the database created
    '''
    
    DEFAULT = 'rest_data.json'
    
    def __init__(self, file = DEFAULT) :
        '''Create a database from the JSON file of restaurants data'''
        
        # Create database connection
        conn = sqlite3.connect('restaurants.db')
        cur = conn.cursor()
        
        # Create Cities table
        cur.execute('DROP TABLE IF EXISTS Cities')
        cur.execute('''CREATE TABLE Cities(
            id INTEGER NOT NULL PRIMARY KEY UNIQUE,
            city TEXT UNIQUE ON CONFLICT IGNORE)''')
        
        # Create Costs table
        cur.execute('DROP TABLE IF EXISTS Costs')
        cur.execute('''CREATE TABLE Costs(
            id INTEGER NOT NULL PRIMARY KEY ON CONFLICT IGNORE,
            cost TEXT)''')
        
        # Create Cuisines table
        cur.execute('DROP TABLE IF EXISTS Cuisines')
        cur.execute('''CREATE TABLE Cuisines(
            id INTEGER NOT NULL PRIMARY KEY UNIQUE,
            cuisine TEXT UNIQUE ON CONFLICT IGNORE)''')
        
        # Create Restaurants table
        cur.execute('DROP TABLE IF EXISTS Restaurants')
        cur.execute('''CREATE TABLE Restaurants(
            id INTEGER NOT NULL PRIMARY KEY UNIQUE,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE ON CONFLICT IGNORE,
            loc INTEGER,
            cost INTEGER,
            kind INTEGER,
            addr TEXT UNIQUE ON CONFLICT IGNORE)''')
            
        
        # Read in JSON file of restaurant data
        with open(file, 'r') as infile :
            data = json.load(infile)
            
            for name, val in data.items() :
                # Update Cities table
                cur.execute('INSERT INTO Cities (city) VALUES (?)', (val['City'],))
                cur.execute('SELECT id FROM Cities WHERE city = ?', (val['City'],))
                city_id = cur.fetchone()[0]
                
                # Update Costs table
                cur.execute('INSERT INTO Costs (id, cost) VALUES (?, ?)', (len(val['Price']), val['Price']))
                cur.execute('SELECT id FROM Costs WHERE cost = ?', (val['Price'],))
                costs_id = cur.fetchone()[0]

                # Update Cuisines table
                cur.execute('INSERT INTO Cuisines (cuisine) VALUES (?)', (val['Cuisine'],))
                cur.execute('SELECT id FROM Cuisines WHERE cuisine = ?', (val['Cuisine'],))
                cuisine_id = cur.fetchone()[0]
                
                # Update Restaurants table
                cur.execute('''INSERT INTO Restaurants 
                        (name, url, loc, cost, kind, addr)
                        VALUES (?, ?, ?, ?, ?, ?)''', (name, val['Website'], city_id, costs_id, cuisine_id, val['Address']))
                
        conn.commit()
        conn.close()
        self.dbase = 'restaurants.db'
          
    @property
    def db(self) :
        return self.dbase
                
                
if __name__ == '__main__' :
 
    # Scrape data
    restaurants = Restaurants()
    
    # Check that web scraping works
    for k, v in restaurants.data.items() :
        print('Name:', k)
        for k2, v2 in v.items():
            print(k2 + ': ' +  v2)
        print()
    
    # Write out JSON file
    restaurants.write_data()  
    
    # Check that writing to json works
    with open('rest_data.json', 'r') as fh :
        my_data = json.load(fh)     
        i = 1
        for k, v in my_data.items():
            print('Record', i)
            print('Name: ', k)
            for k2, v2 in v.items() :
                print(k2 + ': ' + v2)
            print()
            i += 1
            
    # Create database. Check for database consists in running lab3front.
    my_db = RestaurantsDB().db
    