# **DAT comment scraper**

**D** *[elfi]* **A** *[pollo]* **T** *[vnet]* comment scraper is [Scrapy](http://scrapy.org/) based set of spiders
which collects comments from 3 major latvian news portals: [delfi.lv](http://www.delfi.lv/),
[apollo.lv](http://apollo.tvnet.lv/) and [tvnet.lv](http://www.tvnet.lv/)

## **Install**

1. Clone the repo
2. Install requirements

     `$ pip install -r requirements.txt`

   + for delfi.lv comments
     + `$ docker pull scrapinghub/splash`
     + `$ docker run -p 8050:8050 scrapinghub/splash`

     + change `SPLASH_URL` variable in `comment_scraper/settings.py` to point to your docker instance with splash. In case of _localhost_ to:

            SPLASH_URL = 'http://127.0.0.1:8050'



  _More info
    [here (ScrapyJS)](https://github.com/scrapinghub/scrapy-splash) and
    [here (Splash)](http://splash.readthedocs.org/en/latest/install.html)_

## **Usage**

`$ scrapy crawl <spider name>`

where <spider name\> is  `delfi`, `apollo` or `tvnet`

dates can be passed to spider via `dfrom` and `dto` variables in format yyyy-mm-dd,
without arguments spider collects only todays comments

`$ scrapy crawl <spider name> -a dfrom=2016-01-01 -a dto=2016-02-01`

_in this example spider will run thru all dates from 2016-01-01 to 2016-02-01_

_[More info about Scrapy](http://doc.scrapy.org/en/latest/)_