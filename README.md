# Scrapy Project
Simple project to follow links in a government site and download the PDFs with metadata.

This project expects that its run on Python >= 3.5.0 and make sure that the requirements for [scrapy](https://docs.scrapy.org/en/latest/index.html) is installed by running the below command:

```
pip install -r requirements.txt
```

To run the project please use the code below:
```
scrapy crawl gov_site -o pdf_meta_data.jl
```

This will save the output meta data of PDFs mentioned in the spider links in a [JL](http://jsonlines.org/) format in the root directory.  
The downloaded PDFs will be saved at location `scrapy_project/PDF_DUMP`, where the latter part of the path can be configured via variable `pdf_dump_location` defined in the [spider's](https://github.com/shreya-de/scrapy_project/blob/master/scrapy_project/spiders/gov_site.py#L6) file.

Regarding the meta of PDFs there is only 1 [URL](https://www.privacy.gov.ph/memorandum-circulars/) page having links to other pages which lists PDFs with a meta information.  
Such URLs are then followed by the spider and meta data is saved along with PDF.  
However at other URLs, only the PDFs is downloaded as there is as no meta data is available in a detailed way.
