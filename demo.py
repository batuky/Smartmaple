import logging
import os
import sys
import pymongo
import requests
import string
import threading
import time
import logging
import math
from queue import Queue
from collections import Counter
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

mongo_uri = os.environ.get('MONGODB_URI')

class NewsScraper:
    """
    Class to scrape news articles and handle MongoDB operations for news data and performance stats.
    """

    def __init__(self, db_name):
        """
        Initialize NewsScraper with the specified database name.
        """

        try:
            mongo_uri = os.environ.get('MONGODB_URI')
            
            if mongo_uri:
                self.client = pymongo.MongoClient(mongo_uri)
                self.db = self.client[db_name]
                self.news_collection = self.db["news"]
                self.performance_collection = self.db["stats"]
                self.word_frequency_collection = self.db["word_frequency"]
            else:
                sys.exit("MONGODB_URI environment variable not found!")

        except pymongo.errors.ConnectionFailure as e:
            # When there is a connection error, this part works.
            print("Could not connect to MongoDB.", e)
        except Exception as e:
            # When there is an environment variable error, this part works.
            print("Error:", e)

        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = time.time()
        self.lock = threading.Lock()

    def save_performance_data(self, request_count, successful_requests, failed_requests):
        """
        Save performance data to MongoDB.

        Parameters:
        - request_count (int): Number of requests made during scraping.
        - successful_requests (int): Number of successful requests.
        - failed_requests (int): Number of failed requests.
        - start_time (float): Start time of scraping process.
        """

        end_time = time.time()
        elapsed_time = end_time - self.start_time

        performance_data = {
            "Request Count": request_count,
            "Successful Requests": successful_requests,
            "Failed Requests": failed_requests,
            "Elapsed Time (seconds)": elapsed_time,
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        self.performance_collection.insert_one(performance_data)
        logging.info("Performance data saved to MongoDB.")

    def save_to_mongodb(self, the_news_url, header, summary, text, img_url_list, publish_date, update_date):
        """
        Save news data to MongoDB.

        Parameters:
        - the_news_url (str): URL of the news article.
        - header (str): Header of the news article.
        - summary (str): Summary of the news article.
        - text (str): Text content of the news article.
        - img_url_list (list): List of image URLs associated with the news article.
        - publish_date (str): Publish date of the news article.
        - update_date (str): Update date of the news article.
        """

        existing_news = self.news_collection.find_one({"URL": the_news_url})

        if existing_news is None:
            the_news = {
                "URL": the_news_url,
                "Header": header,
                "Summary": summary,
                "Text": text,
                "Image URLs": img_url_list,
                "Publish Date": publish_date if publish_date else 'No information',
                "Update Date": update_date if update_date else 'No information'
            }
            self.news_collection.insert_one(the_news)
            logging.info(f"{the_news_url} successfully added to MongoDB.")
        else:
            logging.info(f"{the_news_url} already exists in MongoDB. Skipped.")

    def extract_news_details(self, the_news):
        """
        Extract URL, header, and summary from a news article.
        """

        the_news_url = the_news.find('a')['href']
        header = the_news.find('h2', class_='haber-baslik').text.strip()
        summary = the_news.find('div', class_='haber-content').find('div', class_='haber-desc').text.strip()
        return the_news_url, header, summary
    
    def extract_image_urls(self, detail_soup):
        """
        Extract image URLs from parsed news content.
        """

        img_url_list = []
        haber_main_img = detail_soup.find_all('img', class_='onresim wp-post-image')
        for img in haber_main_img:
            src = img['data-src']
            img_url_list.append(src)
        detay_img_tags = detail_soup.select('div.post_line img')
        for img in detay_img_tags:
            src = img['src']
            if not src.startswith('data:image/svg+xml;base64') and src != '#':
                img_url_list.append(src)
        return img_url_list  

    def extract_text(self, detail_soup):
        """
        Extract text content from parsed news content.
        """

        return ' '.join([p.text.strip() for p in detail_soup.select('div.post_line div.yazi_icerik p')])

    def extract_date(self, detail_soup):
        """
        Extract publish and update dates from parsed news content.
        """

        dates = detail_soup.select('div.yazibio span.tarih time')
        publish_date = ''
        update_date = ''
        for date in dates:
            datetime_attr = date['datetime']
            if 'Yayınlanma' in date.parent.text:
                publish_date = datetime_attr
            elif 'Güncelleme' in date.parent.text:
                update_date = datetime_attr
        return publish_date, update_date
    

    def upper_tr(self, text):
        """
        Convert Turkish characters to upper case.
        """

        # Dictionary for Turkish characters
        tr_to_upper = {
            'i': 'İ',
            'ı': 'I',
            'ğ': 'Ğ',
            'ü': 'Ü',
            'ş': 'Ş',
            'ö': 'Ö',
            'ç': 'Ç'
        }

        # Convert characters
        text = ''.join(tr_to_upper.get(c, c).upper() for c in text)
        return text

    def get_top_10_words(self, news_collection):
        """
        Get the top 10 most used words from the news text stored in MongoDB.
        """

        all_text = ""
        # Concatenate all news texts
        for document in news_collection.find():
            all_text += document['Text'] + " "

        # Split the text and remove punctuation
        translator = str.maketrans('', '', string.punctuation)
        all_text = all_text.translate(translator)
        words = all_text.split()
        # To avoid case sensitivity, all words were converted to lowercase.
        words = [self.upper_tr(word) for word in words]
        # Calculate word counts
        word_counts = Counter(words)
        top_10_words = word_counts.most_common(10)

        return top_10_words
    
    def plot_and_save_top_10_words(self, top_10_words):
        """
        Plot and save the top 10 most used words as a graph and save it as a PNG file.
        """

        words = [word[0] for word in top_10_words]
        counts = [count[1] for count in top_10_words]

        plt.figure(figsize=(10, 6))
        plt.bar(words, counts, color='skyblue')
        plt.xlabel('Words')
        plt.ylabel('Counts')
        plt.title('Top 10 Most Used Words in News Text')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('top_10_words.png')

    def add_top_10_words_to_db(self, top_10_words):
        """
        Add the top 10 most used words to MongoDB in a 'word_frequency' collection.
        """

        existing_words = {word['Word']: word['Count'] for word in self.word_frequency_collection.find()}
        for word, count in top_10_words:
            if word in existing_words:
                # If the word exists, update the count
                new_count = existing_words[word] + count
                self.word_frequency_collection.update_one(
                    {"Word": word},
                    {"$set": {"Count": new_count}}
                )
                logging.info(f"Word '{word}' count updated in MongoDB 'word_frequency' collection.")
            else:
                # If the word does not exist, insert it
                word_data = {
                    "Word": word,
                    "Count": count
                }
                self.word_frequency_collection.insert_one(word_data)
                logging.info(f"Word '{word}' added to MongoDB 'word_frequency' collection.")

        # Delete old entries that are no longer in the top 10 list
        top_10_words_set = {word[0] for word in top_10_words}
        for word in existing_words:
            if word not in top_10_words_set:
                self.word_frequency_collection.delete_one({"Word": word})
                logging.info(f"Word '{word}' removed from MongoDB 'word_frequency' collection.")

    def print_grouped_data_by_update_date(self, news_collection):
        """
        Print grouped data based on update dates from the MongoDB collection.
        """
        pipeline = [
            {"$match": {"Update Date": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": {"$dateFromString": {"dateString": "$Update Date"}}}}, "count": {"$sum": 1}}}
        ]

        grouped_data = list(news_collection.aggregate(pipeline))
        for data in grouped_data:
            print(f"Update Date: {data['_id']} - Count: {data['count']}")

    def get_parsed_page_content(self, url):
        """
        Get parsed page content from the specified URL.

        Parameters:
        - url (str): URL of the web page to parse.

        Returns:
        - BeautifulSoup object: Parsed page content.
        """

        response = requests.get(url)
        with self.lock:
            self.request_count += 1  # Update with locking mechanism
        return BeautifulSoup(response.text, 'html.parser') 

    def scrape_news(self):
            """
            Scrape news articles from the specified website and store data in MongoDB.
            """
            
            max_threads = 20
            # Divide the number of pages by the number of threads.
            last_page = 50  # 50 Pages determined
            pages_per_thread = math.ceil(last_page / max_threads)  # Ceiling process to share pages to threads
            
            # Start threads
            threads = []
            start_page = 1
            is_reached_page_limit = False
            for _ in range(max_threads):
                end_page = start_page + pages_per_thread
                if(end_page >= last_page + 1):
                    end_page = last_page + 1
                    is_reached_page_limit = True
                thread = threading.Thread(target=self.worker, args = (start_page, end_page))
                threads.append(thread)
                thread.start()
                if is_reached_page_limit:
                    break
                start_page = start_page + pages_per_thread

            # Wait for all threads to finish
            for thread in threads:
                thread.join()

            # Save performance data
            self.save_performance_data(self.request_count, self.successful_requests, self.failed_requests)
       
    def worker(self, start_page, end_page):
        """
        Scrape news articles from a website and save data to MongoDB.

        Process URLs in the queue, fetch news details, and update MongoDB collections.
        Implements locking for thread-safe updates to request counts and statistics.
        """

        for page_num in range(start_page, end_page):
            url = f'https://turkishnetworktimes.com/kategori/gundem/page/{page_num}/'
            try:
                soup = self.get_parsed_page_content(url)
                news = soup.find_all('article', class_='col-12')
                the_news_url = None
                for the_news in news:
                    try:
                        the_news_url, header, summary = self.extract_news_details(the_news)
                        detail_soup = self.get_parsed_page_content(the_news_url)        
                        img_url_list = self.extract_image_urls(detail_soup)
                        text = self.extract_text(detail_soup)
                        publish_date, update_date = self.extract_date(detail_soup)
                        self.save_to_mongodb(the_news_url, header, summary, text, img_url_list, publish_date, update_date)
                        with self.lock:
                            self.successful_requests += 1  # Update with locking mechanism
                    
                    except Exception as e:
                        logging.error(f"News URL: {the_news_url}. Error: {str(e)}")
                        with self.lock:
                            self.failed_requests += 1  # Update with locking mechanism
            except Exception as e:
                logging.error(f"Page URL: {url}. Error: {str(e)}")
                with self.lock:
                    self.failed_requests += 1  # Update with locking mechanism

def get_user_input():
    global user_choice
    user_choice = input("Would you like to run print_grouped_data_by_update_date function? Answer the question in 10 seconds (1 for Yes / 0 for No): ")

if __name__ == "__main__":
    try:
        user_choice = '0'  # Default value
        threads_list = []
        while True:
            if not os.path.exists('logs'):
                os.makedirs('logs', exist_ok=True)

            log_file = os.path.join('logs', 'logs.log')
            logging.basicConfig(filename=log_file, filemode='a', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

            db_name = "batuhan_kaya"
            news_scraper = NewsScraper(db_name)
            news_scraper.scrape_news()

            top_10_words = news_scraper.get_top_10_words(news_scraper.news_collection)
            print("Top 10 Words:", top_10_words)
            news_scraper.plot_and_save_top_10_words(top_10_words)
            news_scraper.add_top_10_words_to_db(top_10_words)
            # print_grouped_data_by_update_date is optional function 
            user_input_thread = threading.Thread(target=get_user_input)
            user_input_thread.start()
            # Wait for 10 seconds or until the user input is received
            user_input_thread.join(timeout=10)
            # Check if user input is received
            if user_input_thread.is_alive():
                user_choice = '0'  # If no input received in 10 seconds, use default value (0)
                print("Default choice (0) selected as no input received.")
            
            if user_choice == '1':
                news_scraper.print_grouped_data_by_update_date(news_scraper.news_collection)
            elif user_choice != '0':
                print("Invalid input. Not running the function.")
        
            time.sleep(1200)  # Web scraping starts every 20 minutes

    except KeyboardInterrupt:
        for thread in threads_list:
                thread.join()
        print("Web scraping is stopping.")

