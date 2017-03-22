from bs4 import BeautifulSoup
import urllib3
import logging
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

error_handler = logging.FileHandler(filename='meb_error.log')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)

debug_handler = logging.FileHandler(filename='meb_debug.log')
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(formatter)
logger.addHandler(debug_handler)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

http = urllib3.PoolManager(num_pools=1)


class Ilce:

    def __repr__(self):
        return str("<Ilce: %s - %s>" % (self.iladi, self.ad))

    def __init__(self, ad, kod, url, iladi):
        self.iladi = iladi
        self.ad = ad
        self.kod = kod
        self.url = url + "&ILCEKODU=" + str(kod)

    def okullar(self):
        okullar = []
        for p in self.pages():
            for o in p.get():
                okullar.append(o)
        return okullar

    def pages(self):
        logger.debug('%s - %s ilçesi indiriliyor.' % (self.iladi, self.ad))
        try:
            respone = http.urlopen('GET', self.url)
            self.data = BeautifulSoup(respone.data, 'html.parser')
        except Exception:
            logger.exception('%s - %s ilçesi sayfası indirilemedi!' % (self.iladi, self.ad))
            raise

        logger.debug('Sayfalar oluşturuluyor.')

        pages = []

        try:
            lastpage = int(self.data.find('a', {'class': 'last'}).attrs.get('href').split('=')[-1])
            logger.debug('Toplam alt sayfa sayısı: %s' % lastpage)

            for i in range(lastpage):
                pages.append(Page(i + 1, self.url))
        except Exception:
            logger.exception('%s - %s ilçesi alt sayfaları oluşturulamadı!' % (self.iladi, self.ad))
            raise

        return pages

class Il:
    _ilceler = []

    def __str__(self):
        return str(self.ad)

    def __repr__(self):
        return str("<Il: %s>" % self.ad)

    def __init__(self, ad, kod, base_url):
        self.ad = ad
        self.kod = kod
        self.url = base_url + "?ILKODU=" + str(kod)

    def ilceler(self):

        logger.info('%s ili indiriliyor.' % self.ad)
        try:
            respone = http.urlopen('GET', self.url)
            self.data = BeautifulSoup(respone.data, 'html.parser')
        except Exception:
            logger.exception('%s sayfası indirilemedi!' % self.ad)
            raise

        logger.info('%s ilçeleri ayrıştırılıyor.' % self.ad)
        ilceler = []
        try:
            select = self.data.find('select', {'id': 'jumpMenu6'})
            options = select.find_all('option')
            options.pop(0)
            for opt in options:
                ilceler.append(
                    Ilce(opt.contents[0], opt.attrs.get('value').split('=')[-1], self.url, self.ad)
                )
        except Exception:
            logger.exception('%s ilçeleri ayrışıtırılamadı!' % self.ad)
            raise

        return ilceler

    def okullar(self):
        """
        İl'e ait okulları döner
        :return:
        """
        schools = []
        for ilce in self.ilceler():
            for o in ilce.okullar():
                schools.append(o)
        return schools

class Okul:
    def __repr__(self):
        return str("<Okul: %s>" % self.ad)

    def __init__(self, data):
        try:
            a = data.find_all('a')[0]
            website = a.attrs.get('href')
            self.website = website if website != "#" else None
            self.il = a.contents[0].split(' - ')[0]
            self.ilce = a.contents[0].split(' - ')[1]
            self.ad = " ".join(a.contents[0].split(' - ')[2:])
            self.type = self._type(self.ad)
        except Exception:
            logger.exception('Okul datası hatalı!\nDATA: %s' % data)
            raise

    def _type(self, ad):
        if re.findall("Ortaokul|ORTAOKUL", ad):
            return "ortaokul"
        elif re.findall('ilkokul|İlkokul|İLKOKUL', ad):
            return "ilkokul"
        elif re.findall("Lise|lise|LİSE", ad):
            return "lise"
        elif re.findall("Sanat Okulu", ad):
            return "sanat"
        elif re.findall("Halk Eğitim", ad):
            return "halkegitim"
        else:
            logger.warning('"%s" için Okul Tipi anlaşılamadı!' % self.ad)
            return None


class Page:
    def __repr__(self):
        return str("<Page: %s>" % self.no)

    def __init__(self, no, base_url):
        self.url = base_url + "&SAYFANO=" + str(no)
        self.no = no
        self._contents = []

    def _build_schools(self):

        logger.debug('Sayfa indiriliyor: %s' % self.url)
        respone = http.urlopen('GET', self.url)
        data = BeautifulSoup(respone.data, 'html.parser')

        schools = []

        try:
            div = data.find('div', {'id': 'grid'})
            table = div.find('table')
            contents = table.find_all('tr')
            contents.pop(0)  # table'ın ilk satırını çıkar
            for cont in contents:
                okul = Okul(cont)
                logger.debug('Okul: %s oluşturuldu' % okul.ad)
                schools.append(okul)
        except Exception:
            logger.exception('Sayfa %s için okullar ayrıştırılamadı.' % self.url)
        return schools

    def get(self):
        return self._build_schools()

class Meb:
    def __init__(self):
        self.meb_url = 'http://www.meb.gov.tr/baglantilar/okullar/'
        self.iller = []
        self._buil_iller()

    def _buil_iller(self):
        try:
            logger.debug('İller alınıyor...')
            respone = http.urlopen('GET', self.meb_url)
            soup = BeautifulSoup(respone.data, 'html.parser')
            select = soup.find('select', {'id': 'jumpMenu5'})
            options = select.find_all('option')
            options.pop(0)  # ilk değeri çıkar
            options.pop(81)  # BAKANLIK seçeneğini çıkar

            for opt in options:
                il = Il(opt.contents[0], opt.attrs.get('value').split('=')[1], self.meb_url)
                logger.debug("Il: %s oluşturuldu." % il.ad)
                self.iller.append(il)
        except Exception:
            logger.exception('Iller oluşuturulamadı!')
            raise

    def okullar(self):
        schools = []
        for il in self.iller:
            for o in il.okullar():
                schools.append(o)
        return schools