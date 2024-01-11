import requests                 #Navegación
import lxml.html as html        #Para que reconozca los '//ol,li,div,p,span,etc...'
import os                       #Carpetas
import datetime                 #Fecha para la carpeta
import csv                      #Data
import json                     #Data

today = datetime.date.today().strftime('%Y-%m-%d')

# Obtengo de ./XPATH el útlimo modificado (Para no tener que estar cambiando el código cada vez que se modifica el XPATH)

list_XPATHS = []
for file in os.listdir('./XPATH'):
    if file.endswith('.json'):
        list_XPATHS.append(file)
list_XPATHS.sort()

XPATHS = json.load(open(f'./XPATH/{list_XPATHS[-1]}', 'r'))
print(f'XPATHS: ./XPATH/{list_XPATHS[-1]}')

HOME_URL = XPATHS['HOME_URL']

# Indices de los distintos XPATHS para poder cambiarlos en caso de que no funcionen
index_XPATHS = {
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

# get_URL es una función que obtiene un link a la búsqueda a realizar. por ejemplo: "https://listado.mercadolibre.com.ar/palabra1-palabra2#D[A:palabra1%20palabra2%20]"
# es el resultado de buscar "palabra1 palabra2".
# Con los carácteres especiales como "@" hace una url que no funciona. #TODO arreglar esto con regex
def get_URL(toSearch):
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

#parse_article viene a recopilar todos los datos del artículo para devolverlos en una lista [Nombre, Ventas, Disponibles, ...]
#De tener un error (Por ej: 404 not found), devuelve None.
def parse_article(link):
    try:
        response = requests.get(link)
        if response.status_code != 200: #Hay error
            raise ValueError(f'Error: {response.status_code}\nLink: {link}')
        #else: Está todo Ok
        
        article = response.content.decode('utf-8')      #para que lea "ñ" y demás símbolos
        parsed = html.fromstring(article)

        try:
            #Obtenemos todo sobre el artículo
            nombre = parsed.xpath(XPATHS['Nombre'][index_XPATHS['Nombre']])[0]
            ventas = parsed.xpath(XPATHS['Ventas'][index_XPATHS['Ventas']])
            disponibles = parsed.xpath(XPATHS['Disponibles'][index_XPATHS['Disponibles']])
            precioReal = parsed.xpath(XPATHS['PrecioReal'][index_XPATHS['PrecioReal']])
            moneda = parsed.xpath(XPATHS['Moneda'][index_XPATHS['Moneda']])
            descuento = parsed.xpath(XPATHS['Descuento'][index_XPATHS['Descuento']])
            linksImagenes = parsed.xpath(XPATHS['LinksImagenes'][index_XPATHS['LinksImagenes']])
            linkOpinion = parsed.xpath(XPATHS['LinkOpinion'][index_XPATHS['LinkOpinion']])
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
            
            #print(f'[DEBUG] {nombre}\n{ventas}\n{disponibles}\n{precioReal}\n{descuento}\n{precioFinal}\n{linksImagenes}\n{linkOpinion}')

            line = [nombre, ventas, disponibles, precioReal, descuento, precioFinal, moneda, linksImagenes, linkOpinion, link]
            return line
            
        except IndexError:
            print(f'Error artículo: {link}')
            return
        
    except ValueError as ve:
        print(ve)
        return
    

def parse_home(url, pags_MAX):
    global index_XPATHS
    try:
        response = requests.get(url)
        if response.status_code != 200: #Hubo error
            raise ValueError(f'Error: {response.status_code}\n\tLink: {url}')
        home = response.content.decode('utf-8')
        parsed = html.fromstring(home)

        #Generar carpeta del producto
        if not os.path.isdir('./SCRAPES'):
            os.mkdir('./SCRAPES')
        if not os.path.isdir(f'./SCRAPES/{toSearch}'):
            os.mkdir(f'./SCRAPES/{toSearch}')
        #Generar subcarpeta con la fecha
        subcarpeta = f'./SCRAPES/{toSearch}/{today}'
        if not os.path.isdir(subcarpeta):
            os.mkdir(subcarpeta)

        #Genero <HORA ACTUAL>.csv y lo abro
        time = datetime.datetime.now().strftime('%H-%M')
        with open(f'{subcarpeta}/{time}_data.csv', 'w', encoding='utf-8') as file:
            fieldNames = ['Nombre', 'Ventas', 'Disponibles', 'Precio_Real', 'Descuento', 'Precio_Final', 'Moneda', 'Links_Imágenes', 'Link_Opinión', 'Link_Artículo']
            csv_writer = csv.writer(file)
            #Escribir encabezado
            csv_writer.writerow(fieldNames)

            pags_TOTAL = parsed.xpath(XPATHS['TotalPages'][index_XPATHS['TotalPages']])
            if pags_TOTAL:
                pags_TOTAL = int(pags_TOTAL[1])
            else:
                pags_TOTAL = 1
                print('No se encontró el total de páginas. Se examinará solo la primera página.')
            pags_TOTAL = min(pags_MAX, pags_TOTAL)
            pagina = 1
            siguientes = parsed.xpath(XPATHS['LinkSiguiente'][index_XPATHS['LinkSiguiente']])
            #Siguientes es una lista de links a las siguientes páginas. La lista puede tener 1 (hay página siguiente) o 0 elementos (no hay más siguientes)
            bad_links = []
            while(pagina <= pags_TOTAL and (pagina < pags_TOTAL or len(siguientes) == 0)):
                with open(f'{subcarpeta}/{time}_log.txt', 'a', encoding='utf-8') as log:
                    current_time = datetime.datetime.now().strftime('%H:%M:%S')
                    log.write(f'{current_time} | Página {pagina} URL: {url}\n')
                try:
                    print(f'Página: ({pagina}/{pags_TOTAL})')
                    linksArticulos = parsed.xpath(XPATHS['LinksArticulos'][index_XPATHS['LinksArticulos']])
                    print(f'Artículos encontrados: {len(linksArticulos)}')
                    if len(linksArticulos) == 0:
                        raise ValueError(1, f'Error 1: No se encontraron artículos en la página {pagina}/{pags_TOTAL}')
                    for link in linksArticulos:
                        line = parse_article(link)
                        if line is not None:
                            csv_writer.writerow(line)
                        else:
                            with open(f'{subcarpeta}/{time}_log.txt', 'a', encoding='utf-8') as log:
                                current_time = datetime.datetime.now().strftime('%H:%M:%S')
                                log.write(f'{current_time} | WARN Artículo no procesado: {link}\n')
                            bad_links.append(link)
                    #Cambio la URL para la siguiente página
                    if siguientes:
                        url = siguientes[0]
                        response = requests.get(url)
                        if response.status_code != 200: #Hubo error
                            raise ValueError(2, f'Error 2: {response.status_code}\n\tPágina: {pagina}\n\tLink: {url}')
                        home = response.content.decode('utf-8')
                        parsed = html.fromstring(home)
                    pagina += 1
                    #Re-escaneo los links a las siguientes páginas (1 o 0 elementos)
                    siguientes = parsed.xpath(XPATHS['LinkSiguiente'][index_XPATHS['LinkSiguiente']])
                
                
                except ValueError as ve:
                    numero_error = ve.args[0]
                    ve = ve.args[1]
                    with open(f'{subcarpeta}/{time}_log.txt', 'a', encoding='utf-8') as log:
                        current_time = datetime.datetime.now().strftime('%H:%M:%S')
                        log.write(f'{current_time} | {ve}\n')
                        if numero_error == 1:
                            index_XPATHS['LinksArticulos'] += 1
                            try:
                                XPATH_LinksArticulos = XPATHS['LinksArticulos'][index_XPATHS['LinksArticulos']]
                            except IndexError:
                                print(f'[DEBUG] No se encontró el XPATH de los links de los artículos. Se examinaron {index_XPATHS["LinksArticulos"]} XPATHS.')
                                log.write(f'\tNo se encontró nuevo XPATH de los links de los artículos. Se examinaron {index_XPATHS["LinksArticulos"]} XPATHS.\n')
                                break
                            print(f'[DEBUG] Se cambió el XPATH de los links de los artículos: {XPATH_LinksArticulos}')
                            log.write(f'\tSe cambió el XPATH de los links de los artículos: {XPATH_LinksArticulos}\n')
                        else:
                            break
            print(f'{len(bad_links)} total bad links: ')
            for link in bad_links:
                print(link)
    except ValueError as ve:
        print(ve)

def same_html(parsed_last, parsed):
    links_articulos_last = parsed_last.xpath(XPATHS['LinksArticulos'][index_XPATHS['LinksArticulos']])
    links_articulos_new = parsed.xpath(XPATHS['LinksArticulos'][index_XPATHS['LinksArticulos']])
    res = True
    if len(links_articulos_last) != len(links_articulos_new):
        print(f'Links Artículos Last: {len(links_articulos_last)}')
        print(f'Links Artículos New : {len(links_articulos_new)}')
        res = False
    if parsed_last.xpath(XPATHS['LinkSiguiente'][index_XPATHS['LinkSiguiente']]) != parsed.xpath(XPATHS['LinkSiguiente'][index_XPATHS['LinkSiguiente']]):
        print(f'Link Siguiente Last: {parsed_last.xpath(XPATHS["LinkSiguiente"][index_XPATHS["LinkSiguiente"]])}')
        print(f'Link Siguiente New : {parsed.xpath(XPATHS["LinkSiguiente"][index_XPATHS["LinkSiguiente"]])}')
        res = False
    if parsed_last.xpath(XPATHS['TotalPages'][index_XPATHS['TotalPages']]) != parsed.xpath(XPATHS['TotalPages'][index_XPATHS['TotalPages']]):
        print(f'Total Pages Last: {parsed_last.xpath(XPATHS["TotalPages"][index_XPATHS["TotalPages"]])}')
        print(f'Total Pages New : {parsed.xpath(XPATHS["TotalPages"][index_XPATHS["TotalPages"]])}')
        res = False
    return res


# Compara el HTML de la página actual con el último guardado en la carpeta HTML
# Si son iguales, no hace nada
# Si son distintos, crea un nuevo archivo HTML con el nuevo contenido. Devuelve si hubo cambios o no.
def compare_html(url, pags_MAX, toSearch):
    try:
        response = requests.get(url)
        if response.status_code != 200: #Hubo error
            raise ValueError(f'Error: {response.status_code}\nLink: {url}')
        home = response.content.decode('utf-8')
        parsed = html.fromstring(home)
        
        # Obtengo todas las versiones de HTML que se guardaron en la carpeta
        htmls = []
        for file in os.listdir('./HTML'):
            if file.endswith('.html') and file.startswith(f'{toSearch}_'):
                htmls.append(file)
        htmls.sort()

        total = len(htmls)
        if total == 0:
            # Creo archivo
            print(f'{toSearch}_00000 HTML created')
            with open(f'./HTML/{toSearch}_00000.html', 'w', encoding='utf-8') as file:
                file.write(home)
        else:
            # Obtengo el último archivo html
            print(f'Last found: {htmls[-1]}')
            with open(f'./HTML/{htmls[-1]}', 'r', encoding='utf-8') as file:
                last_html = file.read()
                parsed_last = html.fromstring(last_html)
                if same_html(parsed_last, parsed):
                    print(f'HTML not changed.')
                    return False
                else:
                    print(f'HTML changed. New: {toSearch}_{total:05d}')
                    # Creo archivo html siguiente
                    with open(f'./HTML/{toSearch}_{total:05d}.html', 'w', encoding='utf-8') as file:
                        file.write(home)
        return True
        
    except ValueError as ve:
        print(ve)
        exit()


if __name__ == '__main__':
    print(f'Fecha: {today}')
    toSearch = input('Producto a buscar: ').lower()
    url = get_URL(toSearch)
    url = f'{HOME_URL}{url}'
    #Número de páginas máximas que examina. Aprox 54 productos por página, dependiendo lo que se busque.
    pags_MAX = int(input('Cantidad de páginas (-1 para todas): '))
    if pags_MAX == -1:
        pags_MAX = 999999999
    # Chequeo si la version de HTML cambió con respecto a la última vez que se corrió el programa
    cambios = compare_html(url, pags_MAX, toSearch)
    if cambios:
        print('Hubo cambios. TODO: Realizar tester y algoritmo de corrección de XPATHS')
    parse_home(url, pags_MAX)