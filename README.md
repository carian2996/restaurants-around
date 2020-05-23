# Restaurants Around
An easy way to analyze restaurants around you...

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
- TODO: Once the first scraper was built, second one will be similar
- TODO: Parsing data (json) into a suitable format was an easy (but import) step

## Resources
Some resources that helped me shape this project are listed next:

1. [Muhammad, SK.](https://www.linkedin.com/in/msalikkhan/), Uber Eats Scraper. Github repository. December, 2018. [Link](https://github.com/salik95/Ubereats-Scraper).
2. [Yu, P.](https://www.linkedin.com/in/paulynnyu/), So You Want to Open a Ghost Kitchen. January, 2020. [Link](https://towardsdatascience.com/so-you-want-to-open-a-ghost-kitchen-cc303cef5332).
3. [Mich, J.](https://www.linkedin.com/in/john-mich-1333b733/) How can we use Selenium Webdriver in Colab? Stack Overflow. June 2018. [Link](https://stackoverflow.com/questions/51046454/how-can-we-use-selenium-webdriver-in-colab-research-google-com).
4. [Baiju M.](https://in.linkedin.com/in/baijum), Locating Elements using Selenium. Selenium. 1999. [Link](https://selenium-python.readthedocs.io/locating-elements.html).