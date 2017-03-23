from bs4 import BeautifulSoup
import urllib3
import logging
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

error_handler = logging.FileHandler(filename='meb_error.log')
error_handler.setLevel(logging.WARNING)
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)

debug_handler = logging.FileHandler(filename='meb_debug.log', mode='w')
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(formatter)
logger.addHandler(debug_handler)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

http = urllib3.PoolManager(num_pools=1)

def capitalize(string):
    all = []
    for s in str(string).split(' '):
        cap = list(s.capitalize())
        for i, c in enumerate(s):
            if i == 0:
                continue
            if c == "I":
                cap[i] = "ı"
        all.append("".join(cap))

    return " ".join(all)

class Ilce:

    def __repr__(self):
        return str("<Ilce: %s - %s>" % (self.iladi, self.ad))

    def __init__(self, ad, kod, url, iladi):
        self.iladi = iladi
        self.ad = capitalize(ad)
        self.kod = kod
        self.url = url + "&ILCEKODU=" + str(kod)

    def okullar(self):
        okullar = []
        for p in self.pages():
            for o in p.get():
                okullar.append(o)
        return okullar

    def pages(self):
        logger.info('%s - %s ilçesi indiriliyor.' % (self.iladi, self.ad))
        try:
            respone = http.urlopen('GET', self.url)
            data = BeautifulSoup(respone.data, 'html.parser')
        except Exception:
            logger.exception('%s - %s ilçesi sayfası indirilemedi!' % (self.iladi, self.ad))
            raise

        logger.debug('Sayfalar oluşturuluyor.')

        pages = []

        try:
            lastpage = int(data.find('a', {'class': 'last'}).attrs.get('href').split('=')[-1])
            logger.debug('Toplam alt sayfa sayısı: %s' % lastpage)

            for i in range(lastpage):
                pages.append(Page(i + 1, self.url))
        except Exception:
            logger.exception('%s - %s ilçesi alt sayfaları oluşturulamadı!' % (self.iladi, self.ad))
            raise

        return pages

class Il:

    def __str__(self):
        return str(self.ad)

    def __repr__(self):
        return str("<Il: %s>" % self.ad)

    def __init__(self, ad, kod, base_url):
        self.ad = capitalize(ad)
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
        logger.info("%s ili okulları alınıyor..." % self.ad)
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
            self.ad = capitalize(" ".join(a.contents[0].split(' - ')[2:]))
            self.type = self._type(self.ad)
        except Exception:
            logger.exception('Okul datası hatalı!\nDATA: %s' % data)
            raise


    def _type(self, ad):
        MESLEK_LISESI = "Mesleki Eğitim Merkezi|" \
                        "MESLEKİ EĞİTİM MERKEZİ|" \
                        "Teknik Eğitim Merkezi|" \
                        "MESLEKİ EĞİTİM MERKEZ|" \
                        "Mesleki Eğitimi Merkezi|" \
                        "Turizm Eğitim Merkezi|" \
                        "TURİZM EĞİTİM MERKEZİ|" \
                        "EğitimUygulama|" \
                        "TEKNİK EĞİTİM MERKEZİ|" \
                        "Tekin Mes|" \
                        "Eğitim  Merkezi|" \
                        "Mes\.Eğt|" \
                        "Eğitim Enstitüsü|"

        OGRETMENEVI = "ÖĞRETMENEVİ MÜDÜRLÜĞÜ|" \
                      "ÖĞRETMENEVİ|" \
                      "Öğretmenevi|" \
                      "Öğretmen Evi|" \
                      "ÖĞRETMEN EVİ|" \
                      "Ögretmen Evi|" \
                      "Öğretmeni"

        if re.findall("Ortaokul|ORTAOKUL|Orta Okul|ortaokul|ORTOKULU|Ortaoku|Ortakulu|ORTA OKULU|Ortaoklu|ORTAOOKULU|Ortaoklulu|Ortokulu", ad):
            return "Ortokul"
        elif re.findall('ilkokul|İlkokul|İLKOKUL|İlköğretim|Ilkokulu|İlokulu|İlkokolu|İlk Okulu|İlkolkulu|İLOKULU|İLK OKULU|İkokulu|İlkkulu|İllkokulu|İlköğ', ad):
            return "İlkokul"
        elif re.findall("Lise|lise|LİSE", ad):
            return "Lise"
        elif re.findall("Sanat Okulu|Sanat Merkezi|SANAT OKULU|SANAT MERKEZİ|Akşam Sanat Ok|sanat Merkezi", ad):
            return "Sanat Okulu"
        elif re.findall("Halk Eğitim|HALK EĞİTİMİ MERKEZİ|Halk Eğt|HALK EĞİTİM MERKEZİ", ad):
            return "Halk Eğitim Merkezi"
        elif re.findall("Anaokulu|anaokulu|ANAOKULU|ANA OKULU|OKUL ÖNCESİ|ANAOKU|Ana Okulu", ad):
            return "Anaokulu"
        elif re.findall("Araştırma Merkezi|ARAŞTIRMA MERKEZİ|Araştırma  Merkezi", ad):
            return "Araştırma Merkezi"
        elif re.findall("Eğitim Müdürlüğü|EĞİTİM MÜDÜRLÜĞÜ", ad):
            return "Milli Eğitim Müdürlüğü"
        elif re.findall(MESLEK_LISESI, ad):
            return "Meslek Lisesi"
        elif re.findall("Uygulama Merkezi|UYGULAMA MERKEZİ", ad):
            return "Uygulama Merkezi"
        elif re.findall("Olgunlaşma Enstitüsü", ad):
            return "Olgunlaşma Enstitüsü"
        elif re.findall(OGRETMENEVI, ad):
            return "Öğretmenevi"
        elif re.findall("YBO", ad):
            return "Yatılı Bölge Okulu"
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

    def get(self):
        logger.info('İndiriliyor: %s' % self.url)
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