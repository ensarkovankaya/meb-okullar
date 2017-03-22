from bs4 import BeautifulSoup
import urllib3
import logging
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)

http = urllib3.PoolManager(num_pools=1)


class Ilce:
    _pages = []

    def __repr__(self):
        return str("<Ilce: %s - %s>" % (self.iladi, self.ad))

    def __init__(self, ad, kod, url, iladi):
        self.iladi = iladi
        self.ad = ad
        self.kod = kod
        self.url = url + "&ILCEKODU=" + str(kod)
        self.data = None

    def _get(self):
        logger.debug('%s - %s ilçesi indiriliyor.' % (self.iladi, self.ad))
        try:
            respone = http.urlopen('GET', self.url)
            self.data = BeautifulSoup(respone.data, 'html.parser')
        except Exception:
            logger.exception('%s - %s ilçesi sayfası indirilemedi!' % (self.iladi, self.ad))
            raise

    def _build_pages(self):
        if self.data is None:
            self._get()

        logger.debug('Sayfalar oluşturuluyor.')

        try:
            lastpage = int(self.data.find('a', {'class': 'last'}).attrs.get('href').split('=')[-1])
            logger.debug('Toplam alt sayfa sayısı: %s' % lastpage)

            for i in range(lastpage):
                self._pages.append(Page(i + 1, self.url))
        except Exception:
            logger.exception('%s - %s ilçesi alt sayfaları oluşturulamadı!' % (self.iladi, self.ad))
            raise

    def okullar(self):
        okullar = []
        for p in self.pages():
            for o in p.get():
                okullar.append(o)
        return okullar

    def pages(self):
        """
        Sayfaları döner
        :return:
        """
        if len(self._pages) == 0:
            self._build_pages()
        return self._pages

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
        self.data = None

    def _get(self):
        logger.info('%s ili indiriliyor.' % self.ad)
        try:
            respone = http.urlopen('GET', self.url)
            self.data = BeautifulSoup(respone.data, 'html.parser')
        except Exception:
            logger.exception('%s sayfası indirilemedi!' % self.ad)
            raise

    def _build_ilceler(self):
        if self.data is None:
            self._get()

        logger.info('%s ilçeleri ayrıştırılıyor.' % self.ad)
        select = self.data.find('select', {'id': 'jumpMenu6'})
        options = select.find_all('option')
        options.pop(0)
        for opt in options:
            self._ilceler.append(
                Ilce(opt.contents[0], opt.attrs.get('value').split('=')[-1], self.url, self.ad)
            )

    def ilceler(self):
        if len(self._ilceler) == 0:
            self._build_ilceler()
        return self._ilceler

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
            self.il, self.ilce, self.ad = a.contents[0].split(' - ')
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
        self.data = None
        self._contents = []

    def _get(self):
        logger.debug('Sayfa indiriliyor: %s' % self.url)
        respone = http.urlopen('GET', self.url)
        self.data = BeautifulSoup(respone.data, 'html.parser')

    def _build_okullar(self):
        if self.data is None:
            self._get()

        try:
            div = self.data.find('div', {'id': 'grid'})
            table = div.find('table')
            contents = table.find_all('tr')
            contents.pop(0)  # table'ın ilk satırını çıkar
            for cont in contents:
                okul = Okul(cont)
                logger.debug('Okul: %s oluşturuldu' % okul.ad)
                self._contents.append(okul)
        except Exception:
            logger.exception('Sayfa %s için okullar ayrıştırılamadı.' % self.url)

    def get(self):
        if len(self._contents) == 0:
            self._build_okullar()
        return self._contents

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