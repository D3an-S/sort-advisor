import pathlib, random
random.seed(42)
d = pathlib.Path("security_tests"); d.mkdir(exist_ok=True)
w = lambda name, text: (d / name).write_text(text, encoding="utf-8")

w("t1_script_spaltenname.csv", "<script>alert('xss')</script>,<img src=x onerror=alert(1)>\n3,a\n1,b\n2,c\n")
w("t2_html_in_zellen.csv", "wert\n<b>fett</b>\n[Link](http://example.com)\n<script>alert(1)</script>\n")
w("t3_formel.csv", 'wert\n"=HYPERLINK(""http://example.com"";""Klick"")"\n=1+1\n@SUM(1)\n')
w("t4_ueber_5mb.csv", "wert\n" + "1234567890\n" * 600_000)
w("t5_150k_zeilen.csv", "wert\n" + "\n".join(str(random.random()) for _ in range(150_000)))
w("t6_leer.csv", "")
(d / "t7_kein_csv.csv").write_bytes(bytes(range(256)) * 50)
w("t8_wahrheitswerte.csv", "flag\nTrue\nFalse\nTrue\n")
w("t9_absteigend_100k.csv", "wert\n" + "\n".join(str(i) for i in range(100_000, 0, -1)))