# **DAT comment scraper**

[**D**]*elfi* [**A**]*pollo* [**T**]*vnet* **comment scraper** is [Scrapy](http://scrapy.org/) based set of spiders
which collects comments from 3 major latvian news portals: [delfi.lv](http://www.delfi.lv/),
[apollo.lv](http://apollo.tvnet.lv/) and [tvnet.lv](http://www.tvnet.lv/)

## **Install**

1. Clone the repo
2. Install requirements

     `$ pip install -r requirements.txt`

   + for delfi.lv comments

       Install PhantomJS

       [Download](http://phantomjs.org/download.html)

       [How to install PhantomJS on Ubuntu](https://gist.github.com/julionc/7476620)

       [Install and configure PhantomJS](http://attester.ariatemplates.com/usage/phantom.html)


## **Usage**

`$ scrapy crawl <spider name>`


where `<spider name>` is  `delfi`, `apollo` or `tvnet`

dates can be passed to spider via `dfrom` and `dto` variables in format yyyy-mm-dd,
without arguments spider collects only todays comments

`$ scrapy crawl <spider name> -a dfrom=2016-01-01 -a dto=2016-02-01`

_in this example spider will run thru all dates from 2016-01-01 to 2016-02-01_

_[More info about Scrapy](http://doc.scrapy.org/en/latest/)_
