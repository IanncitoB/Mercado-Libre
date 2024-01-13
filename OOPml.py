import requests                 #Navegación
import lxml.html as html        #Para que reconozca los '//ol,li,div,p,span,etc...'
import os                       #Carpetas
import datetime                 #Fecha para la carpeta
import csv                      #Data
import json                     #Data


class HomeScrapper:
    def __init__(self, toSearch, pags_MAX):
        last_XPATH = max([file for file in os.listdir('./XPATH') if file.endswith('.json')])
        print(f'Using {last_XPATH} as XPATH')
        self.XPATHS = json.load(open(f'./XPATH/{last_XPATH}', 'r'))

        BASE_URL = self.XPATHS['HOME_URL']
        suffix = self.get_suffix(toSearch)
        self.home_url = f'{BASE_URL}{suffix}'
        self.pags_MAX = pags_MAX
        self.toSearch = toSearch

        self.index_XPATHS = {
            'LinksArticulos': 0,
            'LinkSiguiente': 0,
            'TotalPages': 0,
            'Ventas': 0,
            'Nombre': 0,
            'Disponibles': 0,
            'PrecioReal': 0,
            'Moneda': 0,
            'Descuento': 0,
            'LinksImagenes': 0,
            'LinkOpinion': 0,
            'Estrellas': 0,
            'Calificaciones': 0,
            'Porcentajes': 0,
            'Comentarios': 0,
        }

        self.fileManager = FileManager(toSearch)
        self.logManager = LogManager(self.fileManager.folder, self.fileManager.time_start, self.home_url)
        self.dataManager = dataManager(self.fileManager.folder, self.fileManager.time_start)
    
#-------- PARSERS -------
    def parse_page(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                home = response.content.decode('utf-8')
                parsed = html.fromstring(home)
                return parsed
            else:
                raise ValueError(3, f'Error: {response.status_code}\n└─▶\tLink: {url}')
        except ValueError as ve:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            num, msg = ve.args
            self.logManager.write_log(f'{time}\t{msg}')
            print(f'[DEBUG][parse_page] {time}\t{msg}')
            return None
    
    def parse_article(self, link):
        try:
            response = requests.get(link)
            if response.status_code == 200:
                article = response.content.decode('utf-8')
                parsed = html.fromstring(article)
                return parsed
            else:
                raise ValueError(3, f'Error: {response.status_code}\n└─▶\tLink: {link}')
        except ValueError as ve:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            num, msg = ve.args
            self.logManager.write_log(f'{time}\t{msg}')
            print(f'[DEBUG][parse_article] {time}\t{msg}')
            return None
    
#-------- GETTERS --------
    def get_suffix(self, toSearch):
        palabras = toSearch.split(' ')
        res = f'/{palabras[0]}'
        palabras.pop(0)
        for pal in palabras:
            res = f'{res}-{pal}'
        res = f'{res}#D[A:'
        palabras = toSearch.split(' ')
        res = f'{res}{palabras[0]}'
        palabras.pop(0)
        for pal in palabras:
            res = f'{res}%20{pal}'
        res = f'{res}]'
        return res
    
    def get_links(self, parsed, url):
        try:
            links = parsed.xpath(self.XPATHS['LinksArticulos'][self.index_XPATHS['LinksArticulos']])
            if len(links) == 0:
                raise ValueError(1, f'Error 1: No se encontraron links en {url}')
            return links
        except IndexError:
            raise ValueError(2, f'No hay más XPATHS para LinksArticulos')
        except ValueError as ve:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            num, msg = ve.args
            if num == 1:
                self.index_XPATHS['LinksArticulos'] += 1
                return self.get_links(parsed, url)   # Vuelvo a intentar con el nuevo XPATH
            self.logManager.write_log(f'{time}\t{msg}')
            print(f'[DEBUG][get_links] {time}\t{msg}')
            return None
    
    def next_page(self, parsed, url):
        try:
            link = parsed.xpath(self.XPATHS['LinkSiguiente'][self.index_XPATHS['LinkSiguiente']])
            if len(link) == 0:
                raise ValueError(1, f'Error 1: No se encontró link a la siguiente página en {url}')
            return link[0]
        except IndexError:
            raise ValueError(2, f'No hay más XPATHS para LinkSiguiente')
        except ValueError as ve:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            num, msg = ve.args
            if num == 1:
                self.index_XPATHS['LinkSiguiente'] += 1
                return self.next_page(parsed)  # Vuelvo a intentar con el nuevo XPATH
            self.logManager.write_log(f'{time}\t{msg}')
            print(f'[DEBUG][next_page] {time}\t{msg}')
            return None
    
    def get_total_pages(self, parsed, url):
        try:
            pages = parsed.xpath(self.XPATHS['TotalPages'][self.index_XPATHS['TotalPages']])
            if len(pages) == 0:
                raise ValueError(1, f'Error 1: No se encontró el total de páginas en {url}')
            return int(pages[1]) # WARNING: Puede darte index error si cambia el formato de la página
        except IndexError:
            raise ValueError(2, f'No hay más XPATHS para TotalPages')
        except ValueError as ve:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            num, msg = ve.args
            if num == 1:
                self.index_XPATHS['TotalPages'] += 1
                return self.get_total_pages(parsed)
    
    def get_article_data(self, parsed, url):
        try:
            try:
                nombre = parsed.xpath(self.XPATHS['Nombre'][self.index_XPATHS['Nombre']])[0]
                ventas = parsed.xpath(self.XPATHS['Ventas'][self.index_XPATHS['Ventas']])
                disponibles = parsed.xpath(self.XPATHS['Disponibles'][self.index_XPATHS['Disponibles']])
                precioReal = parsed.xpath(self.XPATHS['PrecioReal'][self.index_XPATHS['PrecioReal']])
                moneda = parsed.xpath(self.XPATHS['Moneda'][self.index_XPATHS['Moneda']])
                descuento = parsed.xpath(self.XPATHS['Descuento'][self.index_XPATHS['Descuento']])
                linksImagenes = parsed.xpath(self.XPATHS['LinksImagenes'][self.index_XPATHS['LinksImagenes']])
                linkOpinion = parsed.xpath(self.XPATHS['LinkOpinion'][self.index_XPATHS['LinkOpinion']])
                if linkOpinion:
                    linkOpinion = f'https://articulo.mercadolibre.com.ar{linkOpinion[0]}'#Si tiene opiniones, se queda con el único link
                else:
                    linkOpinion = ''
                if len(descuento) != 0:     #tiene dto
                    descuento = int((descuento[0].split('%'))[0])
                    precioFinal = int(precioReal[1].replace('.', ''))
                    precioReal = int(precioReal[0].replace('.', ''))
                else:
                    precioFinal = int(precioReal[0].replace('.', ''))
                    precioReal = precioFinal
                line = [nombre, ventas, disponibles, precioReal, descuento, precioFinal, moneda, linksImagenes, linkOpinion, url]
                if line:
                    self.logManager.write_log(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} \tDatos obtenidos de {url}')
                return line
            except IndexError:
                raise ValueError(1, f'Error 1: No se encontró algún dato en {url}')
        except ValueError as ve:
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            num, msg = ve.args
            # TODO: fijarse cual dato produjo error y sumarle 1 al index_XPATHS correspondiente
            self.logManager.write_log(f'{time}\t{msg}')
            print(f'[DEBUG][get_article_data] {time}\t{msg}')
            return None

# ------- WRITERS --------
    def write_data(self, line):
        self.dataManager.write_line(line)
    
class FileManager:
    def __init__(self, toSearch):
        if not os.path.isdir('./SCRAPES'):
            os.mkdir('./SCRAPES')
        if not os.path.isdir(f'./SCRAPES/{toSearch}'):
            os.mkdir(f'./SCRAPES/{toSearch}')
        self.today = datetime.date.today().strftime('%Y-%m-%d')
        if not os.path.isdir(f'./SCRAPES/{toSearch}/{self.today}'):
            os.mkdir(f'./SCRAPES/{toSearch}/{self.today}')
        self.time_start = datetime.datetime.now().strftime('%H-%M')

        self.folder = f'./SCRAPES/{toSearch}/{self.today}'


class LogManager:
    def __init__(self, folder, time_start, home_url):
        self.folder = folder
        self.home_url = home_url
        self.log_file = f'{self.folder}/{time_start}_log.txt'
        self.log = open(self.log_file, 'w', encoding='utf-8')
        self.log.write(f'Inicio del log: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        self.log.write(f'URL: {self.home_url}\n')
        self.log.write(f'Folder: {self.folder}\n')
        self.log.write('-----------------------------------------\n')
        self.log.close()
    
    def write_log(self, text):
        with open(self.log_file, 'a', encoding='utf-8') as log:
            log.write(f'{text}\n')

class dataManager:
    def __init__(self, folder, time_start):
        self.folder = folder
        self.time_start = time_start
        self.data_file = f'{self.folder}/{self.time_start}_data.csv'
        self.fieldNames = ['Nombre', 'Ventas', 'Disponibles', 'PrecioReal', 'Descuento', 'PrecioFinal', 'Moneda', 'LinksImagenes', 'LinkOpinion', 'LinkArticulo']
        self.file = open(self.data_file, 'w', encoding='utf-8')
        self.csv_writer = csv.writer(self.file)
        self.csv_writer.writerow(self.fieldNames)
    
    def __del__(self):
        self.file.close()
    
    def write_line(self, line):
        self.csv_writer.writerow(line)

# ------------------------------------------ MAIN -------------------------------------------------

if __name__ == '__main__':
    toSearch = input('Ingrese lo que desea buscar: ')
    pags_MAX = int(input('Ingrese la cantidad de páginas a buscar (-1 para todas): '))
    if pags_MAX == -1:
        pags_MAX = 999_999_999
    homeScrapper = HomeScrapper(toSearch, pags_MAX)
    page_url = homeScrapper.home_url
    parsed = homeScrapper.parse_page(page_url)

    pages_to_scrap = homeScrapper.get_total_pages(parsed, page_url)
    pages_to_scrap = min(pages_to_scrap, pags_MAX)
    print(f'[DEBUG][main] Páginas a scrapear: {pages_to_scrap}')

    for i in range(pages_to_scrap):
        print(f'[DEBUG][main] Página {i+1}:')
        homeScrapper.logManager.write_log(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} \tPágina {i+1}:')
        links = homeScrapper.get_links(parsed, page_url)
        for link in links:
            parsed_article = homeScrapper.parse_article(link)
            line = homeScrapper.get_article_data(parsed_article, link)
            if line:
                homeScrapper.write_data(line)
        page_url = homeScrapper.next_page(parsed, page_url)
        parsed = homeScrapper.parse_page(page_url)
    
    print('[DEBUG][main] Scrapeo finalizado')
    HomeScrapper.logManager.write_log(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} \tFinalizado')
    
