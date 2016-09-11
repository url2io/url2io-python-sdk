import sys; sys.path.append('..')
import url2io

api = url2io.API('demo')

print "get article"
ret = api.article(url='http://www.url2io.com/docs')
print ret.keys()

print "get article & next"
ret = {'next': 'http://tech.sina.com.cn/i/2010-08-18/19554560539.shtml'}
print 'get: ', ret.get('next')
while ret.get('next'):
    ret = api.article(url=ret.get('next'), fields=['next','text'])
    print 'next: ', ret.get('next')
