from arsenic import get_session, browsers, services
from requests_html import HTML
import time
import asyncio
import logging
import structlog # pip install structlog


def set_arsenic_log_level(level = logging.WARNING):
    # Create logger
    logger = logging.getLogger('arsenic')

    # We need factory, to return application-wide logger
    def logger_factory():
        return logger

    structlog.configure(logger_factory=logger_factory)
    logger.setLevel(level)
    

async def scraper(url, body_delay=0):
    service = services.Chromedriver()
    browser = browsers.Chrome(**{"goog:chromeOptions":{
        'args': ['--headless', '--disable-gpu']
    }})

    async with get_session(service, browser) as session:
        try:
            await asyncio.wait_for(session.get(url), timeout=60)
        except asyncio.TimeoutError:
            return []
        if body_delay > 0:
            await asyncio.sleep(body_delay)
        body = await session.get_page_source()
        return body


async def extract_links(home_url):
    content = await scraper(url=home_url)
    html_r = HTML(html=content)
    fabric_links = [x for x in list(
        html_r.links) if x.startswith("/en/fabric")]
    return fabric_links


async def extract_product_detail(product_url, i=-1, start_time=None):
    content = await scraper(url=product_url, body_delay=10)
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

    if start_time != None:
        end = time.time() - start_time
        print(f'{i} took {end} seconds')

    return data


async def products_detail(links, start_time=None):
    results = []
    for i, link in enumerate(links):
        product_url = f'{url_base}{link}'
        results.append(
            asyncio.create_task(extract_product_detail(
                product_url, i=i, start_time=start_time))
        )
        if i == 5:
            break

    list_of_product_detail = await asyncio.gather(*results)
    return list_of_product_detail


async def run(url):
    start = time.time()
    fabric_links = await extract_links(url_home)
    results = await products_detail(fabric_links, start_time=start)
    print(time.time() - start)
    print(results)


if __name__ == '__main__':
    set_arsenic_log_level()
    url_base = 'https://www.spoonflower.com'
    url_home = f'{url_base}/en/shop?on=fabric'
    asyncio.run(run(url_home))
