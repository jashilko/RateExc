from ftplib import FTP
from io import StringIO
from bs4 import BeautifulSoup


path = '/www/mosexibank.ru/rateExc.txt'

ftp = FTP("31.31.196.33") 
ftp.login("u2458235", "aGeKIqt7") 
r = StringIO()
ftp.retrlines("RETR " + path, r.write)
ftp.quit()

doc = r.getvalue()
soup = BeautifulSoup(doc, 'html.parser')
res = soup.find_all("td", align="center")
print(res[2].string)
print(res[3].string)
print(res[4].string)
print(res[5].string)

