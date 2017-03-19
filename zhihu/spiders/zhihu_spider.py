# -*- coding: UTF-8 -*-
import scrapy
import json
import re
import urllib

#用于删除所爬文字中带有的html符号的类
class Tool:
    #编译标记了图片及七个空格以及没有图片的情况的正则表达式
    removingImg = re.compile('<img.*?>| {7}|')
    #去链接标签
    removeAddr = re.compile('<a.*?>|</a>')
    #去段标签
    replaceLine = re.compile('<tr>|<div>|</div>|</p>')
    replaceTD = re.compile('<td>')
    replacePara = re.compile('<p.*?>')
    replaceBR = re.compile('<br><br>|<br>')
    removeExtraTag = re.compile('<.*?>')
    
    def replace(self,x):
        #sub为替换函数
        x = re.sub(self.removingImg , "" , x)
        x = re.sub(self.removeAddr, "" , x)
        x = re.sub(self.replaceLine,"\n" , x)
        x = re.sub(self.replaceTD , "\t" , x)
        x = re.sub(self.replacePara , "\n  ",x)
        x = re.sub(self.replaceBR , "\n" , x)
        x = re.sub(self.removeExtraTag , "" , x)
        # strip可用于把句子前后的空白去掉
        return x.strip()


class ZhihuSpider(scrapy.Spider):
    tool = Tool()
    name = "zhihu"
    headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch, br",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type":" application/x-www-form-urlencoded; charset=UTF-8",
            'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0",
            'Host': "www.zhihu.com",
            "Upgrade-Insecure-Requests": '1',
            'Referer': "http://www.zhihu.com/",
            }
    searchWord = urllib.quote('魏则西')
    searchUrl = "https://www.zhihu.com" + "/r/search?q=" + searchWord + '&type=content&offset=0'
    # 找到的url都放在这个空列表里
    searchedUrl = []
    
    
    def start_requests(self):
        urls = [
            'https://www.zhihu.com/login/email',
        ]
        parameters = '''/answers?include=data%5B*%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset=3&limit=40&sort_by=default'''
        userAgen = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        for url in urls:
            yield scrapy.Request(url=url, meta = {'cookiejar' : 1}, headers=self.headers, callback=self.parse)
            
            
    def parse(self, response):
        xsrf = scrapy.Selector(response).xpath('//input[@name="_xsrf"]/@value').extract()[0]
        url = 'https://www.zhihu.com/login/email'
        
        yield scrapy.FormRequest.from_response(response, url=url, headers = self.headers, meta={'cookiejar': response.meta['cookiejar']}, formdata={'_xsrf': xsrf, 'email': '306235911@qq.com', 'password': '7b6a5z10b'}, callback=self.parse_after)

    # 用于获得搜索页面
    def parse_after(self, response):
        url = self.searchUrl
        # 下面的offset貌似是从第几个答案开始爬
        yield scrapy.Request(url, meta={'cookiejar': response.meta['cookiejar']}, headers=self.headers, callback=self.question_parse)
    
    # 用于迭代生成问题列表    
    def question_parse(self, response):
        pattern = re.compile('a target=\"_blank\" href=\"/question(.+?)"' , re.S)
        questions = json.loads(response.body.decode('utf-8'))
        
        next_url = questions['paging']['next']
        
        items = re.findall(pattern , str(questions['htmls']))
        parameters = '''/answers?include=data%5B*%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset=0&limit=20&sort_by=default'''
        if items:
            for item in items:
                content = self.tool.replace(item)
                self.searchedUrl.append(content.encode('utf-8'))
        print self.searchedUrl
        print next_url
        if next_url != '':
            next_search_url = 'https://www.zhihu.com' + next_url
            yield scrapy.Request(next_search_url, meta={'cookiejar': response.meta['cookiejar']}, headers=self.headers, callback=self.question_parse)
        else:
            print '11111111111111111'
            yield scrapy.Request(url = "https://www.zhihu.com/topic", meta={'cookiejar': response.meta['cookiejar']}, headers=self.headers, callback=self.content)
            
    def content(self, response):
        parameters = '''/answers?include=data%5B*%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset=0&limit=20&sort_by=default'''
        for i in self.searchedUrl:
            url = 'https://www.zhihu.com/api/v4/questions' + i + parameters
            yield scrapy.Request(url, meta={'cookiejar': response.meta['cookiejar']}, headers=self.headers, callback=self.last_parse)
        
        
    def last_parse(self, response):
         # 定义要写入的文件名
        filename = "zhihu.txt"
        # 在文件打开的状态下进行以下操作
        with open(filename, 'a') as f:
            pattern = re.compile("editable_content': u'(.+?)', u'" , re.S)
            questions = json.loads(response.body.decode('utf-8'))
            
            next_url = questions['paging']['next']
            totals = questions['paging']['totals']
            
            items = re.findall(pattern , str(questions['data']))
            contents = []
            for item in items:
                content = "\n" + self.tool.replace(item) + "\n"
                contents.append(content.encode('utf-8'))
            
            pattern2 = re.compile("offset=(\d+)" , re.S)
            now_offset = re.search(pattern2 , next_url).group(1).strip()
            print now_offset
            
            for i in contents:
                a = i.decode("unicode-escape")
                f.write(a.encode('utf-8'))
                
        if questions['data'] != []:
            yield scrapy.Request(next_url, meta={'cookiejar': response.meta['cookiejar']}, headers=self.headers, callback=self.last_parse)
        else:
            print 'done'

                
