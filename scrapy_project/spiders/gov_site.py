import scrapy, os


class Spider(scrapy.Spider):
    name = "gov_site"
    pdf_dump_location = "PDF_DUMPS"

    def start_requests(self):
        self.start_urls = [
            "https://www.privacy.gov.ph/data-privacy-act-primer/",
            "https://www.privacy.gov.ph/memorandum-circulars/",
            "https://www.privacy.gov.ph/advisories/",
            "https://www.privacy.gov.ph/advisory-opinions/",
            "https://www.privacy.gov.ph/commission-issued-orders/"
        ]
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, meta={'source_url': 'index'})


    def followedPageTdTextExtractor(self, td_tag):
        # Special function to extract text available in the meta tags for PDF which available in the followed pages
        text_parts = td_tag.css('::text').getall()
        text_string = "".join(text_parts).strip()
        return text_string


    def isUrlForPDF(self, url):
        # Checks if the given URL is for PDF download
        return url.strip().lower().endswith(".pdf")


    def getCleanURL(self, response):
        # The base part of URL is sometimes used to save data in folder.
        # Hence we need to clean "/" occuring at the right end, otherwise the base part of URL will become empty.
        return response.url.strip().rstrip("/")


    def savePDFFile(self, response):
        # Get absolute path to save the PDF. We had explicitly passed "source_url" via the callback to save the PDF files in an organized way
        curr_pdf_folder = os.path.join(self.pdf_dump_location, os.path.basename(response.meta['source_url']))
        pdf_name = os.path.basename(response.url)
        if not os.path.exists(curr_pdf_folder):
            os.makedirs(curr_pdf_folder)

        abs_path = os.path.join(curr_pdf_folder, pdf_name)
        self.logger.info('Saving PDF %s | Found on page: %s' % (abs_path[-10:], response.meta['source_url']))
        with open(abs_path, 'wb') as f:
            f.write(response.body)


    def parse(self, response):
        self.logger.info('Crawling page: %s' % response.url)

        if response.url == "https://www.privacy.gov.ph/memorandum-circulars/":
            # Above URL was found to have page links that had meta tags for PDF. Hence follow is by passing an extra variable: "extract_pdf_with_meta"
            # This variable will later be used in "Case II" mentioned aftrer few lines below.
            follow_urls = response.css("section.news_content a::attr(href)").getall()
            if follow_urls is not None:
                for url in follow_urls:
                    yield response.follow(url, callback=self.parse, meta={'extract_pdf_with_meta': True, 'source_url': self.getCleanURL(response)})

        elif response.url in self.start_urls:
            # Download PDF's available on other mentioned pages
            all_urls_in_page = response.css("a::attr(href)").getall()
            pdf_urls = list(filter(self.isUrlForPDF, all_urls_in_page))
            for url in pdf_urls:
                yield response.follow(url, callback=self.parse, meta={'source_url': response.url})

        '''
        Control coming below can belong to 3 cases:
            CASE I  : It's a PDF url which needs to be downloaded
            CASE II : It came after following a parent URL and having "meta_data" which needs to be saved and PDF will be downloaded
            CASE III: It was a general continuation after "yield" statement
        '''

        # Corresponds to CASE I
        if self.isUrlForPDF(response.url):
            self.savePDFFile(response)

        # Corresponds to CASE II
        elif response.meta.get('extract_pdf_with_meta'):
            tr_tags_array = response.xpath("/html/body/div[1]/section[2]/div/div/table[1]/tbody/tr")
            meta_data = {
                'pdf_parent_url': response.url
            }
            if tr_tags_array is not None:
                for tr_tags in tr_tags_array:
                    td_tags = tr_tags.css("td")
                    # After analyzing HTML, it was found that 1st TD is for key, 2nd is a separator and 3rd is for value
                    meta_key = self.followedPageTdTextExtractor(td_tags[0])
                    meta_value = self.followedPageTdTextExtractor(td_tags[2])
                    meta_data[meta_key] = meta_value
                    if meta_key == 'pdf version':
                        # There is an extra data that can be saved for meta key "pdf version", i.e. the URL of the PDF
                        pdf_url = td_tags[2].css('a::attr(href)').get().strip()
                        self.logger.info('Saving PDF metadata %s | Found on page: %s' % (pdf_url[-10:], response.url))
                        meta_data['pdf_url'] = pdf_url
                        # Dowload the PDF as well
                        yield response.follow(pdf_url, callback=self.parse, meta={'source_url': self.getCleanURL(response)})
            yield meta_data

        # Corresponds to CASE III
        else:
            pass