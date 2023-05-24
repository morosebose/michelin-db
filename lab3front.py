'''
CIS 41B Spring 2023
Surajit A Bose
Lab 3 front end
'''

import sqlite3
import tkinter as tk                      
import tkinter.messagebox as tkmb
import webbrowser
from os.path import exists

class DisplayWindow(tk.Toplevel) :
    '''
    OOP implementation of the tk.Toplevel class. 
    - Master is MainWindow
    - Display restaurant data
    - Display clickable URL for restaurant
    '''
    def __init__(self, master, rest_tup):
        '''
        Create and display the window of restaurant info
        
        @param master the MainWindow object calling this constructor
        @param rest_tup the tuple of restaurant data. Tuple values are in order:
            - name
            - address
            - cuisine
            - cost
            - url
            
        @return None
        '''
        super().__init__(master)
        self.transient(master)
        frame = tk.Frame(self)
        for i in range (4):
            # must use double quotes as some restaurant names have apostrophe
            # TODO: Remove zip and country from address before displaying
            lab = tk.Label(frame, text = f"{rest_tup[i]}", font =('Helvetica', 14))
            # Displaying four labels, labels 0 and 3 in blue, middle two in default color
            if i % 3 == 0 :
                lab.config(fg = 'blue')
            lab.grid()
        frame.grid(padx = 20, pady = 20)
        tk.Button(self, text = 'Restaurant Website', command = lambda : self.opensite(rest_tup[-1])).grid(padx = 5, pady = 10)
    
    def opensite(self, url) :
        webbrowser.open(url)
  

class DialogWindow(tk.Toplevel) :
    '''
    OOP implementation of the tk.Toplevel class. 
    - Master is MainWindow
    - Open a dialog window prompting for user choice
    - Return user choice to main window
    '''
    def __init__(self, master, desired, datab, elems = None) : 
        '''
        Create and display listbox to get user's choice
        of city, cuisine, or restaurant
        
        @param master the MainWindow object calling this constructor
        @param desired the field from the table(must be city, cuisine, or name)
        @param datab the database table (must be Cities, Cuisines, or Restaurants)
        @parem elems the list of restaurants meeting criterion of city or cuisine
        
        @return None
        '''
        super().__init__(master)
        self.grab_set()
        self.focus_set()
        self.transient(master)
        if elems : 
            self.elems = elems
        else :
            self.elems = []
        self.choice = None
        self.protocol('WM_DELETE_WINDOW', self.no_val)
        tk.Label(self, text = f'Click on a {desired} to select',  font = ('Helvetica', 16), padx = 10, pady = 10).grid()
        frame = tk.Frame(self)
        sb = tk.Scrollbar(frame, orient = 'vertical')
        lb = tk.Listbox(frame, height = 6, yscrollcommand = sb.set)
        sb.config(command = lb.yview)
        lb.grid(row = 0, column = 0)
        sb.grid(row = 0, column = 1, sticky = 'NS')
        frame.grid(row = 1, column = 0, padx = 10, pady = 10)
        if self.elems: 
            lb.config(selectmode = 'multiple')
        else: 
            master.cur.execute(f'SELECT {desired} FROM {datab}') 
            for elem in master.cur.fetchall() :
                self.elems.append(elem[0])
        for elem in self.elems :
            lb.insert(tk.END, elem)
        tk.Button(self, text = 'Click to select', command = lambda : self.setChoiceAndClose(lb.curselection())).grid(padx = 5, pady = 10)
        
    def setChoiceAndClose(self, indices) :
        chosen = []
        for ind in indices :
            chosen.append(self.elems[ind])
        self.choice = chosen
        self.destroy()
        
    @property
    def chose(self):
        return self.choice
    
    def no_val(self) :
        '''
        If user closes dialog window without making a selection:
        - Set user choice to None
        - Close dialog window
        '''
        self.choice = None
        self.destroy()
        

class MainWindow(tk.Tk) :
    '''
    OOP implementation of tk.Tk class. 
    - Create root window for application
    - Spawn other windows as needed to display data or get user choice
    '''
    
    DEFAULT = 'restaurants.db'
    
    def __init__(self) :   
        'Instantiate MainWindow object with all necessary widgets'
        super().__init__()
        
        # check for existence of database
        # TODO: this only checks that file exists, not that it is valid DB
        # Note: Could put the whole method in try/except for sqlite3Error
        # But that creates a database, opens a window, then fails when user
        # clicks on a button. That is bad UX
        # Better UX to be non pythonic and use if clause
        #TODO: Figure out pythonic way with good UX, e.g., using uri?
        okay = exists(MainWindow.DEFAULT) 
        if not okay :
            tkmb.showerror(f'Cannot open {MainWindow.DEFAULT}', parent = self)
            raise SystemExit

        self.conn = sqlite3.connect(MainWindow.DEFAULT)
        self.curr = self.conn.cursor()
        self.protocol('WM_DELETE_WINDOW', self.closeout)
        self.title('Restaurants')
        
        fr = tk.Frame(self, padx = 20, pady = 20)
        fr.grid()
        
        tk.Label(fr, text = 'Local Michelin Guide Restaurants', fg = 'blue', font =('Helvetica', 20, 'bold'), padx = 20, pady = 20 ).grid(row = 0, column = 1, columnspan = 3)
        tk.Button(fr, text = 'Search by City', font = ('Helvetica', 20, 'bold'), bg = 'gray', fg = 'black', command = lambda : self.getInitialChoice('city')).grid(row = 3, column = 0, columnspan = 2)
        tk.Button(fr, text = 'Search by Cuisine', font = ('Helvetica', 20, 'bold'), bg = 'gray', fg = 'black', command = lambda : self.getInitialChoice('cuisine')).grid(row = 3, column = 2, columnspan = 2)

    def getInitialChoice(self, desired) :
        '''
        Get user's choice of either city or cuisine to list restaurants
        Use user's choice to generate list of appropriate restaurants
        Pass list on to method to get user's choice of restaurants
        '''
        # TODO: Sort lists to be displayed alphabetically
        datab, field = ('Cities', 'loc') if desired == 'city' else ('Cuisines', 'kind')
        dialog = DialogWindow(self, desired, datab)
        self.wait_window(dialog)
        choice = dialog.chose
        if choice:  
            rest_list = []
            self.curr.execute(f'''SELECT name FROM Restaurants JOIN {datab} 
                              ON Restaurants.{field} = {datab}.id
                              AND {datab}.{desired} = '{choice[0]}'
                              ''')
            for record in self.curr.fetchall() :
                rest_list.append(record[0])
            self.getRestaurantChoice('name', 'Restaurants', rest_list)
            
    def getRestaurantChoice(self, desired, datab, rest_list) :
        '''
        Get user's choice of restaurants from those that match criterion of cuisine or city
        Pass user's choice on to the method to display card with restaurant deets
        
        @param desired the field from the table(must be name)
        @param datab the database table (must be Restaurants)
        @parem elems the list of restaurants meeting criterion of city or cuisine
        
        @return None
        '''
        dialog = DialogWindow(self, desired, datab, rest_list)
        self.wait_window(dialog)
        rest_list = dialog.chose
        if rest_list :
            self.displayRestCard(rest_list)
    
    def displayRestCard(self, rest_list) :
        '''
        Display all the details of each restaurant chosen by the user
        
        @param rest_list list of restaurants chosen by user
        
        @return None
        '''
        for rest in rest_list:
            # Use double quotes around variable because 
            # some restaurant names have apostrophe
            self.curr.execute(f'''SELECT Restaurants.name, Restaurants.addr, 
                        Cuisines.cuisine, Costs.cost,
                        Restaurants.url
                        FROM Restaurants JOIN Cuisines JOIN Costs
                        ON Cuisines.id = Restaurants.kind 
                        AND Costs.id = Restaurants.cost
                        AND Restaurants.name = "{rest}"
                        ''')
            DisplayWindow(self, self.curr.fetchone())
    
    @property
    def cur (self) :
        return self.curr
    
    def closeout(self) :
        '''
        Ask for user confirmation before closing main window.
        - If user confirms, close database and quit gracefully
        - If user cancels, do nothing
        '''        
        close = tkmb.askokcancel('Confirm close', 'Close all windows and quit?', parent=self)
        if close: 
            self.conn.close()
            self.destroy()
            self.quit()
            
        
if __name__ == '__main__' :
    MainWindow().mainloop()
    
