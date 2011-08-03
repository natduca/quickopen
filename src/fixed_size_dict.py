# Copyright 2011 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
class _LinkedListNode(object):
  def __init__(self, d):
    self.prev = None
    self.next = None
    self.data = d

  def __repr__(self):
    if self.prev:
      pd = self.prev.data
    else:
      pd = "None"
    if self.next:
      nd = self.next.data
    else:
      nd = "None"
    
    return "(prev=%s, %s, next=%s)" % (pd, self.data, nd)

class _LinkedList(object):
  def __init__(self):
    self.head = None
    self.tail = None

  def as_list(self):
    if not self.head:
      return []
    n = self.head
    ret = []
    while n:
      ret.append(n.data)
      n = n.next
    return ret

  def __repr__(self):
    return 'LinkedList(%s)' % ",".join([repr(x) for x in self.as_list()])

  def insert_front(self, d):
    if self.head == None:
      if isinstance(d, _LinkedListNode):
        node = d
      else:
        node = _LinkedListNode(d)
      self.head = node
      self.tail  = node
      node.prev = None
      node.next = None
      return node
    else:
      return self.insertBefore(self.head, d)

  def insert_before(self, node, d):
    if isinstance(d, _LinkedListNode):
      new_node = d
    else:
      new_node = _LinkedListNode(d)
    new_node.prev = node.prev
    new_node.next = node
    if node.prev == None:
      self.head = new_node
    else:
      node.prev.next = new_node
    node.prev = new_node
    return new_node

  def insert_after(self, node, d):
    if isinstance(d, _LinkedListNode):
      new_node = d
    else:
      new_node = _LinkedListNode(d)
    new_node.prev = node
    new_node.next = node.next
    if node.next == None:
      self.tail = new_node
    else:
      node.next.prev = new_node
    node.next = new_node
    return new_node

  def append(self, d):      
    if self.tail == None:
      return self.insert_front(d)
    else:
      return self.insert_after(self.tail, d)

  def remove(self, n):
    if n.prev == None:
      self.head = n.next
    else:
      n.prev.next = n.next

    if n.next == None:
       self.tail = n.prev
    else:
       n.next.prev = n.prev
    n.next = None
    n.prev = None

  def move_to_back(self, n):
    self.remove(n)
    n_ = self.append(n)
    assert n_ == n



class FixedSizeDict(object):
  def __init__(self, max_size):
    self._max_size = max_size
    self._dict = dict()
    self._lru = _LinkedList()

  def __repr__(self):
    keys = self._lru.as_list()
    keys.reverse()

    a = []
    for k in keys:
      a.append( (k, self._dict[k][1]))
    return repr(a)

  def __setitem__(self, k, v):
    if k not in self._dict:
      if len(self._dict) == self._max_size:
        n_to_evict = self._lru.head
        self._lru.remove(n_to_evict)
#        print "evicting ", n_to_evict.data
        del self._dict[n_to_evict.data]
      else:
        pass
#        print "adding", k
      n = self._lru.append(k)
      self._dict[k] = (n, v)
#      print repr(self._lru)
    else:
      t = self._dict[k]
#      print "renewing ", k
      self._lru.move_to_back(t[0])
#      print repr(self._lru)
      self._dict[k] = (t[0], v)

  def __getitem__(self, k):
    t = self._dict[k]
#    print "renewing ", k
    self._lru.move_to_back(t[0])
#    print repr(self._lru)
    return t[1]

  def __contains__(self, k):
    return k in self._dict

  def __delitem__(self, k):
    t = self._dict[k]
    self._lru.remove(t[0])
    del self._dict[k]
