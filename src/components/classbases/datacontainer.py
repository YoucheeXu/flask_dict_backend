#!/usr/bin/python3
# -*- coding: utf-8 -*-

# 后进先出
class Stack():
    def __init__(self):
        self.__data_list = []
    def push(self, x):
        self.__data_list.append(x)
    def pop(self):
        if self.is_empty():
            raise IndexError("stack is empty")
        return self.__data_list.pop()
    def get_size(self):
        return len(self.__data_list)
    def is_empty(self):
        return len(self.__data_list) == 0

# 先进先出
class Queue():
    def __init__(self):
        self.__data_list = []
    def enqueue(self, x):    # 入队操作
        self.__data_list.append(x)
    def dequeue(self):    # 出队操作
        if self.is_empty():
            raise IndexError("queue is empty")
        return self.__data_list.pop(0)
    def get_size(self):
        return len(self.__data_list)
    def is_empty(self):
        return len(self.__data_list) == 0
