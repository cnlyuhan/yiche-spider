import pymysql
import pickle
from .settings import carid_filepath


class CarproPipeline:

    def open_spider(self, spider):
        pass

    def process_item(self, item, spider):
        pass

    def close_spider(self, spider):
        pass


class mysqlPipeline(object):
    sql3 = "insert into brand values (%d, '%s', '%s')"
    sql4 = "insert into carItem values (%d, '%s', %f, %f, %f)"
    db = pymysql.connect(host='localhost', user='root', password='123456', port=3306, autocommit=True)
    cursor = db.cursor()

    def open_spider(self, spider):
        self.cursor.execute("create database if not exists yichedotcom;")
        self.cursor.execute("use yichedotcom;")
        sql1 = """
        create table if not exists brand (
            brandID int primary key,
            brandName varchar(20),
            brandURL  varchar(100)
        );
        """

        sql2 = """
                create table if not exists carItem (
                    carID int primary key,
                    carName varchar(100),
                    priceLow float,
                    priceHigh float,
                    rating float
                );
                """

        self.cursor.execute(sql1)
        self.cursor.execute(sql2)

    def process_item(self, item, spider):
        if item.__class__.__name__ == 'BrandItem':
            try:
                self.cursor.execute(self.sql3 % (item['brand_id'], item['brand_name'], item['brand_url']))
                # print(item['brand_name'], '插入成功！')
            except:
                pass
        else:
            try:
                self.cursor.execute(self.sql4 % (
                item['car_id'], item['car_name'], item['car_price_low'], item['car_price_high'], item['car_price_low']))
                print(item['car_name'], '插入成功')
            except Exception as e:
                print(e)
                # 插入不成功，从set中删除carid，表示此车没有爬取
                spider.carid_set.discard(item['car_id'])

            # pass
        return item

    def close_spider(self, spider):
        self.cursor.close()
        self.db.close()
        carid_set = spider.carid_set
        print('即将保存：', carid_set)
        print(len(carid_set))
        f = open(carid_filepath, 'wb')
        pickle.dump(carid_set, f)
        print("saved sucessfully")
        f.close()


"""
pymysql.err.IntegrityError: (1062, "Duplicate entry '694' for key 'brand.PRIMARY'")
"""
