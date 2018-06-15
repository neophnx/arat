(for i in standalone.py `find server -name '*.py'` `find tests -name '*.py'` ; do echo -en "$i ";  python3 -m pylint $i 2>/dev/null |tail -2 |head -1 |cut -d " " -f 7; done ) | tee pylint.scores.txt
sort -n -k2 pylint.scores.txt > pylint.scores.sorted.txt

