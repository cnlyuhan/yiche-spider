# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BrandItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    brand_name = scrapy.Field()
    brand_url = scrapy.Field()
    brand_id = scrapy.Field()

class CarItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    car_name = scrapy.Field()
    car_id = scrapy.Field()
    car_price_high = scrapy.Field()
    car_price_low = scrapy.Field()
    car_rating = scrapy.Field()
