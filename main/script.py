import requests
from bs4 import BeautifulSoup
import csv

output = []  # list to store ebay items data
pagination_urls = []  # urls of the result pages to be parsed


def remove_space_control_characters(string):
    s = str(string).replace('\n', '')
    s = s.replace('\t', '')
    return s


def detailed_item_page_parser(url, item):
    local_page = requests.get(url)
    local_soup = BeautifulSoup(local_page.content, 'html.parser')

    # itemsSold is the nr of total sells of that item
    itemsSold = local_soup.find('a', {"class": "vi-txt-underline"})
    if itemsSold is not None:
        item['itemsSold'] = itemsSold.contents[0]
    else:
        item['itemsSold'] = '0'

    # itemAvailability is the nr of items available
    itemAvailability = local_soup.find('span', {"id": "qtySubTxt"})
    if itemAvailability is not None:
        item['itemAvailability'] = remove_space_control_characters(itemAvailability.span.contents[0])
    else:
        item['itemAvailability'] = '1'

    # itemRatings is the nr of reviews of an inserate/product
    itemRatings = local_soup.find('a', {"class": "prodreview vi-VR-prodRev"})
    if itemRatings is not None:
        item['itemRatings'] = itemRatings.contents[0]
    else:
        item['itemRatings'] = '0'

    # itemCondition
    itemCondition = local_soup.find('div', {"id": "vi-itm-cond"})
    if itemCondition is not None:
        item['itemCondition'] = itemCondition.contents[0]
    else:
        item['itemCondition'] = 'NA'

    return item


def main_result_page_parser(url):
    local_page = requests.get(url)
    local_soup = BeautifulSoup(local_page.content, 'html.parser')

    find_and_add_next_pagination_url(local_soup)

    resultItems = list(local_soup.find('ul', {"id": "ListViewInner"}).children)

    for next_item in resultItems:
        try:
            item = {}

            # itemTitle is the title of an inserate
            itemTitle = next_item.find('a', class_='vip')
            item['itemTitle'] = itemTitle.get('title')[28:]

            # itemURL is the url to the detailed page of an inserate
            item['itemURL'] = next_item.a['href']

            # itemPrice is the price of an item
            try:
                # pricerange --> use lower price as price
                itemPrice = next_item.find('span', class_='prRange')
                item['itemPrice'] = itemPrice.contents[1]  # takes lower border price for price range inserates

            except (AttributeError, IndexError):
                itemPrice = next_item.find('span', class_='bold')
                item['itemPrice'] = itemPrice.contents[len(itemPrice) - 1]  # last item in list is actual price

            # itemFormat find the format of the inserate on ebay
            itemFormat = next_item.find('li', class_='lvformat').span
            if itemFormat is not None:
                item['itemFormat'] = itemFormat.contents[0]
            else:
                item['itemFormat'] = 'NA'

            # itemShippingCost is the cost of delivery of an item
            itemShippingCost = next_item.find('span', class_='fee')
            if itemShippingCost is not None:
                item['itemShippingCost'] = itemShippingCost.contents[0]
            else:
                item['itemShippingCost'] = 'None'

            # parses for detailed information of the item
            item = detailed_item_page_parser(item['itemURL'], item)

            # removes space control characters of all results and transforms them into strings
            for key in item:
                item[key] = remove_space_control_characters(item[key])

            output.append(item)  # adds newly parsed item to resultItem list
            print(item)  # TODO: delete
        except:
            continue


def find_and_add_next_pagination_url(s):
    """
    finds and appends the next pages url on the url list
    :param s: soup in which next url should be found
    :return: None
    """
    nextPageButton = s.find('a', class_="gspr next")
    try:
        nextPaginationUrl = nextPageButton.get('href')
        pagination_urls.append(nextPaginationUrl)
    except (IndexError, AttributeError):
        print('probably last page!')

    print('URLs to parse:' + str(pagination_urls))


def main():
    root = input('Input the main result page URL of your ebay search and press Enter! \n')
    page = requests.get(root)
    soup = BeautifulSoup(page.content, 'html.parser')
    pagination_urls.append(root)
    print("Parser started! ")

    while len(pagination_urls) > 0:
        p = pagination_urls.pop(0)
        main_result_page_parser(p)
    print('All Done!')
    print(str(len(output)) + ' results found!')
    create_output_file(root)


def create_output_file(keyword_url):
    local_page = requests.get(keyword_url)
    local_soup = BeautifulSoup(local_page.content, 'html.parser')
    keyword = local_soup.find('span', {"class": "kwcat"}).b.contents[0]
    filename = keyword+'.csv'
    with open(filename, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['itemURL', 'itemTitle', 'itemPrice', 'itemShippingCost', 'itemRatings',
                                          'itemFormat', 'itemsSold', 'itemAvailability', 'itemCondition'])
        w.writeheader()
        for item in output:
            w.writerow(item)
    print('File successfully created! ')

main()  # starts the parser
