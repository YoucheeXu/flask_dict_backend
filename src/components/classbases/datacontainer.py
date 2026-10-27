#!/usr/bin/python3


class Stack:
    """ 后进先出
    """
    def __init__(self):
        self.__data_list: list[object] = []
    def push(self, x: object):
        self.__data_list.append(x)
    def pop(self):
        if self.is_empty():
            raise IndexError("stack is empty")
        return self.__data_list.pop()
    def get_size(self):
        return len(self.__data_list)
    def is_empty(self):
        return len(self.__data_list) == 0

class Queue:
    """ 先进先出
    """
    def __init__(self):
        self.__data_list: list[object] = []
    def enqueue(self, x: object):
        """ 入队操作

        Args:
            x (object): _description_
        """
        self.__data_list.append(x)
    def dequeue(self):
        """ 出队操作

        Raises:
            IndexError: _description_

        Returns:
            _type_: _description_
        """
        if self.is_empty():
            raise IndexError("queue is empty")
        return self.__data_list.pop(0)
    def get_size(self):
        return len(self.__data_list)
    def is_empty(self):
        return len(self.__data_list) == 0
