from selenium.webdriver.common.by import By

from .config.model.models import Author, Link, Article, Journal, Ranking
from .config.driver import constants as cts
from .config.driver import driver as web
from .config.MongoClient import update_link, insert_article, insert_journal ,find_all_links_with_scrapped_false, insert_all_links, find_all_journals_with_scrapped_false, update_journal
from bs4 import BeautifulSoup
from datetime import datetime


def get_articles_links(soup):
    articles = soup.find_all("h3", class_="text-md-md-lh")
    links: list[Link] = []
    for art in articles:
        link = Link(title=art.text, link=art.find("a").get("href"), webSite=cts.IEEE_BASE_URL, scrapped=False,
                    date=str(datetime.now()))
        links.append(link)
    return insert_all_links(links)


def extract_article(soup, link) -> Article:
    try:
        title = soup.find("h1", class_="document-title text-2xl-md-lh")
        authors = []
        d = soup.find("div", class_="u-pb-1 doc-abstract-pubdate").text
        date=d.split(":")[1]
        year= date.split(' ')[-2]
        abs = soup.find('div', class_='abstract-text row').div.div.text
        abstract=abs.split(":",1)[1]
        journal = soup.find("div", class_="u-pb-1 stats-document-abstract-publishedIn")
        citation = soup.find("div", class_="document-banner-metric-container row")
        views_container = soup.find("div", class_="document-banner-metric-container row")
        views = views_container.select('div > button')[1]
        return Article(title=str(title.span.string), link=link, authors=authors, publishing_date=str(date),year=int(year),
                       abstract=str(abstract), journal=str(journal.a.string),
                       citation=int(citation.button.div.text),
                       download=None, views=int(views.div.text))
        
        
    except:
        print("Error")

def extract_authors(soup2) -> list[Author]:
    try:
        # AuthorDetails=soup2.find_all("div", class_="authors-accordion-container")
        AuthorDetails=soup2.find_all("xpl-author-item")
        author: Author
        authors :list[Author]=[]
        for author in AuthorDetails:
            name=author.div.a.text
            l=author.find_all("div",class_="row")
            
            for lll in l:
                country=lll.text.split(',')[-1]
                d=lll.div.find_all("div")[1].text
                establishment=d.split(',')[1]

            author=Author(name=str(name),establishment=str(establishment),country=str(country))   
            authors.append(author)
        
        # print(authors)
        return authors
    except:
        print("cannot extract authors")

    


def extract_journal(soup, journal: Journal) -> Journal:
    try:
        
        firstdiv=soup.find("div", class_ = "cell100x1 dynamiccell" )
        tbody=firstdiv.find_all("div", class_="cellslide")[1].table.tbody
       
        rank:Ranking
        ranks: list[Ranking] = []
       
        for item in tbody.select("tr"):
        
            year=item.select("td")[1].text
            quartile=item.select("td")[2].text
            category=item.select("td")[0].text
            rank = Ranking(category= str(category), year= int(year), quartile = str(quartile))
            ranks.append(rank)
        
        journal.ranking=ranks
    
        return  journal
    except:
        print("Error")

class Deamon:
    deamon = None

    def __init__(self, browserType: str):
        self.deamon = web.Driver(browserType)

    def start_scrapping_links(self, keyword: str):
        url = cts.IEEE_BASE_URL + cts.IEEE_SEARCH_SUFFIX + keyword + cts.IEEE_SEARCH_CONFIG
        self.deamon.open_page(url)
        condition = True
        i = 1
        while condition:
            try:
                print(f'Page N{i}')
                i += 1
                html = self.deamon.get_source_page((By.TAG_NAME, cts.IEEE_RESULTS_LIST_TAG_NAME))
                soup = BeautifulSoup(html, 'html.parser')
                get_articles_links(soup)
                self.deamon.ieee_next_page(cts.IEEE_NEXT_PAGE_CLASS_NAME, cts.IEEE_RESULTS_LIST_CLASS_NAME)
                if i > 2:
                    condition = False
                    print('Enough links')
            except:
                condition = False
                print('You are in the last page !!')
                self.stop()

    def start_scrapping_articles(self):

        links_to_be_scrapped: list[Link] = find_all_links_with_scrapped_false(cts.IEEE_BASE_URL)
        i = 1
        for lk in links_to_be_scrapped:

            try:
                print(f'Article N{i}')
                article = self.get_article(lk)
                authors = self.get_authors(lk)
                article.authors = authors
                updated_link = update_link(lk)
                article.link = updated_link
                print(article)
                insert_article(article)
                try:
                    jrnl= Journal(name=article.journal, link='', scrapped=False, ranking=[])
                    insert_journal(jrnl)
                    # print(f'journal {jrnl.dict()} ')
                except:
                    print("can't create journal")
                i += 1
                if i >=10:
                    break
                
            except:
                print(f"Couldn't scrap Article with link {lk.link}")
        print('Finished scrapping articles')

    def start_scrapping_journals(self):

            journals_to_be_scrapped: list[Journal] = find_all_journals_with_scrapped_false()
            i = 1
            for j in journals_to_be_scrapped:

                try:
                    print(f'journal N{i}')
                    journ = self.get_journal(j)
                    uJ = update_journal(journ)
                    
                    
                    i += 1
                    
                except:
                    print(f"Couldn't scrap journal with name {j.name}")
            print('Finished scrapping journals')

    def get_article(self, link: Link) -> Article:
        url = cts.IEEE_BASE_URL + link.link 
        self.deamon.open_page(url)
        html = self.deamon.get_source_page((By.TAG_NAME, cts.IEEE_ARTICLE_DETAILS_TAG_NAME))
        soup = BeautifulSoup(html, 'html.parser')
        return extract_article(soup, link)
    
    def get_authors(self, link: Link) -> Article:
        try:
                
            url = cts.IEEE_BASE_URL + link.link + 'authors#authors'
            self.deamon.open_page(url)
            html1 = self.deamon.get_source_page((By.TAG_NAME, cts.IEEE_ARTICLE_DETAILS_TAG_NAME))
            soup1 = BeautifulSoup(html1, 'html.parser')
        except:
            print("cannot get authors")
        return extract_authors(soup1)
    
    def get_journal(self, journal: Journal) -> Journal:
        url = cts.SJR_BASE_URL +cts.SJR_SEARCH_SUFFIX+ journal.name
        self.deamon.open_page(url)
        html = self.deamon.get_source_page((By.CLASS_NAME, 'search_results'))
        soup = BeautifulSoup(html, 'html.parser')
       
        try:
            linkSoup=soup.find("div", class_="search_results")
            # print(linkSoup)
            link=linkSoup.find_all("a")[0].get("href")
            journalUrl=cts.SJR_BASE_URL+str(link)
            journal.link=journalUrl
        except:
            print("can't extrate journal link")
       
        self.deamon.open_page(journalUrl)
        html = self.deamon.get_source_page((By.CLASS_NAME, 'background'))
        soup = BeautifulSoup(html, 'html.parser')

        return extract_journal(soup, journal)

    def stop(self):
        self.deamon.close_page()


if __name__ == '__main__':
    acm_deamon = Deamon('Firefox')
    acm_deamon.start_scrapping_links('blockchain')
    acm_deamon.start_scrapping_articles()
    acm_deamon.stop()
    # dirname = os.path.dirname(os.path.abspath(__file__))
    # print(dirname)