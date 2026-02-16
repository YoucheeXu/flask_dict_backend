#!/usr/bin/python3
# -*- coding: utf-8 -*-
''' Dictbase for google
'''
import os
import json
from html import unescape
import codecs
import re
from typing import override, Any

from src.components.classbases.dictbase import DictBase
from src.components.classbases.ziparchive import ZipArchive


class GDictBase(DictBase):
    # TODO: autodetect zip format
    def __init__(self):
        super().__init__()
        self._dictzip: ZipArchive = ZipArchive()
        self._stylezip: ZipArchive = ZipArchive()

    @override
    def open(self, name: str, src: str) -> tuple[int, str]:
        _ = super().open(name, src)
        filepath, filename = os.path.split(self._src)
        name, _ = os.path.splitext(filename)
        stylesrc = os.path.join(filepath, name + "-style.zip")
        _ = self._stylezip.open(stylesrc)

        # TODO: change to extract all files automatically
        jsname = "google-toggle.js"
        jsfile = os.path.join(self._tempdir, jsname)
        # print(f"jsfile = {jsfile}")
        if not os.path.isfile(jsfile):
            if self._stylezip.has_file(jsname):
                data = self._stylezip.read_file(jsname)
                # if data is None:
                    # return -1, f"Fail to read {jsname} in {self.__stylezip}"
                with open(jsfile, "wb") as f:
                    _ = f.write(data)
        cssname = "google.css"
        cssfile = os.path.join(self._tempdir, cssname)
        # print(f"cssfile = {cssfile}")
        if not os.path.isfile(cssfile):
            if self._stylezip.has_file(cssname):
                data = self._stylezip.read_file(cssname)
                # if data is None:
                    # return -1, f"Fail to read {cssname} in {self.__stylezip}"
                with open(cssfile, "wb") as f:
                    _ = f.write(data)

        if self._download is not None:
            self._download["SavePath"] = os.path.join(self._tempdir, "{}.json")

        return self._dictzip.open(self._src)

    @override
    def close(self) -> bool:
        _ = self._dictzip.close()
        return super().close()

    @override
    def query_word(self, word: str) -> tuple[int, str]:
        htmlfile = os.path.join(self._tempdir, word + ".html")
        if os.path.isfile(htmlfile):
            return 1, htmlfile

        dictjson = ""
        msg = ""
        # filename = os.path.join(word[0], word + ".json")
        filename = word[0].lower() + "/" + word + ".json"
        if self._dictzip.has_file(filename):
            dictjson = str(self._dictzip.read_file(filename),'utf-8')
        elif self._download is not None:
            json_url = (self._download["URL"]).format(word)
            json_url = json_url.replace(" ", "%20")
            return 0, str(json_url)
        else:
            msg = f"no word '{word}' in '{self._name}'"
            return -1, msg

        if dictjson:
            inword = self._get_inword(dictjson)

            if inword:
                if inword != word:
                    msg = f"word '{word}', wrong word '{inword}' in '{self._name}'"
                    return -1, msg
            else:
                msg = f"no word '{word}' in '{self._name}'"
                return -1, msg

        else:
            msg = f"Fail to read json '{word}' in '{self._name}'"
            return -1, msg

        # print("%s = %s" %(word, dict))

        if dictjson:
            dictdata: dict[str, Any] = json.loads(dictjson, strict=False)
            if dictdata["ok"]:
                info = dictdata["info"]
                ret = self._parse_json(info, htmlfile)
                # print("%s = %s" %(word, dict))
                if ret:
                    return 1, htmlfile
                return -1, f"Fail to parse '{word}' in '{self._name}'"
        else:
            msg = f"Fail to read word '{word}' in '{self._name}'"
            return -1, msg

        msg = "Unknown error!"
        return -1, msg

    def _get_inword(self, dictjson: str) -> str:

        data: dict[str, Any] = json.loads(dictjson, strict = False)

        if data["ok"]:
            info: str = data["info"]
            # print(info)
            # GetApp().log("info", info)
            # regex = re.compile(r'\\(?![/u"])')
            # info_fixed = regex.sub(r"\\\\", info)
            # GetApp().log("info", info_fixed)
            # data = json.loads(info_fixed, strict = False)
            # info = info.replace('\\"', '"')
            # info = info.replace('/', '')
            info = info.replace('\\', '\\\\')
            data = json.loads(info, strict = True)
            return data["primaries"][0]["terms"][0]["text"]

        return ""

    def _process_primary(self, tabalign: str, dict_primary: Any) -> str:
        primary = dict_primary
        xml: str = ""
        html: str = ""
        is_meaning = False
        if isinstance(primary, list):
            for data in primary:
                html = self._process_primary(tabalign, data)
                # console.log("html1: " + html + "")
                if html[0] == "<":
                    xml += "\n" + tabalign
                xml += html
        elif isinstance(primary, dict):
            # let hasChild = false
            # let hastyp = false
            if "type" in primary:
                # hastyp = True
                if primary["type"] == "container":
                    # print(primary)
                    xml += f'{tabalign}<div class = "wordtyp">{primary["labels"][0]["text"]}: </div>\n'
                    xml += tabalign + "<div class = '" + primary["type"] + "1'>\n"
                    tabalign += "\t"
                    entries = primary["entries"]
                    html = self._process_terms(tabalign, entries[0]["terms"], entries[0]["type"])
                    if html[0] == "<":
                        xml += "\n" + tabalign
                    xml += html
                else:
                    if "labels" in primary:
                        # if(xml.substr(-1, 1) == ">"){
                        # xml += "\n"
                        # }
                        xml += f"{tabalign}<div class = '{primary["type"]}'>"
                        tabalign += "\t"
                        xml += f"\n{tabalign}<div class = 'labels'>{primary['labels'][0]['text']}</div>"
                        html = self._process_terms(tabalign, primary["terms"], primary["type"])
                        if html[0] == "<":
                            xml += "\n" + tabalign
                        xml += html
                    else:
                        if primary["type"] == "meaning":
                            is_meaning = True
                        if primary["type"] == "example" and is_meaning:
                            xml += "\n"
                            is_meaning = False
                        xml += f"{tabalign}<div class = '{primary["type"]}'>"
                        tabalign += "\t"
                        html = self._process_terms(tabalign, primary["terms"], primary["type"])
                        if html[0] == "<":
                            xml += "\n" + tabalign
                        # console.log("html4: " + html + "")
                        xml += html
                if "entries" in primary:
                    html = self._process_primary(tabalign, primary["entries"])
                    # console.log("html: " + html + "")
                    # console.log("xml: " + xml + "")
                    # console.log("html2: " + html + "")
                    if html[0] == "<":
                        xml += "\n" + tabalign + "Q: "
                    xml += html
                # xml += tabalign + "</div>\n"
                tabalign = tabalign[0]
                # console.log(xml.substr(-3, 3))
                if xml[-3] == ">":
                    xml += tabalign
                if xml[-1] == ">":
                    xml += "\n" + tabalign
                xml += "</div>\n"
                # tabalign = tabalign.slice(0, -2)
        elif isinstance(primary, str):
            html = self._process_primary(tabalign, json.loads(primary, strict=False))
            # console.log("html3: " + html + "")
            xml += html
        return xml

    def _process_terms(self, tabalign: str, dict_terms: Any, typ: str) -> str:
        terms = dict_terms
        xml: str = ""
        html: str = ""
        if isinstance(terms, list):
            for data in terms:
                # data = terms[i]
                html = self._process_terms(tabalign, data, typ)
                # if(html.slice(0,1) == "<"){
                # xml += "\n" + tabalign
                # }
                xml += html
        elif isinstance(terms, dict):
            # let hastyp = false
            if "type" in terms:
                # hastyp = True
                if terms["type"] != "text" or typ == "headword" or typ == "related":
                    if terms["type"] == "sound":
                        '''xml += '<div class="'+ terms["type"] + '">'
                        # xml += terms["text"] +"</div>"
                        xml += '<embed typ="application/x-shockwave-flash" src="SpeakerApp16.swf"' +
                            'width="20" height="20" id="movie28564" name="movie28564" bgcolor="#000000"' +
                            'quality="high" flashlets="sound_name='+ terms["text"] + '"wmode="transparent">'
                        xml += "</div>"'''
                        # alert(terms["text"])
                        xml += self._get_sound(tabalign, terms["text"])
                    else:
                        # console.log("P: " + xml)
                        # if(xml.substr(-1, 1) == ">"){
                        # xml += "\n" + tabalign
                        # }
                        xml += f"\n{tabalign}<div class = '{terms["type"]}'>{terms['text']}</div>"
                else:
                    xml += f"{terms["text"]}"
        return xml

    '''
    def process_term(dict_terms: Any) str:
        terms = dict_terms

        xml = ""
        for (let i in terms)
            let data = terms[i]
            xml += (data["text"])
        }
        return xml
    }
    '''

    def _get_sound(self, tabalign: str, url: str) -> str:
        sound = \
            '\n' + \
            tabalign + \
            "<div class = 'sound' id = 'Player'>\n" + \
            tabalign + \
            '\t' + \
            "<button class = 'jp-play' id = 'playpause' title = 'Play'></button>\n" + \
            tabalign + \
            '\t' + \
            "<audio id = 'myaudio'>\n" + \
            tabalign + \
            '\t' + \
            '\t' + \
            '<source src = ' + \
            url + \
            " typ= 'audio/mpeg'>\n" + \
            tabalign + \
            '\t' + \
            '\t' + \
            'Your browser does not support the audio tag.\n' + \
            tabalign + \
            '\t' + \
            '</audio>\n' + \
            tabalign + \
            '</div>'
        return sound

    def _parse_json(self, json_str: str, htmlfile: str) -> bool:
        # regex = re.compile(r'\\(?![/u"])')
        # info_fixed = regex.sub(r"\\\\", info)
        # dict = info_fixed
        # info = str(info).replace(/\\x/g, "\\u00")
        jsonstr =  json_str.replace("\\x", "\\u00")
        obj = json.loads(jsonstr, strict = True)
        tabalign = '\t\t'
        dictdata = self._process_primary(tabalign, obj["primaries"])
        # dictdata = unescape(dictdata.replace("\\", "&#"))
        # dictdat_bytes = dictdata.encode('utf-8', errors='replace')
        # print(f"dictdata = {dictdata}")
        # decoded_once  = codecs.decode(dictdata, 'unicode_escape', errors='replace')
        # dictdata = decoded_once.encode('utf-8', errors='replace').decode('utf-8', errors='replace')

        jsname = "google-toggle.js"
        cssname = "google.css"

        css = tabalign + '<link rel="stylesheet" href="../../../assets/player.css">' + '\n'
        css += tabalign + f"<link rel='stylesheet' typ='text/css' href='{cssname}'>"

        js = tabalign + '<script src="../../../assets/player.js"></script>' + '\n'
        js += tabalign + f"<script src='{jsname}'></script>"
        togeg = tabalign + '<div id="toggle_example" align="right">- Hide Examples</div>'
        html = f"<!DOCTYPE html>\n<html>\n\t<body>\n{css}\n{js}\n{togeg}\n{dictdata}\n\t</body>\n</html>"
        with open(htmlfile, 'w', encoding="UTF-8") as f:
            _ = f.write(html)
        return True

    @override
    def check_addword(self, localfile: str) -> tuple[int, str]:
        basename = os.path.basename(localfile)
        word, _ = os.path.splitext(basename)
        filename = word[0].lower() + "/" + word + ".json"
        if os.path.isfile(localfile):
            with open(localfile, "r", encoding="utf-8") as f:
                dictjson = f.read()
                inword = self._get_inword(dictjson)

                # os.remove(localfile)

                if inword != "":
                    if inword == word:
                        _ = self._dictzip.add_file(filename, dictjson)
                        return 1, f"OK to add '{word}' to {self._name}"
                    return 0, f"expected word: {word}, inword: {inword}"

                return -1, f"No valid data in {localfile}"

        return -1, f"No file {localfile}"

    @override
    def get_wordlist(self, word: str, limit: int = 100):
        word_list: list[str] = []
        # filename = word[0] + "/" + word + ".*\.json"
        pattern = "^" + word + ".*"
        # print("Going to find: " + fileName)
        _ = self._dictzip.search_file(pattern, word_list)

        for i in range(len(word_list)):
            word_list[i] = word_list[i][2: -5]
            if i > limit:
                break

        return word_list

    @override
    def del_word(self, word: str) -> bool:
        filename = word[0] + "/" + word + ".json"
        return self._dictzip.del_file(filename)
