# -*- coding: utf-8 -*-
'''
# Created on Jan-10-20 17:49 
# delegate.py
# @author: 
'''

# 一个key只对应一个函数
# 修改：不考虑效率，全部用下面的Delagte实现
# class DelegateOne():
#     DICT = {}

#     @staticmethod
#     def set_listener(name, method):
#         DelegateOne.DICT[name] = method

#     @staticmethod
#     def remove_listener(name):
#         if name in DelegateOne.DICT:
#             del DelegateOne.DICT[name]

#     @staticmethod
#     def call(name, *args):
#         if name in DelegateOne.DICT:
#             return (DelegateOne.DICT[name])(*args)


# 一个key可以对应多个回调函数
class Delegate:
    """
    消息代理
    """
    DICT = {}

    @staticmethod
    def add_listener(name, method):
        if name in Delegate.DICT:
            # 重复添加检测
            for item in Delegate.DICT[name]:
                if item == method:
                    print('重复添加，忽略')
                    return
            # print('多重代理')
            Delegate.DICT[name].append(method)
        else:
            # print('首次代理')
            mds = [method]
            Delegate.DICT[name] = mds

    @staticmethod
    def call(name, *args):
        if name in Delegate.DICT:
            rst = None
            if args is None:
                for func in Delegate.DICT[name]:
                    rst = func()
            else:
                for func in Delegate.DICT[name]:
                    rst = func(*args)
            return rst

    @staticmethod
    def broadcast(name, *args):
        if name in Delegate.DICT:
            if args is None:
                for func in Delegate.DICT[name]:
                    func()
            else:
                for func in Delegate.DICT[name]:
                    func(*args)



if __name__ == '__main__':
    class Test:
        def hello2(self, a, b):
            print('hello, ' + a + ',' + b)

        def hello(self):
            print('only hello')

        def hello1(self, a):
            print('hello1,' + a)
            return 'rturn hello1'


    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    tst = Test()
    Delegate.add_listener('0', tst.hello)
    Delegate.add_listener('1', tst.hello1)
    Delegate.add_listener('2', tst.hello2)

    print(Delegate.call('0'))
    print(Delegate.call('1', 'hello'))
    print(Delegate.call('2', 'df', 'dfa'))
    print(Delegate.call('shit'))

    print('Delegate One----')
    DelegateOne.set_listener('0', tst.hello1)
    print(DelegateOne.call('0', 'jason'))
