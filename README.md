# Restaurants Around
An easy way to analyze restaurants around you...

## How to Use:
1. Be sure to install of `./requirements.txt`. Works better inside a `venv`.
2. Modify `./scraper/location.txt` with `address`, `latitude` and `longitude` of your delivery address (home, office, etc.).
3. In your command line, run: `python3 ue_scraper.py location.txt` or `python3 rappi_scraper.py location.txt` to get two files, a `json` file with raw data containing all restaurant data and a `csv` file with data parsed. Feel free to modify `./scraper/parser/parser.py` if you want to include more columns from the `json` file.
4. Once data gather, execute the `./main/unique_restaurants.py` file to get a de-duplicated list of restaurants from Uber Eats and Rappi.

## Thinking Process
I describe the overall problem solving mindset I took to analyze restaurants registered in food delivery services (Uber Eats, Rappi). This works is divided in two pieces: 
- Get the data from public web sites
- Analyze information collected in previous step

### Create Dataset: Overall Steps
First we need to identify what restaurants are around us. Each food delivery site allow us to search in their web sites to submit an address and look for all possible and available restaurants in a certain radius. 

First approach was using the [Request](https://requests.readthedocs.io/en/master/) python library to handle POST and GET request to the page. No success for Uber Eats since web page loaded dynamically on scrolling. I decided to move using [Selenium](https://www.selenium.dev/).

#### 1. Search and learn
- Search for previous works around scraping data from food delivery services
- Go step by step and understand how Uber Eats web page works
#### 2. Experiment and fail
- Build a try-error notebook to explore methods, attributes and tricks for scraping
- Identify several way to tackle the problem and give priority to one or two options 
#### 3. FTW (in production)
- Having developed the logic for one case I was able to create a functional python script
- Ran successfully first scraper over UberEats page
#### 4. Replicate and scale
- Rappi was easy to scrap, they allow REST protocols. So I was able to get all information at once without reaching domain so many times.
- Parser was though really simple. Loads a json file from the scraper and transform it into a csv.

### Create Dataset: Deduplicate Restos
#### 1. The Obvious
- Assuming that a restaurant wishes to be easily identified it would correctly submit its information in each platform correctly. So, first action taken was directly match names among datasets.
#### 2. Name and Address
- Because the obvious isn’t always an option I tried to identify restaurants using their names and their directions. Some use cases can be: Food chain restaurants (McDonald’s (Zócalo) <> McDonalds (Centro)). Similar names (Tacos Paisa <> Tacos Paisano).
- To address previous point I used a [TF-IDF](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) statistic to calculate similarity between tokens built them from address and restaurant name
- An optimized TF-IDF algorithm (built by ING Analytics) was used to tackle this problem. Algorithm is best described [here](https://medium.com/wbaa/https-medium-com-ingwbaa-boosting-selection-of-the-most-similar-entities-in-large-scale-datasets-450b3242e618).
#### 3. Geolocation
- Mexico City has bad reputation when we talk about directions. You can give any address directions in several ways. Avenues and main streets can have more than one official name and this represented an issue for TF-IDF.
- In order to build restaurant tokens that provide more information to TF-IDF I used a hexagonal hierarchical geospatial indexing ([H3](https://github.com/uber/H3)) and assign location (latitude, longitude) to an specific geospatial polygon and used that information to help TF-IDF to better identify restaurants with the same address.

#### 4. Final Output
Combining all three approaches ended up with a unique list of restaurants reducing a initial list of 1,966 restaurants (Eats and Rappi) to 1,822 restaurants with 140 restaurants identified in both food delivery services.

## Resources
Some resources that helped me shape this project are listed next:

1. [Muhammad, SK](https://www.linkedin.com/in/msalikkhan/). _Uber Eats Scraper_. Github repository. December, 2018. [Link](https://github.com/salik95/Ubereats-Scraper).
2. [Yu, P](https://www.linkedin.com/in/paulynnyu/). _So You Want to Open a Ghost Kitchen_. January, 2020. [Link](https://towardsdatascience.com/so-you-want-to-open-a-ghost-kitchen-cc303cef5332).
3. [Mich, J](https://www.linkedin.com/in/john-mich-1333b733/). _How can we use Selenium Webdriver in Colab?_ Stack Overflow. June 2018. [Link](https://stackoverflow.com/questions/51046454/how-can-we-use-selenium-webdriver-in-colab-research-google-com).
4. [Baiju M](https://in.linkedin.com/in/baijum). _Locating Elements using Selenium. Selenium_. 1999. [Link](https://selenium-python.readthedocs.io/locating-elements.html).
[Li, S](https://www.linkedin.com/in/susanli/). _De-duplicate the Duplicate Records from Scratch_. Medium. October, 2019. [Link](https://requests.readthedocs.io/en/master/).
[Sun, Z](https://nl.linkedin.com/in/zhesun1984). _Boosting the selection of the most similar entities_. Medium. July, 2017. [Link](https://medium.com/wbaa/https-medium-com-ingwbaa-boosting-selection-of-the-most-similar-entities-in-large-scale-datasets-450b3242e618).
[Anonymous](https://codereview.stackexchange.com/users/42228/user3369309). _Finding the longest substring in common_. Stack Overflow. May, 2014. [Link](https://codereview.stackexchange.com/q/49752).

#### Updates
_(May 27) Update: I found out I was blocked from ubereats.com 😆so I won’t be able to reproduce scraper results. But that can be fixed easily with a new IP 😎._

