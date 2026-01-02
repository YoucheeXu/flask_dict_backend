#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
modified from
https://github.com/csarron/mdict-analysis

"""
import re
import struct
from io import BytesIO, BufferedIOBase
# zlib compression is used for engine version >=2.0
import zlib
from typing import cast

# pip install python3-lzo-indexer
# pip install python-lzo
# LZO compression is used for engine version < 2.0
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo
try:
    import lzo
except ImportError:
    lzo = None
    print("LZO compression support is not available")
# try:
    # import xml.etree.cElementTree as ET
# except ImportError:
import xml.etree.ElementTree as ET

from src.components.classbases.utils.ripemd128 import ripemd128
from src.components.classbases.utils.pureSalsa20 import Salsa20


class MdPackage:
    ''' read from mdd, mdx
    '''
    def __init__(self, srcfile: str, is_mdd: bool = False, encoding: str = 'UTF-16',
            passcode: tuple[bytes, str] | None = None):
        self._file_pos: int = 0

        self._version: float = 0
        self._is_substyle: bool = False

        self._encrypt: int = 0

        self._stylesheet = {}
        # def _recordBlockOffset: any
        self._num_format: str = ">I"
        self._width_num: int = 4

        # def _keyBlockOffset: any
        self._entries_num: int = 0

        self._wigdth_num: int = 0

        self._keyblock_list: list[tuple[int, bytes]] = []
        self._key_list: list[str] = []
        # <word, [record_strt, record_end, compressblock_strt, compressed_size, decompressed_size]>
        self._record_dict: dict[str, tuple[int, int, int, int, int]] = {}

        self._header_tag: dict[str, str] = {}
        self._srcfile: str = srcfile
        self._is_mdd: bool = is_mdd
        self._encoding: str = encoding.upper()
        self._passcode = passcode

    def open(self):
        print(f"open {self._srcfile}")
        self._header_tag = self._read_header()
        # print('Finish to __read_header')

        self._keyblock_list = self._read_keyblocks()
        # print('Finish to __read_keyblocks')

        if self._is_mdd:
            self._decode_mdd_recordblock()
            # print('Finish to __decode_mdd_recordblock')
        else:
            self._decode_mdx_recordblock()
            # print('Finish to __decode_mdx_recordblock')

        self._key_list = list(self._record_dict.keys())

    def has_record(self, key: str):
        return key in self._key_list

    def read_record(self, key: str) -> tuple[int, str]:
        if key in self._key_list:
            record_strt, record_end, compressblock_strt, \
                compressblk_size, decompress_size = self._record_dict[key]
        else:
            return -1, f"There is no {key} in {self._srcfile}"

        with open(self._srcfile, 'rb') as f:
            _ = f.seek(compressblock_strt)
            recordblock_compressed = f.read(compressblk_size)
            # 4 bytes indicates block compression type
            recordblock_type = recordblock_compressed[:4]
            # 4 bytes adler checksum in uncompressed content
            adler32 = cast(int, struct.unpack('>I', recordblock_compressed[4:8])[0])
            # print(f"adler32: {adler32}")

            # record_block: Buffer
            record_block = self._decompress(recordblock_type,
                recordblock_compressed, decompress_size)

            # notice that adler32 return signed value
            assert adler32 == zlib.adler32(record_block) & 0xffffffff

            assert len(record_block) == decompress_size

            record = record_block[record_strt: record_end]
            # convert to utf-8
            record = record.decode(self._encoding, errors = 'ignore').strip('\x00')
            # substitute styles
            if self._is_substyle and self._stylesheet:
                record = self._substitute_stylesheet(record)

            return 1, record

    def search_record(self, word_list: list[str], pattern: str, limit: int) -> int:
        regexp = re.compile(pattern)
        i = 0
        for key in self._key_list:
            match = re.search(regexp, key)
            if match:
                word_list.append(key)
                i += 1
            if i > limit:
                break

        return len(word_list)

    def check_addrecord(self, word: str, record: str) -> tuple[int, str]:
        raise NotImplementedError(f"Don't support to add record: {word}, {record}")

    def del_record(self, word: str) -> bool:
        raise NotImplementedError("Don't support to delete word: " + word)

    def close(self) -> bool:
        return True

    def _read_header(self):
        with open(self._srcfile, "rb") as f:
            # number of bytes of header text, big-endian, integer
            headersize_bytes = f.read(4)
            # print(f"sizeOfHeaderRaw = {headersize_bytes.join()}")

            header_size = cast(int, struct.unpack(">I", headersize_bytes)[0])
            # print(f"header_size = {header_size}")

            header_bytes = f.read(header_size)

            # 4 bytes: adler32 checksum in header, in little endian
            adler32_bytes = f.read(4)
            # print(f"adler32Raw = { adler32_bytes.join() }")
            adler32 = cast(int, struct.unpack("<I", adler32_bytes)[0])
            # print(f"adler32 = { adler32 }")
            assert adler32 == zlib.adler32(header_bytes) & 0xffffffff
            # mark down key block offset
            self._file_pos = f.tell()

        # header text in utf-16 encoding ending with '\x00\x00'
        header_text = header_bytes[:-2].decode('utf-16')
        # print(f"header_text = {header_text}")
        header_tags = self._parse_header(header_text)
        if not header_tags:
            raise RuntimeError("Fail to decode header_tags in " + self._srcfile)
        # print(header_tags)

        if not self._encoding:
            encoding = header_tags["Encoding"]
            if encoding in ['GBK', 'GB2312']:
                encoding = 'GB18030'
            self._encoding = encoding
        # print(f"Encoding = { self.__encoding }")

        # encryption flag
        #   0x00 - no encryption
        #   0x01 - encrypt record block
        #   0x02 - encrypt key info block
        if 'Encrypted' not in header_tags or header_tags['Encrypted'] == 'No':
            self._encrypt = 0
        elif header_tags['Encrypted'] == 'Yes':
            self._encrypt = 1
        else:
            self._encrypt = int(header_tags['Encrypted'])
        # print(f"Encrypted: { self.__encrypt }")

        # stylesheet attribute if present takes form of:
        #   style_number # 1-255
        #   style_begin  # or ''
        #   style_end    # or ''
        # store stylesheet in dict in the form of {'number' : ('style_begin', 'style_end')}
        if header_tags.get('StyleSheet'):
            lines = header_tags['StyleSheet'].splitlines()
            for i in range(0, len(lines), 3):
                self._stylesheet[lines[i]] = (lines[i+1], lines[i+2])
            self._is_substyle = True
        else:
            self._is_substyle = False
        # print("stylesheet = " + str(self.__stylesheet))

        self._version = float(header_tags['GeneratedByEngineVersion'])
        # print(f"version in Dict = { self.__version }")

        # before version 2.0, number is 4 bytes integer
        # version 2.0 and above uses 8 bytes
        if self._version < 2.0:
            self._width_num = 4
            self._num_format = '>I'
        else:
            self._width_num = 8
            self._num_format = '>Q'

        return header_tags

    def _salsa_decrypt(self, cipher_text: bytes, encrypt_key: bytes):
        temp = b"\x00" * 8
        s20 = Salsa20(encrypt_key, temp, 8)
        print(f"ciphertext: {cipher_text}, encrypt_key: {encrypt_key}")
        return s20.encrypt_bytes(cipher_text)

    def _decrypt_regcode_by_deviceid(self, reg_code: bytes, deviceid: str):
        deviceid_digest = ripemd128(deviceid)
        temp = b"\x00" * 8
        s20 = Salsa20(deviceid_digest, temp, 8)
        encrypt_key = s20.encrypt_bytes(reg_code)
        return encrypt_key

    def _decrypt_regcode_by_email(self, reg_code: bytes, email: str) -> bytes:
        email_digest = ripemd128(email.decode().encode('utf-16-le'))
        temp = b"\x00" * 8
        s20 = Salsa20(email_digest, temp, 8)
        encrypt_key = s20.encrypt_bytes(reg_code)
        return encrypt_key

    def _read_keyblocks(self):
        with open(self._srcfile, 'rb') as f:
            _ = f.seek(self._file_pos)

            # the following numbers could be encrypted
            if self._version >= 2.0:
                bytes_num = self._width_num * 5
            else:
                bytes_num = self._width_num * 4

            block = f.read(bytes_num)

            if self._encrypt & 1:
                if self._passcode is None:
                    raise RuntimeError('user identification is needed to read encrypted file')
                # regcode, userid
                regcode, userid = self._passcode
                # if isinstance(userid, unicode):
                    # userid = userid.encode('utf8')

                if self._header_tag['RegisterBy'] == 'EMail':
                    encrypted_key = self._decrypt_regcode_by_email(regcode, userid)
                else:
                    encrypted_key = self._decrypt_regcode_by_deviceid(regcode, userid)

                block = self._salsa_decrypt(block, encrypted_key)

            # decode self block
            sf = BytesIO(block)

            # number in key blocks
            keyblocks_num = self._read_number(sf)
            # print(f"int in Key Blocks = {keyblocks_num}")

            # number in entries
            self._entries_num = self._read_number(sf)
            # print(f"number of Entries = {self.__entries_num}")

            # number in bytes in key block info after decompression
            keyblockinfodecomp_size: int = 0
            if self._version >= 2.0:
                # int in Bytes After __decompression
                keyblockinfodecomp_size = self._read_number(sf)
                # print(f"number of key block info After decompression = {keyblockinfodecomp_size} bytes")

            # number in bytes in key block info
            keyblockinfo_size = self._read_number(sf)
            # print(f"int in bytes in key block info = { keyblockinfo_size }")

            # int in bytes in key block
            keyblock_size = self._read_number(sf)
            # print(f"int in bytes in key block = {keyblock_size}")

            # 4 bytes: adler checksum in previous 5 numbers
            if self._version >= 2.0:
                adler32 = cast(int, struct.unpack('>I', f.read(4))[0])
                # print(f"adler checksum in previous 5 ints = {adler32}")
                assert adler32 == zlib.adler32(block) & 0xffffffff

            # read key block info
            # which indicates key block's compressed and decompressed size
            keyblock_info = f.read(keyblockinfo_size)
            keyblockinfo_list = self._decord_keyblockinfo(keyblock_info,
                keyblockinfodecomp_size)
            # print('Finish to __decord_keyblockinfo')
            assert keyblocks_num == len(keyblockinfo_list)

            # read key block
            keyblock_compressed = f.read(keyblock_size)
            # print(f"keyblock_compressed = {keyblock_compressed.join()}")

            # extract key block
            keyblock_list = self._decode_keyblocks(keyblock_compressed, keyblockinfo_list)

            self._file_pos = f.tell()

        return keyblock_list

    def _parse_header(self, header_text: str) -> dict[str, str]:
        ''' extract attributes from <Dict attr="value" ... >
        '''
        root = ET.fromstring(header_text)

        return root.attrib

    # def __read_buffer(self, len: int, offset?: int) -> Buffer:
        # buf = Buffer.alloc(len)
        # pos: any
        # if offset:
            # pos = offset
        # else:
            # pos = null
            # self.__file_pos += len
        # num = fs.readSync(f, buf, 0, len, pos)
        # assert(num == len)
        # return buf

    def _read_number(self, f: BufferedIOBase) -> int:
        data = f.read(self._width_num)
        num = cast(int, struct.unpack(self._num_format, data)[0])
        return num

    def _decord_keyblockinfo(self, keyblockinfo_compressed: bytes,
            keyblockinfodecomp_size: int):
        if self._version >= 2:
            # zlib compression
            compr_type = keyblockinfo_compressed[:4]
            # print(f"Type in compression in keyblock_info = { compr_type }")
            assert compr_type == b'\x02\x00\x00\x00'
            # decrypt if needed
            if self._encrypt & 0x02:
                keyblockinfo_compressed = self._mdx_decrypt(keyblockinfo_compressed)

            # print(f"keyblockinfo_compressed = {keyblockinfo_compressed.join()}")
            keyblock_info = self._decompress(compr_type,
                keyblockinfo_compressed, keyblockinfodecomp_size)
            # print(f"keyblock_info = {keyblock_info}")

            # adler checksum
            adler32 = cast(int, struct.unpack('>I', keyblockinfo_compressed[4:8])[0])
            # print(f"adler32 in keyblock_info = {adler32}")
            assert adler32 == zlib.adler32(keyblock_info) & 0xffffffff
        else:
            # no compression and encrypt
            keyblock_info = keyblockinfo_compressed

        # keyblkinfo_text = ''.join(map(lambda x:(',') + str(x), keyblock_info))
        # print('keyBlockInfo =', keyblkinfo_text)
        # decode # [keyblockcompressed_size, keyblockdecompressed_size]
        keyblockinfo_list: list[tuple[int, int]] = []
        entries_num: int = 0
        i: int = 0
        if self._version >= 2:
            byte_format = '>H'
            byte_width = 2
            textterm_size = 1
        else:
            byte_format = '>B'
            byte_width = 1
            textterm_size = 0

        keyblkinfo_len = len(keyblock_info)
        # print(f"keyblkinfo_len = {keyblkinfo_len}")
        while i < keyblkinfo_len:
            # number in entries in current key block
            entries_num += cast(int, struct.unpack(self._num_format,
                keyblock_info[i: i+self._width_num])[0])
            # print(f"entries_num: {entries_num}")
            i += self._width_num
            # text head size
            # print(f"byte_format: {byte_format}")
            # print(f"strt: {i}, end: {i + byte_width}")
            texthead_size = cast(int, struct.unpack(byte_format,
                keyblock_info[i: i+byte_width])[0])
            # print(f"texthead_size: {texthead_size}")
            i += byte_width
            # text head
            if self._encoding != 'UTF-16':
                i += texthead_size + textterm_size
            else:
                i += (texthead_size + textterm_size) * 2
            # text tail size
            texttail_size = cast(int, struct.unpack(byte_format, keyblock_info[i: i+byte_width])[0])
            # print(f"texttail_size: {texttail_size}")
            i += byte_width
            # text tail
            if self._encoding != 'UTF-16':
                i += texttail_size + textterm_size
            else:
                i += (texttail_size + textterm_size) * 2

            # print(f"self.__num_format: {self.__num_format}")

            # key block compressed size
            keyblockcompressed_size = cast(int, struct.unpack(self._num_format,
                keyblock_info[i:i+self._width_num])[0])
            # print(f"keyblockcompressed_size: {keyblockcompressed_size}")
            i += self._width_num
            # key block decompressed size
            keyblockdecompressed_size = cast(int, struct.unpack(self._num_format,
                keyblock_info[i:i+self._width_num])[0])
            # print(f"keyblockdecompressed_size: {keyblockdecompressed_size}")
            i += self._width_num

            keyblockinfo_list += [(keyblockcompressed_size, keyblockdecompressed_size)]
            # assert(entries_num == self.__entries_num)
        # print(f"keyblockinfo_list = { keyblockinfo_list }")
        return keyblockinfo_list

    def _fast_decrypt(self, data: bytes, key: bytes) -> bytes:
        b = bytearray(data)
        key_ary = bytearray(key)
        previous = 0x36
        for i in range(len(b)):
            t = (b[i] >> 4 | b[i] << 4) & 0xff
            t = t ^ previous ^ (i & 0xff) ^ key_ary[i % len(key_ary)]
            previous = b[i]
            b[i] = t
        bb = bytes(b)
        bbb = ''.join(map(lambda x:(',') + str(x), bb))
        # print('FastDecrypt =', bbb)
        return bb

    def _mdx_decrypt(self, comp_block: bytes):
        tail = struct.pack(b'<L', 0x3695)
        # print('Tail of key of compBlock =', tail)
        msg = comp_block[4:8]
        # print('msg =', str(msg))
        key = ripemd128(msg + tail)
        # key_text = ''.join(map(lambda x:(',0x' if len(hex(x))>=4 else ',0x0') + hex(x)[2:], key))
        key_text = ''.join(map(lambda x:(',') + str(x), key))
        # print('Key of compBlock =', key_text)
        return comp_block[0:8] + self._fast_decrypt(comp_block[8:], key)

    def _decode_keyblocks(self, keyblock_compressed: bytes,
            keyblockinfo_list: list[tuple[int, int]]):
        key_list: list[tuple[int, bytes]] = []
        i = 0
        for compressed_size, decompressed_size in keyblockinfo_list:
            start = i
            end = i + compressed_size
            # 4 bytes : compression type
            keyblock_type = keyblock_compressed[start:start+4]
            # print(f"keyBlockTypeStr: {keyBlockTypeStr}")

            # 4 bytes : adler checksum in decompressed key block
            adler32 = cast(int, struct.unpack('>I', keyblock_compressed[start+4:start+8])[0])

            # print(f"strt: {start}, end: {end}")
            key_block = self._decompress(keyblock_type,
                keyblock_compressed[start: end], decompressed_size)
            # print(f"key_block: {key_block.join()}")
            assert adler32 == zlib.adler32(key_block) & 0xffffffff

            # extract one single key block into a key list
            key_list += self._decode_keyblock(key_block)

            i += compressed_size

        # print(f"len in keyblock_list = {len(key_list)}")
        return key_list

    def _decode_keyblock(self, key_block: bytes):
        key_list: list[tuple[int, bytes]] = []
        keystrt_idx = 0
        keyend_idx = 0
        while keystrt_idx < len(key_block):
            # the corresponding record's offset in record block
            key_id = cast(int, struct.unpack(self._num_format,
                key_block[keystrt_idx:keystrt_idx+self._width_num])[0])
            # key text ends with '\x00'
            if self._encoding == 'UTF-16':
                delimiter = b'\x00\x00'
                width = 2
            else:
                delimiter = b'\x00'
                width = 1
            i = keystrt_idx + self._width_num
            while i < len(key_block):
                if key_block[i:i+width] == delimiter:
                    keyend_idx = i
                    break
                i += width
            key_text = key_block[keystrt_idx+self._width_num: keyend_idx] \
                .decode(self._encoding, errors='ignore')
            # print('keyText1 =', keyText1)
            key_bytes = key_text.encode('utf-8').strip()
            keystrt_idx = keyend_idx + width
            key_list += [(key_id, key_bytes)]
        return key_list

    def _decode_mdd_recordblock(self):
        with open(self._srcfile, 'rb') as f:
            _ = f.seek(self._file_pos)

            size_counter = 0

            recordblocks_num = self._read_number(f)
            entries_num = self._read_number(f)
            assert entries_num == self._entries_num

            recordblockinfo_size = self._read_number(f)
            recordblock_size = self._read_number(f)

            # record block info section
            recordblockinfo_list: list[tuple[int, int]] = []
            for i in range(recordblocks_num):
                compressed_size = self._read_number(f)
                decompressed_size = self._read_number(f)
                recordblockinfo_list += [(compressed_size, decompressed_size)]
                size_counter += self._width_num * 2
            assert size_counter == recordblockinfo_size

            # actual record block
            offset = 0
            i = 0
            size_counter = 0
            for compressed_size, decompressed_size in recordblockinfo_list:
                compressblock_strt = f.tell()
                # compressblock_strt = f.read(compressed_size)
                recordblock_compressed = f.read(compressed_size)
                # 4 bytes: compression type
                recordblock_type = recordblock_compressed[:4]
                # 4 bytes: adler32 checksum in decompressed record block
                adler32 = cast(int, struct.unpack('>I', recordblock_compressed[4:8])[0])

                # recordBlockTypeStr = recordblock_type.join()
                record_block = self._decompress(recordblock_type,
                    recordblock_compressed, decompressed_size)
                # notice that adler32 return signed value
                assert adler32 == zlib.adler32(record_block) & 0xffffffff

                assert len(record_block) == decompressed_size

                # split record block according to the offset info from key block
                while i < len(self._keyblock_list):
                    record_strt, key_bytes = self._keyblock_list[i]
                    # reach the end in current record block
                    if record_strt - offset >= len(record_block):
                        break

                    # record end index
                    if i < len(self._keyblock_list) - 1:
                        record_end = self._keyblock_list[i + 1][0]
                    else:
                        record_end = len(record_block) + offset
                    i += 1

                    # yield key_text, data
                    info = record_strt-offset, record_end-offset, \
                        compressblock_strt, compressed_size, decompressed_size
                    self._record_dict[key_bytes.decode("UTF-8")] = info

                offset += len(record_block)
                size_counter += compressed_size

            assert size_counter == recordblock_size

    def _decode_mdx_recordblock(self):
        with open(self._srcfile, 'rb') as f:
            _ = f.seek(self._file_pos)

            recordblocks_num = self._read_number(f)
            # print(f"int in Record Blocks = { recordblocks_num }")

            entries_num = self._read_number(f)
            assert entries_num == self._entries_num

            recordblockinfo_size = self._read_number(f)
            # print(f"recordblockinfo_size = { recordblockinfo_size }")

            recordblock_size = self._read_number(f)
            # print(f"recordblock_size = { recordblock_size }")

            # print(f"mid in file = {f.tell()}")

            # record block info section
            recordblockinfo_list: list[tuple[int, int]] = []
            size_counter: int = 0
            for i in range(recordblocks_num):
                compressed_size = self._read_number(f)
                decompressed_size = self._read_number(f)
                recordblockinfo_list += [(compressed_size, decompressed_size)]
                size_counter += self._width_num * 2

            assert size_counter == recordblockinfo_size

            # actual record block data
            offset = 0
            i = 0
            size_counter = 0
            for compressed_size, decompressed_size in recordblockinfo_list:
                compressblock_strt = f.tell()
                # print(f"compressblock_strt = { compressblock_strt }")
                recordblock_compressed = f.read(compressed_size)
                # 4 bytes indicates block compression type
                recordblock_type = recordblock_compressed[: 4]
                # 4 bytes adler checksum in uncompressed content
                adler32 = cast(int, struct.unpack('>I', recordblock_compressed[4:8])[0])

                record_block = self._decompress(recordblock_type,
                    recordblock_compressed, decompressed_size)

                # notice that adler32 return signed value
                assert adler32 == zlib.adler32(record_block) & 0xffffffff

                assert len(record_block) == decompressed_size

                # split record block according to the offset info from key block
                # for word, record_strt in self._KeyDict.items():
                while i < len(self._keyblock_list):
                    record_strt, key_text = self._keyblock_list[i]

                    # reach the end in current record block
                    if record_strt - offset >= len(record_block):
                        break

                    # record end index
                    if i < len(self._keyblock_list) - 1:
                        record_end = self._keyblock_list[i + 1][0]
                    else:
                        record_end = len(record_block) + offset

                    i += 1

                    info = record_strt-offset, record_end-offset, \
                        compressblock_strt, compressed_size, decompressed_size
                    self._record_dict[key_text.decode("UTF-8")] = info

                offset += len(record_block)
                size_counter += compressed_size

            assert size_counter == recordblock_size

    def _substitute_stylesheet(self, txt: str):
        txt_list: list[str] = re.split(r'`\d+`', txt)
        txt_tag = re.findall(r'`\d+`', txt)
        txt_styled = txt_list[0]
        for j, p in enumerate(txt_list[1:]):
            style = self._stylesheet[txt_tag[j][1:-1]]
            if p and p[-1] == '\n':
                txt_styled += style[0] + p.rstrip() + style[1] + '\r\n'
            else:
                txt_styled += + style[0] + p + style[1]
        return txt_styled

    def _decompress(self, compr_type: bytes, compr_block: bytes, decompr_size: int) -> bytes:
        match compr_type:
            case b'\x00\x00\x00\x00':    # no compression
                return compr_block[8:]
            case b'\x01\x00\x00\x00':   # lzo compression
                if lzo is None:
                    raise RuntimeError("LZO compression is not supported")
                # decompress
                header = b'\xf0' + struct.pack('>I', decompr_size)
                return lzo.decompress(header + compr_block[8:])
            case b'\x02\x00\x00\x00':   # zlib compression
                return zlib.decompress(compr_block[8:])
            case _:
                raise NotImplementedError(f"Don't suport type in compression: {compr_type}")
