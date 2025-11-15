http://127.0.0.1:5000/dicts/古汉语常用字字典[第5版]/output/好.html

http://127.0.0.1:5000/public/dicts/Google/output/good-error.html

http://127.0.0.1:5000//dicts/Google/output/able.html
=> http://127.0.0.1:5000/public/dicts/Google/output/able.html

http://127.0.0.1:5000/public/dicts/assets/player.js 

<link rel="stylesheet" type="text/css" href="{{ url_for('vendor.static', filename='vendor.css') }}">
<script src="{{ url_for('vendor.static', filename='vendor.js') }}"></script>
在上述示例中，url_for('vendor.static', filename='vendor.css') 会生成一个类似于 “/vendor/static/vendor.css” 的 URL，用于引用 “vendor” 文件夹中的 “vendor.css” 文件。

<link rel="stylesheet" type="text/css" href="{{ url_for('static', filename='style.css') }}">
<script src="{{ url_for('static', filename='script.js') }}"></script>
< img src="{{ url_for('static', filename='image.jpg') }}" alt="Static Image">
上述示例中，url_for('static', filename='style.css') 会生成一个类似于 “/static/style.css” 的 URL，用于引用名为 “style.css” 的 CSS 文件。同样地，我们可以使用该方法链接 JavaScript 文件和图像文件。

put download to the dir of dict.

## TODO

- [ ] download dict / audio file
- [ ] user progress file
- [ ] 
