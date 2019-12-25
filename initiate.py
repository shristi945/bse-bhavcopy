import os
import cherrypy
from jinja2 import Environment, FileSystemLoader
import io
import requests
import csv
from bs4 import BeautifulSoup
import zipfile
from processing.connection import Connection

env = Environment(loader=FileSystemLoader('templates'))

maps = {
    "SC_CODE" : "code",
    "SC_NAME": "name",
    "OPEN": "open",
    "HIGH": "high",
    "LOW" : "low",
    "CLOSE" : "close"
}

r = Connection().conn

class Index(object):
    @cherrypy.expose
    def index(self):
        tmpl = env.get_template('index.html')
        return tmpl.render(site_title = 'BhavCopy.com', data =self.driver_fun ())
    
    @cherrypy.expose
    def get_data(self, name=None):
        data1 =self.get_data_from_db(name)
        if name:
            html1 ='''
            <html>  
                <head>
                    <style>
                        input[type=text] {{
                        width: 60%;
                        padding: 12px 20px;
                        margin: 8px 0;
                        box-sizing: border-box;
                        }}
                        input[type=submit]{{
                        background-color: #009879;
                        border: none;
                        color: white;
                        padding: 16px 32px;
                        text-decoration: none;
                        margin: 4px 2px;
                        cursor: pointer;
                        }}
                    </style>
                    <link href = 'static/css/style.css' rel = 'stylesheet' media="screen,projection" type="text/css">
                </head>
                <body>
                    <div align = 'center' style="background-color:#009879">
                        <h3 style='color:white'>BhavCopy</h3>
                    </div>
                    <form method = 'GET' action = 'index'>
                        <div align = "center">
                            <p><h4>Details of <b>{0}</b> are in below table:</h4><p>
                            <table class="content-table">
                                <thead>
                                    <th>Name</th>
                                    <th>Open</th>
                                    <th>High</th>
                                    <th>Low</th>
                                    <th>Close</th>
                                </thead>
                            <tbody>'''.format(data1[0])       
            html4 = ""
            for data in data1:
                html2 = "<tr>"
                html4 = html4 + "<td>{0}</td>".format(data)
                html5 = "</tr>"
            
            html2 = html2+html4+html5        
                       
                                   
            html3 = \
                    '''
                    </tbody>
                        </table>
                    </div>
                    <div align = "center">
                        <a href="./">Back</a>
                    </div>
                </form>
            </body>
        </html>
                    
                    '''
                            
            return html1+html2+html3
        
    
    def get_csv_url(self):
        url = "https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx"
        csv_url = ""

        response = requests.request("GET", url=url)
        print(response)
        # print(response.text)

        soup = BeautifulSoup(response.text, features="html.parser")
        for a in soup.find_all("a", href=True):
            try:
                if a["id"] == "ContentPlaceHolder1_btnhylZip":
                    print(a["href"])
                    csv_url = a["href"]
            except:
                continue
        return csv_url
    
    def insert_data_to_db(self, csv_url):
        response = requests.request("GET", url=csv_url)
        with io.BytesIO(response.content) as zip_file:
            with zipfile.ZipFile(zip_file) as zip_file:
                # Get first file in the archive
                for zip_info in zip_file.infolist():
                    # Open file
                    with zip_file.open(zip_info) as file:
                        # Load CSV file, decode binary to text
                        with io.TextIOWrapper(file) as text:

                            reader = csv.DictReader(text)
                            score = 1
                            for row in reader:
                                r.zincrby( "code",score,row["SC_CODE"])
                                r.zincrby( "name",score,row["SC_NAME"])
                                r.zincrby( "open", score, row["OPEN"] )
                                r.zincrby( "high", score,row["HIGH"])
                                r.zincrby( "low",score,row["LOW"])
                                r.zincrby( "close",score,row["CLOSE"])

                                score += 1    
                            count = 1
                            data = {}
                            code = r.zrange("code", 0, 9)
                            name = r.zrange("name", 0, 9)
                            open_ = r.zrange("open", 0, 9)
                            high = r.zrange("high", 0, 9)
                            low = r.zrange("low", 0, 9)
                            close = r.zrange("close", 0, 9)
                            data = {'code':code, 'name': name, 'open':open_, 'high':high, 'low':low, 'close':close}

                            return data
                            
    def get_data_from_db(self, name):
        
        if name:
            name_list = r.zrange("name", 0, -1)
            count = 0
            for names in name_list:
                count +=1
                if name.upper().strip() == names.decode("utf-8").strip():
                    break

            name = r.zrange("name", 0, count-1)
            open_ = r.zrange("open", 0, count-1)
            high = r.zrange("high", 0, count-1)
            low = r.zrange("low", 0, count-1)
            close = r.zrange("close", 0, count-1)

            name = name[-1].decode("utf-8")
            open_ = open_[-1].decode("utf-8")
            high = high[-1].decode("utf-8")
            low = low[-1].decode("utf-8")
            close = close[-1].decode("utf-8")

            data1 = [name, open_, high, low, close]

            return data1

    def driver_fun (self):
        csv_url = self.get_csv_url()
        if csv_url:
            return self.insert_data_to_db(csv_url)
        else:
            return "file not on website"
            
            
if __name__ == '__main__':
    
    config = {
        
        '/static': {
            'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__)),
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        }
    }
    # RUN
    cherrypy.quickstart(Index(), '/', config=config)

    
    
