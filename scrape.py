from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from requests_html import HTML
import re
import time

url_base = 'https://www.spoonflower.com'
url_home = f'{url_base}/en/shop?on=fabric'


def scraper(url, body_delay=0):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    if body_delay > 0:
        time.sleep(body_delay)
    return driver.page_source


def extract_id_slug(url_path):
    regex = r"^[^\s]+/(?P<id>\d+)-(?P<slug>[\w_-]+)$"
    group = re.match(regex, url_path)
    if not group:
        return None, None
    return group['id'], group['slug']


def extract_links(home_url):
    content = scraper(url=home_url)
    html_r = HTML(html=content)
    fabric_links = [x for x in list(
        html_r.links) if x.startswith("/en/fabric")]
    return fabric_links


def extract_product_detail(product_url):
    content = scraper(url=product_url, body_delay=10)
    html_r = HTML(html=content)

    data = {}

    title_el = html_r.find(".design-title", first=True)
    title = None
    if title_el == None:
        return data
    title = title_el.text
    data['title'] = title

    size_el = html_r.find("#fabric-size", first=True)
    size = None
    if size_el != None:
        size = size_el.text
    data['size'] = size

    price_parent_el = html_r.find('.b-item-price', first=True)
    price_el = price_parent_el.find('.visuallyhidden', first=True)
    for i in price_el.element.iterchildren():
        attrs = dict(**i.attrib)
        try:
            del attrs['itemprop']
        except:
            pass
        attrs_keys = list(attrs.keys())
        if len(attrs_keys) > 0:
            data[i.attrib['itemprop']] = i.attrib[attrs_keys[0]]
    return data


if __name__ == '__main__':
    fabric_links = extract_links(url_home)
    result = []

    start = time.time()
    for i, link in enumerate(fabric_links):
        product_url = f'{url_base}{link}'
        print(product_url)
        product_detail = extract_product_detail(product_url)
        result.append(product_detail)
        ellap = time.time() - start
        print(f"{i} done {ellap}")

        if i == 5:
            break
    
    print(time.time() - start)
    print(result)
