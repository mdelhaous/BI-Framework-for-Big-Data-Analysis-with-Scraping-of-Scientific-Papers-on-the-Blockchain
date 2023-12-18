from selenium.webdriver.common.by import By
import time
from .config.model import models
from .config.driver import constants as cts
from .config.driver import driver as web
from .config.MongoClient import find_all_links_with_scrapped_false, find_all_journals_with_scrapped_false,update_link,update_journal, insert_article, insert_all_links, insert_journal
from bs4 import BeautifulSoup
from datetime import datetime


def get_articles_links(soup):
    articles = soup.find_all("span", class_="hlFld-Title")
    links: list[models.Link] = []
    for art in articles:
        link = models.Link(title=art.text, link=art.find("a").get("href"), webSite=cts.ACM_BASE_URL, scrapped=False,
                    date=str(datetime.now()))
        links.append(link)
    return insert_all_links(links)


def extract_article(soup, link) -> models.Article:
    art=models.Article
    try:
        title = soup.find("h1", class_="citation__title")
        date = soup.find("span", class_="CitationCoverDate").string
        year= date.split(' ')[-1]
        abstract = soup.find('div', class_='abstractSection abstractInFull')
        journal = soup.find("span", class_="epub-section__title")
        citation = soup.find("span", class_="citation")
        download = soup.find("span", class_="metric")
        
        return models.Article(title=str(title.string), link=link, authors=[], publishing_date=str(date),year=int(year),
                       abstract=str(abstract.p.text), journal=str(journal.string), citation=int(citation.span.text),
                       download=int(download.text), views=int(-1))
    except:
        print("Error")

def extract_journal(soup, journal: models.Journal) -> models.Journal:
    try:
        
        firstdiv=soup.find("div", class_ = "cell100x1 dynamiccell" )
        tbody=firstdiv.find_all("div", class_="cellslide")[1].table.tbody
        
        rank:models.Ranking
        ranks: list[models.Ranking] = []
       
        for item in tbody.select("tr"):
            
                year=item.select("td")[1].text
                quartile=item.select("td")[2].text
                category=item.select("td")[0].text
                rank = models.Ranking(category= str(category), year= int(year), quartile = str(quartile))
                ranks.append(rank)
        
        journal.ranking=ranks
    
        return  journal
    except:
        print("Error")

def extract_Authors(soup,article:models.Article)->list[models.Author]:
    try:
        author:models.Author
        authors:list[models.Author]=[]
        AUTH=soup.find_all("div",class_="auth-info")

        for a in AUTH:
            # print(a.span[0])
            name=a.find_all("span")[0].text.strip()
            print(name)
            establishment=a.find_all("span")[1].text
            country=establishment.split(',')[-1]
            author=models.Author(name=str(name), establishment=str(establishment), country=str(country))
            authors.append(author)
        article.authors=authors
        return article
    except:
        print("cannot scrapping authors")







class Deamon:
    deamon = None

    def __init__(self, browserType: str):
        self.deamon = web.Driver(browserType)

    def start_scrapping_links(self, keyword: str):
        url = cts.ACM_BASE_URL + cts.ACM_SEARCH_SUFFIX + keyword + cts.ACM_SEARCH_CONFIG
        self.deamon.open_page(url)
        condition = True
        i = 1
        while condition:
            try:
                print(f'Page N{i}')
                i += 1
                html = self.deamon.get_source_page((By.CLASS_NAME, cts.ACM_PAGINATION_NAV_CLASS_NAME))
                soup = BeautifulSoup(html, 'html.parser')
                get_articles_links(soup)
                self.deamon.acm_next_page(cts.ACM_NEXT_PAGE_CLASS_NAME, cts.ACM_PAGINATION_NAV_CLASS_NAME)
                if i >1:
                    condition= False
            except:
                condition = False
                print('You are in the last page !!')
                self.stop()

    def start_scrapping_articles(self):

        links_to_be_scrapped: list[models.Link] = find_all_links_with_scrapped_false(cts.ACM_BASE_URL)
        i = 1
        for lk in links_to_be_scrapped:

            try:
                print(f'Article N{i}')
                article = self.get_article(lk)
                
                article=self.get_authors(article)                
                updated_link = update_link(lk)
                article.link = updated_link
                insert_article(article)
                try:
                    jrnl= models.Journal(name=article.journal, link='', scrapped=False, ranking=[])
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

        journals_to_be_scrapped: list[models.Journal] = find_all_journals_with_scrapped_false()
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

    def get_article(self, link: models.Link) -> models.Article:
        url = cts.ACM_BASE_URL + link.link
        self.deamon.open_page(url)
        html = self.deamon.get_source_page((By.CLASS_NAME, cts.ACM_ARTICLE_TITLE_CLASS_NAME))
        soup = BeautifulSoup(html, 'html.parser')
        return extract_article(soup, link)
    
    def get_authors(self,article:models.Article):
        self.deamon.show_authors()
        time.sleep(4)
        html = self.deamon.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        return extract_Authors(soup,article)

    def get_journal(self, journal: models.Journal) -> models.Journal:
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
    acm_deamon = Deamon('chrome')
    #acm_deamon.start_scrapping_links('blockchain')
    acm_deamon.start_scrapping_articles()
    acm_deamon.start_scrapping_journals()
    acm_deamon.stop()
    # dirname = os.path.dirname(os.path.abspath(__file__))
    # print(dirname)
