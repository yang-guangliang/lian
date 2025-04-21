## **内存和文件系统（loader）**

为加强内存和文件的管理，尤其是避免内存不足问题，我们基于LRU（Least Recently Used）算法实现两层的内存管理，即item层和bundle层，并在bundle层实现了和本地硬盘的交互，即文件管理。