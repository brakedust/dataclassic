# try:
#     import ujson as json
# except ImportError:
import json

import zlib
# import pickle
# from collections import OrderedDict

class JsonEncoder(object):
    """
    A json string encoder
    """

    def __init__(self, **kwargs):
        #self.encode_args = kwargs
        self._decoder = json.JSONDecoder()
        self._encoder = json.JSONEncoder(**kwargs)

    def encode(self, val):
        """
        encodes a dict/list object to a json string
        :param val: the value to encode
        """
        #return json.dumps(val, **self.encode_args)
        return self._encoder.encode(val)

    def decode(self, val):
        """
        Decodes a json string into a dict/list object
        :param val: the value to decode
        """
        #return json.loads(val)

        return self._decoder.decode(val)


class ZlibEncoder(object):
    """
    A zlib compressed json string encoded
    """

    def __init__(self, base_encoder=JsonEncoder):
        """
        :param base_encoder: The encoder whose ouput will be compressed
        """
        self.base_encoder = base_encoder()

    def encode(self, val):
        enc_val = self.base_encoder.encode(val).encode('utf-8')
        #enc_val =json.dumps(val)
        #enc_val = enc_val.encode('utf-8')
        return zlib.compress(enc_val)
        #return zlib.compress(json.dumps(val).encode('utf-8'))


    def decode(self, val):

        val = zlib.decompress(val)
        val = val.decode('utf-8')
        return self.base_encoder.decode(val)


        #return json.loads(zlib.decompress(val)).decode('utf-8')


# class PickleEncoder(object):
#     """
#     A pickle based encoder - probably don't use this one
#     """

#     def __init__(self, **kwargs):
#         self.encode_args = kwargs

#     def encode(self, val):
#         """
#         encodes a dict/list object to a json string
#         """
#         return pickle.dumps(val, **self.encode_args)

#     def decode(self, val):
#         """
#         Decodes a json string into a dict/list object
#         """
#         return pickle.loads(val)
