# Meb Okulları Listesi

[Milli Eğitim Bakanlığı](http://www.meb.gov.tr/baglantilar/okullar/) 
web sitesindeki 81 ilin okullarının listesini çeken python kodu.

*Not: Web sitesinde yer alan Bakanlık seçeneği altındaki yurt dışı okulları dahil değil.*

## Okullar CSV

Okulların indirilmiş ve kategorize edilmiş güncel halini **meb-okullar.csv** dosyasında bulabilirsiniz.

*Son Güncelleme: 24 Mart 2017*

## Gereksinimler

* Python 3.5 =>
* beautifulsoup4
* urllib3

``pip install -r requirements``

## Kullanım

```
from meb import Meb

m = Meb() # Meb'in web sitesinden illerin listesini indirir.
m.iller # illerin listesi
[<Il: Adana>, <Il: Adıyaman>, ...]

m.okullar()  # Tum okullari indirir.
# Internet hızınıza bagli olarak bu islem vakit alir.
[<Okul: Okul Adı>, ...]

m.tocsv('/path/to/okullar.csv')  # Okulları verilen dosyaya yazar
# NOT: .tocsv() methodu butun okulları tekrar indirmeye baslayacagi icin
# m.okullar() komutunu kullanmadan sadece bunu kullanin.
```

### Belirli Bir İl veya İlçenin Okulları
```
# Tek Bir İlin Okullarını İndirme #

adana = m.iller[0]
adana.__dict__
# {'url': 'http://www.meb.gov.tr/baglantilar/okullar/?ILKODU=1', 'kod': '1', 'ad': 'Adana'}

adana_okullari = adana.okullar()  # Adana ili okullarını indirir.
[<Okul: Büyüksofulu Ortaokulu>, ...]

okul = adana_okullari[0]
okul.__dict__
# {'type': 'Ortaokul', 'il': 'Adana', 'ilce': 'Aladağ', 'website': 'http://sofulu.meb.k12.tr', 'ad': 'Büyüksofulu Ortaokulu'}

```

```
# Tek Bir İlçenin Okullarını İndirme #

adana_ilceleri = adana.ilceler() # Adana ili ilcelerini indirir
# Merkez'e bağlı okullar ilçler altında Büyükşehir veya Merkez olarak geliyor.
[<Ilce: Adana - Aladağ>, <Ilce: Adana - Bahçe>, ...]

aladag = adana_ilceleri[0]
aladag.__dict__
# {'url': 'http://www.meb.gov.tr/baglantilar/okullar/?ILKODU=1&ILCEKODU=2', 'kod': '2', 'ad': 'Aladağ', 'iladi': 'Adana'}


aladag_okullari = aladag.okullar()  # Okulları indirir.
[<Okul: Büyüksofulu Ortaokulu>, ...]

okul = aladag_okullari[0]
okul.__dict__
# {'type': 'Ortaokul', 'il': 'Adana', 'ilce': 'Aladağ', 'website': 'http://sofulu.meb.k12.tr', 'ad': 'Büyüksofulu Ortaokulu'}
```

## Okul Tipleri

* None (Belirlenemeyen)
* Anaokulu
* İlkokul
* Ortaokul
* Lise
* Sanat Okulu
* Halk Eğitim Merkezi
* Araştırma Merkezi
* Milli Eğitim Müdürlüğü
* Meslek Lisesi
* Uygulama Merkezi
* Olgunlaşma Enstitüsü
* Öğretmenevi
* Yatılı Bölge Okulu